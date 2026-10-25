# Maintaining php2shell-migration

For people changing the skill itself. Users start with [README.md](README.md).

## Layout

```
SKILL.md                     entry point the agents load (frontmatter + workflow)
agents/openai.yaml           optional Codex UI metadata (other tools ignore it)
references/security/         advisories (+ php-advisory-data.json), supported versions, verification, policy
references/frameworks/       23 framework references + other-php-projects.md + framework-lifecycle.json
references/migration/        workflow, Composer, language changes, DB, deployment/rollback, legacy
references/testing/          strategy, per-framework commands, security checks, report format (rules R1-R14)
scripts/                     detect-project.py, check-php-version.py, validate-results.py,
                             validate-references.py, refresh-lifecycle-data.py, install.py, run-validation.sh
templates/                   migration-plan.md, migration-report.md, test-results.json (+ .schema.json)
examples/                    Laravel, WordPress, legacy walkthroughs (their JSON reports are validated by the tests)
tests/                       unittest suite for the skill's own scripts + synthetic fixtures
VALIDATION-RESULTS.md        recorded results of the last development validation run
```

The format is the [Agent Skills specification](https://agentskills.io/specification); `validate-references.py` enforces its frontmatter rules plus stricter cross-client ones. `SKILL.md` must stay under 500 lines, and its description under 500 characters (portability across clients). Detail goes into `references/`.

## The skill's own tests

These test the skill's scripts against synthetic fixtures, with no credentials and no network. They say **nothing** about any application being migrated; each migration tests the real application.

```sh
python3 -m unittest discover -s tests -v                                  # unit tests
python3 scripts/validate-references.py                                   # docs/reference integrity (offline)
python3 scripts/validate-references.py --online --report url-report.json # also probe every URL
sh scripts/run-validation.sh                                             # all offline checks in one go
```

`run-validation.sh` needs a POSIX shell (Git Bash or WSL on Windows); its commands also run directly in PowerShell. See [tests/README.md](tests/README.md) for what each test module covers.

## Updating references

1. `python3 scripts/refresh-lifecycle-data.py` refreshes `references/frameworks/framework-lifecycle.json` from endoflife.date (a secondary source).
2. Recheck php.net ([supported versions](https://www.php.net/supported-versions.php), [archive](https://www.php.net/archive/)) and the [php-src advisories](https://github.com/php/php-src/security/advisories). Update `references/security/php-advisory-data.json`, `php2shell-advisories.md` and `php-supported-versions.md`, including their "Last verified" dates.
3. Register any new CVE in `php2shell-advisories.md` with its source; the validator rejects unregistered CVE IDs.
4. Run `scripts/validate-references.py --online`. Fix broken links, or mark them unverified with the official homepage as fallback. Never substitute a guessed URL.
5. Run the unit tests; some assert the advisory data.

## Agent discovery paths

`scripts/install.py` holds the per-tool skill folders (`TOOLS`). When a vendor changes its paths:

1. Update `TOOLS`.
2. Update the "Supported tools" table in README.md, citing the vendor doc.
3. Run the tests. `tests/test_install.py` checks that the default install still covers every tool, and that every project path is listed in the README.

## Design rules

- Scripts use the Python standard library only. Nothing touches the network except `refresh-lifecycle-data.py` and `validate-references.py --online`.
- The detector never executes project code and never prints file contents, only redacted paths, package names and versions.
- Report rules derive `overall_result` from evidence. Change the rules only with matching tests, and never to make a report look better.

## License

MIT. It was chosen because the skill is meant to be copied into many repositories and agent setups: it is short, permissive, compatible with most corporate policies, and needs only the notice kept. Referenced third-party documentation stays under its owners' terms; this repository links to it and does not reproduce it.
