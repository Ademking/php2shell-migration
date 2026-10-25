# Skill self-tests

These tests cover **the skill's own scripts**: detection, version classification, report validation and reference integrity. They do not test any PHP application. A migration still has to run the target application's real tests (see `references/testing/testing-strategy.md`).

Run from the skill root:

```sh
python3 -m unittest discover -s tests -v
```

Standard library only; no network, no PHP, no credentials. One test probes `https://unreachable.invalid/`, a reserved TLD that never resolves.

## Modules

| Module | Covers |
|---|---|
| `test_project_detection.py` | Framework detection, version sources (lock vs `installed.php` vs version files), monorepos, malformed metadata, CLI/CI vs web runtimes, declared vs deployed mismatches, mod_php flagging, test-runner detection, secret redaction (fake secrets planted in fixtures must never appear in output), no network access, no modification of scanned files |
| `test_version_detection.py` | PHP version parsing, PHP2Shell affected/fixed boundaries for every branch, EOL handling by date, vendor builds, branch-only tags, pre-releases, exit codes, Composer constraint matching, framework lifecycle lookup |
| `test_validation_reporting.py` | JSON schema checks, every anti-fabrication rule (R2 to R14), the overall-result derivation for pass/fail/skipped/blocked/not_run, the Markdown summary, the CLI, the example reports in `examples/` |
| `test_install.py` | Installer: the default locations cover every supported tool in both scopes, per-tool selection, dry run, copy/update, refusal of foreign directories, symlink mode, uninstall removes only this skill, custom `--dir`, zip layout for claude.ai/API, README lists every path |
| `test_reference_integrity.py` | The shipped docs pass the offline validator; all 23 framework references exist; frontmatter rules; URL rules (malformed, tracking params); section completeness/order; duplicate-document detection; unregistered CVE detection; broken relative links |

## Fixtures (`tests/fixtures/`, synthetic)

| Fixture | Scenario |
|---|---|
| `laravel/` | Modern Laravel 12 with a lock, a patched Docker FPM image, a CI runtime, PHPUnit, and planted secrets in `.env`/Dockerfile |
| `symfony/` | Symfony 7.4 with `vendor/composer/installed.php` newer than the lock; compose with secrets in the environment |
| `wordpress/` | WordPress 6.9.1, no Composer, nginx → PHP 8.1 FPM; `wp-config.php` with fake credentials |
| `legacy-php/` | Custom PHP 5.6 code (`mysql_*`, `ereg`), no tests |
| `vulnerable-runtime-config/` | Declares PHP ≥8.2 but deploys `php:8.1-apache` (mod_php); CI on affected 8.3.30 |
| `malformed-composer/` | Broken `composer.json` and `composer.lock` |
| `monorepo/` | Laravel 13 + WordPress 7.0 + a shared library; a root compose runtime |
| `unsupported-framework/` | Laravel 8 (EOL) |
| `no-test-runner/` | Slim 4 API without any test runner |

Lifecycle-dependent tests pin "today" to 2026-10-24 (the data verification date), so the suite stays deterministic as time passes. Refreshing the lifecycle data can still change expected results; update the tests deliberately if it does.
