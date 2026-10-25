# Example: custom legacy PHP 5.6 application

> Uses the synthetic fixture `tests/fixtures/legacy-php`. The detector output is **real output** from the bundled script (2026-10-24). The plan is illustrative.

## 1. Detection (actual output)

```text
$ python3 scripts/detect-project.py tests/fixtures/legacy-php
[.]
  No known framework signature: treat as custom/unrecognized PHP (references/frameworks/other-php-projects.md)
  composer: php >=5.3; lock no; vendor no; ext -
  test tooling: none found -> no test runner: automated tests will be 'blocked' until one exists
  runtime[cli] PHP 5.6.40 from .php-version: runtime_unsupported

Findings:
  [high] runtime_unsupported: cli runtime PHP 5.6.40 declared in .php-version is runtime unsupported
  [low] dependency_inconsistent: composer.json without composer.lock: installed dependency versions cannot be established
  [high] status_unknown: No web runtime declaration found in source: the PHP version serving requests must be verified on the host
```

```text
$ python3 scripts/check-php-version.py 5.6.40
PHP 5.6.40: runtime_unsupported [branch eol]
  CVE-2026-109618: affected_unless_vendor_backport (fixed in no official release)
  CVE-2026-109619: affected_unless_vendor_backport (fixed in no official release)
  note: Branch receives no official PHP security releases: migrate to a supported branch (vendor backports are a temporary measure only).
```

## 2. Interpretation

- PHP 5.6 has no php.net backport (php.net published source backports only for 7.4, 8.0 and 8.1). Unless an LTS vendor covers this exact build, treat the runtime as **unpatchable**.
- The code uses `mysql_connect` and `ereg_replace`, both removed in PHP 7.0, so a direct jump to 8.x is impossible without code changes.
- The web runtime is unknown (status_unknown). It must be checked on the host.

## 3. Incremental plan (abridged)

| Stage | Goal | Key work | Exit criteria |
|---|---|---|---|
| 0 | Containment | Restrict access (VPN/IP allow-list), block multipart if unused, apply the php.net mitigations | Recorded as open findings |
| 1 | Safety net | Git repository; container on the current PHP; HTTP characterisation tests for the key URLs | Characterisation suite green on 5.6 |
| 2 | PHP 7.4 | `mysql_*` → PDO/mysqli, `ereg*` → `preg_*`; PHPCompatibility `testVersion 7.4` | Suite green on 7.4 |
| 3 | PHP 8.0 → 8.4 | Fix 8.0 semantic changes (string/number comparison), 8.1 null-to-internal deprecations, 8.2 dynamic properties | Suite green on 8.4.27 |
| 4 | Deploy (owner) | New image/package, restart workers, verify the web runtime | `web_runtime_verified` |

Blockers to confirm with the owner: hidden dependencies on removed extensions, and data stored in latin1 by `mysql_*` (charset changes with PDO).

## 4. Report excerpt (analysis only)

```json
{
  "skill": "php2shell-migration",
  "summary": "Analysis only; containment recommended; incremental migration planned.",
  "project": {"name": "fixture-legacy", "framework": "custom", "framework_version_before": null, "framework_version_after": null,
              "php_version_before": "5.6.40", "php_version_after": null},
  "security": {"advisories_checked": [], "runtime_patch_verified": false, "web_runtime_verified": false,
               "remaining_findings": [
                 {"id": "rt-1", "category": "runtime_unsupported", "severity": "critical", "description": "PHP 5.6.40: EOL, no php.net backport for PHP2Shell."},
                 {"id": "rt-2", "category": "status_unknown", "severity": "high", "description": "Serving runtime not declared in source; host not inspected."}]},
  "migration": {"status": "planned", "files_changed": [], "database_changes": [], "rollback_available": false},
  "tests": [
    {"name": "syntax_check", "layer": "structural", "status": "blocked", "command": null, "exit_code": null, "summary": "No PHP 5.6 or target binary available in this environment.", "evidence": []},
    {"name": "test_suite", "layer": "automated_tests", "status": "blocked", "command": null, "exit_code": null, "summary": "No test runner; characterisation tests are stage 1 of the plan.", "evidence": []}
  ],
  "limitations": ["Advisories were not rechecked online in this run (offline analysis).", "No runtime or host access."],
  "overall_result": "blocked"
}
```
