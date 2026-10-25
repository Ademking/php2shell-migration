# Joomla

**Last verified: 2026-10-24.** Lifecycle from endoflife.date via [framework-lifecycle.json](framework-lifecycle.json). Confirm on the official technical requirements page.

## A. Project identification

- Website: https://www.joomla.org. User docs: https://docs.joomla.org. Developer manual: https://manual.joomla.org. Source: https://github.com/joomla/joomla-cms.
- Signals: `configuration.php` at the root (a `JConfig` class with DB credentials and `$secret`: **never print it**), `administrator/`, `components/`, `libraries/`, `plugins/`, `templates/`, `administrator/manifests/files/joomla.xml`.
- Version: `administrator/manifests/files/joomla.xml` `<version>`, or the `MAJOR_VERSION`/`MINOR_VERSION`/`PATCH_VERSION` constants in `libraries/src/Version.php` (3.8+). The detector reads both. In the admin UI: System → System Information.
- Generations: **3.x** (legacy MVC, `libraries/cms`, `JFactory`); **4.x/5.x/6.x** (namespaced `Joomla\CMS\...`, the `api/` application, Web Services, the `cli/joomla.php` console). Joomla 1.5/2.5 sites are a migration, not an upgrade.

## B. PHP compatibility

- Official: https://downloads.joomla.org/technical-requirements (minimum/recommended PHP, DB and web server per major).
- Lifecycle (endoflife.date, 2026-10-24): **6** (security to 2029-10-16) and **5** (to 2027-10-12) supported; **4** EOL 2025-10-14; **3** EOL 2023-08-17.
- PHP ranges differ per major; newer majors drop old PHP. Check the requirements page for the exact minor you target.
- Extensions: `json`, `simplexml`, `dom`, `zlib`, `gd`, `mysqlnd`/`pdo_mysql` or `pgsql`, `intl` (recommended), `mbstring`.
- Third-party extensions (components, modules, plugins, templates) decide the real ceiling: check the Joomla Extensions Directory (https://extensions.joomla.org) and the vendor changelogs.

## C. Upgrade strategy

- Official: https://docs.joomla.org/Portal:Upgrading_Versions and the per-major migration docs (e.g. "Joomla 3.x to 4.x Step by Step Migration", "Joomla 4.4 to 5.x").
- **Bridge releases**: you must be on the last minor of a major before moving to the next (3.10 → 4.x, 4.4 → 5.x, 5.4 → 6.x; the 5.4 → 6.0 notes are at https://manual.joomla.org/updates/54-60/). Never skip a major.
- Sequence:
  1. Patch PHP.
  2. Update to the latest minor of the current major (System → Update → Joomla).
  3. Update all extensions.
  4. Run the **Pre-Update Check** in the Joomla Update component, which lists extension compatibility and PHP/DB requirements.
  5. Replace or remove incompatible extensions.
  6. Update to the next major.
  7. Run System → Maintenance: Database → "Fix".
  8. Move PHP.
- Joomla 5 ships a **"Behaviour - Backward Compatibility"** plugin that keeps some 4.x APIs working. For 5.4 → 6.x, the official notes say to disable that plugin, and that the **"Behaviour - Backward Compatibility 6"** plugin must be installed and enabled for the upgrade (https://manual.joomla.org/updates/54-60/compat-plugin/). Test extensions with and without it.
- Joomla 6 minimums per the official Joomla guide (read 2026-10-24): PHP 8.3, MySQL 8.0.13, MariaDB 10.6, PostgreSQL 14. The Joomla Update component will not offer 6.x until the server meets them.
- Templates: overrides in `templates/<tpl>/html/` must be compared against the new core layouts.
- CLI (4+): `php cli/joomla.php list` shows the available commands; core update commands exist in recent versions. Confirm them with `list` before use.

## D. Automated migration tooling

- No official Rector set. Use Rector PHP sets for custom extensions; refactor `JFactory`/`J*` legacy classes to namespaced APIs by hand, or with custom rules.
- PHPCompatibility for custom extensions.
- Pre-Update Check (built in) for extension compatibility metadata. It relies on the extension authors' declarations, so verify by testing.
- Manual: custom components using removed legacy MVC, template overrides, third-party extensions you cannot modify.

## E. Test plan

| Layer | Command / action |
|---|---|
| Structural | `php -l` over custom extensions and template overrides; System → Maintenance: Database shows no schema problems |
| Security | Joomla Update shows no pending core updates; extension updates applied; runtime check; Joomla Security Centre (https://developer.joomla.org/security-centre.html) for core advisories |
| Static | PHPCompatibility on custom code |
| Tests | project tests if present; otherwise `blocked`. Core development uses PHPUnit and Cypress (https://github.com/joomla/joomla-cms) |
| DB | update on a disposable copy; Database "Fix" shows nothing outstanding afterwards |
| Runtime | front page, menu items, login, registration, forms, admin dashboard; enable "Debug System" + "Log Deprecated API" on staging and review `administrator/logs` |

## F. Recovery and rollback

- Full backup of files + DB before the update (Akeeba Backup, a third-party extension, is common; or a manual dump and archive).
- Core majors change the DB schema, so rollback = restore files + DB together.
- Clear cache (System → Clear Cache) and OPcache after restore.
- Limitations: commercial extensions may need licence renewals to obtain compatible versions.

## G. Sources

- https://downloads.joomla.org/technical-requirements
- https://docs.joomla.org/Portal:Upgrading_Versions (HTTP 403 to automated requests on 2026-10-24: not machine-verified)
- https://manual.joomla.org/updates/54-60/
- https://guide.joomla.org/user-guide/migration/joomla-5-to-6-planning-and-upgrade-step-by-step
- https://manual.joomla.org
- https://developer.joomla.org/security-centre.html
- https://endoflife.date/joomla (secondary)
- docs.joomla.org returned HTTP 403 to automated requests. The manual.joomla.org and guide.joomla.org pages above were read instead.
- Verified: 2026-10-24.
