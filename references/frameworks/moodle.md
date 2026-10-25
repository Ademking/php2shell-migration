# Moodle

**Last verified: 2026-10-24.** Lifecycle from endoflife.date via [framework-lifecycle.json](framework-lifecycle.json). Confirm on the official releases page.

## A. Project identification

- Website: https://moodle.org. User/admin docs: https://docs.moodle.org. Developer docs: https://moodledev.io. Source: https://github.com/moodle/moodle (mirror of git.moodle.org).
- Signals: `version.php` with `$version`, `$release`, `$branch`, `$maturity`; `config-dist.php`; `lib/moodlelib.php`; `admin/cli/`; `config.php` (DB credentials, `$CFG->dataroot`: **never print**); and the **moodledata** directory (outside the web root).
- Version: `$release` in `version.php` (the detector reads it, also from `public/version.php`). Site administration → Notifications shows it too.
- Generations: 3.x, 4.x (4.0 brought a new navigation/UI), 5.x. Recent releases restructured the code tree (a `public/` web root was introduced in the 5.x series; check the release notes of your target before changing web server document roots).

## B. PHP compatibility

- Official: each release's notes and requirements at https://moodledev.io/general/releases, and the PHP policy https://moodledev.io/general/development/policies/php.
- Lifecycle (endoflife.date, 2026-10-24, with `supportedPhpVersions` from that source):

  | Moodle | PHP | Security support until | Notes |
  |---|---|---|---|
  | 5.3 | 8.3 – 8.4 | 2029-10-01 | |
  | 5.2 | 8.2 – 8.4 | 2027-10-04 | |
  | 5.1 | 8.2 – 8.4 | 2027-04-19 | |
  | 5.0 | 8.1 – 8.4 | 2026-10-05 | **EOL** |
  | 4.5 | 8.1 – 8.3 | 2027-10-04 | **LTS** |
  | ≤ 4.4 | ≤ 8.3 | ended | **EOL** |

- Moodle also requires specific DB versions and PHP settings (`max_input_vars` ≥ 5000 is a well-known requirement). The environment check enforces them (`admin/environment.xml`).
- Extensions: `iconv`, `mbstring`, `curl`, `openssl`, `tokenizer`, `soap`, `ctype`, `zip`, `zlib`, `gd`, `simplexml`, `spl`, `pcre`, `dom`, `xml`, `xmlreader`, `intl`, `json`, `hash`, `fileinfo`, `sodium`, and a DB driver. The environment page lists them for each version.

## C. Upgrade strategy

- Official: https://docs.moodle.org/en/Upgrading (choose the docs version for your target) and the release notes of the target, which state the **minimum version you can upgrade from**. Older sites need an intermediate upgrade.
- Sequence (staging copy of code + DB + moodledata):
  1. Patch PHP.
  2. `php admin/cli/maintenance.php --enable`.
  3. Read the Upgrading page for the target first: the 5.x page covers web-server routing configuration and Composer dependency installation, which older upgrade habits skip.
  4. Replace the code (Git: `git checkout MOODLE_405_STABLE` style branches; or extract the release), keeping `config.php`, and add the plugins' compatible versions to the same tree.
  5. `php admin/cli/upgrade.php --non-interactive`.
  6. `php admin/cli/purge_caches.php`.
  7. `php admin/cli/maintenance.php --disable`.
  8. Move PHP when the target supports it.
- Plugins: check https://moodle.org/plugins for versions supporting the target. Additional plugins live in typed directories (`mod/`, `blocks/`, `local/`, `theme/`, `auth/`, ...). Use `admin/cli/uninstall_plugins.php` for removals.
- Themes: custom themes based on old parents (e.g. Clean/More, removed long ago) need rework.
- Cron: `admin/cli/cron.php` must run with the new PHP binary.

## D. Automated migration tooling

- **moodle-plugin-ci** (https://github.com/moodlehq/moodle-plugin-ci): runs PHP lint, phpcs (moodle-cs), PHPDoc checks, PHPUnit, Behat and Grunt checks for plugins.
- **moodle-cs** (https://github.com/moodlehq/moodle-cs): the PHP_CodeSniffer standard, which includes PHPCompatibility checks.
- Rector PHP sets for custom plugins (never for core).
- Manual: deprecated APIs listed in each plugin type's `upgrade.txt` / `UPGRADING.md` files in core, renderers/templates (Mustache) in themes, web service function changes for integrations.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `php admin/cli/check_database_schema.php`; `php -l` on custom plugins; the environment check (Site administration → Server → Environment) for the target version |
| Security | `php admin/cli/checks.php` (security/performance checks, recent versions); runtime check of the web and cron PHP; Moodle security announcements https://moodle.org/security/ |
| Static | `moodle-plugin-ci phplint`, `moodle-plugin-ci phpcs` for custom plugins |
| Tests | `php admin/tool/phpunit/cli/init.php` then `vendor/bin/phpunit` (needs `$CFG->phpunit_prefix` and `phpunit_dataroot`); Behat via `admin/tool/behat/cli/init.php` (needs a browser setup), otherwise `blocked` |
| DB | upgrade on a disposable copy; `check_database_schema.php` clean afterwards |
| Runtime | login (manual + SSO in test), course view, activity submission (assign/quiz), gradebook, file upload, messaging, cron run (`php admin/cli/cron.php` once on staging); check the logs |

## F. Recovery and rollback

- Backup: DB + moodledata + code (including plugins), taken in maintenance mode.
- Moodle does not support downgrades: rollback = restore all three from the same point.
- Limitations: large moodledata volumes need snapshot-based backups. Record the snapshot ID.

## G. Sources

- https://moodledev.io/general/releases
- https://moodledev.io/general/development/policies/php
- https://docs.moodle.org/en/Upgrading (blocks plain HTTP probes; content read via a fetch tool on 2026-10-24)
- https://moodle.org/security/ (HTTP 403 to automated requests on 2026-10-24: not machine-verified)
- https://github.com/moodlehq/moodle-plugin-ci
- https://endoflife.date/moodle (secondary)
- Verified: 2026-10-24.
