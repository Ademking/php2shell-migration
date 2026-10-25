# PHP language compatibility

**Last verified: 2026-10-24.** Summary of what usually breaks per branch. The authoritative lists are the official migration guides: https://www.php.net/manual/en/appendices.php ("Migrating from PHP X to Y").

## High-impact changes by version

| Moving to | Typical breakage to search for | Official guide |
|---|---|---|
| 7.0 | `mysql_*` removed, `ereg*` removed, PHP 4 constructors deprecated, `split()` removed, uniform variable syntax | https://www.php.net/manual/en/migration70.php |
| 7.2/7.3/7.4 | `create_function`, `each()` deprecated (7.2); `continue` targeting `switch` warns (7.3); curly brace string offsets, `money_format`, `real` type deprecated (7.4) | https://www.php.net/manual/en/migration74.php |
| 8.0 | String/number comparison changes, `match` keyword reserved, `@` no longer silences fatals, required-after-optional params, arithmetic on arrays/null throws `TypeError`, removed `each()`, `create_function`, `$php_errormsg` | https://www.php.net/manual/en/migration80.php |
| 8.1 | Passing `null` to non-nullable internal params deprecated, `Serializable` without `__serialize` deprecated, return type deprecations for internal class overrides (`#[\ReturnTypeWillChange]`) | https://www.php.net/manual/en/migration81.php |
| 8.2 | Dynamic properties deprecated (`#[\AllowDynamicProperties]`), `${var}` string interpolation deprecated, `utf8_encode/decode` deprecated | https://www.php.net/manual/en/migration82.php |
| 8.3 | Typed class constants, `json_validate()`; minor deprecations | https://www.php.net/manual/en/migration83.php |
| 8.4 | Implicitly nullable parameter types deprecated (`function f(Foo $x = null)`), new property hooks / asymmetric visibility, `E_STRICT` constant deprecated, `exit()` behaviour changes | https://www.php.net/manual/en/migration84.php |
| 8.5 | See the official guide; includes deprecations to check before targeting 8.5 | https://www.php.net/manual/en/migration85.php |

This table is a search aid, not a complete list. Read the guide for every branch you cross.

## Tools

| Tool | Use | Notes |
|---|---|---|
| `php -l` | Syntax check per file with the **target** binary | Necessary, nowhere near sufficient. |
| PHPCompatibility (PHP_CodeSniffer standard) | Static detection of removed/changed features by `testVersion` | `vendor/bin/phpcs -p --standard=PHPCompatibility --runtime-set testVersion 8.4- src/`. Check the installed release supports the target version; development versions track newer PHP. |
| Rector | Automated upgrades (`withPhpSets()`, `LevelSetList`/`SetList` in older configs) | Always `--dry-run` first; review every change. |
| PHPStan | Type-level errors surfaced by new runtime behaviour | Use `phpVersion` to analyse for the target. |
| Deprecation logs | Runtime deprecations during tests (`E_DEPRECATED`) | Run the suite with deprecations reported on the target runtime. |

Example Rector config (adapt the paths and target; check Rector's docs for your installed version):

```php
<?php
use Rector\Config\RectorConfig;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src', __DIR__ . '/tests'])
    ->withPhpSets(php84: true);
```

```sh
vendor/bin/rector process --dry-run
```

## Manual review is required for

- Code relying on loose comparison (`==`) between strings and numbers (PHP 8.0 semantic change, silent behaviour change).
- Serialization formats stored in DB/cache (`Serializable`, `__sleep`).
- Locale-dependent float/string conversion (changed in 8.0).
- Extensions removed from core or moved to PECL (e.g. `imap` unbundled in 8.4, `pspell` in 8.4, `oci8` in 8.4); check the target's extension list.
- Reflection, `ReturnTypeWillChange`, and magic methods in libraries you maintain.
- Anything Rector changed in auth, crypto, money or date handling.

## Sources

- https://www.php.net/manual/en/appendices.php
- https://getrector.com/documentation
- https://github.com/PHPCompatibility/PHPCompatibility
- https://phpstan.org/config-reference
