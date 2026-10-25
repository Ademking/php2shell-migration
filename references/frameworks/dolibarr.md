# Dolibarr ERP & CRM

**Last verified: 2026-10-24.** endoflife.date has no Dolibarr data, so lifecycle is **unknown** in the detector. Dolibarr maintains only recent major versions; check the official wiki.

## A. Project identification

- Website: https://www.dolibarr.org. Wiki (docs): https://wiki.dolibarr.org. Source: https://github.com/Dolibarr/dolibarr.
- Signals: `htdocs/main.inc.php`, `htdocs/filefunc.inc.php` (`DOL_VERSION`), `htdocs/conf/conf.php` (DB credentials, `$dolibarr_main_instance_unique_id`: **never print**), `htdocs/custom/` (external modules), and the **documents directory** (`$dolibarr_main_data_root`, outside the web root, holding uploaded files and `install.lock`).
- Version: `DOL_VERSION` in `htdocs/filefunc.inc.php` (the detector reads it). UI: Home → Setup → About → Dolibarr.
- Packaging: tarball/zip, DoliWamp (Windows), Debian/Ubuntu packages, and Docker images. The Debian package manages files differently; follow its update path instead of overwriting files.

## B. PHP compatibility

- Official: the "Prerequisites" / system requirements wiki pages (https://wiki.dolibarr.org) and the **ChangeLog** of each release (https://github.com/Dolibarr/dolibarr/blob/develop/ChangeLog). Each major states the minimum PHP and the newest PHP it was tested with.
- Old majors do not run on current PHP, and new majors drop old PHP. Moving PHP and Dolibarr often has to alternate.
- Extensions: `mysqli` or `pgsql`, `gd`, `curl`, `mbstring`, `xml`, `zip`, `intl`, `imap` (email collector; note that PHP 8.4 moved `imap` to PECL), `calendar`.
- External modules from DoliStore (https://www.dolistore.com) declare compatible Dolibarr versions.

## C. Upgrade strategy

- Official: https://wiki.dolibarr.org/index.php/Installation_-_Upgrade (title may vary by language; the English wiki has an "Upgrade" chapter).
- Sequence (staging):
  1. Patch PHP.
  2. Back up the DB and the documents directory.
  3. Replace the program files with the new release (keep `htdocs/conf/conf.php` and `htdocs/custom/`).
  4. Remove `install.lock` from the documents directory.
  5. Open `/install/`, choose the upgrade for your from-version, and run the migration steps (`upgrade.php`, then `upgrade2.php`).
  6. Recreate `install.lock`.
  7. Re-enable the modules.
- Dolibarr can migrate across several majors in sequence through the wizard, but upgrading **one major at a time** with tests in between is safer for customised instances.
- External modules in `htdocs/custom/` must have versions compatible with the target. Disable incompatible ones before upgrading.
- Database: the migration scripts in `htdocs/install/mysql/migration/*.sql` alter the schema and are one-way.

## D. Automated migration tooling

- No official Rector set. Use Rector PHP sets and PHPCompatibility on `htdocs/custom/` modules.
- Dolibarr's own `dev/` directory contains code-quality configs used by core developers (phpcs rules). Use them for custom modules.
- Manual: hooks and triggers in custom modules, PDF/ODT document models, API (REST) consumers.

## E. Test plan

| Layer | Command / action |
|---|---|
| Structural | `php -l` over `htdocs/custom/`; the upgrade wizard reports no SQL errors |
| Security | runtime check; GitHub advisories https://github.com/Dolibarr/dolibarr/security/advisories; confirm `install.lock` exists after upgrade (otherwise the installer stays reachable) |
| Static | PHPCompatibility on custom modules |
| Tests | core PHPUnit tests exist in the repo (`test/phpunit/`) for development checkouts with a test DB; production instances: mark `blocked` and rely on smoke tests |
| DB | full upgrade on a disposable copy; compare row counts of key tables (`llx_societe`, `llx_facture`, `llx_commande`) |
| Runtime | login, third parties, proposals → orders → invoices flow, PDF generation, email sending to a test mailbox, scheduled jobs (`scripts/cron/cron_run_jobs.php` on staging), REST API with a test key; `documents/dolibarr.log` if logging is enabled |

## F. Recovery and rollback

- Backup DB + documents directory + `htdocs/conf/conf.php` + `htdocs/custom/`.
- Rollback = restore all four. Migrations are one-way.
- Limitations: accounting/legal-compliance modules (country-specific) need business validation that tests alone cannot provide. Record it as a limitation.

## G. Sources

- https://wiki.dolibarr.org
- https://github.com/Dolibarr/dolibarr/blob/develop/ChangeLog
- https://github.com/Dolibarr/dolibarr/security/advisories
- https://www.dolibarr.org
- Unverified: the exact wiki URL of the upgrade page (it is language-specific). The wiki home is the fallback.
- Verified: 2026-10-24.
