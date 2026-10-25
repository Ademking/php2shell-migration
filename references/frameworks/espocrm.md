# EspoCRM

**Last verified: 2026-10-24.** endoflife.date has no EspoCRM data, so lifecycle is **unknown** in the detector. EspoCRM supports only its current release line; check the official docs.

## A. Project identification

- Website: https://www.espocrm.com. Docs: https://docs.espocrm.com. Source: https://github.com/espocrm/espocrm.
- Signals: `application/Espo/` (core PHP), `client/` (front end), `custom/Espo/Custom/` (customisations), `data/config.php` and `data/config-internal.php` (the latter holds DB credentials and secrets in newer versions; never print either), `command.php`, `cron.php`, `public/` (newer installs use `public/` as the web root).
- Version: the `'version'` key in `data/config.php` (the detector extracts only that value). Admin UI: Administration → System → About.
- EspoCRM uses Slim internally for routing. The detector reports Slim as a component, not as a separate app.

## B. PHP compatibility

- Official: server requirements https://docs.espocrm.com/administration/server-configuration/ (supported PHP versions and required extensions per current release).
- Typical required extensions: a PDO driver (`pdo_mysql`, or `pdo_pgsql` on versions with PostgreSQL support), `openssl`, `json`, `zip`, `gd`, `mbstring`, `xml`, `curl`, `exif`, `bcmath`. Optional: `zmq` (WebSocket), `ldap`. *This list is indicative.* The server-configuration page for your version is authoritative.
- EspoCRM upgrades frequently and moves its minimum PHP forward. Old instances often cannot upgrade until PHP is raised first. Check the minimum PHP of **each intermediate** release on your path.
- Extensions (EspoCRM add-ons, e.g. Advanced Pack, Sales Pack) have their own compatibility. Check them before upgrading core.

## C. Upgrade strategy

- Official: https://docs.espocrm.com/administration/upgrading/ .
- CLI upgrade (recommended for anything non-trivial): `php command.php upgrade`. It downloads the next upgrade package and applies it; repeat until current. Run it as the web server user. `php command.php upgrade --help` shows the options (e.g. upgrading from a local package file).
- Sequence:
  1. Patch PHP within the branch.
  2. Upgrade EspoCRM step by step (each step can require a newer PHP).
  3. Update add-on extensions.
  4. `php command.php rebuild`.
  5. Move PHP to the target branch.
- Customisations in `custom/Espo/Custom/` (metadata JSON, PHP classes) survive upgrades but may use removed APIs. Check the developer changelog / "API changes" notes.
- Cron/daemon: `cron.php` scheduling must keep running with the new PHP binary path.

## D. Automated migration tooling

- No official Rector set. Use PHPCompatibility + PHPStan on `custom/Espo/Custom`.
- Rector PHP sets for custom PHP classes only.
- Manual: hooks, custom entity definitions, formula scripts (EspoCRM formula language, not PHP), custom API actions.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `php -l` over `custom/`; `php command.php rebuild` succeeds |
| Security | runtime check (both the web runtime and the PHP used by `cron.php`); GitHub advisories https://github.com/espocrm/espocrm/security/advisories |
| Static | PHPCompatibility on custom code |
| Tests | the core repo has PHPUnit tests for developers (`vendor/bin/phpunit` in a dev checkout); production installs have none, so mark the app suite `blocked` and rely on smoke tests |
| DB | upgrade on a disposable copy |
| Runtime | login, entity list/detail/edit, workflows/BPM (if licensed), email fetching, scheduled jobs (Administration → Scheduled Jobs → log), API with a test API user; `data/logs/` |

## F. Recovery and rollback

- Backup: DB + the entire instance directory (`data/`, `custom/`, `client/custom/`).
- The upgrade script changes files and schema, so rollback = restore both.
- `php command.php clear-cache` after restore.
- Limitations: paid extensions need the licence to download compatible versions.

## G. Sources

- https://docs.espocrm.com/administration/server-configuration/
- https://docs.espocrm.com/administration/upgrading/
- https://github.com/espocrm/espocrm/releases
- https://github.com/espocrm/espocrm/security/advisories
- Unverified: the exact extension list for each version. Read the server-configuration page for the target.
- Verified: 2026-10-24.
