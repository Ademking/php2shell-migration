# CakePHP

**Last verified: 2026-10-24.** Lifecycle rows from endoflife.date via [framework-lifecycle.json](framework-lifecycle.json). Confirm on the official release policy.

## A. Project identification

- Website: https://cakephp.org. Book (docs): https://book.cakephp.org/5/en/index.html. Source: https://github.com/cakephp/cakephp; app skeleton https://github.com/cakephp/app.
- **3.x to 5.x signals**: `bin/cake`, `config/app.php` (+ `config/app_local.php` with secrets in 4.x/5.x), `src/Application.php`, `src/Controller/AppController.php`, `webroot/`, and `cakephp/cakephp` in the lock file.
- **2.x signals**: `lib/Cake/VERSION.txt`, `app/Config/core.php`, `app/Config/database.php` (credentials), `app/Console/cake`, `app/webroot/`.
- **1.x**: `cake/` directory with `cake/VERSION.txt`.
- Version: the last line of `vendor/cakephp/cakephp/VERSION.txt` (or `lib/Cake/VERSION.txt` for 2.x); `bin/cake version`; `composer show cakephp/cakephp`.

## B. PHP compatibility

- Official: the requirements in each book's installation chapter (e.g. https://book.cakephp.org/5/en/installation.html) and the `php` constraint of the release.
- Lifecycle (endoflife.date, 2026-10-24):

  | CakePHP | PHP | Status |
  |---|---|---|
  | 5.4 / 5.3 | 8.2 – 8.5 | supported |
  | 5.2 | 8.1 – 8.5 | supported |
  | 5.1 / 5.0 | 8.1 – 8.5 / 8.1 – 8.3 | **EOL** (2026-07-19 / 2026-01-09) |
  | 4.6 | 7.4 – 8.3 | supported |
  | 4.5 and older 4.x | ≤ 8.3 | **EOL** |
  | 3.x, 2.x, 1.x | ≤ 7.x / 8.0 era | **EOL** |

- Note: 4.6 tops out at PHP 8.3 in this data. A 4.x app wanting PHP 8.4+ must move to 5.x.
- Extensions: `mbstring`, `intl` (required), `simplexml`, PDO driver.

## C. Upgrade strategy

- Official migration guides: https://book.cakephp.org/5/en/appendices/5-0-migration-guide.html (4 → 5), https://book.cakephp.org/4/en/appendices/4-0-migration-guide.html (3 → 4), and per-minor guides (e.g. "5.3 Migration Guide") in the book appendices.
- Sequence:
  1. Patch PHP.
  2. Upgrade to the latest minor of the current major (e.g. 4.6) and fix deprecations (enable deprecation warnings in `config/app.php` `Error.errorLevel`).
  3. Run the **upgrade tool** for the next major.
  4. Update plugins (`cakephp/migrations`, `cakephp/authentication`, `cakephp/authorization`, `cakephp/debug_kit`, `friendsofcake/*`) to compatible majors.
  5. Repeat.
- 2.x → 3.x+ is effectively a rewrite (ORM, namespaces, directory layout). There is a 2.x → 3 upgrade-shell history, but expect manual work.
- Config: compare `config/app.php` with the `cakephp/app` skeleton for the target version.
- Database: `cakephp/migrations` (Phinx-based) or the newer migrations backend. Check the migrations plugin major too.

## D. Automated migration tooling

- **cakephp/upgrade** (https://github.com/cakephp/upgrade): official Rector-based tool, e.g. `bin/cake upgrade rector --rules cakephp50 <path>`. Follow its README for the exact command for your version.
- Rector PHP sets for language upgrades; PHPStan (`cakephp/cakephp-codesniffer` for style).
- Manual: ORM behaviour changes (entities, finders with named args in 5.x), `Authentication`/`Authorization` plugin configuration, component/helper signature changes, middleware queue.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `php -l src/ config/ tests/`; `bin/cake routes` |
| Security | `composer audit`; runtime check |
| Static | `vendor/bin/phpstan analyse`; `vendor/bin/rector process --dry-run`; `vendor/bin/phpcs` |
| Tests | `vendor/bin/phpunit` (fixtures need a test DB configured in `config/app_local.php` `Datasources.test`) |
| DB | `bin/cake migrations status`; `bin/cake migrations migrate` on a disposable DB; `bin/cake migrations rollback` there |
| Runtime | `bin/cake server` or the container; HTTP smoke tests; check `logs/error.log` |

## F. Recovery and rollback

- One commit per major/minor step. The upgrade-tool output gets its own commit.
- DB restore as rollback for shared environments; `bin/cake cache clear_all` after code rollback.
- Limitations: plugins without a release for the target major are blockers. List them.

## G. Sources

- https://book.cakephp.org/5/en/installation.html
- https://book.cakephp.org/5/en/appendices/5-0-migration-guide.html
- https://github.com/cakephp/upgrade
- https://github.com/cakephp/cakephp/security/advisories
- https://endoflife.date/cakephp (secondary)
- Verified: 2026-10-24.
