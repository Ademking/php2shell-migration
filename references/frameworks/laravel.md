# Laravel

**Last verified: 2026-10-24.** Lifecycle rows come from [framework-lifecycle.json](framework-lifecycle.json) (endoflife.date). Re-check the official support table before acting: compatibility facts change.

## A. Project identification

- Website: https://laravel.com. Docs: https://laravel.com/docs. Source: https://github.com/laravel/framework (framework), https://github.com/laravel/laravel (application skeleton).
- Signals: `artisan` at the root, `bootstrap/app.php`, `routes/web.php`, `config/app.php`, and `laravel/framework` in `composer.lock`. A `artisan` file alone is ambiguous: October CMS and Lumen-era apps have one too.
- Installed version (no code execution): `composer.lock` → `laravel/framework` `version`, or `vendor/composer/installed.json`. With PHP available: `php artisan --version` or `composer show laravel/framework`. `php artisan about` (Laravel 9.21+) also prints the PHP version and drivers. It boots the app, so run it only in a safe environment.
- Generations:
  - **11+** (slim skeleton): `bootstrap/app.php` uses `Application::configure()`; no `app/Http/Kernel.php` or `app/Console/Kernel.php`; middleware is registered in `bootstrap/app.php`.
  - **5.x to 10**: `app/Http/Kernel.php`, `app/Console/Kernel.php`, `app/Exceptions/Handler.php`.
  - **≤ 5.x**: `app/Http/routes.php` (≤ 5.2) or `routes/` (5.3+). **Lumen** uses `laravel/lumen-framework`; it is a separate upgrade path.

## B. PHP compatibility

- Official: the "Support Policy" table in each version's release notes, e.g. https://laravel.com/docs/12.x/releases and https://laravel.com/docs/13.x/releases. Server requirements: https://laravel.com/docs/12.x/deployment#server-requirements.
- Lifecycle data (endoflife.date, 2026-10-24):

  | Laravel | PHP | Security fixes until | Status |
  |---|---|---|---|
  | 13 | 8.3 – 8.5 | 2028-03-17 | supported |
  | 12 | 8.2 – 8.5 | 2027-02-24 | security fixes only |
  | 11 | 8.2 – 8.4 | 2026-03-12 | **EOL** |
  | 10 | 8.1 – 8.3 | 2025-02-04 | **EOL** |
  | ≤ 9 | ≤ 8.2 | ended | **EOL** |

- Required extensions (deployment docs): Ctype, cURL, DOM, Fileinfo, Filter, Hash, Mbstring, OpenSSL, PCRE, PDO, Session, Tokenizer, XML, plus the PDO driver for your DB, `redis`/`phpredis` if used, and `bcmath`/`intl`/`gd` as packages require.
- Target selection: for Laravel 12 apps patching PHP2Shell, the 8.2 → 8.2.35 / 8.3 → 8.3.36 / 8.4 → 8.4.27 patch is immediate. Moving to 8.5 also requires every package to allow it (`composer why-not php 8.5.12`).
- Unsupported versions: any major past its security date above, `laravel/lumen-framework`, and packages abandoned on Packagist.

## C. Upgrade strategy

- Official guides: https://laravel.com/docs/12.x/upgrade (11 → 12) and https://laravel.com/docs/13.x/upgrade (12 → 13). Older guides are under `/docs/<version>/upgrade`.
- **One major at a time** (10 → 11 → 12 → 13), with tests green at each step. Laravel's guides only cover the step from the previous major.
- Sequence:
  1. Patch PHP in the current branch.
  2. Update to the latest minor of the current major and clear deprecations.
  3. Bump `laravel/framework` and the first-party packages (Sanctum, Horizon, Telescope, Cashier, Scout, Livewire/Inertia) together, following the guide.
  4. Bump PHP to the target branch if the new major needs it.
- Composer: `composer require laravel/framework:^12.0 --with-all-dependencies` (or edit the constraints and `composer update -W`), then review `composer.lock`.
- The 11+ slim skeleton is **optional** for upgraded apps. Do not restructure the old `Kernel` layout as part of a security migration.
- Config: compare `config/*.php` against the skeleton for the target version (https://github.com/laravel/laravel, compare branches); new env keys go into `.env.example` only, never into the real `.env`.
- Database: `php artisan migrate --pretend` shows the SQL first. Framework upgrades sometimes ship new migrations for jobs/cache/sessions tables, so publish and review them.
- Breaking areas to inspect: middleware registration, exception handler, rate limiting, `Carbon` major version (Laravel 11 added Carbon 3 support; check which major your lock resolves), model casts (`casts()` method), queue/batch serialisation, password rehashing, and any vendor-published views/config.
- Custom code: service providers, macros, overridden framework classes, packages that pin `illuminate/*`.

## D. Automated migration tooling

- Rector + **rector-laravel** (community, https://github.com/driftingly/rector-laravel): per-version sets, e.g. `LaravelSetList::LARAVEL_120`. Run with `--dry-run` first.
- **Larastan** (PHPStan extension for Laravel, https://github.com/larastan/larastan): `vendor/bin/phpstan analyse`.
- PHPCompatibility for language-level changes.
- Laravel Shift (https://laravelshift.com) is a commercial third-party service. Use it only if the user chooses it.
- Unsafe to automate: auth guards/policies, queue payload changes, Eloquent behaviour changes (casts, date serialisation), and anything in `app/Exceptions` or the middleware order. Review these manually.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate --strict`; `php -l` on `app/ config/ database/ routes/ tests/`; `php artisan config:cache && php artisan config:clear`; `php artisan route:list` |
| Security | `composer audit`; `php -v` of the FPM/Octane runtime; `scripts/check-php-version.py` |
| Static | `vendor/bin/phpstan analyse` (Larastan); `vendor/bin/rector process --dry-run` |
| Tests | `php artisan test` (or `vendor/bin/phpunit`, `vendor/bin/pest`); use `--parallel` only if the suite already supports it |
| DB | `php artisan migrate:status`; `php artisan migrate` against a disposable DB; `php artisan migrate:rollback --step=1` on that DB if migrations are reversible |
| Runtime | `php artisan serve` or the project's container; HTTP smoke tests for login, key pages and APIs; `php artisan queue:work --once` and `php artisan schedule:list` with test data |

Extensions/packages: run the first-party package test suites if the app customised them; check Horizon/Octane start-up. Evidence of success: the suite passes on the target PHP, there are no new deprecations in `storage/logs`, and `composer audit` is clean.

## F. Recovery and rollback

- Commit per stage; keep `composer.lock` changes with the code change.
- Back up the DB before running new migrations in any shared environment. `migrate:rollback` only works if the `down()` methods are correct, so treat a restore as the real rollback.
- Clear caches after rollback: `php artisan optimize:clear`.
- Octane/Horizon/queue workers keep old code in memory. Restart them after a deploy or rollback (`php artisan octane:reload`, `php artisan horizon:terminate`, `php artisan queue:restart`).
- Limitations: `.env` differences between environments are invisible to source inspection.

## G. Sources

- https://laravel.com/docs/12.x/releases (support policy)
- https://laravel.com/docs/12.x/upgrade
- https://laravel.com/docs/13.x/upgrade
- https://laravel.com/docs/12.x/deployment#server-requirements
- https://github.com/laravel/framework/security/advisories
- https://endoflife.date/laravel (secondary, lifecycle table)
- Verified: 2026-10-24 (URL reachability per `validate-references.py --online`; versions from endoflife.date data dated the same day).
