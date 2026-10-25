# CodeIgniter

**Last verified: 2026-10-24.** endoflife.date has no CodeIgniter data, so lifecycle status is **unknown** in the detector. Check the official sources below before acting.

## A. Project identification

- Website: https://codeigniter.com. CodeIgniter 4 user guide: https://codeigniter.com/user_guide/. CodeIgniter 3 guide: https://codeigniter.com/userguide3/.
- Source: CI4 https://github.com/codeigniter4/CodeIgniter4 (distributed as `codeigniter4/framework`); CI3 https://github.com/bcit-ci/CodeIgniter.
- **CI4 signals**: `spark` CLI at the root, `app/Config/App.php`, `app/Controllers/`, `public/index.php`, `writable/`, and either `vendor/codeigniter4/framework/` (Composer install) or `system/` (manual install).
- **CI3 signals**: `application/config/config.php`, `application/controllers/`, `system/core/CodeIgniter.php` with `define('CI_VERSION', '3.x')`, and `index.php` at the root defining `$system_path`/`$application_folder`.
- Version: CI4 `CodeIgniter::CI_VERSION` in `system/CodeIgniter.php` (or under `vendor/codeigniter4/framework/system/`); `composer show codeigniter4/framework`. CI3: `CI_VERSION` in `system/core/CodeIgniter.php`. The detector reads both.

## B. PHP compatibility

- Official: CI4 server requirements https://codeigniter.com/user_guide/intro/requirements.html (minimum PHP and required extensions: `intl`, `mbstring`, plus `json`, the DB driver, and `curl` for CURLRequest).
- Each CI4 minor has raised the PHP minimum over time. The **changelog / upgrade notes** of the target version state it (https://codeigniter.com/user_guide/changelogs/index.html).
- CI3: the last 3.1.x releases target older PHP. Running CI3 on PHP 8.2+ produces dynamic-property deprecations in core classes. CI3 is in maintenance mode with very infrequent releases (check the CI3 repository's release history). Plan migration to CI4 as a separate project.
- Target selection: the newest supported PHP branch listed for the latest CI4 release. For CI3, the newest PHP its last release tolerates, verified by tests, as containment only.

## C. Upgrade strategy

- Official: https://codeigniter.com/user_guide/installation/upgrading.html (one page per version step, e.g. "Upgrading from 4.5.x to 4.6.0").
- CI4 sequence:
  1. Patch PHP.
  2. Follow **each** upgrade page between your version and the target, in order.
  3. Composer installs: `composer update codeigniter4/framework`.
  4. **Merge project files manually**: CI4 does not update `app/Config/*`, `public/index.php` or `spark` for you. Diff them against `vendor/codeigniter4/framework/app/` and `vendor/codeigniter4/framework/public/` for the new version.
  5. Clear `writable/cache`.
- CI3 → CI4: a rewrite of controllers/models/config using the guide https://codeigniter.com/user_guide/installation/upgrade_4xx.html (namespaces, new routing, a different Query Builder API in places, new session/validation). Budget it as a migration project. Characterisation tests first ([../migration/legacy-applications.md](../migration/legacy-applications.md)).
- Config: new `app/Config/*.php` properties. Missing ones fall back to defaults, which can silently change behaviour (CSRF, filters, auto-routing).
- Security-relevant changes to check: auto-routing (legacy vs improved, `$autoRoutesImproved`), CSRF filter configuration, and `Config\Security`/`Config\Filters`.

## D. Automated migration tooling

- Rector with PHP sets for language upgrades. There is no official CodeIgniter Rector set; write custom rules or refactor by hand for framework API changes.
- PHPStan, with the community `codeigniter/phpstan-codeigniter` extension if the project uses it.
- PHPCompatibility for CI3 codebases.
- Manual: route definitions, filters, model return types (`returnType`, entities), validation rules, CI3 → CI4 rewrites.

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `php -l` over `app/`; `php spark routes` (CI4) |
| Security | `composer audit`; runtime check; review `app/Config/Filters.php` (CSRF/secure headers) diff |
| Static | `vendor/bin/phpstan analyse`; PHPCompatibility |
| Tests | `vendor/bin/phpunit` (CI4 projects ship `phpunit.xml.dist` and `tests/` using `CIUnitTestCase`) |
| DB | `php spark migrate:status`; `php spark migrate` on a disposable DB; `php spark migrate:rollback` there if migrations are reversible |
| Runtime | `php spark serve` or the container; HTTP smoke tests for main routes, forms (CSRF), auth; check `writable/logs` |

## F. Recovery and rollback

- Commit the merged `app/Config` changes separately from the framework bump, so config regressions can be reverted alone.
- DB: backup + restore; CI4 migrations support `down()`, but treat a restore as authoritative.
- Clear `writable/cache` and `writable/session` (file sessions) after rollback.
- Limitations: manually installed CI4 (`system/` copied in) has no lock file. Record the version from `CI_VERSION`.

## G. Sources

- https://codeigniter.com/user_guide/intro/requirements.html
- https://codeigniter.com/user_guide/installation/upgrading.html
- https://codeigniter.com/user_guide/installation/upgrade_4xx.html
- https://codeigniter.com/user_guide/changelogs/index.html
- https://github.com/codeigniter4/CodeIgniter4/security/advisories
- https://github.com/bcit-ci/CodeIgniter (CI3)
- Unverified: CI3 maintenance status beyond its release history. No official lifecycle page was found; marked unknown.
- Verified: 2026-10-24.
