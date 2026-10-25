# phpMyAdmin

**Last verified: 2026-10-24.** Lifecycle from endoflife.date via [framework-lifecycle.json](framework-lifecycle.json). Confirm on https://www.phpmyadmin.net/downloads/.

phpMyAdmin is a database administration tool, not an application framework. It matters for PHP2Shell because php.net describes an exploit that runs **"before any application code runs"** on mod_php. **phpMyAdmin's login screen gives no protection against a vulnerable runtime.** Any phpMyAdmin reachable from untrusted networks on an unpatched PHP is a priority-one finding.

## A. Project identification

- Website: https://www.phpmyadmin.net. Docs: https://docs.phpmyadmin.net/en/latest/. Source: https://github.com/phpmyadmin/phpmyadmin.
- Signals: `libraries/classes/Version.php` (5.x) or `src/Version.php` (newer development line), `libraries/Config.php` (older), `config.sample.inc.php`, `config.inc.php` (contains `blowfish_secret` and possibly credentials: **never print**), `themes/`, `ChangeLog`, `RELEASE-DATE-*`.
- Version: `VERSION` constant in the version file (the detector reads it); the home page "phpMyAdmin" panel after login.
- Installation types: release archive (self-managed), **distribution package** (`apt install phpmyadmin`, files under `/usr/share/phpmyadmin`, config under `/etc/phpmyadmin`), Docker image (`phpmyadmin/phpmyadmin` or `phpmyadmin` official image), and hosting control panels (cPanel/Plesk bundle their own copy and PHP). **The update path depends on the type**: distro and panel copies are updated by their vendor, not by replacing files.

## B. PHP compatibility

- Official: requirements https://docs.phpmyadmin.net/en/latest/require.html and the download page (each release lists its PHP requirement).
- Lifecycle (endoflife.date, 2026-10-24): **5.2** supported (latest 5.2.3); 5.1/5.0 and older EOL; the data source lists 4.9 as not EOL, but **confirm on phpmyadmin.net before relying on 4.9**, since it is a legacy line.
- Extensions: `mysqli`, `mbstring` (strongly recommended), `openssl`/`sodium` (cookie auth encryption), `zip`, `gd`, `xml`, `ctype`.
- The phpMyAdmin version and the PHP runtime are independent upgrades. Patching PHP (same branch) needs nothing from phpMyAdmin.

## C. Upgrade strategy

- Official: "Upgrading from an older version" in https://docs.phpmyadmin.net/en/latest/setup.html.
- Archive installs:
  1. Patch PHP.
  2. Download the new release from phpmyadmin.net and verify its signature/checksum (the downloads page publishes them).
  3. Extract into a **new** directory.
  4. Copy `config.inc.php` (and custom themes) across; do not copy the old code.
  5. Switch the web server alias.
  6. Remove the old directory.
- Configuration storage (`phpmyadmin` database, "pmadb"): the docs describe updating its tables via `sql/create_tables.sql` / upgrade scripts for some versions. Check the release notes and run on a test DB first.
- Distro installs: `apt-get install --only-upgrade phpmyadmin` (or the distro equivalent); the vendor decides the version.
- Docker: bump the image tag and pin it.
- Hardening while you are there (strongly recommended): restrict access by IP/VPN/SSO at the web server, use `AllowNoPassword false`, keep it off the public internet, and consider removing it entirely if unused.

## D. Automated migration tooling

- Not applicable for phpMyAdmin itself: you never refactor its code, you replace it with an official release.
- PHPCompatibility could be run against a custom theme or plugin, if any exists.
- Manual: `config.inc.php` options removed/renamed between versions (see the configuration docs), custom themes.

## E. Test plan

| Layer | Command / action |
|---|---|
| Structural | the release checksum/signature verified; `php -l config.inc.php` |
| Security | phpMyAdmin security announcements (PMASA) https://www.phpmyadmin.net/security/; runtime check of the PHP serving phpMyAdmin (it is often a **different** vhost/pool from the main app); access restriction verified (an anonymous request from outside the allowed network is refused) |
| Static | n/a |
| Tests | no project test suite for an installation, so mark `test_suite` as `skipped` with the reason "third-party tool installation, no tests" and run smoke tests instead |
| DB | configuration storage table updates on a test DB only |
| Runtime | login page loads, login with a **test** DB user, run `SELECT 1`, browse a test schema, no warnings on the home page about configuration storage or `blowfish_secret` |

## F. Recovery and rollback

- Keep the previous release directory until the new one is verified. Rollback = switch the alias back (or restore the previous image tag).
- Back up the configuration storage DB before running its upgrade SQL.
- Limitations: panel- and distro-managed copies cannot be upgraded independently. Record the vendor's version and advisory status instead.

## G. Sources

- https://www.phpmyadmin.net/downloads/
- https://docs.phpmyadmin.net/en/latest/require.html
- https://docs.phpmyadmin.net/en/latest/setup.html
- https://www.phpmyadmin.net/security/
- https://www.php.net/archive/2026.php (statement on exploitation before application code runs)
- https://endoflife.date/phpmyadmin (secondary)
- Verified: 2026-10-24.
