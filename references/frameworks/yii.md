# Yii

**Last verified: 2026-10-24.** endoflife.date has no Yii data, so lifecycle status is **unknown** in the detector. Use the official release-cycle page.

## A. Project identification

- Website: https://www.yiiframework.com. Yii 2 guide: https://www.yiiframework.com/doc/guide/2.0/en. Source: Yii 2 https://github.com/yiisoft/yii2; Yii 1.1 https://github.com/yiisoft/yii; Yii 3 packages under https://github.com/yiisoft.
- **Yii 2 signals**: `yiisoft/yii2` in the lock file; a `yii` console script at the root; the basic template's `config/web.php`, `web/index.php`, `controllers/`, `models/`, `views/`; the advanced template's `common/`, `frontend/`, `backend/`, `console/`, `environments/`.
- **Yii 1.1 signals**: `protected/` (with `config/main.php`, `controllers/`, `yiic.php`), and a bundled `framework/yii.php` or `yiisoft/yii` in Composer.
- **Yii 3**: many `yiisoft/*` packages (e.g. `yiisoft/yii-http`, `yiisoft/di`, `yiisoft/config`) and no `yiisoft/yii2`. It is a different framework, not an upgrade target for Yii 2 apps without a rewrite.
- Version: `composer show yiisoft/yii2`; `Yii::getVersion()` reads `BaseYii::getVersion()` in `vendor/yiisoft/yii2/BaseYii.php`.

## B. PHP compatibility

- Official: release cycle https://www.yiiframework.com/release-cycle; requirements in the Yii 2 guide ("Installing Yii") and the `require.php` constraint of `yiisoft/yii2` in the target release.
- Yii 2 keeps a very wide PHP range across 2.0.x patch releases. Newer PHP branches are supported by updating **within 2.0.x**. Check the CHANGELOG of the 2.0.x release for PHP 8.x fixes.
- Yii 1.1: check the release-cycle page for its support status. Treat it as legacy and plan migration.
- Extensions: `mbstring`, `intl` (recommended), `ctype`, PDO driver, plus `gd`/`imagick` for image extensions. The bundled `requirements.php` checker of the app templates lists them (run it only on a local/CLI copy).
- Extensions ecosystem: many Yii 2 extensions (`yiisoft/yii2-*` and third-party) declare their own PHP constraints. `composer why-not php <target>`.

## C. Upgrade strategy

- Official: `framework/UPGRADE.md` in the Yii 2 repo (https://github.com/yiisoft/yii2/blob/master/framework/UPGRADE.md) lists breaking changes per 2.0.x release. Read every entry between your version and the target.
- Sequence (Yii 2):
  1. Patch PHP.
  2. `composer update yiisoft/yii2 yiisoft/yii2-* -W` to the latest 2.0.x.
  3. Apply the UPGRADE.md notes.
  4. Move PHP to the target branch.
  5. Run the tests.
- Bower/NPM assets: older Yii 2 apps use `fxp/composer-asset-plugin`, which is abandoned. Recent templates use the asset-packagist repository. Switching is a dependency change; plan it separately.
- Yii 1.1 → Yii 2: a rewrite (different namespaces, ActiveRecord API, widgets). Guide: https://www.yiiframework.com/doc/guide/2.0/en/intro-upgrade-from-v1.
- Config: `config/web.php`/`main.php` components (`request.cookieValidationKey` is a secret, so never print it), `db.php` (credentials).
- Database: Yii migrations in `migrations/` or `console/migrations/`.

## D. Automated migration tooling

- Rector PHP sets for language upgrades. There is no official Yii Rector set; write custom rules for framework API changes.
- PHPStan, with the `proget-hq/phpstan-yii2` extension (community) for Yii 2 magic properties if the project uses it.
- PHPCompatibility for Yii 1.1 codebases.
- Manual: ActiveRecord behaviours, RBAC (`authManager`) data, URL rules, widgets with removed parameters.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `php -l` over app code; `php yii help` (console boots) |
| Security | `composer audit`; runtime check |
| Static | `vendor/bin/phpstan analyse`; PHPCompatibility |
| Tests | `vendor/bin/codecept run` (app templates ship Codeception unit/functional/acceptance suites; acceptance needs a running server) |
| DB | `php yii migrate/history`; `php yii migrate/new` (pending); `php yii migrate` on a disposable DB; `php yii migrate/down 1` there |
| Runtime | `php yii serve` (basic template) or the container; HTTP smoke tests; check `runtime/logs/app.log` |

## F. Recovery and rollback

- Commit per stage; Yii migrations support `down()`/`safeDown()`, but use a DB restore as the authoritative rollback.
- Clear `runtime/cache` and `web/assets/*` after code rollback.
- Limitations: the advanced template's `environments/` + `php init` overwrite local config, so never re-run `init` on a configured environment.

## G. Sources

- https://www.yiiframework.com/release-cycle
- https://github.com/yiisoft/yii2/blob/master/framework/UPGRADE.md
- https://www.yiiframework.com/doc/guide/2.0/en/intro-upgrade-from-v1
- https://github.com/yiisoft/yii2/security/advisories
- https://www.yiiframework.com/doc/guide/2.0/en
- Verified: 2026-10-24.
