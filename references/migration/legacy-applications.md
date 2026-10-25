# Legacy applications

**Last verified: 2026-10-24.** For applications on PHP 5.x/7.x, EOL frameworks (Laravel ≤ 9, Symfony ≤ 4, Drupal 7, Joomla 3, CakePHP 2, Yii 1, CodeIgniter 3, Zend Framework 1/2), or no framework at all.

## Containment first

A legacy app on an EOL runtime is in category 2 (`runtime_unsupported`). Before any modernisation:

1. Get the runtime patched with what exists: a distribution/LTS vendor package with a documented PHP2Shell backport, or php.net's source backports for 7.4/8.0/8.1 built by a competent operator.
2. Apply the interim mitigations ([../security/php2shell-advisories.md](../security/php2shell-advisories.md#interim-mitigations-not-fixes)).
3. Reduce exposure: put it behind authentication/VPN, and block multipart if unused.

PHP 5.x and 7.0 to 7.3 have no php.net backport. Treat them as unpatchable and prioritise migration or isolation.

## Incremental plan

Climb one step at a time, keeping the app working at every step:

1. **Characterisation tests** before changing anything: HTTP-level tests that record current responses for key pages and APIs (curl/Playwright/Codeception scripts against a local copy), plus DB fixtures. Without tests, every later step is unverified.
2. **Put it under version control** and into a reproducible container on its *current* runtime.
3. **Runtime ladder**: 5.6 → 7.4 (largest break: `mysql_*` removal, use `mysqli`/PDO) → 8.0 → 8.1/8.2 → target. At each rung run `php -l`, PHPCompatibility for the next version, the characterisation tests, and fix.
4. **Framework ladder**: follow each major's official upgrade guide in order. No skipping where the framework says not to.
5. **Dependencies**: replace copied-in libraries with Composer packages where possible; record versions.

## Blockers to document explicitly

- Extensions with no modern equivalent (`mysql`, `mcrypt`; `ereg` was removed in 7.0) and the replacement chosen.
- Encoded/obfuscated code (ionCube, Zend Guard): needs the vendor's version for the target PHP.
- Abandoned commercial plugins/modules.
- Code relying on `register_globals`, `magic_quotes` or similar pre-5.4 behaviour.
- Missing source (only deployed files exist).

Each blocker gets an owner and a decision (replace, rewrite, vendor-patch, retire) in the plan. The skill reports them; it does not decide alone to drop a feature.

## When to stop and escalate

- The fix needs business decisions (dropping a feature, changing data formats).
- The app cannot be run locally at all (no DB dump, missing services): only planning and static work are possible, and tests are `blocked`.
