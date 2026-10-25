---
name: php2shell-migration
description: Detects, patches and verifies PHP apps exposed to PHP2Shell (CVE-2026-109618, CVE-2026-109619) or running outdated PHP. Upgrades the runtime, framework/CMS (Laravel, Symfony, WordPress, Drupal, Magento and 18 more), Composer dependencies and deployment config without changing behaviour, runs layered tests and writes a truthful JSON/Markdown report. Use to patch PHP2Shell, upgrade PHP or a PHP framework, modernise legacy PHP, or check a PHP runtime's security status.
license: MIT
compatibility: Any Agent Skills client (Claude Code, claude.ai and the Claude API, Codex, GitHub Copilot, Cursor, Gemini CLI, OpenCode and others). Needs a shell and Python 3.8+ for the bundled scripts. PHP, Composer, git, network and test-environment access enable full verification; without them (e.g. sandboxed API containers) the skill degrades to planning and honest reporting.
metadata:
  version: "1.0.0"
  advisory-data-verified-on: "2026-10-24"
---

# PHP2Shell migration

Remediate PHP2Shell and outdated PHP **safely and verifiably**. Two separate deliverables, never conflated:

1. **Runtime remediation**: the PHP binary that serves web requests is a patched, supported release.
2. **Application modernisation**: framework, dependencies and code run correctly on that runtime.

A framework upgrade does not patch the runtime. A patched runtime does not make the app secure. Passing this skill's own tests says nothing about the target application; every run must test the **actual application**.

## Inputs and outputs

- **Input**: a PHP project directory (and, if available, access to its test/staging environment).
- **Outputs** (write into the project, e.g. `migration/` or a location the user picks):
  - `migration-plan.md` from [templates/migration-plan.md](templates/migration-plan.md) (before any edit)
  - `test-results.json` matching [templates/test-results.schema.json](templates/test-results.schema.json), validated by `scripts/validate-results.py`
  - `migration-report.md` from [templates/migration-report.md](templates/migration-report.md)

## Hard safety rules

- Never deploy, never touch production, never run destructive DB operations against non-disposable data.
- Never run exploit attempts or expose a vulnerable runtime to the internet to "test" it.
- Never call `phpinfo()` on a reachable URL; never print `.env`, `wp-config.php`, `app/etc/env.php`, `config.php` or other secrets.
- Never use `--ignore-platform-reqs`, `--no-audit`/disabled security checks, force-updates, or remove features to make dependency resolution pass.
- Never discard user changes: check `git status` first; work on a new branch; stash nothing without saying so.
- Never invent CVEs, versions, dates, commands or test results. Unknown is a valid answer; record it.
- If you cannot run commands, edit files, browse, or reach the runtime: say so, produce the plan and a report whose tests are `not_run`/`blocked`, and stop claiming beyond the evidence.

## Workflow

### 1. Establish facts (no edits)

1. `git status` / note uncommitted work. If not a repo, recommend a backup before step 4.
2. Run the detector (no network, no code execution, secrets redacted):
   ```sh
   python3 <skill-dir>/scripts/detect-project.py <project> --output detect.json
   ```
   It reports every application root, framework + version + confidence, Composer state, test tooling and runtime declarations, kept apart as `web`, `cli` and `ci`.
3. Classify each concrete PHP version you find:
   ```sh
   python3 <skill-dir>/scripts/check-php-version.py "$(php -v | head -n1)" --sapi cli
   ```
   Exit 0 patched, 2 affected/unsupported, 3 unknown. Distro builds (`-1ubuntu`, `+deb`, `.el9`) need the vendor notice: see [vulnerability-verification.md](references/security/vulnerability-verification.md).
4. Refresh the facts that drift: re-read the official advisories and supported-versions page ([php2shell-advisories.md](references/security/php2shell-advisories.md), [php-supported-versions.md](references/security/php-supported-versions.md)). If you cannot reach them, record "advisory recheck: unreachable" and do not claim verification.

### 2. Classify the situation

Assign one or more of these categories ([remediation-policy.md](references/security/remediation-policy.md)):

| # | Category | Action |
|---|---|---|
| 1 | `runtime_affected`: supported branch below the fixed release | Immediate runtime security update (same branch). |
| 2 | `runtime_unsupported`: EOL branch | Migrate to a supported branch; vendor backports are a stop-gap. |
| 3 | Patched runtime, `framework_outdated` | Plan framework upgrade separately. |
| 4 | `dependency_vulnerable`: package/plugin/extension | `composer audit` / CMS update tooling. |
| 5 | `deployment_mismatch`: deployed config differs from source | Fix deployment declarations; verify on host. |
| 6 | `status_unknown`: evidence insufficient | Say so; list the evidence needed. |

### 3. Plan (before editing)

