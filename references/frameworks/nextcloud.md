# Nextcloud

**Last verified: 2026-10-24.** Lifecycle from endoflife.date via [framework-lifecycle.json](framework-lifecycle.json). Confirm on the official maintenance schedule.

## A. Project identification

- Website: https://nextcloud.com. Admin manual: https://docs.nextcloud.com/server/latest/admin_manual/. Source: https://github.com/nextcloud/server.
- Signals: `occ` at the root, `version.php` (`$OC_VersionString`, `$OC_Version`), `lib/private/`, `apps/`, `core/`, `config/config.php` (contains `secret`, `passwordsalt`, DB credentials: **never print**), and the `data/` directory (often outside the web root).
- Version: `$OC_VersionString` in `version.php` (the detector reads it); `sudo -u www-data php occ status`.
- ownCloud (`owncloud` strings in `version.php`, `$OC_Channel` with ownCloud branding) is a different product with its own upgrade path. Migrating from ownCloud to Nextcloud follows a dedicated official guide.
- Packaging variants: tarball/zip, the official Docker image (`nextcloud:<ver>-apache|fpm`), All-in-One (AIO), and Snap. **AIO and Snap manage PHP themselves**, so the runtime update comes from the vendor container/snap, not from the host.

## B. PHP compatibility

- Official: system requirements per major https://docs.nextcloud.com/server/latest/admin_manual/installation/system_requirements.html (switch the doc version to your major) and the maintenance/release schedule https://github.com/nextcloud/server/wiki/Maintenance-and-Release-Schedule.
- Lifecycle (endoflife.date, 2026-10-24): **35** (to 2027-09-30), **34** (to 2027-06-30), **33** (to 2027-02-28) supported; **32** EOL 2026-09-30; older EOL.
- Each major supports a specific PHP range. A PHP jump may require a Nextcloud major first, and vice versa.
- Extensions (admin manual, "PHP Modules"): `ctype`, `curl`, `dom`, `fileinfo`, `filter`, `gd`, `json`, `libxml`, `mbstring`, `openssl`, `posix`, `session`, `simplexml`, `xmlreader`, `xmlwriter`, `zip`, `zlib`, a DB driver, plus recommended `intl`, `sodium`, `bcmath`, `gmp`, `imagick`, `apcu`/`redis`.

## C. Upgrade strategy

- Official: https://docs.nextcloud.com/server/latest/admin_manual/maintenance/upgrade.html .
- **Never skip a major** (e.g. 31 → 33 directly is not supported). Upgrade to the latest minor of the current major first, then one major at a time.
- Sequence:
  1. Patch PHP within a branch that the current major supports.
  2. `occ maintenance:mode --on`.
  3. Back up.
  4. Run the web updater or the CLI updater (`sudo -u www-data php updater/updater.phar`), or replace the code manually and run `sudo -u www-data php occ upgrade`.
  5. Run `occ db:add-missing-indices`, `occ db:add-missing-columns`, `occ db:add-missing-primary-keys` and `occ maintenance:repair`.
  6. `occ app:update --all`.
  7. `occ maintenance:mode --off`.
  8. Repeat per major; move PHP when the target major supports it.
- Apps: incompatible apps are disabled during the upgrade. Check https://apps.nextcloud.com for compatible releases.
- Config: `config/config.php` keys (e.g. `overwrite.cli.url`, `trusted_domains`) are preserved. Compare against `config.sample.php` for deprecations.
- Run `occ` as the **web server user**; running as root causes permission problems.

## D. Automated migration tooling

- Nextcloud core is not refactored by users. Rector/PHPStan/Psalm only apply to **custom apps** (Nextcloud uses Psalm in core; `nextcloud/ocp` provides public API stubs).
- `occ app:check-code` was removed from recent versions, so use static analysis against the OCP stubs instead.
- Manual: custom apps using private `OC\` APIs (unsupported, break often), external storage, SSO/LDAP config.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `occ integrity:check-core` (signature check); `occ status` |
| Security | `occ update:check`; `occ setupchecks` (recent versions; also shown in Administration → Overview); runtime check of the PHP **used by the web server and by cron** (`crontab -u www-data -l`); advisories https://github.com/nextcloud/security-advisories/security/advisories |
| Static | Psalm/PHPStan on custom apps |
| Tests | custom apps: `vendor/bin/phpunit` in the app directory *(example)*; core server tests are for core development only, so for an instance mark the suite `blocked` and rely on smoke tests |
| DB | `occ upgrade` on a disposable copy (DB + `data/` snapshot); `occ db:add-missing-indices` reports nothing |
| Runtime | web login, file upload/download, sharing, WebDAV (`curl -u testuser ... /remote.php/dav/`), desktop/mobile client sync against staging, background jobs (`occ background-job:list` on recent versions), `nextcloud.log` |

## F. Recovery and rollback

- Backup: `config/`, `data/` (or a storage snapshot), `themes/` and the DB, all in maintenance mode.
- **Downgrades are not supported** by Nextcloud: rollback = restore code + config + DB + data from the same point in time.
- Limitations: large `data/` volumes make full copies impractical. Use storage snapshots and record the snapshot ID as the rollback checkpoint.

## G. Sources

- https://docs.nextcloud.com/server/latest/admin_manual/installation/system_requirements.html
- https://docs.nextcloud.com/server/latest/admin_manual/maintenance/upgrade.html
- https://github.com/nextcloud/server/wiki/Maintenance-and-Release-Schedule
- https://nextcloud.com/security/ (links to the advisories)
- https://github.com/nextcloud/security-advisories/security/advisories
- https://endoflife.date/nextcloud (secondary)
- Verified: 2026-10-24.
