# TYPO3

**Last verified: 2026-10-24.** Lifecycle from endoflife.date via [framework-lifecycle.json](framework-lifecycle.json). Confirm on https://get.typo3.org.

## A. Project identification

- Website: https://typo3.org. Docs: https://docs.typo3.org. Source: https://github.com/TYPO3/typo3 (mirror; review happens at https://review.typo3.org).
- **Composer mode** signals: `typo3/cms-core` in the lock file, `public/typo3/`, `vendor/bin/typo3`, `config/system/settings.php` (v12+; DB credentials and `encryptionKey`: **never print**). ≤ v11: `public/typo3conf/LocalConfiguration.php`.
- **Legacy (non-Composer) mode** signals: `typo3/sysext/core/`, `typo3conf/`, `typo3_src` symlink to a source package.
- Version: `typo3/cms-core` in the lock file; `Typo3Version::VERSION` in `typo3/sysext/core/Classes/Information/Typo3Version.php` (the detector reads it); the backend → Help → About; `vendor/bin/typo3` prints the version in its banner.
- Generations: LTS majors (9.5, 10.4, 11.5, 12.4, 13.4, 14.x). Upgrades go **LTS to LTS**.

## B. PHP compatibility

- Official: the system requirements per version at https://get.typo3.org (e.g. https://get.typo3.org/version/13) and the installation guide.
- Lifecycle (endoflife.date, 2026-10-24): **14** (to 2029-06-30) and **13** (to 2027-12-31) supported; **12** EOL 2026-04-30; 11 and older EOL. TYPO3 GmbH sells **ELTS** (extended support) for EOL LTS versions (https://typo3.com/services/extended-support-elts). ELTS patches the CMS, but a PHP2Shell fix still has to come from the PHP runtime.
- Each LTS supports a specific PHP range. Check get.typo3.org for the target, then extensions via `composer why-not php <target>`.
- Extensions (PHP): `pdo` + driver, `json`, `pcre`, `session`, `xml`, `filter`, `hash`, `mbstring`, `openssl`, `intl`, `zip`, `zlib`, `gd` or `imagick`/GraphicsMagick (per the system requirements).

## C. Upgrade strategy

- Official: https://docs.typo3.org/m/typo3/reference-coreapi/main/en-us/Administration/Upgrade/Major/Index.html (major upgrade procedure) and the core changelog with Breaking/Deprecation/Feature entries per version: https://docs.typo3.org/c/typo3/cms-core/main/en-us/Index.html.
- Sequence:
  1. Patch PHP.
  2. Update to the latest patch of the current LTS.
  3. Fix deprecations (the deprecation log; the Extension Scanner in the Install Tool → Upgrade → "Scan Extension Files").
  4. Update third-party extensions to versions supporting the next LTS (TER: https://extensions.typo3.org; Packagist).
  5. Bump all `typo3/cms-*` constraints together.
  6. `composer update`.
  7. `vendor/bin/typo3 upgrade:list` → `vendor/bin/typo3 upgrade:run` (upgrade wizards).
  8. Install Tool → "Analyze Database Structure" (apply only safe changes; review drops).
  9. `vendor/bin/typo3 cache:flush`.
- Legacy mode → Composer mode is recommended and documented in the installation guide ("Migrate to Composer"). Do it as a separate stage.
- TypoScript/TSconfig and Fluid templates change between LTS versions. Review the Breaking changelog entries for each version you cross.

## D. Automated migration tooling

- **TYPO3 Rector** (https://github.com/sabbelasichon/typo3-rector): community-maintained, with per-version sets (e.g. `Typo3LevelSetList::UP_TO_TYPO3_13`).
- **Fractor** (from the same ecosystem) for non-PHP files (FlexForms, TypoScript, Fluid, composer.json).
- Extension Scanner (built in) for deprecated core API use.
- `saschaegerer/phpstan-typo3` (community) for PHPStan.
- Manual: TCA changes, Extbase persistence configuration, hooks replaced by PSR-14 events, backend modules.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `php -l` on `packages/` / `public/typo3conf/ext/<custom>`; `vendor/bin/typo3 list` (CLI boots) |
| Security | `composer audit`; TYPO3 security bulletins https://typo3.org/help/security-advisories; runtime check |
| Static | Extension Scanner; `vendor/bin/rector process --dry-run` (typo3-rector); `vendor/bin/phpstan analyse` |
| Tests | `vendor/bin/phpunit` for extension unit/functional tests via `typo3/testing-framework` (functional tests need a DB, otherwise `blocked`) |
| DB | `vendor/bin/typo3 upgrade:list` shows nothing pending after `upgrade:run` on a disposable copy; database analyzer clean |
| Runtime | front end per site/language, backend login, page/content editing, forms (`EXT:form`), scheduler tasks (`vendor/bin/typo3 scheduler:run` on staging); `var/log/typo3_*.log` |

## F. Recovery and rollback

- Backup the DB + `fileadmin/` + `config/` (or `typo3conf/`) + code.
- Upgrade wizards and schema changes are one-way, so rollback = restore DB + code; `cache:flush`.
- Limitations: TER extensions without a release for the target LTS are blockers. List them with alternatives.

## G. Sources

- https://get.typo3.org
- https://docs.typo3.org/m/typo3/reference-coreapi/main/en-us/Administration/Upgrade/Major/Index.html
- https://docs.typo3.org/c/typo3/cms-core/main/en-us/Index.html
- https://typo3.org/help/security-advisories
- https://github.com/sabbelasichon/typo3-rector
- https://typo3.com/services/extended-support-elts
- https://endoflife.date/typo3 (secondary)
- Verified: 2026-10-24.