Fill [templates/migration-plan.md](templates/migration-plan.md): current/target runtime and framework versions with sources, intermediate stages, extension compatibility, breaking changes, DB/deployment risks, test coverage and acceptance criteria, rollback. Choose the target PHP as the newest **supported, security-patched** release that the framework version officially supports; never hardcode it. Follow:

- [migration-workflow.md](references/migration/migration-workflow.md): overall sequence
- framework reference: `references/frameworks/<id>.md` (ids from the detector: `laravel`, `symfony`, `wordpress`, `drupal`, `codeigniter`, `yii`, `cakephp`, `joomla`, `october-cms`, `suitecrm`, `espocrm`, `nextcloud`, `magento`, `prestashop`, `opencart`, `slim`, `dolibarr`, `typo3`, `moodle`, `mediawiki`, `laminas`, `phalcon`, `phpmyadmin`), or [other-php-projects.md](references/frameworks/other-php-projects.md)
- [legacy-applications.md](references/migration/legacy-applications.md) when no direct upgrade path exists: produce an incremental plan and list blockers

If a production runtime is affected, **the runtime patch is the first and independent task**: same-branch patch releases are low risk and must not wait for a framework migration. Interim mitigations from php.net are listed in [php2shell-advisories.md](references/security/php2shell-advisories.md); they are not fixes.

### 4. Execute (on a branch)

1. Create a branch/checkpoint (`git switch -c php2shell-migration-<date>`). Record it in the report.
2. Runtime: update Docker base images, CI matrices, `.php-version`, PaaS/FPM declarations to the exact patched version ([deployment-and-rollback.md](references/migration/deployment-and-rollback.md)).
3. Application, one stage at a time: Composer constraints ([composer-dependencies.md](references/migration/composer-dependencies.md)), language changes ([php-language-compatibility.md](references/migration/php-language-compatibility.md)), framework steps from its reference, DB migrations only on disposable copies ([database-migrations.md](references/migration/database-migrations.md)).
4. Commit per stage with clear messages so each stage can be reverted.

Preserve business logic, auth, authorisation, API contracts, user data, scheduled tasks, queues, storage and integrations. Stop and ask when a change would alter behaviour.

### 5. Test the application (mandatory)

Run every layer the environment allows ([testing-strategy.md](references/testing/testing-strategy.md), commands in [framework-test-commands.md](references/testing/framework-test-commands.md), security checks in [security-verification.md](references/testing/security-verification.md)):

1. Structural: `composer validate`, lock consistency, `php -l` on every file, framework config checks.
2. Security: advisory recheck, runtime version, `composer audit`, extensions, deployment config.
3. Static analysis: PHPStan / Rector dry-run / PHPCompatibility where the project supports them.
4. Automated tests: the project's real suite (PHPUnit, Pest, framework runners).
5. Runtime: start with the intended runtime in a test environment, health/smoke HTTP checks, logs.
6. Regression & DB: before/after comparison, migrations on a disposable DB.

Record each test as `passed`, `failed`, `skipped`, `blocked` or `not_run` with the **actual** command, exit code and evidence. A missing runner/service is `blocked`, not `passed`.

### 6. Report

```sh
python3 <skill-dir>/scripts/validate-results.py test-results.json --markdown test-results.md
```

The validator rejects fabricated or over-claiming reports (rules in [results-report-format.md](references/testing/results-report-format.md)); fix the report, not the rules. Then complete [templates/migration-report.md](templates/migration-report.md). Always state separately: runtime patch verified, application migration completed, automated tests passed, deployment runtime verified, remaining findings. Verifying only the CLI never verifies the web runtime.

## Examples

- [examples/laravel-migration.md](examples/laravel-migration.md)
- [examples/wordpress-migration.md](examples/wordpress-migration.md)
- [examples/legacy-php-migration.md](examples/legacy-php-migration.md)

## Paths and tool availability

`<skill-dir>` is the directory containing this `SKILL.md` (for example `~/.agents/skills/php2shell-migration` or `.claude/skills/php2shell-migration`). Relative links and `scripts/`, `templates/`, `references/` paths in this skill resolve against it, not against the project being migrated; use absolute paths when running scripts. Use `python` or `py -3` where `python3` does not exist (Windows).

In sandboxed environments without network or project access (e.g. the Claude API code-execution container), do the read-only analysis you can, mark advisory rechecks `unreachable` and execution steps `blocked`, and say so.

Commands here are POSIX-shell examples; adapt to the tools you actually have (PowerShell, a container, a CI job). If PHP/Composer are absent locally, use the project's container or mark the step `blocked`. Bundled scripts need only the Python 3 standard library and make no network calls, except `scripts/refresh-lifecycle-data.py` and `scripts/validate-references.py --online`, which you run explicitly.
