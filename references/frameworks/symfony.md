# Symfony

**Last verified: 2026-10-24.** Re-check https://symfony.com/releases before acting: compatibility facts change.

## A. Project identification

- Website: https://symfony.com. Docs: https://symfony.com/doc/current/index.html. Source: https://github.com/symfony/symfony.
- Signals (Flex, 4+): `symfony.lock`, `config/bundles.php`, `src/Kernel.php`, `bin/console`, `public/index.php`, and `symfony/framework-bundle` in the lock file. Many other projects (Laravel, Drupal, PrestaShop, SuiteCRM 8, Magento) **embed Symfony components**. Only `symfony/framework-bundle` plus a Kernel means a Symfony application.
- Pre-Flex (2.x/3.x): `app/AppKernel.php`, `app/config/config.yml`, `web/app.php`, `app/console` (2.x) or `bin/console` (3.x).
- Version: `composer.lock` → `symfony/framework-bundle`; `bin/console --version` (boots the kernel); `composer show symfony/*`.
- `extra.symfony.require` in `composer.json` (e.g. `"7.4.*"`) pins all `symfony/*` packages through Flex. It is the main constraint to change.

## B. PHP compatibility

- Official: each release page (https://symfony.com/releases/7.4, https://symfony.com/releases/8.1) states the minimum PHP. Requirements: https://symfony.com/doc/current/setup.html#technical-requirements.
- Lifecycle (endoflife.date, 2026-10-24):

  | Symfony | Security fixes until | Notes |
  |---|---|---|
  | 8.1 | 2027-01-31 | current minor |
  | 8.0 | 2026-07-31 | **EOL** |
  | 7.4 | 2029-11-30 | **LTS** |
  | 7.0 to 7.3 | ended | **EOL**: update to 7.4 |
  | 6.4 | 2027-11-30 | **LTS** |
  | ≤ 6.3, 5.x, 4.x, 3.x | ended (check releases page) | **EOL** |

- Minimum PHP is per major (6.4 needs 8.1+, 7.x needs 8.2+, 8.x needs 8.4+). Confirm on the release page, then check that every bundle allows the target: `composer why-not php 8.4.27`.
- Extensions: Ctype, iconv, PCRE, Session, SimpleXML, Tokenizer (the technical requirements page), plus `intl` for many apps and the DB PDO driver.

## C. Upgrade strategy

- Official: minor upgrades https://symfony.com/doc/current/setup/upgrade_minor.html; major upgrades https://symfony.com/doc/current/setup/upgrade_major.html; per-version `UPGRADE-X.Y.md` files in the repository.
- Symfony's model: **a major release = the last minor of the previous major minus its deprecated code.** So:
  1. Patch PHP.
  2. Upgrade to the last minor of the current major (e.g. 6.4).
  3. Fix **all** deprecations reported in the logs and the test suite (the PHPUnit bridge reports them).
  4. Jump to the next major (7.0, then 7.4), and repeat.
- Composer: change `extra.symfony.require` and the `symfony/*` constraints together, then run `composer update "symfony/*" -W`.
- Flex recipes: `composer recipes` lists outdated recipes; `composer recipes:update <package>` updates them interactively. Review every config diff.
- Doctrine ORM/DBAL majors often move together with Symfony majors. Follow Doctrine's own UPGRADE files.
- Custom code: compiler passes, event subscribers, voters (security), custom authenticators (the new authenticator system has been mandatory since 6.0), form types, console commands (`#[AsCommand]`), and Twig extensions.

## D. Automated migration tooling

- Rector ships Symfony sets (`SymfonySetList`, or `->withSymfonyContainerXml()` / `->withPreparedSets()`). Run per major with `--dry-run`. Docs: https://getrector.com/documentation.
- PHPStan + `phpstan/phpstan-symfony` (container-aware analysis).
- `symfony/phpunit-bridge` with `SYMFONY_DEPRECATIONS_HELPER` to make deprecations fail or report.
- Manual review is required for security configuration (`security.yaml` firewalls, access control), serializer/normalizer behaviour (API contracts), and messenger transport/serialization changes.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate --strict`; `bin/console lint:container`; `bin/console lint:yaml config`; `bin/console lint:twig templates`; `bin/console cache:clear --env=prod` (no-debug warmup) |
| Security | `composer audit` (or `symfony check:security` with the Symfony CLI); runtime check of the FPM/FrankenPHP binary |
| Static | `vendor/bin/phpstan analyse`; `vendor/bin/rector process --dry-run` |
| Tests | `vendor/bin/phpunit` (older bridge setups: `bin/phpunit`); deprecation count compared with the baseline |
| DB | `bin/console doctrine:migrations:status`; migrate a disposable DB; `bin/console doctrine:schema:validate` |
| Runtime | `bin/console debug:router` vs baseline; HTTP smoke tests; messenger consumers start (`bin/console messenger:consume --limit=1` in test) |

Evidence: the suite passes with zero new deprecations, `lint:container` succeeds, and the container compiles in prod mode.

## F. Recovery and rollback

- One commit per minor/major step. `composer.lock`, `symfony.lock` and the recipe-updated config change together.
- Doctrine migrations: `doctrine:migrations:migrate prev` exists, but restoring the backup is the reliable rollback.
- Clear `var/cache` on rollback; long-running workers (messenger, RoadRunner/FrankenPHP worker mode) must restart.
- Limitations: environment variables and secrets vaults (`config/secrets`) are not inspected by the detector by design.

## G. Sources

- https://symfony.com/releases
- https://symfony.com/doc/current/setup/upgrade_major.html
- https://symfony.com/doc/current/setup/upgrade_minor.html
- https://symfony.com/doc/current/setup.html#technical-requirements
- https://symfony.com/blog/category/security-advisories
- https://endoflife.date/symfony (secondary)
- Verified: 2026-10-24.
