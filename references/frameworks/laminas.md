# Laminas (and Zend Framework) / Mezzio

**Last verified: 2026-10-24.** endoflife.date has no Laminas data, so lifecycle is **unknown** in the detector. Laminas is a set of independently versioned components, so there is no single "framework version".

## A. Project identification

- Website: https://getlaminas.org. Docs: https://docs.laminas.dev (components, MVC), https://docs.mezzio.dev (Mezzio). Source: https://github.com/laminas and https://github.com/mezzio.
- **Laminas MVC** signals: `config/application.config.php`, `config/modules.config.php`, `module/<Name>/Module.php`, `public/index.php` calling `Laminas\Mvc\Application::init()`, and `laminas/laminas-mvc` in the lock file.
- **Mezzio** signals: `config/config.php` (ConfigAggregator), `config/pipeline.php`, `config/routes.php`, and `mezzio/mezzio` in the lock file.
- **Zend Framework** (pre-2020 name): `zendframework/*` packages (ZF2/ZF3) or `library/Zend/` (ZF1, EOL 2016). ZF packages are abandoned and must become Laminas packages.
- Version: per component, e.g. `composer show 'laminas/*'`. Report the versions of `laminas-mvc` (or `mezzio/mezzio`) and the key components rather than one number.

## B. PHP compatibility

- Official: each package's `composer.json` `php` constraint (Packagist / the GitHub release), plus the Laminas maintenance status shown in each repository README and on https://getlaminas.org.
- Laminas components drop old PHP versions in new minors/majors independently. The practical check is `composer why-not php <target>`, which lists every blocking component.
- Some components are archived or security-only. Check each repository's README/status before targeting it, and choose replacements for archived ones (often a PSR-based library).
- Extensions: depend on the components used (`intl` for i18n, `mbstring`, PDO for laminas-db, ...).

## C. Upgrade strategy

- Official: per-component migration guides in each component's docs (e.g. "Migration" pages under https://docs.laminas.dev), and the Zend → Laminas migration guide https://docs.laminas.dev/migration/.
- ZF2/ZF3 → Laminas: run the migration (namespace `Zend\` → `Laminas\`, packages `zendframework/*` → `laminas/*`, with `laminas/laminas-zendframework-bridge` historically providing aliases). Then remove the bridge once the code uses the Laminas names.
- ZF1: a rewrite (to Laminas MVC, Mezzio or another framework). Treat it as legacy ([../migration/legacy-applications.md](../migration/legacy-applications.md)).
- Laminas MVC within the line:
  1. Patch PHP.
  2. `composer update 'laminas/*' -W` within the current majors.
  3. Read each component's migration notes for majors.
  4. Update one major family at a time (servicemanager, eventmanager, and mvc are tightly coupled).
- Service manager v3 → v4 and similar major moves change factory signatures. Review every factory.
- Mezzio: follow the Mezzio migration guides; middleware pipeline order matters for auth.

## D. Automated migration tooling

- Rector PHP sets. The historic `laminas/laminas-migration` tool handled Zend → Laminas renames; check its repository status before use (it may be archived), as plain Rector rename rules can do the same.
- PHPStan or Psalm (Laminas projects often use Psalm).
- Manual: factories and abstract factories, config merges, view helpers, forms/input filters (validation behaviour = security behaviour).

## E. Test plan

| Layer | Command |
|---|---|
| Structural | `composer validate`; `php -l module/ src/ config/`; `vendor/bin/laminas` *(if laminas-cli is installed)* |
| Security | `composer audit`; runtime check; Laminas advisories via https://getlaminas.org/security/ and the GitHub advisories of each component |
| Static | `vendor/bin/psalm` or `vendor/bin/phpstan analyse` |
| Tests | `vendor/bin/phpunit` |
| DB | app-specific (laminas-db has no migrations; check for Doctrine migrations or Phinx) |
| Runtime | the dev server (`php -S 0.0.0.0:8080 -t public`, dev only) or container; route smoke tests; forms with validation; auth flows |

## F. Recovery and rollback

- Commit per component family upgrade. `composer.lock` is the rollback unit together with the code.
- Clear the config cache (`data/cache/config-cache.php` or the configured path) after rollback.
- Limitations: archived components with no replacement are blockers. List them.

## G. Sources

- https://getlaminas.org
- https://docs.laminas.dev
- https://docs.laminas.dev/migration/
- https://docs.mezzio.dev
- https://getlaminas.org/security/
- Unverified: the archived/security-only status of individual components. Check each repo at upgrade time.
- Verified: 2026-10-24.
