# Phalcon

**Last verified: 2026-10-24.** endoflife.date has no Phalcon data, so lifecycle is **unknown** in the detector. Phalcon is unusual: the framework is a **compiled PHP extension**, so it gates every PHP runtime change.

## A. Project identification

- Website: https://phalcon.io. Docs: https://docs.phalcon.io. Source: https://github.com/phalcon/cphalcon (extension, written in Zephir); https://github.com/phalcon/phalcon (pure-PHP port, check its status before relying on it).
- Signals: `ext-phalcon` in `composer.json` `require`; `Phalcon\` namespaces in `public/index.php` / `app/config/*.php` (`Phalcon\Mvc\Application`, `Phalcon\Di\FactoryDefault`); `.phalcon/` (DevTools project marker); dev packages `phalcon/devtools`, `phalcon/ide-stubs`, `phalcon/migrations`.
- The **installed** version is a property of the PHP runtime, not the repository: `php --ri phalcon` or `php -r 'echo Phalcon\Support\Version::get();'` (v5; v3/v4 use `Phalcon\Version::get()`). Check the CLI **and** the FPM/Apache runtime: they can load different extension builds.
- Generations: **3.x** (old namespaces), **4.x** (requires the separate `psr` PECL extension), **5.x** (namespaces reorganised, e.g. `Phalcon\Support\*`, no `psr` extension needed).

## B. PHP compatibility

- Official: the installation page in the docs (https://docs.phalcon.io/latest/installation/ or the versioned equivalent) and the PECL package page https://pecl.php.net/package/phalcon, which lists the PHP versions each release supports.
- **A PHP upgrade is blocked until a Phalcon build exists for the target PHP branch** (and thread-safety/architecture). Before choosing a target PHP, confirm the build availability: PECL release notes, distro packages, or the official Docker images/PPAs the project uses.
- Same-branch PHP patch releases (e.g. 8.3.30 → 8.3.36) keep the extension ABI, so the existing Phalcon build continues to work. The PHP2Shell patch is therefore unblocked even when a branch migration is not.
- 4.x needs the `psr` extension at a compatible version, which is another gate.

## C. Upgrade strategy

- Official: upgrade guides in the docs (e.g. "Upgrade Guide" from 4.x to 5.x at https://docs.phalcon.io).
- Sequence:
  1. Patch PHP within the branch (rebuild is not needed; restart workers).
  2. Upgrade Phalcon within its major for the current PHP.
  3. If the target PHP needs a newer Phalcon major, migrate the code (namespace moves, removed classes) **first** on the old PHP if that Phalcon major supports it, then move PHP.
- Build/install: `pecl install phalcon` (needs compiler toolchain and PHP headers), or OS/Docker packages. Pin the version in the Dockerfile (`pecl install phalcon-5.x.y`) and enable it with `docker-php-ext-enable phalcon`.
- Volt templates, ORM models (`Phalcon\Mvc\Model`), DI service definitions and annotations all change between majors.

## D. Automated migration tooling

- No official Rector set for Phalcon majors. Use Rector rename rules (`RenameClassRector`) for namespace moves, with a mapping built from the upgrade guide.
- `phalcon/ide-stubs` lets PHPStan/Psalm analyse code that uses the extension.
- Manual: ORM behaviour (events, behaviours, metadata caching), security component usage (`Phalcon\Encryption\Security` in 5.x), Volt syntax.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `php -m \| grep -i phalcon` on **each** runtime (CLI, FPM); `php -l` on app code |
| Security | runtime check; `composer audit` for Composer-managed parts; extension version recorded as evidence |
| Static | `vendor/bin/phpstan analyse` with ide-stubs |
| Tests | `vendor/bin/phpunit` or `vendor/bin/codecept run` (Phalcon apps commonly use Codeception) |
| DB | `phalcon/migrations` (`vendor/bin/phalcon-migrations`) *(example; depends on setup)* on a disposable DB |
| Runtime | container/FPM start with the extension loaded; routes, Volt pages, forms, auth; check that the FPM error log has no "Class Phalcon\... not found" |

## F. Recovery and rollback

- Keep the previous image (PHP + Phalcon build) pinned by digest; this is the rollback unit, because the code and the extension must match.
- Code rollback alone is not enough after a Phalcon major change: the runtime must roll back too.
- Limitations: building the extension needs toolchain access. If unavailable, the branch migration is `blocked` (the same-branch PHP patch is still possible).

## G. Sources

- https://docs.phalcon.io
- https://pecl.php.net/package/phalcon
- https://github.com/phalcon/cphalcon
- https://github.com/phalcon/cphalcon/security/advisories
- https://phalcon.io
- Unverified: the exact docs path for the current installation and upgrade guides (they are versioned). The docs home is the fallback.
- Verified: 2026-10-24.
