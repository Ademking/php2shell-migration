# Magento Open Source / Adobe Commerce

**Last verified: 2026-10-24.** Lifecycle from endoflife.date via [framework-lifecycle.json](framework-lifecycle.json). Adobe's system-requirements page is authoritative.

## A. Project identification

- Product: Magento Open Source and Adobe Commerce (https://business.adobe.com/products/magento/magento-commerce.html). Docs: https://experienceleague.adobe.com/en/docs/commerce. Source: https://github.com/magento/magento2. Community fork: Mage-OS (https://mage-os.org), with its own release line.
- Signals: `bin/magento`, `app/etc/di.xml`, `app/etc/config.php` (module list), `app/etc/env.php` (DB credentials, crypt key: **never print**), `pub/`, `generated/`, `var/`. Edition by meta-package in the lock: `magento/product-community-edition` (Open Source) or `magento/product-enterprise-edition` (Adobe Commerce); Adobe Commerce Cloud adds `magento/magento-cloud-metapackage` and `.magento.app.yaml`.
- Version: the meta-package version in `composer.lock`; `bin/magento --version`.
- Generations: **Magento 1** (`app/Mage.php`, `app/etc/local.xml`) is EOL since 2020 and needs a re-platform via the Data Migration Tool. **Magento 2.x** upgrades in place; patch levels are named `2.4.7-p3` style.

## B. PHP compatibility

- Official: system requirements https://experienceleague.adobe.com/en/docs/commerce-operations/installation-guide/system-requirements (PHP, MySQL/MariaDB, OpenSearch, Redis, Varnish, RabbitMQ, Composer per release), and the lifecycle policy https://experienceleague.adobe.com/en/docs/commerce-operations/release/planning/lifecycle-policy.
- Lifecycle data (endoflife.date, 2026-10-24, `supportedPhpVersions` as recorded there; confirm with Adobe):

  | Release | PHP | Status |
  |---|---|---|
  | 2.4.9 | 8.5 (per data source; confirm the full range on Adobe's page) | supported |
  | 2.4.8 | 8.3, 8.4 | supported |
  | 2.4.7 | 8.2, 8.3 | supported |
  | 2.4.6 | 8.1, 8.2 | supported |
  | ≤ 2.4.5 | ≤ 8.1 | **EOL** |

- Magento constrains **service versions** too (OpenSearch/Elasticsearch, MariaDB/MySQL, Redis). A PHP move often implies a release move, which implies service upgrades. Plan them together.
- Extensions (PHP): `bcmath`, `ctype`, `curl`, `dom`, `fileinfo`, `filter`, `gd`, `hash`, `iconv`, `intl`, `json`, `libxml`, `mbstring`, `openssl`, `pcre`, `pdo_mysql`, `simplexml`, `soap`, `sockets`, `sodium`, `tokenizer`, `xmlwriter`, `xsl`, `zip` (per system requirements).

## C. Upgrade strategy

- Official: the upgrade guide https://experienceleague.adobe.com/en/docs/commerce-operations/upgrade-guide/overview, including "Perform an upgrade" with the Composer root update plugin.
- Security first: Adobe ships **security patch releases** (`-pN`) and **isolated security patches** for supported lines. Apply the latest `-p` for your line before any feature upgrade.
- Sequence (staging):
  1. Patch PHP.
  2. `bin/magento maintenance:enable`.
  3. `composer require-commerce magento/product-community-edition 2.4.8-pN --no-update` (via `magento/composer-root-update-plugin`), then `composer update`.
  4. `bin/magento setup:upgrade`.
  5. `bin/magento setup:di:compile`.
  6. `bin/magento setup:static-content:deploy -f` (production mode).
  7. `bin/magento indexer:reindex`, `bin/magento cache:flush`.
  8. `bin/magento maintenance:disable`.
- Third-party modules (Marketplace and custom `app/code/<Vendor>`): check each vendor's compatibility statement for the target release. They are the usual blocker.
- Database: `setup:upgrade` runs schema/data patches (declarative schema, `db_schema.xml`), so it is effectively one-way.
- Breaking areas: removed/changed core classes used in plugins/preferences (`di.xml`), Laminas package majors, PHPUnit major in dev tests, Elasticsearch → OpenSearch moves.

## D. Automated migration tooling

- **Upgrade Compatibility Tool (UCT)** (Adobe Commerce; https://experienceleague.adobe.com/en/docs/commerce-operations/upgrade-guide/upgrade-compatibility-tool/overview): scans custom code against a target version.
- **Quality Patches Tool** (`magento/quality-patches`, `vendor/bin/magento-patches status`) for patches.
- Rector PHP sets + `magento/magento-coding-standard` (PHP_CodeSniffer standard, includes PHPCompatibility checks).
- PHPStan with `bitexpert/phpstan-magento` (community) for factory/proxy generation.
- Manual: plugins (interceptors), preferences overriding core classes, payment/shipping integrations, GraphQL schema changes.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `bin/magento setup:di:compile` (fails on many incompatibilities); `bin/magento module:status` |
| Security | `composer audit`; `vendor/bin/magento-patches status`; Adobe security bulletins (https://helpx.adobe.com/security/products/magento.html); runtime check for the web FPM **and** the cron PHP |
| Static | `vendor/bin/phpcs --standard=Magento2 app/code`; UCT (Commerce) |
| Tests | `vendor/bin/phpunit -c dev/tests/unit/phpunit.xml.dist app/code/<Vendor>` (unit); integration tests need `dev/tests/integration/etc/install-config-mysql.php` and a disposable DB, otherwise `blocked`; MFTF for functional tests where configured |
| DB | `bin/magento setup:db:status` before; `setup:upgrade` on a disposable copy |
| Runtime | storefront home/category/product/search, cart, checkout with test payment methods, customer login, admin login and order view; `bin/magento cron:run` once on staging; `var/log/system.log`, `exception.log` |

## F. Recovery and rollback

- Backup: code (Git + `composer.lock`), DB dump, `pub/media`, `app/etc/env.php` (secret: store securely).
- `setup:upgrade` is one-way, so rollback = restore DB + code + regenerate (`generated/`, `pub/static`) in maintenance mode.
- Never run `setup:upgrade` against production from the agent.
- Limitations: Adobe Commerce packages need `repo.magento.com` access keys (`auth.json`, which is secret). Without them, `composer` steps are `blocked`.

## G. Sources

- https://experienceleague.adobe.com/en/docs/commerce-operations/installation-guide/system-requirements
- https://experienceleague.adobe.com/en/docs/commerce-operations/release/planning/lifecycle-policy
- https://experienceleague.adobe.com/en/docs/commerce-operations/upgrade-guide/overview
- https://helpx.adobe.com/security/products/magento.html (HTTP 403 to automated requests on 2026-10-24: not machine-verified); search results on 2026-10-24 show current bulletins also under adobe.com/trust/security/products/commerce/
- https://github.com/magento/magento2
- https://endoflife.date/magento (secondary)
- Unverified: the full PHP range for 2.4.9 (the secondary data lists only 8.5).
- Verified: 2026-10-24.
