# Composer dependencies

**Last verified: 2026-10-24** against https://getcomposer.org/doc/03-cli.md and https://getcomposer.org/doc/06-config.md.

## Principles

- `composer.lock` is the source of truth for installed versions. Commit it for applications.
- Change constraints only when the selected target requires it, and explain each change in the plan.
- **Forbidden**: `--ignore-platform-reqs`, `--ignore-platform-req=php`, `--no-audit` as a workaround, `audit.ignore` entries without a written justification, deleting the lock to "start fresh", removing packages/features to make the solver happy.

## Read-only inspection

```sh
composer validate --strict          # composer.json schema + lock freshness
composer check-platform-reqs        # do installed packages accept this PHP/extensions?
composer audit                      # security advisories for locked packages (Packagist/GitHub advisories)
composer outdated --direct          # newer versions of direct dependencies
composer why-not php 8.4.27         # which packages block a PHP target ("prohibits" is an alias)
composer depends vendor/package     # who requires a package
```

`composer why-not php <version>` is the quickest way to list the packages that block a target PHP version.

## Targeting a PHP version

`config.platform.php` makes Composer resolve as if the given PHP version were installed. Use it to make dependency resolution match the **deployment** runtime when the local CLI differs:

```sh
composer config platform.php 8.4.27
```

Remove or update it when the deployment runtime changes. A stale `platform.php` is a common cause of `deployment_mismatch`. Keep `require.php` honest: it states which runtimes the application supports.

## Upgrading

```sh
composer update vendor/package --with-dependencies   # targeted (-w)
composer update --with-all-dependencies              # broader (-W); review the diff
composer require vendor/package:^X.Y --with-all-dependencies
```

After every update: `composer validate`, `composer audit`, review `git diff composer.lock` (package list, major jumps, removed packages), then run the tests.

## Lock-file consistency

- `composer validate` reports when the lock is out of date with `composer.json` (content-hash mismatch).
- `composer install` on a clean checkout (CI) must succeed without changes to the lock.
- The detector flags `composer.json` requirements missing from the lock and malformed metadata.

## Abandoned packages

`composer outdated` marks abandoned packages, and recent Composer 2.x releases also report them in `composer audit` (controlled by the `audit.abandoned` config; check your version's docs). Replace them using the replacement suggested on Packagist, or vendor-patch them with a documented owner. Do not leave them silently.

## Non-Composer projects

WordPress, Joomla, OpenCart, Dolibarr, phpMyAdmin tarball installs and many legacy apps manage code without Composer. Follow their own update mechanism (see the framework reference). Copy third-party libraries in `lib/`/`vendor/` only from the upstream release, record the version, and check upstream advisories by hand.

## Sources

- https://getcomposer.org/doc/03-cli.md#audit
- https://getcomposer.org/doc/03-cli.md#validate
- https://getcomposer.org/doc/06-config.md#platform
- https://getcomposer.org/doc/articles/versions.md
- https://github.com/advisories
