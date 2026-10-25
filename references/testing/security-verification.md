# Security verification (Layer 2)

**Last verified: 2026-10-24.**

## Checklist

| Check | How | Result recorded as |
|---|---|---|
| Advisories rechecked | Read php.net archive (current year), php-src GHSAs, CVE API ([../security/php2shell-advisories.md](../security/php2shell-advisories.md#how-to-recheck-agent-procedure)) | `security.advisories_checked[]` with `verified` / `unreachable` / `not_checked` |
| Intended runtime patched | `php -v` (target binary) → `scripts/check-php-version.py` | test `runtime_version_check`; sets `runtime_patch_verified` only if passed |
| Vendor backport (if vendor build) | package changelog / vendor CVE page | evidence lines in `runtime_version_check` |
| Web runtime matches | observe the serving SAPI in the test env ([../security/vulnerability-verification.md](../security/vulnerability-verification.md)) | test `web_runtime_check`; sets `web_runtime_verified` |
| Dependencies | `composer audit --format=json` (or CMS tooling) | test `dependency_audit`; each advisory → `remaining_findings` |
| Unsupported packages | `composer outdated --direct`, abandoned packages, EOL framework (detector `lifecycle`) | findings `framework_outdated` / `dependency_vulnerable` |
| Extensions/platform | `composer check-platform-reqs` on the target runtime | test `platform_reqs` |
| Deployment config | `scripts/detect-project.py` after changes | test `deployment_config`; `deployment_mismatch` findings |
| Mitigations (only if runtime not yet patched) | confirm the ini values effective for the SAPI, e.g. FPM pool `php_admin_value`, then restart workers | finding stays open |

## Effective ini values without exposing them publicly

- FPM: `php-fpm -tt` (tests the config and dumps it, run as admin on the host), or read the pool files.
- CLI ini differs from FPM/Apache ini; `php -i` shows CLI only.
- Never put `phpinfo()` on a reachable URL.

## Out of scope / prohibited

- Exploit attempts, PoC execution, fuzzing production.
- Disabling `composer audit` or ignoring advisories to get a green run.
- Claiming "secure". Report what was checked and what remains.
