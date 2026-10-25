# Example: WordPress behind nginx + PHP-FPM 8.1

> Uses the synthetic fixture `tests/fixtures/wordpress`. The detector output below is **real output** from running the bundled script on that fixture (2026-10-24). The remediation steps are illustrative.

## 1. Detection (actual output)

```text
$ python3 scripts/detect-project.py tests/fixtures/wordpress
[.]
  WordPress 6.9.1 - confidence high; lifecycle supported (cycle 6.9, latest 6.9.10, PHP see docs)
    - version string in wp-includes/version.php
    - marker wp-includes/version.php
    - marker wp-load.php
    - supporting marker wp-config.php
  test tooling: none found -> no test runner: automated tests will be 'blocked' until one exists
  runtime[web] PHP 8.1 from deploy/nginx.conf: runtime_unsupported

Findings:
  [high] runtime_unsupported: web runtime PHP 8.1 declared in deploy/nginx.conf is runtime unsupported
```

The fixture's `wp-config.php` contains (fake) credentials. They do not appear anywhere in the output; the test suite asserts this.

## 2. Interpretation

- Category 2 (`runtime_unsupported`): `fastcgi_pass unix:/run/php/php8.1-fpm.sock` points at PHP 8.1, which php.net no longer patches. On Debian/Ubuntu the `php8.1-fpm` package may carry a vendor backport. Collect the package changelog (`apt changelog php8.1-fpm | grep CVE-2026-109618`) before deciding how urgent containment is. Either way, migrate.
- WordPress 6.9.1 is behind the 6.9.x line (6.9.10 is latest per endoflife.date). Update it in the same maintenance window, as a separate step.
- No test runner: the `test_suite` result will be `blocked`, and smoke tests carry the weight.

## 3. Plan (abridged)

1. Staging copy (files + DB). Run `wp core verify-checksums` and `wp plugin list --update=available`.
2. Check every plugin's `Requires PHP` / changelog for PHP 8.4. Run PHPCompatibilityWP over `wp-content/plugins` and `wp-content/themes` (report only).
3. Install `php8.4-fpm` with the extensions WordPress needs; create the pool; switch `fastcgi_pass` to `php8.4-fpm.sock`; reload nginx; restart FPM.
4. `wp core update` (6.9.x latest), `wp plugin update <slug>` one at a time for critical plugins, `wp core update-db`.
5. Smoke tests: home, post, search, login, admin, forms, checkout (if WooCommerce, with sandbox payment). Review `debug.log`.
6. Verify the web runtime: Tools → Site Health → Info → Server shows the PHP version without `phpinfo()`, or run `php-fpm8.4 -v` on the host.

## 4. Report excerpt (plan stage: nothing executed yet)

```json
{
  "skill": "php2shell-migration",
  "summary": "Plan prepared; no changes executed yet.",
  "project": {"name": "fixture-wordpress", "framework": "wordpress", "framework_version_before": "6.9.1", "framework_version_after": null,
              "php_version_before": "8.1", "php_version_after": null},
  "security": {"advisories_checked": [{"id": "CVE-2026-109618", "source": "https://www.php.net/archive/2026.php", "checked_on": "2026-10-24", "result": "verified"}],
               "runtime_patch_verified": false, "web_runtime_verified": false,
               "remaining_findings": [{"id": "rt-1", "category": "runtime_unsupported", "severity": "high", "description": "nginx config points at PHP 8.1 FPM (EOL branch)."}]},
  "migration": {"status": "planned", "files_changed": [], "database_changes": [], "rollback_available": false},
  "tests": [
    {"name": "syntax_check", "layer": "structural", "status": "not_run", "command": null, "exit_code": null, "summary": "", "evidence": []},
    {"name": "test_suite", "layer": "automated_tests", "status": "blocked", "command": null, "exit_code": null, "summary": "No test runner exists in the project.", "evidence": []},
    {"name": "web_runtime_check", "layer": "runtime", "status": "blocked", "command": null, "exit_code": null, "summary": "No access to the serving host from this environment.", "evidence": []}
  ],
  "limitations": ["No host access: the serving runtime is known only from deploy/nginx.conf.", "No automated tests in the project."],
  "overall_result": "blocked"
}
```
