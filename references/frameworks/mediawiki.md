# MediaWiki

**Last verified: 2026-10-24.** Lifecycle from endoflife.date via [framework-lifecycle.json](framework-lifecycle.json). Confirm on the official Version lifecycle page.

## A. Project identification

- Website/docs: https://www.mediawiki.org. Source: https://gerrit.wikimedia.org/g/mediawiki/core (canonical), mirrored at https://github.com/wikimedia/mediawiki.
- Signals: `includes/Defines.php` (`MW_VERSION`), `maintenance/`, `extensions/`, `skins/`, `LocalSettings.php` (DB credentials, `$wgSecretKey`, `$wgUpgradeKey`: **never print**), `composer.local.json` (extension dependencies).
- Version: `define( 'MW_VERSION', '...' )` in `includes/Defines.php` (the detector reads it); `Special:Version` on the wiki; `php maintenance/run.php version` (the `run.php` entry point exists in recent versions; older ones use `php maintenance/version.php`).
- Generations: LTS releases (e.g. 1.39, 1.43) and short-lived non-LTS releases. Extensions and skins are branched per release as `REL1_xx`.

## B. PHP compatibility

- Official: https://www.mediawiki.org/wiki/Compatibility#PHP (PHP ranges per release) and https://www.mediawiki.org/wiki/Version_lifecycle.
- Lifecycle (endoflife.date, 2026-10-24): **1.46** (to 2027-07-31), **1.45** (to 2026-12-31), **1.43 LTS** (to 2027-12-31) supported; 1.44, 1.42, 1.41, 1.40 and **1.39 LTS** (2025-12-31) EOL. The official Version lifecycle page (read 2026-10-24) agrees and lists **1.47** as the next LTS, planned for November 2026.
- Each release has a minimum PHP and a set of PHP versions it is tested with. Check the compatibility table for the target.
- Extensions (PHP): `mbstring`, `xml`, `intl`, `json`, `fileinfo`, a DB driver (`mysqli`/`pdo_pgsql`/`pdo_sqlite`), plus recommended `apcu`; `luasandbox` for Scribunto if used.
- Extensions (MediaWiki): every extension must be on the `REL1_xx` branch matching core, or explicitly declare compatibility in `extension.json` (`requires.MediaWiki`).

## C. Upgrade strategy

- Official: https://www.mediawiki.org/wiki/Manual:Upgrading .
- Sequence:
  1. Patch PHP.
  2. Read `RELEASE-NOTES-1.xx` / `UPGRADE` for every version crossed.
  3. Download the new core (tarball or `git checkout REL1_xx`).
  4. Copy `LocalSettings.php`, `images/` and the extensions/skins, each **switched to its matching REL branch**.
  5. `composer update --no-dev` (with `composer.local.json` merged).
  6. `php maintenance/run.php update` (`php maintenance/update.php` on older versions) against the DB.
  7. Move PHP when supported.
- LTS → LTS jumps are the usual path. Check the release notes for the oldest version that supports a direct upgrade.
- `LocalSettings.php`: removed/renamed `$wg*` settings are listed in the release notes. Old extension loading with `require_once` should become `wfLoadExtension()`.

## D. Automated migration tooling

- No official Rector set. Use Rector PHP sets for custom extensions only.
- MediaWiki's codesniffer (`mediawiki/mediawiki-codesniffer`) and Phan (`mediawiki/mediawiki-phan-config`) are the standard static-analysis setups used by core and extensions.
- Manual: hooks (the hook system was reworked to interface-based handlers), deprecated global functions, skin APIs, `LocalSettings.php` options.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `php -l` on custom extensions; `composer validate`; `php maintenance/run.php checkComposerLockUpToDate` *(recent versions)* |
| Security | `composer audit`; runtime check; security releases via https://lists.wikimedia.org/postorius/lists/mediawiki-announce.lists.wikimedia.org/ |
| Static | Phan / codesniffer on custom extensions |
| Tests | core/extension PHPUnit: `composer phpunit:entrypoint` or `php tests/phpunit/phpunit.php` depending on the version *(example)*; needs a test DB, otherwise `blocked` |
| DB | `run.php update` on a disposable copy; re-run reports nothing to do |
| Runtime | Main Page, page view/edit/save, search, login, file upload, `Special:Version` lists the expected extensions, job queue (`php maintenance/run.php runJobs` on staging), API (`api.php?action=query&meta=siteinfo`) |

## F. Recovery and rollback

- Backup: DB (`mysqldump`) + `images/` + `LocalSettings.php` + extensions.
- `update.php` schema changes are one-way, so rollback = restore DB + code.
- Limitations: extensions without a REL branch for the target are blockers.

## G. Sources

- https://www.mediawiki.org/wiki/Compatibility
- https://www.mediawiki.org/wiki/Version_lifecycle
- https://www.mediawiki.org/wiki/Manual:Upgrading
- https://lists.wikimedia.org/postorius/lists/mediawiki-announce.lists.wikimedia.org/
- https://endoflife.date/mediawiki (secondary)
- Verified: 2026-10-24.
