# PHP2Shell advisories (CVE registry)

**Last verified: 2026-10-24.** Every CVE identifier used anywhere in this skill must be registered here with its source; `scripts/validate-references.py` enforces that. Re-verify before every migration: advisories get updated.

"PHP2Shell" is the name used by security vendors and press for the two CVEs below. php.net's own announcement does not use the name; it calls them "Critical remote code execution vulnerabilities".

## Verified identifiers

| CVE | GHSA (php-src) | Title (official) | CVSS v4 | Published | Fixed in |
|---|---|---|---|---|---|
| CVE-2026-109618 | [GHSA-w8hw-w9fx-j79w](https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w) | RCE via OOM corruption | 9.2 (Critical) | 2026-10-21 | 8.2.35, 8.3.36, 8.4.27, 8.5.12 |
| CVE-2026-109619 | [GHSA-6wmf-4rv5-p3rp](https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp) | RCE via stale global state | 9.2 (Critical) | 2026-10-21 | 8.2.35, 8.3.36, 8.4.27, 8.5.12 |

CVSS vector (both, as published in the GHSA): `CVSS:4.0/AV:N/AC:H/AT:P/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N`.

How each fact was verified on 2026-10-24:

- **php.net announcement**: [php.net archive 2026, entry 2026-10-21-5](https://www.php.net/archive/2026.php#2026-10-21-5): "Security advisory: Critical remote code execution vulnerabilities, update now". It lists the fixed releases, the affected SAPIs and the mitigations. Release entries 2026-10-21-1 to -4 announce 8.2.35, 8.3.36, 8.4.27 and 8.5.12.
- **GitHub security advisories** (linked above): affected `< 8.2.35, < 8.3.36, < 8.4.27, < 8.5.12`; patched versions as listed.
- **CVE records**: the CVE Services API (`https://cveawg.mitre.org/api/cve/<ID>`) returned state `PUBLISHED`, assigner `php`, published 2026-10-21. The affected ranges cover the 8.2 to 8.5 branches and reference the GHSA. The cve.org and NVD web pages render with JavaScript and could not be read by a plain fetch; the NVD 2.0 API returned status `Analyzed` with CWE-416 for both.

## What is affected

Quoted from the php.net announcement: "all PHP installations serving web requests, including PHP-FPM, Apache with mod_php, php-cgi, FrankenPHP and LiteSpeed". php.net considers the risk **highest for mod_php**, where a demonstrated exploit triggers "before any application code runs". The CVE-2026-109618 GHSA describes mod_php as validated, and FPM, FrankenPHP and LSAPI as susceptible based on source analysis.

So application code, frameworks and WAF rules in the app cannot fix this. **Only the runtime can.**

### Older branches (8.1 and earlier)

- php.net: PHP 8.1 and older "no longer receive updates from the PHP project".
- php.net: the PHP security team provided "minimal source-backports for PHP 7.4, PHP 8.0, and PHP 8.1" for people building from source. Linux distributions and LTS vendors received patches in advance.
- The CVE records enumerate only the 8.2 to 8.5 ranges. **This skill treats 8.1 and older as affected** unless a vendor security notice for the exact installed package says otherwise, because php.net shipped backports for those branches. Claims that the bugs reach back to PHP 5.x (for example on Wikipedia) are **unverified** by primary sources. Do not repeat them as fact.

## Interim mitigations (not fixes)

php.net: "There are no complete mitigations, updating is the only safe choice." If a runtime cannot be updated immediately, apply these and record them as **temporary** in the report:

- **CVE-2026-109618**: `memory_limit=-1`, preferably enforced via `php_admin_value` in the FPM pool or Apache config. `post_max_size = 8M` (no uploads) or `32M` (uploads needed), with `upload_max_filesize` below it. Enforce memory with a container/cgroup limit. Do **not** use `RLIMIT_AS`/`RLIMIT_DATA`. The GHSA also suggests blocking multipart requests at the frontend if they are unused, and limiting input variables, nesting and parts.
- **CVE-2026-109619**: `session.upload_progress.enabled=0`, then restart every worker. Set it in `php.ini`, an FPM pool, or server configuration applied before request parsing. **Not** `ini_set()` or FPM `.user.ini`. On PHP 8.5 also set `fatal_error_backtraces=0`. The GHSA mentions `pm.max_requests=1` as an option if performance allows.
- Hiding diagnostics (`display_errors`, `error_reporting`, `@`) "does not help" (php.net).

## Related, not yet detailed

- **CVE-2026-115560**: php.net "Informational advisory: Session upload progress" (2026-10-23, [php.net archive 2026](https://www.php.net/archive/2026.php)). It is a separate issue, with a full advisory promised for the next release. It recommends `session.upload_progress.enabled=0` (already a mitigation above). Affected and fixed versions were **not published** as of 2026-10-24. Recheck.
- PHP 8.6.0 RC4 contains the fixes, but php.net says "DO NOT use this version in production".

## Secondary sources (context only, never the basis for version decisions)

- CISA alert: [Critical Vulnerabilities in PHP Require Immediate Patching](https://www.cisa.gov/news-events/alerts/2026/10/21/critical-vulnerabilities-php-require-immediate-patching) (HTTP 403 to automated requests on 2026-10-24: not machine-verified); the URL appeared in search results
- AlmaLinux packages: [AlmaLinux blog](https://almalinux.org/blog/2026-10-21-php2shell-cve-2026-109618-cve-2026-109619/)
- Red Hat CVE page: [access.redhat.com](https://access.redhat.com/security/cve/cve-2026-109618)

Secondary sources disagree on exploitability and timeline details. Base decisions on php.net and the GHSAs.

## Machine-readable copy

[php-advisory-data.json](php-advisory-data.json) holds the fixed versions and branch support dates used by `scripts/check-php-version.py`. Update it together with this file.

## How to recheck (agent procedure)

1. Fetch https://www.php.net/archive/ (current year) and https://github.com/php/php-src/security/advisories. Look for new entries since the date above.
2. Fetch `https://cveawg.mitre.org/api/cve/CVE-2026-109618` (and -109619). Compare the `affected` ranges and `dateUpdated`.
3. If anything changed, update both files and the date. If unreachable, record `"result": "unreachable"` in `advisories_checked`. Never write `verified` from memory.
