# Migration report: <project name>

- Date: YYYY-MM-DD
- Branch / commits: `<branch>`, `<first>`..`<last>`
- Machine-readable results: `test-results.json` (validated with `scripts/validate-results.py`: VALID/INVALID)
- Overall result: `<verified | partially_verified | failed | blocked | not_verified>`

## The five answers

| Question | Answer | Evidence |
|---|---|---|
| 1. Runtime patch verified? | yes / no | command + output excerpt |
| 2. Application migration completed? | yes / partially / no | stages done |
| 3. Automated tests passed? | yes / no / blocked | test_suite summary |
| 4. Deployment (web) runtime verified? | yes / no | how it was observed, environment |
| 5. Remaining security findings | count | list below |

"Verified" means everything in scope was checked and passed. It does not mean the application is secure.

## Versions

| Component | Before | After | Source |
|---|---|---|---|
| PHP (web) | | | |
| PHP (CLI/CI) | | | |
| Framework / CMS | | | |

## What changed

- Files: <list or `git diff --stat`>
- Dependencies: <composer.lock package changes, majors>
- Database: <migrations run, on which (disposable) database>
- Deployment declarations: <Dockerfile, CI, PaaS, FPM>

## Test results

<paste the rendered `test-results.md` table or link to it>

Tests not run, skipped or blocked, and why:

- ...

## Remaining findings

| ID | Category | Severity | Description | Proposed next step / owner |
|---|---|---|---|---|

## Limitations

- <environment limits, unverifiable claims, sources unreachable>

## Rollback

<exact steps, checkpoints, backup locations>

## Hand-off for production (to be done by the system owner)

1. Deploy `<artefact>` to staging, verify the web runtime version, smoke test.
2. Schedule production rollout; restart all PHP workers; verify the serving version.
3. Remove interim mitigations only after the patched runtime is verified (keep `session.upload_progress.enabled=0` if the feature is unused).
