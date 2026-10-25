# PrestaShop

**Last verified: 2026-10-24.** endoflife.date has no PrestaShop data, so lifecycle is **unknown** in the detector. Use the official devdocs.

## A. Project identification

- Website: https://www.prestashop.com (project: https://www.prestashop-project.org). Developer docs: https://devdocs.prestashop-project.org. Source: https://github.com/PrestaShop/PrestaShop.
- Signals: `config/defines.inc.php`, `classes/PrestaShopAutoload.php`, `classes/`, `controllers/`, `modules/`, `themes/`, `override/`, and an admin directory with a **randomised name** (`admin123abc/`). 1.7+/8/9: `app/AppKernel.php` (Symfony kernel), `app/config/parameters.php` (DB credentials and cookie keys: never print), `bin/console`. 1.6: `config/settings.inc.php` (credentials and `_PS_VERSION_`: never print).
- Version: `const VERSION` in `app/AppKernel.php` (1.7+), or `_PS_INSTALL_VERSION_` in `install/install_version.php` if the installer folder still exists (it should not in production). The detector reads these; it never reads `settings.inc.php`. Admin: Advanced Parameters → Information.
- Generations: **1.6** (legacy, Smarty-only back office), **1.7** (partly Symfony back office), **8.x**, **9.x** (Symfony-based, newer PHP). PrestaShop embeds Symfony; the detector reports it as a component.

## B. PHP compatibility

- Official: system requirements per major, e.g. https://devdocs.prestashop-project.org/8/basics/installation/system-requirements/ and https://devdocs.prestashop-project.org/9/basics/installation/system-requirements/ (PHP ranges, MySQL, extensions).
- Each major supports a bounded PHP range, and 1.6/1.7 stop at old PHP versions. A PrestaShop 1.6 shop cannot run on a supported PHP branch, so its runtime remediation depends on a PrestaShop upgrade (or containment, see [../migration/legacy-applications.md](../migration/legacy-applications.md)).
- Extensions (devdocs): `curl`, `dom`, `fileinfo`, `gd`, `iconv`, `intl`, `json`, `mbstring`, `openssl`, `pdo_mysql`, `simplexml`, `zip`.
- Modules and themes from PrestaShop Addons declare compatible versions. Check each one.

## C. Upgrade strategy

- Official: https://devdocs.prestashop-project.org/8/basics/keeping-up-to-date/upgrade/ (and the 9.x equivalent), using the **Update Assistant** module (`autoupgrade`, https://github.com/PrestaShop/autoupgrade), formerly "1-Click Upgrade". It also offers a CLI (`modules/autoupgrade/cli-upgrade.php`, per its README).
- Sequence (staging):
  1. Patch PHP within a range that the current version supports.
  2. Update modules/themes to versions compatible with the target.
  3. Run the Update Assistant to the target (check whether it requires intermediate versions, e.g. via 1.7.8 / 8.x).
  4. Clear the cache (`var/cache`).
  5. Move PHP to the target range.
  6. Regenerate the theme assets.
- `override/` classes are the biggest risk: they replace core classes and break silently. Inventory them; disable overrides on staging (Advanced Parameters → Performance) to find dependencies.
- Payment modules: test against sandbox gateways only.

## D. Automated migration tooling

- No official Rector set. Use Rector PHP sets and PHPCompatibility on custom modules and `override/`.
- PHPStan with the PrestaShop stubs/`prestashop/php-dev-tools` (official dev tooling for module developers) where the project uses it.
- Manual: overrides, hooks (renamed/removed hooks between majors), Smarty → Twig back-office changes, module `install()`/`upgrade` scripts.

## E. Test plan

| Layer | Command / action |
|---|---|
| Structural | `php -l` over `modules/<custom>`, `override/`, `themes/<custom>`; `php bin/console` lists commands (1.7+) |
| Security | `composer audit` (root `composer.lock` in 1.7+); module updates; PrestaShop security advisories https://github.com/PrestaShop/PrestaShop/security/advisories; Friends-of-Presta module advisories (secondary, https://security.friendsofpresta.org) |
| Static | PHPCompatibility on custom modules/overrides |
| Tests | shop instances rarely have tests, so mark the suite `blocked` with a reason; module repos may have `vendor/bin/phpunit` |
| DB | Update Assistant run on a disposable copy |
| Runtime | storefront home, category, product, search, cart, checkout with sandbox payment, customer account; back-office login, order view, catalogue edit; `var/logs/` |

## F. Recovery and rollback

- The Update Assistant can back up files/DB, but take your **own** backup as well and test restoring it.
- Rollback = restore files + DB + `var/cache` clear.
- Limitations: the randomised admin directory name and `parameters.php` must be preserved; paid Addons modules may require account access.

## G. Sources

- https://devdocs.prestashop-project.org/8/basics/installation/system-requirements/
- https://devdocs.prestashop-project.org/9/basics/installation/system-requirements/
- https://devdocs.prestashop-project.org/8/basics/keeping-up-to-date/upgrade/
- https://github.com/PrestaShop/autoupgrade
- https://github.com/PrestaShop/PrestaShop/security/advisories
- Verified: 2026-10-24.
