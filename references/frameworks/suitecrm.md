# SuiteCRM

**Last verified: 2026-10-24.** endoflife.date has no SuiteCRM data, so lifecycle is **unknown** in the detector. Use the official compatibility matrix.

## A. Project identification

- Website: https://suitecrm.com. Docs: https://docs.suitecrm.com. Source: SuiteCRM 7 https://github.com/salesagility/SuiteCRM; SuiteCRM 8 https://github.com/salesagility/SuiteCRM-Core.
- **SuiteCRM 7 signals**: `suitecrm_version.php` (`$suitecrm_version`), `sugar_version.php` (SugarCRM CE heritage), `config.php` and `config_override.php` (DB credentials: never print), `modules/`, `custom/`, `cache/`, `upload/`.
- **SuiteCRM 8 signals**: a Symfony application at the root (`bin/console`, `.env`, `config/`, `core/`) with the legacy 7.x code under `public/legacy/` (`public/legacy/suitecrm_version.php`).
- Version: read `$suitecrm_version` from the version file (the detector does this). Admin UI: Admin → System → About / Diagnostic Tool.
- SugarCRM CE 6.5 sites (`sugar_version.php` without a SuiteCRM file) are legacy forks. Migrate them via SuiteCRM 7 first.

## B. PHP compatibility

- Official: the compatibility matrix https://docs.suitecrm.com/admin/compatibility-matrix/ (PHP, MySQL/MariaDB, Elasticsearch per release, for 7.x and 8.x).
- 7.x and 8.x are maintained in parallel with **different** PHP ranges. 8.x embeds 7.x legacy code, so both constraints apply.
- Extensions (installation docs): `curl`, `gd`, `imap` (for email; note `imap` moved out of PHP core to PECL in 8.4), `intl`, `json`, `mbstring`, `mysqli`, `openssl`, `soap`, `xml`, `zip`, `ldap` (if used).
- The **`imap` unbundling in PHP 8.4** is a SuiteCRM-specific blocker: inbound email needs the PECL extension or the vendor's alternative. Check the release notes of your target.

## C. Upgrade strategy

- Official: 7.x upgrade docs https://docs.suitecrm.com/admin/installation-guide/upgrading/ and 8.x upgrade/migration docs under https://docs.suitecrm.com/8.x/admin/.
- 7.x within the line:
  1. Patch PHP.
  2. Apply upgrade packages in the documented order (Admin → Upgrade Wizard, or the CLI upgrade for large instances).
  3. Run Admin → Repair → Quick Repair and Rebuild, and execute any SQL it proposes on staging first.
  4. Rebuild relationships/extensions.
- 7.x → 8.x: follow the official migration guide (8.x installs alongside, with the legacy app moved into `public/legacy`). Customisations in `custom/` are carried over, but Angular-based 8.x UI extensions are new work.
- Customisations: only code in `custom/` is upgrade-safe. Changes to core files are overwritten. Diff the core against a pristine release of the same version first to find them.
- Logic hooks, Studio/Module Builder modules, scheduler jobs (`cron.php`) and email settings must be inventoried.

## D. Automated migration tooling

- No official Rector set. Use PHPCompatibility on `custom/` and custom modules.
- Rector PHP sets for custom code only (never on core).
- Manual: logic hooks, custom entry points, SOAP/REST v4.1 vs v8 API integrations (API contract changes), scheduler jobs, PDF templates.

## E. Test plan

| Layer | Command / action |
|---|---|
| Structural | `php -l` over `custom/` and custom modules; Quick Repair and Rebuild completes without errors |
| Security | runtime check; release notes / security advisories (https://github.com/salesagility/SuiteCRM/security/advisories); `composer audit` (8.x root, and 7.x `composer.lock` if present) |
| Static | PHPCompatibility on custom code |
| Tests | 7.x ships Codeception configs in the repo for developers; project-level tests are rare, so usually `blocked` with a reason. 8.x: `vendor/bin/codecept run` *(example; depends on checkout)* |
| DB | upgrade on a disposable copy; Repair shows no pending schema changes |
| Runtime | login, list/detail/edit views of core modules, workflows (AOW), scheduler run (`php -f cron.php` on staging), inbound/outbound email, API calls with test credentials; `suitecrm.log` |

## F. Recovery and rollback

- Backup the DB + the full instance directory (including `upload/` and `custom/`) before any upgrade package.
- Upgrades change the schema and files, so rollback = restore both.
- Clear `cache/` and rebuild after restore.
- Limitations: integrations with external systems (email servers, ERP) must be tested against sandboxes only.

## G. Sources

- https://docs.suitecrm.com/admin/compatibility-matrix/
- https://docs.suitecrm.com/admin/installation-guide/upgrading/
- https://docs.suitecrm.com/8.x/admin/
- https://github.com/salesagility/SuiteCRM/security/advisories
- https://github.com/salesagility/SuiteCRM-Core
- Verified: 2026-10-24.
