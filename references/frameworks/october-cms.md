# October CMS

**Last verified: 2026-10-24.** endoflife.date has no October CMS data, so lifecycle is **unknown** in the detector. Use the official docs and changelog.

## A. Project identification

- Website: https://octobercms.com. Docs: https://docs.octobercms.com. Source: https://github.com/octobercms/october.
- Signals: `modules/system/`, `modules/cms/`, `modules/backend/`, `plugins/<author>/<plugin>/`, `themes/`, `artisan`, `config/cms.php`. Composer packages (v2+): `october/system`, `october/rain`, `october/all`.
- October is **built on Laravel**. The detector reports Laravel as a component of October (not a separate app); the underlying `laravel/framework` major determines most PHP constraints.
- Version: `composer show october/system` / `october/rain`; v1 (Composer-less installs) stores the build in the database (`system_parameters`), visible in Settings → Updates.
- Generations: **v1** (free, builds 4xx, Laravel 6 era, marketplace updates through the backend); **v2/v3+** (licensed, Composer-managed, `php artisan october:*` commands, project licence key in `auth.json`/env). **Winter CMS** (https://wintercms.com) is a community fork of v1 with its own upgrade path; detect it by the `winter/*` packages and treat it separately.

## B. PHP compatibility

- Official: the installation requirements in the docs for your major (https://docs.octobercms.com, "Installation" / "System Requirements"), plus the `php` constraint of `october/rain` in the target release.
- PHP range = intersection of the October release's own constraint and its Laravel major's range (see [laravel.md](laravel.md)). An October release built on an EOL Laravel major inherits that Laravel's PHP ceiling.
- Extensions: as for Laravel, plus `gd`, `zip`, `curl`.
- Plugins: each marketplace plugin declares its own requirements. Abandoned v1 plugins are a common blocker.

## C. Upgrade strategy

- Official: the "Upgrade Guide" pages in the docs for each major (v1 → v2, v2 → v3, ...) and the changelog https://octobercms.com/changelog.
- v2+ sequence:
  1. Patch PHP.
  2. `php artisan october:update` (or `composer update` with the licensed repository credentials) within the current major.
  3. Follow the upgrade guide for the next major; update `composer.json` constraints for `october/*`.
  4. `php artisan october:migrate`.
  5. Update plugins.
- v1 → v2+: requires a **licence** and Composer conversion. Without one, the options are staying on v1 (EOL runtime constraints) or moving to Winter CMS. This is a business decision for the user; document it, don't decide.
- Themes: Twig templates and `theme.yaml`. Check for removed Twig filters/functions in the target version.
- Plugins: `Plugin.php` `registerComponents`, `boot()`, `updates/version.yaml` migrations.
- Database: plugin migrations in `plugins/*/updates/` run on `october:migrate`.

## D. Automated migration tooling

- Rector (PHP sets, plus rector-laravel sets for the underlying Laravel major) for custom plugins.
- PHPStan/Larastan may need stubs for October's facades.
- Manual: plugin APIs, backend controllers/behaviours (`FormController`, `ListController`), Twig changes, marketplace plugins (update from vendor; don't patch in place).

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `php -l plugins/<author>`; `php artisan october:about` / `php artisan --version` *(availability depends on the version)* |
| Security | `composer audit`; runtime check; marketplace plugin update list |
| Static | `vendor/bin/phpstan analyse` (custom plugins) |
| Tests | `vendor/bin/phpunit` in plugin directories that ship `phpunit.xml` (October provides a `PluginTestCase`); otherwise `blocked` |
| DB | `php artisan october:migrate` on a disposable DB |
| Runtime | front-end pages per theme layout, backend login, CMS editing, form submissions, mail; `storage/logs/system.log` |

## F. Recovery and rollback

- Backup DB + `storage/app` (media/uploads) + code. Plugin migrations may be irreversible.
- `php artisan cache:clear` and clear `storage/cms/cache` after rollback.
- Limitations: licensed Composer repository access is needed to install v2+ packages. Without it, installation is `blocked`.

## G. Sources

- https://docs.octobercms.com
- https://octobercms.com/changelog
- https://github.com/octobercms/october
- https://github.com/octobercms/october/security/advisories
- https://wintercms.com (fork, for v1 sites)
- Unverified: exact PHP ranges per October major. Read them from the installation docs for the version in use.
- Verified: 2026-10-24.
