# WordPress

**Last verified: 2026-10-24.** Re-check the official PHP compatibility page before acting: it changes with every release.

## A. Project identification

- Website: https://wordpress.org. Developer docs: https://developer.wordpress.org. Source: https://github.com/WordPress/wordpress-develop (development mirror), https://core.trac.wordpress.org (canonical tracker; HTTP 403 to automated requests on 2026-10-24: not machine-verified).
- Signals: `wp-load.php`, `wp-includes/version.php`, `wp-admin/`, `wp-content/`, `wp-config.php` (contains DB credentials and salts: **never print it**). Composer-managed installs (Bedrock) use `roots/wordpress` or `johnpbloch/wordpress-core`, with core in `web/wp/` and content in `web/app/`.
- Version without executing code: read `$wp_version` from `wp-includes/version.php` (the detector does this). With WP-CLI: `wp core version --extra`.
- Multisite: `define('MULTISITE', true)` in `wp-config.php`. Updates and DB upgrades then apply network-wide (`wp core update-db --network`).
- Generations: WordPress keeps backward compatibility across majors, so there are no structural "generations". Major risk comes from PHP version jumps and plugins.

## B. PHP compatibility

- Official: https://make.wordpress.org/core/handbook/references/php-compatibility-and-wordpress-versions/ (per-release PHP support; the newest PHP versions are often labelled "beta support") and https://wordpress.org/about/requirements/ (recommended hosting).
- Lifecycle: WordPress publishes no EOL dates. Only the latest release is officially supported (https://wordpress.org/download/releases/); security fixes may be backported to older branches at the core team's discretion. Treat anything below the current major as outdated.
- Extensions (handbook "Server Environment"): `json`, `mysqli`, plus recommended `curl`, `dom`, `exif`, `fileinfo`, `hash`, `igbinary`, `imagick` or `gd`, `intl`, `mbstring`, `openssl`, `pcre`, `xml`, `zip`.
- Target selection: core is usually the **least** restrictive component. The binding constraints are plugins and themes: check each one's `Requires PHP` / "Tested up to" header and changelog.
- Abandoned: plugins closed on wordpress.org ("This plugin has been closed") or without updates for years; premium plugins with lapsed licences.

## C. Upgrade strategy

- Official: https://developer.wordpress.org/advanced-administration/upgrade/upgrading/ and the WP-CLI handbook https://developer.wordpress.org/cli/commands/core/update/.
- Sequence:
  1. Patch PHP (same branch).
  2. Update plugins and themes on a staging copy, one at a time for critical ones.
  3. Update core to the latest major (WordPress supports direct updates across majors).
  4. Run the DB upgrade.
  5. Move PHP to the target branch.
  6. Watch `debug.log` for deprecations.
- Commands (staging only): `wp plugin list --update=available`, `wp plugin update <slug>`, `wp theme update --all`, `wp core update`, `wp core update-db`.
- Composer/Bedrock: bump `roots/wordpress` and `wpackagist-plugin/*` constraints and run `composer update`. Premium plugins come from vendor repos.
- Child themes: never edit parent themes. Custom code belongs in a child theme or plugin. `mu-plugins/` are loaded unconditionally, so check them for PHP compatibility too.
- Database: core DB upgrades (`wp_db_version`) are **one-way**.
- Breaking areas: dynamic properties (PHP 8.2 deprecations, common in old plugins), `create_function`/`each` in old plugins (fatal on PHP 8), and jQuery/editor changes for admin-heavy plugins.

## D. Automated migration tooling

- **PHPCompatibilityWP** (https://github.com/PHPCompatibility/PHPCompatibilityWP): PHPCompatibility tuned for WordPress (it knows the polyfills core ships). `phpcs -p --standard=PHPCompatibilityWP --runtime-set testVersion 8.3- wp-content/plugins/<slug>`.
- WordPress Coding Standards (https://github.com/WordPress/WordPress-Coding-Standards) for custom code.
- Rector can upgrade custom plugin/theme code. Never run it on third-party plugins: update those from their vendor instead.
- Unsafe to automate: plugin replacement decisions and anything in `wp-config.php`.

## E. Test plan

| Layer | Command (WP-CLI against staging) |
|---|---|
| Structural | `php -l` over `wp-content/themes`, `wp-content/plugins`, `wp-content/mu-plugins`; `wp core verify-checksums`; `wp plugin verify-checksums --all` (wordpress.org plugins only) |
| Security | `wp core version`; `wp plugin list --fields=name,version,update`; vulnerability lookup for plugins/themes (WPScan/Patchstack/Wordfence databases, secondary); runtime check |
| Static | PHPCompatibilityWP on custom and third-party code (report only) |
| Tests | the project's PHPUnit suite if any (uses the WP test library, `bin/install-wp-tests.sh` pattern); otherwise `blocked`, and recommend characterisation tests |
| DB | `wp core update-db` on a disposable copy; `wp db check` |
| Runtime | load the homepage, a post, search, login, admin dashboard, checkout/forms; enable `WP_DEBUG_LOG` on staging and review `wp-content/debug.log`; Tools → Site Health shows the PHP version and extensions **without** `phpinfo()` |

Evidence: checksums pass, there are no fatal/deprecation entries from updated code in `debug.log`, and the key flows return 200 with expected content.

## F. Recovery and rollback

- Back up files (`wp-content/`, `wp-config.php` handled as a secret) and the DB (`wp db export` on staging) before updating.
- Rollback = restore files + DB together. A core downgrade without the DB restore can break, because DB upgrades are one-way.
- Recent WordPress versions can roll back failed **automatic** plugin updates. Do not rely on that for manual migrations.
- Caching plugins/object caches and OPcache must be flushed after restoring.
- Limitations: premium plugins may require licences to update; page builders can store PHP-serialised data that a PHP jump affects.

## G. Sources

- https://make.wordpress.org/core/handbook/references/php-compatibility-and-wordpress-versions/
- https://wordpress.org/about/requirements/
- https://wordpress.org/download/releases/
- https://developer.wordpress.org/advanced-administration/upgrade/upgrading/
- https://developer.wordpress.org/cli/commands/
- https://wordpress.org/news/category/security/
- Verified: 2026-10-24.
