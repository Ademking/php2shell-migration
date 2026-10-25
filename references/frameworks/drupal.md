# Drupal

**Last verified: 2026-10-24.** Re-check the official PHP requirements and release schedule before acting.

## A. Project identification

- Website: https://www.drupal.org. Docs: https://www.drupal.org/docs. Source: https://git.drupalcode.org/project/drupal.
- Signals (8+): `core/lib/Drupal.php` (or `web/core/lib/Drupal.php` with the recommended-project layout), `drupal/core` or `drupal/core-recommended` in the lock file, `sites/default/settings.php` (contains DB credentials: never print), and `vendor/bin/drush`.
- Drupal 7: `includes/bootstrap.inc` with `define('VERSION', '7.x')`, `sites/all/modules`, and no Composer.
- Version: `const VERSION` in `core/lib/Drupal.php` (the detector reads it); `drush status` (bootstraps Drupal); `composer show drupal/core`.
- Generations: **7** (procedural, EOL 2025-01-05) vs **8 to 11** (Symfony-based, Composer). 7 → 10/11 is a **migration** (content migrated into a new site), not an upgrade. 8 → 9 → 10 → 11 are in-place upgrades.

## B. PHP compatibility

- Official: https://www.drupal.org/docs/getting-started/system-requirements/php-requirements; release schedule: https://www.drupal.org/about/core/policies/core-release-cycles/schedule.
- Lifecycle (endoflife.date, 2026-10-24): **11.4** (to 2027-07-07), **11.3** and **10.6** (to 2026-12-16) supported; 11.2, 10.5 and older **EOL**. Drupal security support is per **minor** release, so a site on an old minor of a supported major is still unsupported.
- PHP minimums move with majors (11.x requires a newer PHP than 10.x). Confirm on the requirements page, then run `composer why-not php <target>` for contrib modules.
- Extensions: the requirements page lists them (PDO driver, `gd`, `json`, `opcache` recommended, `xml`, `mbstring`, ...).
- Unsupported: Drupal 7 (EOL; commercial extended support exists), 8, 9, and 10/11 minors past their dates. Contrib modules without a release for your major: check the project page compatibility field.

## C. Upgrade strategy

- Official: https://www.drupal.org/docs/upgrading-drupal; the major-version upgrade docs under it (e.g. "Upgrading from Drupal 10 to Drupal 11").
- In-place major upgrade sequence:
  1. Patch PHP.
  2. Update to the latest minor of the current major (`composer update "drupal/core-*" -W`, then `drush updatedb`, `drush cache:rebuild`).
  3. Install **Upgrade Status** (https://www.drupal.org/project/upgrade_status) and fix every reported deprecation in custom code.
  4. Update or replace contrib modules to versions compatible with both majors.
  5. Remove modules deprecated or removed from core (install their contrib replacements first).
  6. Bump `drupal/core-recommended`, `drupal/core-composer-scaffold` and `drupal/core-project-message` together.
  7. Run `drush updatedb`, then `drush config:export` and review the config diff.
- Drupal 7: plan a migration with the Migrate API (https://www.drupal.org/docs/upgrading-drupal). Rebuild the theme and custom modules. This is a project in its own right; for PHP2Shell, the short term is a patched runtime + extended support, documented in the plan.
- Config: `drush config:status` before/after; never import config from another environment blindly.
- Patches: `cweagans/composer-patches` entries in `composer.json` must be re-validated against new versions.

## D. Automated migration tooling

- **drupal-rector** (https://github.com/palantirnet/drupal-rector): deprecation fixes for custom modules/themes.
- **Upgrade Status** module: scans for deprecated API use (runs `mglaman/phpstan-drupal` under the hood).
- Project Update Bot patches for contrib (on drupal.org issues).
- `phpstan-drupal` + `phpstan-deprecation-rules` for CI.
- Manual: hooks converted to OOP hooks in recent versions, render arrays, access callbacks, Twig template overrides, entity schema changes.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `php -l` on `web/modules/custom`, `web/themes/custom`; `drush status` |
| Security | `drush pm:security` (lists insecure core/contrib via drupal.org advisories); `composer audit`; runtime check |
| Static | Upgrade Status report (`drush upgrade_status:analyze --all`, if the module provides the command); `vendor/bin/phpstan analyse` with phpstan-drupal |
| Tests | `vendor/bin/phpunit -c web/core web/modules/custom` (needs `SIMPLETEST_DB`, `SIMPLETEST_BASE_URL` for kernel/functional tests); `blocked` if no DB |
| DB | `drush updatedb:status`, `drush updatedb` on a disposable DB; then check the status report for entity/field definition mismatches |
| Runtime | `drush cache:rebuild`; status report (`/admin/reports/status`) on staging; HTTP smoke for front page, login, node view/edit, forms, Views pages |

Evidence: no pending updates, status report free of errors, custom-code tests pass, `drush pm:security` clean.

## F. Recovery and rollback

- DB backup (`drush sql:dump` on staging/disposable only) + files directory (`sites/default/files`) + code commit.
- `drush updatedb` hooks are one-way: rollback = restore DB + previous code.
- `drush config:export` before and after; keep the pre-upgrade config in Git.
- Limitations: contrib modules without a compatible release are hard blockers. List them with owners.

## G. Sources

- https://www.drupal.org/docs/getting-started/system-requirements/php-requirements
- https://www.drupal.org/about/core/policies/core-release-cycles/schedule
- https://www.drupal.org/docs/upgrading-drupal
- https://www.drupal.org/project/upgrade_status
- https://github.com/palantirnet/drupal-rector
- https://www.drupal.org/security
- https://endoflife.date/drupal (secondary)
- Verified: 2026-10-24.
