# Migration plan: <project name>

> Created before any file is modified. Every version claim needs a source and a date. Write "unknown" rather than guessing.

- Date: YYYY-MM-DD
- Prepared by: <agent / person>
- Repository / path: <path>, branch for the work: `<branch>` (created from `<commit>`)
- Uncommitted changes found at start: <none / list; how they are preserved>
- Capabilities available: edit files [yes/no], run commands [yes/no], PHP CLI [version/no], Composer [version/no], network [yes/no], test environment [describe/no], target host access [yes/no]

## 1. Current state (evidence)

| Item | Value | Evidence (file / command / output) |
|---|---|---|
| Application(s) detected | | `detect.json` |
| Framework / CMS + version | | |
| PHP declared (composer `require.php`) | | |
| PHP runtime: web (serving) | | verified on host? yes/no |
| PHP runtime: CLI | | |
| PHP runtime: CI | | |
| Vendor build / backport info | | |
| Extensions required | | |
| Test tooling | | |
| Database engine/version | | |
| Queues / cron / storage / integrations | | |

## 2. Security findings

| ID | Category (`runtime_affected`, `runtime_unsupported`, `framework_outdated`, `dependency_vulnerable`, `deployment_mismatch`, `status_unknown`) | Severity | Evidence | Source (advisory URL, checked on) |
|---|---|---|---|---|

Advisories rechecked this run: <CVE-2026-109618: verified/unreachable on YYYY-MM-DD>, <CVE-2026-109619: ...>

## 3. Targets

| Component | Current | Target | Why this target (source + date) |
|---|---|---|---|
| PHP (web) | | | newest supported patched release supported by the framework |
| Framework / CMS | | | |
| Key packages / plugins | | | |

## 4. Stages

| # | Stage | Changes | Risk | Acceptance tests | Rollback |
|---|---|---|---|---|---|
| 1 | Runtime security patch (same branch) | Dockerfile/CI/... | low | runtime_version_check, test_suite | previous image/package |
| 2 | ... | | | | |

Intermediate upgrades required: <list, e.g. Laravel 10 → 11 → 12>
Blockers: <extension without build, abandoned plugin, missing licence, ...> (owner, decision needed)

## 5. Compatibility and breaking changes to inspect

- Language changes crossed: <links to php.net migration guides>
- Framework upgrade guides: <links>
- Extensions / plugins / modules / themes: <list with compatibility status>
- Custom code areas at risk: <list>

## 6. Database and deployment risks

- Migrations to run (disposable DB only): <list>; reversible: yes/no
- Deployment declarations to change: <files>
- Workers to restart: <FPM, queue, cron, Octane, ...>

## 7. Test plan and acceptance criteria

| Layer | Test name | Command | Required for acceptance |
|---|---|---|---|
| structural | syntax_check | | yes |
| security | dependency_audit | composer audit | yes |
| security | runtime_version_check | | yes |
| runtime | web_runtime_check | | yes |
| automated_tests | test_suite | | yes |
| ... | | | |

Baseline (before changes): <results or "not available: reason">

## 8. Rollback

- Code: `git revert` / branch `<branch>` not merged
- Runtime: previous image digest / package version `<...>`
- Database: backup `<location>`, restore tested on `<date>`: yes/no
- Config: copies of changed server config at `<location>`

## 9. Out of scope / not done by the agent

- Production deployment and production DB migrations (owner: <name/team>)
- <other>
