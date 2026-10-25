# Testing strategy (target application)

**Last verified: 2026-10-24.** Testing the migrated application is mandatory. This is separate from the skill's own `tests/` (which only test the skill's scripts). Every result goes into `test-results.json` ([results-report-format.md](results-report-format.md)).

## Status vocabulary

| Status | Use when |
|---|---|
| `passed` | The command ran, exit code 0, and the output shows success. Evidence recorded. |
| `failed` | The command ran and reported failures (non-zero exit, or failures in output). |
| `skipped` | Deliberately not run because it does not apply (e.g. no DB in a static site). Reason required. |
| `blocked` | Should run but could not: missing runtime, service, tool, permission, network. Reason required. |
| `not_run` | Not attempted (yet). No command, no exit code. |

## Layers

### 1. Structural (`layer: structural`)

| Test name | Command (adapt) | Notes |
|---|---|---|
| `composer_validate` | `composer validate --strict` | Lock freshness and schema |
| `lock_consistency` | `composer install --dry-run` on a clean checkout | No changes expected |
| `syntax_check` | `find . -name '*.php' -not -path './vendor/*' -print0 \| xargs -0 -n1 -P4 php -l` with the **target** PHP | Windows: `Get-ChildItem -Recurse -Filter *.php \| ? FullName -notmatch '\\vendor\\' \| % { php -l $_.FullName }` |
| `framework_config` | framework-specific (see [framework-test-commands.md](framework-test-commands.md)) | e.g. `bin/console lint:container`, `php artisan config:cache` dry run |

### 2. Security (`layer: security`)

| Test name | Command | Notes |
|---|---|---|
| `advisory_recheck` | fetch php.net archive + GHSAs | Record as `advisories_checked` entries |
| `runtime_version_check` | `php -v` / `php-fpm -v` of the target runtime, then `scripts/check-php-version.py` | Required for `runtime_patch_verified` |
| `dependency_audit` | `composer audit` (CMS: see framework reference) | Non-zero exit = advisories found → `failed`, list as findings |
| `platform_reqs` | `composer check-platform-reqs` | Extensions and PHP match |
| `deployment_config` | re-run `scripts/detect-project.py`; review Dockerfile/CI/FPM | No `deployment_mismatch` |
| `web_runtime_check` | see [security-verification.md](security-verification.md) | Required for `web_runtime_verified` |

### 3. Static analysis (`layer: static_analysis`)

Run only tools the project can support; mark others `skipped` with reason.

- PHPStan: `vendor/bin/phpstan analyse --no-progress` (project config; set `phpVersion` for the target).
- Rector: `vendor/bin/rector process --dry-run`, where remaining suggested changes mean incomplete migration.
- PHPCompatibility: `vendor/bin/phpcs --standard=PHPCompatibility --runtime-set testVersion <target>- <paths>`.
- PHP_CodeSniffer project standard: `vendor/bin/phpcs`.

Comparing against a baseline is fine (existing errors before migration). New errors are regressions.

### 4. Automated tests (`layer: automated_tests`)

Named `test_suite` (required for `verified`). Run the project's real suite on the **target runtime**: `vendor/bin/phpunit`, `vendor/bin/pest`, `php artisan test`, `bin/phpunit`, framework/CMS runners. Make sure the suite covers, or record gaps for: unit, integration, DB-backed, HTTP/API, auth/authz, uploads/storage, jobs/scheduler, cache/sessions, business-critical flows. If no runner exists: `blocked` ("no test runner in project"). Offer to add characterisation tests, but do not invent passing results.

### 5. Runtime (`layer: runtime`)

In a test environment, with the intended runtime: start the app (container/compose), check health endpoints, run HTTP smoke tests (`http_smoke`), check logs for errors/deprecations, confirm extensions (`php -m` in the container), build and run the deployment image if one exists.

### 6. Regression and DB (`layer: regression`)

Compare against the Phase 1 baseline (same tests, before vs after). Run migrations on a disposable DB ([../migration/database-migrations.md](../migration/database-migrations.md)). Check API contracts (response codes/shapes for key endpoints) and integrations (sandbox credentials only).

## Interpreting results honestly

- `php -l` passing proves syntax only.
- Passing unit tests do not prove the runtime is patched.
- A patched CLI does not prove the web runtime is patched.
- A green run with 5 tests in a 50k-line app is weak evidence. Say so in limitations.
