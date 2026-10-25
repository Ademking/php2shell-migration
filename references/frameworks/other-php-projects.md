# Other PHP projects (custom, unrecognised, unlisted frameworks)

**Last verified: 2026-10-24.** Use this when `detect-project.py` reports no known framework, or for frameworks/apps without a dedicated reference (e.g. Lumen, Zend Framework 1, Kohana, FuelPHP, Silex, Sylius, Shopware, Matomo, MantisBT, osTicket, GLPI, Roundcube, phpBB, vTiger, ...).

## A. Project identification

- First look for a product identity: `composer.json` `name`, README, LICENSE, a `VERSION`/`version.php`/`CHANGELOG` file, an admin "About" page, HTTP `<meta name="generator">`. Search Packagist/GitHub for the product's official repository and docs.
- If it is a known product without a reference here, find its official: website, docs, source repo, security advisories page, supported-versions/lifecycle page, and its PHP requirements page. Record what you could not find.
- Custom code: identify the entry points (`index.php`, `public/`), autoloading (Composer PSR-4, or manual `require`), bundled libraries (`lib/`, `includes/`, `vendor/` committed), and the configuration files that hold secrets (never print them).
- Version: use the product version file or Git tags; for custom apps, the Git commit is the version.

## B. PHP compatibility

- Known product: its official requirements page decides. If none exists, treat its CI matrix (e.g. `.github/workflows`) as the best evidence of the PHP versions it was tested on, and say so.
- Custom code: determine the **current** working PHP (deployed runtime) and run PHPCompatibility against the target: `vendor/bin/phpcs -p --standard=PHPCompatibility --runtime-set testVersion <target>- --extensions=php <paths>`.
- Extensions: grep for extension functions (`mysql_`, `mcrypt_`, `imap_`, `ldap_`, `gd`, `imagick`, `intl`, `sodium`, `apcu_`, ...), check `composer.json` `ext-*`, and the Dockerfile `docker-php-ext-install` lines.
- Unknown lifecycle: the detector reports `lifecycle: unknown`. Keep it unknown in the report unless an official source says otherwise.

## C. Upgrade strategy

1. Patch the runtime within its branch if that branch is supported (no code change needed).
2. For an EOL branch, follow [../migration/legacy-applications.md](../migration/legacy-applications.md): characterisation tests, then climb PHP versions one branch at a time.
3. Bundled third-party libraries: identify each name and version; replace them with Composer packages where feasible; check each for advisories (GitHub Advisory Database, https://github.com/advisories).
4. Configuration: externalise secrets if they are hardcoded, but only with the user's approval (it changes deployment).
5. Database: hand-written SQL migrations or none. Create a schema dump before/after.

## D. Automated migration tooling

- Rector PHP sets (`->withPhpSets()`), with `--dry-run` first; PHPCompatibility; PHPStan at a low level first (`level 0` → raise gradually); `php -l` with the target binary.
- Unsafe to automate: anything touching authentication, sessions, crypto, money, or serialised data; dynamic code (`eval`, variable functions, `extract`); global-state-heavy legacy code.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `php -l` over all PHP files with the target binary; `composer validate` if Composer exists |
| Security | runtime check; `composer audit` if Composer exists; a manual advisory check for bundled libraries |
| Static | PHPCompatibility; PHPStan level 0+; Rector dry-run |
| Tests | existing suite if any; otherwise mark it `blocked` and propose HTTP characterisation tests (recorded responses for key URLs and flows) |
| DB | schema dump diff on a disposable DB |
| Runtime | start under the target runtime in a container; request every known URL; check the error log for warnings/deprecations/fatals |

## F. Recovery and rollback

- Git checkpoint (initialise Git with the user's consent if there is none, or take a full copy of the directory).
- Previous runtime image/package recorded; DB backup tested.
- Limitations: without tests or a runnable environment, the migration can only be `partially_verified` at best (syntax and static checks), and the report must say so.

## G. Sources

- https://www.php.net/manual/en/appendices.php (official PHP migration guides)
- https://github.com/PHPCompatibility/PHPCompatibility
- https://getrector.com/documentation
- https://phpstan.org/user-guide/getting-started
- https://github.com/advisories
- https://owasp.org/www-project-top-ten/
- Verified: 2026-10-24.
