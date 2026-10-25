# Migration workflow

**Last verified: 2026-10-24.** The end-to-end sequence. Framework specifics live in `../frameworks/<id>.md`.

## Phase 0: Preconditions

- Confirm scope with the user: which application(s), which environments you may touch (local, CI, staging), and who owns production.
- Confirm you can: read files, edit files, run commands, access PHP/Composer, access the network, access a test environment. Record each "no" as a limitation. Skip the phases that need missing capabilities, and mark their tests `blocked`.
- `git status`: if there are uncommitted changes, **do not** stash, reset or overwrite them. Ask, or branch from the current state and say so.

## Phase 1: Inventory (read-only)

1. `python3 scripts/detect-project.py <dir> --output detect.json`
2. For each concrete runtime version: `python3 scripts/check-php-version.py <version>`.
3. Inventory extensions (`composer.json` `ext-*`, Dockerfile `docker-php-ext-install`, `php -m` on the target).
4. Inventory plugins/modules/themes (CMS) and custom code locations.
5. Note test tooling (detector `test_tooling`), DB engine, queues, cron, storage.
6. **Baseline**: run the existing test suite on the **current** runtime before any change, if possible. Store its results; they are the regression reference.

## Phase 2: Plan

Fill `templates/migration-plan.md`. Required decisions:

| Decision | Rule |
|---|---|
| Target PHP | Newest supported, patched release that the target framework version officially supports. Cite the source and date. |
| Target framework | Latest supported release reachable from the current one. List required intermediate majors. |
| Stages | Runtime patch → (framework intermediate majors) → target PHP branch → dependency cleanup → deprecation cleanup. One stage per commit series. |
| Acceptance criteria | Named tests per layer that must pass; what "done" means for each finding. |
| Rollback | Per stage: git revert + previous image/package + DB restore point. |

If the gap is too large for a direct path (e.g. PHP 5.6 app, Laravel 5.x, Drupal 7), use [legacy-applications.md](legacy-applications.md) and list the blockers. Do not attempt a big-bang rewrite silently.

## Phase 3: Execute (per stage)

1. Branch: `git switch -c php2shell/<stage>` (or one branch with stage commits).
2. Change declarations: Dockerfile/compose/CI/`.php-version`/`composer.json` `require.php` and `config.platform.php`.
3. Resolve dependencies honestly ([composer-dependencies.md](composer-dependencies.md)).
4. Apply automated refactoring (Rector) **as a dry run first**. Review diffs and commit separately from manual changes.
5. Fix the remaining incompatibilities manually ([php-language-compatibility.md](php-language-compatibility.md)).
6. Run the test layers ([../testing/testing-strategy.md](../testing/testing-strategy.md)). A stage is complete only when its acceptance tests pass or failures are recorded and accepted by the user.
7. Commit with a message naming the stage and the evidence.

## Phase 4: Verify and report

- Runtime verification: [../security/vulnerability-verification.md](../security/vulnerability-verification.md).
- Write `test-results.json`, validate it with `scripts/validate-results.py`, and render the Markdown.
- Write `migration-report.md`. Remaining risks go under findings/limitations, not in fine print.

## Phase 5: Hand-off (no deployment by the agent)

Provide the deployment and rollback runbook ([deployment-and-rollback.md](deployment-and-rollback.md)) for the humans who own production. The agent never deploys, and never migrates production databases.

## Behaviour preservation checklist

Before marking any stage complete, confirm that nothing changed (unless intended and approved) in: authentication flows, authorisation rules, public/API contracts (routes, payloads, status codes), persisted data formats, scheduled jobs and queues, file storage paths, outbound integrations (mail, payment, webhooks), and configuration keys consumed by other systems.
