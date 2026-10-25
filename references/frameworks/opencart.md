# OpenCart

**Last verified: 2026-10-24.** endoflife.date has no OpenCart data, so lifecycle is **unknown** in the detector. Use the official releases.

## A. Project identification

- Website: https://www.opencart.com. Docs: https://docs.opencart.com. Source: https://github.com/opencart/opencart (the release archives contain an `upload/` directory that becomes the web root).
- Signals: `system/startup.php`, `system/library/`, `catalog/controller/`, `admin/controller/`, `config.php` and `admin/config.php` (DB credentials: **never print**), `image/`, `storage/` (4.x; recommended outside the web root).
- Version: `define('VERSION', '...')` in `index.php` / `admin/index.php` (the detector reads `index.php`). Admin footer shows the version.
- Generations: **1.5.x / 2.x** (legacy), **3.0.x** (Twig templates, OCMOD), **4.x** (namespaced extensions under `extension/<vendor>/`, a new event system, `system/config/`). Extensions are **not** compatible across 3 ↔ 4.
- Modification systems: **OCMOD** (`system/storage/modification/`, generated) and **vQmod** (`vqmod/`). Both patch core files at runtime, which makes upgrades fragile.

## B. PHP compatibility

- Official: the release notes on GitHub (https://github.com/opencart/opencart/releases) state the PHP requirement per release, and `install/` checks requirements during installation.
- 3.0.x releases target older PHP and produce deprecations/errors on PHP 8.x unless patched; 4.x targets PHP 8. Confirm in the release notes for your exact version, because OpenCart's minimums have changed between point releases.
- Extensions: `curl`, `gd`, `mbstring`, `mysqli`, `openssl` (or `mcrypt` for very old versions), `zip`, `zlib`.
- Third-party extensions (OpenCart Marketplace) are tied to specific OpenCart versions.

## C. Upgrade strategy

- Official: the upgrade instructions in the docs/README of the target release (https://docs.opencart.com and the `upgrade` notes shipped in the release).
- Within 3.0.x: replace the files (keep `config.php`, `admin/config.php`, `image/`, custom theme/extension files), then run the upgrade script in `/install/` to update the DB. Delete `/install/` afterwards.
- 3.x → 4.x: effectively a **migration**. Extensions and themes must be replaced with 4.x versions, and custom code rewritten to the 4.x extension structure. Plan it as a separate project.
- Before anything: **diff the installation against a pristine copy of the same release** to find core modifications. They are common in OpenCart shops and will be overwritten.
- OCMOD/vQmod: refresh modifications after the upgrade (Extensions → Modifications → Refresh) and re-test each one.

## D. Automated migration tooling

- No official Rector set. Use Rector PHP sets and PHPCompatibility on custom extensions and modified core files.
- Diff tooling (`diff -ruN pristine/ site/`) is the most important "tool" here.
- Manual: OCMOD XML patches, payment/shipping extensions, Twig template changes, 3 → 4 rewrites.

## E. Test plan

| Layer | Command / action |
|---|---|
| Structural | `php -l` over `catalog/`, `admin/`, `system/` custom files and extensions; modification refresh succeeds |
| Security | runtime check; GitHub advisories https://github.com/opencart/opencart/security/advisories; extension vendor notices |
| Static | PHPCompatibility on custom code |
| Tests | no test suite in shop installs, so mark the suite `blocked` with a reason; rely on HTTP smoke tests |
| DB | run `/install/` upgrade on a disposable copy |
| Runtime | storefront home, category, product, search, cart, checkout with sandbox payment, customer login/registration; admin login, orders, products; check `system/storage/logs/error.log` |

## F. Recovery and rollback

- Backup files (including `image/` and `system/storage/`) + DB.
- Rollback = restore both, then refresh modifications and clear the theme cache.
- Limitations: heavily modified cores make every upgrade a merge exercise. Document each modification and its owner.

## G. Sources

- https://github.com/opencart/opencart/releases
- https://docs.opencart.com
- https://github.com/opencart/opencart/security/advisories
- https://www.opencart.com
- Unverified: exact PHP ranges per OpenCart release. Read them from the release notes of the target version.
- Verified: 2026-10-24.
