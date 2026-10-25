# Slim Framework

**Last verified: 2026-10-24.** endoflife.date has no Slim data, so lifecycle is **unknown** in the detector. Slim is a micro-framework: most migration risk sits in the libraries the app chose around it.

## A. Project identification

- Website and docs: https://www.slimframework.com, v4 docs https://www.slimframework.com/docs/v4/. Source: https://github.com/slimphp/Slim.
- Signals: only `slim/slim` in `composer.json`/`composer.lock`. There are no characteristic directories; `public/index.php` usually calls `AppFactory::create()` (v4) or `new \Slim\App()` (v3). The skeleton (https://github.com/slimphp/Slim-Skeleton) adds `app/`, `src/`, `public/`.
- Version: `composer.lock` → `slim/slim`.
- Generations: **v2** (`\Slim\Slim`, its own request/response), **v3** (PSR-7 via `slim/http`, Pimple container built in), **v4** (PSR-7/PSR-15/PSR-17 with a pluggable PSR-7 implementation, no built-in container, explicit routing/error middleware). Slim is also used inside other products (e.g. EspoCRM).

## B. PHP compatibility

- Official: the `php` constraint of the `slim/slim` release you target (https://github.com/slimphp/Slim/releases) and the v4 docs' installation page.
- Slim 4 supports PHP 7.4+ in its recent releases, and the 4.x line received PHP 8.x compatibility updates. Slim 3 and 2 are unmaintained, so treat them as legacy.
- The **PSR-7 implementation** (`slim/psr7`, `nyholm/psr7`, `guzzlehttp/psr7`, `laminas/laminas-diactoros`) and the **container** (`php-di/php-di`, ...) have their own PHP constraints and majors. Check them with `composer why-not php <target>`.
- Extensions: none beyond what the app uses (`json`, `mbstring`, PDO driver, ...).

## C. Upgrade strategy

- Official: Slim 3 → 4 guide https://www.slimframework.com/docs/v4/start/upgrade.html.
- v4 within line:
  1. Patch PHP.
  2. `composer update slim/slim slim/psr7 -W` (or the chosen PSR-7 package).
  3. Update the container and middleware packages.
  4. Run the tests.
- v3 → v4 (main changes from the guide): create the app via `AppFactory` with an explicit PSR-7 implementation; add the routing and error middleware explicitly (**middleware order changes behaviour**: last added runs first); there is no built-in container, so pass a PSR-11 container; route callables, `$args`, the base path and `pathFor()` → `RouteParser::urlFor()` changed; the error handler API changed; and `$request->getParam()` is gone (use `getParsedBody()`/`getQueryParams()`).
- Auth/CORS/CSRF middleware (often third-party, e.g. `slim/csrf`, `tuupola/slim-jwt-auth`) must be checked for v4 versions. Ordering mistakes here are security bugs.

## D. Automated migration tooling

- Rector PHP sets; no official Slim Rector set exists. The v3 → v4 changes are mostly manual (factory, middleware, container wiring).
- PHPStan works well on Slim apps (plain PSR interfaces).
- Manual: middleware order, error handling (error details must not leak in production: `displayErrorDetails` false), request parsing (`BodyParsingMiddleware` in v4).

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `php -l src/ app/ public/` |
| Security | `composer audit`; runtime check; Slim advisories https://github.com/slimphp/Slim/security/advisories |
| Static | `vendor/bin/phpstan analyse` |
| Tests | `vendor/bin/phpunit` (the skeleton includes tests that build requests through `ServerRequestFactory`); if none exist, mark the suite `blocked` and write HTTP characterisation tests before the v3 → v4 change |
| Runtime | `php -S localhost:8080 -t public` (dev only) or the container; request every route in the route table and compare status codes/bodies with the baseline; check auth-protected routes reject anonymous requests |

## F. Recovery and rollback

- Commit per step; the v3 → v4 change is one large commit series on a branch.
- No framework-owned DB migrations. Use whatever migration tool the app uses (Phinx, Doctrine).
- Limitations: behaviour lives in middleware, so API contract tests are the only reliable regression signal.

## G. Sources

- https://www.slimframework.com/docs/v4/
- https://www.slimframework.com/docs/v4/start/upgrade.html
- https://github.com/slimphp/Slim/releases
- https://github.com/slimphp/Slim/security/advisories
- Verified: 2026-10-24.
