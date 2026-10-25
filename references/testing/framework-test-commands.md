# Framework test commands

**Last verified: 2026-10-24.** Common entry points. Commands marked *(example)* depend on project setup and must be adapted. Always prefer what the project's own `composer.json` scripts, `Makefile`, or CI workflow run: **CI config is the best evidence of how the suite is meant to run.**

| Framework | Test suite | Config / health checks | Migration status |
|---|---|---|---|
| Laravel | `php artisan test` or `vendor/bin/phpunit` / `vendor/bin/pest` | `php artisan about`, `php artisan route:list`, `php artisan config:cache` then `config:clear` | `php artisan migrate:status`, `php artisan migrate --pretend` |
| Symfony | `vendor/bin/phpunit` or `bin/phpunit` (older symfony/phpunit-bridge setups) | `bin/console lint:container`, `bin/console lint:yaml config`, `bin/console lint:twig templates`, `bin/console debug:router` | `bin/console doctrine:migrations:status`, `bin/console doctrine:schema:validate` |
| WordPress | project PHPUnit with WP test library *(example)* | `wp core version`, `wp core verify-checksums`, `wp plugin list --update=available`, `wp theme list` | `wp core update-db --dry-run` |
| Drupal | `vendor/bin/phpunit -c core` (core test runner; needs `SIMPLETEST_DB`) *(example)* | `drush status`, `drush pm:list --status=enabled`, `drush updatedb:status` | `drush updatedb:status`, `drush updatedb` (disposable DB only) |
| CodeIgniter 4 | `vendor/bin/phpunit` | `php spark routes`, `php spark env` | `php spark migrate:status` |
| Yii 2 | `vendor/bin/codecept run` | `php yii help` | `php yii migrate/history`, `php yii migrate/new` |
| CakePHP | `vendor/bin/phpunit` | `bin/cake routes` | `bin/cake migrations status` |
| Joomla | project tests if any *(example)*; core uses PHPUnit + Cypress | System → System Information; `php cli/joomla.php core:check-updates` *(example, Joomla 4+ CLI)* | System → Maintenance: Database ("Fix") |
| October CMS | `vendor/bin/phpunit` (plugin tests) | `php artisan october:about` *(example, v3)* | `php artisan october:migrate` (disposable DB only) |
| SuiteCRM 7 | project tests if any | Admin → Repair → Quick Repair and Rebuild | Admin → Repair (schema sync) |
| SuiteCRM 8 | `vendor/bin/codecept run` *(example)* | `bin/console` *(Symfony app)* | `bin/console suitecrm:app:upgrade` per the upgrade guide *(example)* |
| EspoCRM | `vendor/bin/phpunit` (dev checkout) | `php command.php version` *(example)* | `php command.php rebuild` |
| Nextcloud | app tests: `vendor/bin/phpunit` *(example)* | `php occ status`, `php occ check`, `php occ app:list`, `php occ setupchecks` | `php occ upgrade` (disposable copy), `php occ db:add-missing-indices` |
| Magento / Adobe Commerce | `vendor/bin/phpunit -c dev/tests/unit/phpunit.xml.dist` | `bin/magento --version`, `bin/magento setup:di:compile`, `bin/magento module:status` | `bin/magento setup:db:status`, `bin/magento setup:upgrade` (disposable DB) |
| PrestaShop | `vendor/bin/phpunit` (dev checkout) | `php bin/console prestashop:module list` *(example)* | 1-Click Upgrade / Update Assistant module |
| OpenCart | project tests if any | Admin → Dashboard / Maintenance | upgrade via `/install` (OpenCart 3) per upgrade guide |
| Slim | `vendor/bin/phpunit` | HTTP smoke tests against routes | app-specific |
| Dolibarr | `phpunit test/phpunit/AllTests.php` *(example; dev checkout)* | Home → Setup → About | `/install/upgrade.php` (disposable DB) |
| TYPO3 | `vendor/bin/phpunit` (extension tests via typo3/testing-framework) | `vendor/bin/typo3 list`, Install Tool → Environment | `vendor/bin/typo3 upgrade:list`, `vendor/bin/typo3 extension:setup` |
| Moodle | `vendor/bin/phpunit` after `php admin/tool/phpunit/cli/init.php`; Behat via `admin/tool/behat/cli/init.php` | `php admin/cli/check_database_schema.php`, `php admin/cli/checks.php` | `php admin/cli/upgrade.php` (disposable copy) |
| MediaWiki | `composer phpunit:entrypoint` / `php tests/phpunit/phpunit.php` (depends on version) *(example)* | `php maintenance/run.php version` (1.40+) | `php maintenance/run.php update` (disposable DB) |
| Laminas MVC / Mezzio | `vendor/bin/phpunit` | `vendor/bin/laminas` *(if laminas-cli installed)* | app-specific (Doctrine migrations if used) |
| Phalcon | `vendor/bin/phpunit` or `vendor/bin/codecept run` | `php -m \| grep phalcon`, `php -r "echo Phalcon\Support\Version::get();"` (v5) | Phalcon migrations (`phalcon/migrations`) *(example)* |
| phpMyAdmin | (dev checkout) `vendor/bin/phpunit` | login page loads; Settings → no config warnings | n/a (configuration storage tables: check via UI) |

## Generic

- Composer scripts: `composer run-script --list`, then `composer test` if defined.
- Syntax: see [testing-strategy.md](testing-strategy.md).
- HTTP smoke: `curl -fsS -o /dev/null -w '%{http_code}\n' http://localhost:8080/health`, plus key pages and authenticated flows with test accounts only.
