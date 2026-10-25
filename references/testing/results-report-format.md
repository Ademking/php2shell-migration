# Results report format

**Last verified: 2026-10-24.** Every migration attempt (including a plan-only or blocked one) produces:

1. `test-results.json`: machine-readable, schema [../../templates/test-results.schema.json](../../templates/test-results.schema.json), starting from [../../templates/test-results.json](../../templates/test-results.json).
2. `test-results.md`: rendered by `python3 scripts/validate-results.py test-results.json --markdown test-results.md` (rendering only happens if the report is valid).
3. `migration-report.md`: narrative from [../../templates/migration-report.md](../../templates/migration-report.md).

## Fields

| Field | Meaning |
|---|---|
| `project.*` | Name, framework id (detector id or `custom`), versions before/after. `null` when unknown. Never guess. |
| `security.advisories_checked[]` | `{id, source, checked_on, result}` with `result` ∈ `verified` (read from the source during this run), `unreachable`, `not_checked`. |
| `security.runtime_patch_verified` | Intended runtime's patch status observed this run. |
| `security.web_runtime_verified` | The runtime serving HTTP observed this run. |
| `security.remaining_findings[]` | `{id, category, severity, description}`, with category ∈ `runtime_affected`, `runtime_unsupported`, `framework_outdated`, `dependency_vulnerable`, `deployment_mismatch`, `status_unknown`, `dependency_inconsistent`, `other`; severity ∈ `critical`, `high`, `medium`, `low`, `info`. |
| `migration.status` | `not_started`, `planned`, `in_progress`, `completed`, `partially_completed`, `failed`, `rolled_back`, `not_required`. |
| `migration.files_changed`, `database_changes`, `rollback_available`, `branch`, `rollback_procedure` | What changed and how to undo it. |
| `tests[]` | `{name, layer, status, command, exit_code, summary, evidence[], limitations[]}`. `layer` ∈ `structural`, `security`, `static_analysis`, `automated_tests`, `runtime`, `regression`. |
| `limitations[]` | Environmental limits, skipped scope, unverifiable items. |
| `overall_result` | See R10. |

### Test status values

`passed`, `failed`, `skipped`, `blocked`, `not_run`. See [testing-strategy.md](testing-strategy.md#status-vocabulary).

### Overall result values

| Value | Permitted exactly when (R10) |
|---|---|
| `failed` | At least one test is `failed`. |
| `blocked` | No test failed, none passed, and at least one is `blocked`. |
| `not_verified` | No test failed, none passed, none blocked (everything `not_run`/`skipped`, or no tests). |
| `verified` | No `failed`/`blocked`/`not_run` tests, **and** `syntax_check`, `dependency_audit`, `test_suite`, `runtime_version_check`, `web_runtime_check` all `passed`, **and** `runtime_patch_verified` and `web_runtime_verified` are true, **and** `remaining_findings` is empty, **and** `migration.status` is `completed` or `not_required`, **and** every `advisories_checked` entry is `verified` (at least one). |
| `partially_verified` | Anything else with at least one passed test. |

`verified` means "everything in scope was checked and passed". It never means "secure".

## Validation rules (enforced by `scripts/validate-results.py`)

- **R1**: Structure matches the JSON schema (types, required keys, enums).
- **R2**: Test names are unique.
- **R3**: `passed`/`failed` tests have the actual executed `command` and an integer `exit_code`.
- **R4**: `passed` tests have `exit_code` 0 and at least one `evidence` entry (output excerpt, log path, artefact).
- **R5**: `not_run` tests have `command: null` and `exit_code: null`.
- **R6/R7**: `skipped`, `blocked` and `failed` tests have a non-empty `summary` giving the reason.
- **R8**: `runtime_patch_verified: true` requires a passed `runtime_version_check`.
- **R9**: `web_runtime_verified: true` requires `runtime_patch_verified` and a passed `web_runtime_check`. A CLI check cannot set it.
- **R10**: `overall_result` equals the value derived above.
- **R11**: `verified` requires advisory entries.
- **R12** (warning): `completed` migration without rollback.
- **R13**: Summaries must not claim the application is "fully/completely/100% secure" or has "no vulnerabilities".
- **R14**: Any `skipped`/`blocked`/`not_run` test requires at least one `limitations` entry.

## Evidence guidelines

Good evidence: `"PHP 8.4.27 (fpm-fcgi) observed via docker compose exec app php-fpm -v"`, `"phpunit: Tests: 412, Assertions: 1630, OK (log: build/phpunit.log)"`, `"composer audit: No security vulnerability advisories found"`. Truncate long output; never include secrets or full environment dumps.

## Example (excerpt)

```json
{
  "name": "test_suite",
  "layer": "automated_tests",
  "status": "blocked",
  "command": null,
  "exit_code": null,
  "summary": "No test runner configured (no phpunit.xml, no tests/ directory).",
  "evidence": []
}
```
