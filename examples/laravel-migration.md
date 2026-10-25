# Example: Laravel 11 on PHP 8.2.20 (illustrative)

> **Illustrative walk-through.** The project, commands and outputs below are a constructed scenario that shows how the skill should behave. They are not results from a real system. The JSON report at the end is validated by the skill's test suite.

## Situation

- App: `acme-portal`, Laravel 11.57.0 (from `composer.lock`), `require.php: ^8.2`.
- Dockerfile: `FROM php:8.2.20-fpm-bookworm`. CI: `php-version: '8.3'`. The developer laptop has PHP 8.4.27.
- Tests: PHPUnit suite (420 tests), Larastan configured.
- Access: repository and a staging Docker host. No production access.

## 1. Facts

```sh
python3 scripts/detect-project.py . --output detect.json
python3 scripts/check-php-version.py "8.2.20" --sapi fpm-fcgi   # exit 2: runtime_affected (fixed in 8.2.35)
```

Findings recorded:

- `runtime_affected` (critical): the web runtime is 8.2.20, and CVE-2026-109618/109619 are fixed in 8.2.35.
- `framework_outdated` (high): Laravel 11 security support ended 2026-03-12 (endoflife.date, verified 2026-10-24).
- `deployment_mismatch` (medium): CI tests on 8.3 while production runs 8.2, so the tests do not exercise the deployed runtime.
- PHP 8.2 itself leaves security support on 2026-12-31 (php.net).

## 2. Plan (abridged)

| Stage | Change | Why |
|---|---|---|
| 1 | Dockerfile → `php:8.2.35-fpm-bookworm`; CI matrix adds `8.2.35` | Immediate PHP2Shell fix, no code change |
| 2 | Laravel 11 → 12 (upgrade guide 12.x) | 11 is EOL; 12 supports PHP 8.2 – 8.5 |
| 3 | PHP 8.2 → 8.4.27 (Dockerfile, CI, `config.platform.php`) | 8.2 EOL on 2026-12-31; 8.4 is in active support |
| 4 | Fix the deprecations surfaced on 8.4 | Implicitly nullable parameters, etc. |

Laravel 13 (PHP 8.3+) is a possible later stage, outside this migration's scope (recorded in the plan).

## 3. Execution highlights

- `git switch -c php2shell-migration-2026-10-24` (the working tree was clean).
- Stage 1 committed alone, so it can ship before the framework work.
- Stage 2: `composer require laravel/framework:^12.0 -W`, then reviewed the `composer.lock` diff; `vendor/bin/rector process --dry-run` with the rector-laravel 12 set; changes reviewed and committed separately.
- No `--ignore-platform-reqs`. `composer why-not php 8.4.27` showed one blocking package; it was updated to its next minor, which allows 8.4.

## 4. Results

The staging host was reachable, so the web runtime was observed with `docker compose exec app php-fpm -v` inside the staging stack. `composer audit` reported one moderate advisory in a transitive package with no fixed release yet, so the overall result is **failed** (rule R10), even though the runtime fix itself is verified.

```json
{
  "skill": "php2shell-migration",
  "summary": "PHP2Shell fixed on staging (8.4.27 FPM observed); Laravel 12; one dependency advisory open.",
  "project": {"name": "acme-portal", "framework": "laravel", "framework_version_before": "11.57.0", "framework_version_after": "12.70.1",
              "php_version_before": "8.2.20", "php_version_after": "8.4.27"},
  "security": {
    "advisories_checked": [
      {"id": "CVE-2026-109618", "source": "https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w", "checked_on": "2026-10-24", "result": "verified"},
      {"id": "CVE-2026-109619", "source": "https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp", "checked_on": "2026-10-24", "result": "verified"}
    ],
    "runtime_patch_verified": true,
    "web_runtime_verified": true,
    "remaining_findings": [
      {"id": "composer-audit-1", "category": "dependency_vulnerable", "severity": "medium", "description": "Transitive package advisory without a fixed release; tracked."}
    ]
  },
  "migration": {"status": "completed", "branch": "php2shell-migration-2026-10-24", "files_changed": ["Dockerfile", ".github/workflows/tests.yml", "composer.json", "composer.lock", "app/Providers/AppServiceProvider.php"],
                "database_changes": [], "rollback_available": true, "rollback_procedure": "Revert branch commits; redeploy previous image digest."},
  "tests": [
    {"name": "syntax_check", "layer": "structural", "status": "passed", "command": "find app config routes database tests -name '*.php' -print0 | xargs -0 -n1 php -l", "exit_code": 0, "summary": "No syntax errors", "evidence": ["0 files with errors (PHP 8.4.27)"]},
    {"name": "dependency_audit", "layer": "security", "status": "failed", "command": "composer audit", "exit_code": 1, "summary": "1 advisory (medium) in a transitive package", "evidence": ["composer audit: Found 1 security vulnerability advisory affecting 1 package"]},
    {"name": "runtime_version_check", "layer": "runtime", "status": "passed", "command": "docker compose exec app php -v", "exit_code": 0, "summary": "PHP 8.4.27 (cli) in the app image", "evidence": ["PHP 8.4.27 (cli) (built: ...)"]},
    {"name": "web_runtime_check", "layer": "runtime", "status": "passed", "command": "docker compose exec app php-fpm -v", "exit_code": 0, "summary": "PHP 8.4.27 (fpm-fcgi) serving staging", "evidence": ["PHP 8.4.27 (fpm-fcgi)"]},
    {"name": "static_analysis", "layer": "static_analysis", "status": "passed", "command": "vendor/bin/phpstan analyse --no-progress", "exit_code": 0, "summary": "No errors at configured level", "evidence": ["[OK] No errors"]},
    {"name": "test_suite", "layer": "automated_tests", "status": "passed", "command": "php artisan test", "exit_code": 0, "summary": "420 passed", "evidence": ["Tests: 420 passed (1611 assertions)"]}
  ],
  "limitations": ["Production runtime not observed (no access); verification covers staging only."],
  "overall_result": "failed"
}
```

Note `overall_result: "failed"`. The `composer audit` exit code was non-zero, so the test is `failed`, and rule R10 then forces `failed`. That is correct: the remaining advisory is real. The report would only become `partially_verified` if the team accepted the advisory, recorded it as a remaining finding, and re-ran the audit with a documented, justified `audit.ignore` entry. Never with the audit disabled.
