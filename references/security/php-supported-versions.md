# PHP supported versions

**Last verified: 2026-10-24** against https://www.php.net/supported-versions.php and https://www.php.net/archive/2026.php.
Lifecycle dates change rarely, but release numbers change monthly. **Always re-read the official page before choosing a target.**

| Branch | Initial release | Active support until | Security support until | Latest release (2026-10-24) | PHP2Shell fixed in |
|---|---|---|---|---|---|
| 8.5 | 2025-11-20 | 2027-12-31 | 2029-12-31 | 8.5.12 | 8.5.12 |
| 8.4 | 2024-11-21 | 2026-12-31 | 2028-12-31 | 8.4.27 | 8.4.27 |
| 8.3 | 2023-11-23 | 2025-12-31 | 2027-12-31 | 8.3.36 | 8.3.36 |
| 8.2 | 2022-12-08 | 2024-12-31 | 2026-12-31 | 8.2.35 | 8.2.35 |
| 8.1 and older | - | ended | ended (8.1: 2025-12-31) | 8.1.34 | no official release |

The 8.1 end date and latest release come from endoflife.date (secondary source; see [framework-lifecycle.json](../frameworks/framework-lifecycle.json)). PHP 8.6 was at RC4 on 2026-10-21 and is not a production target.

## Choosing a target runtime

1. **Security patch first**: the latest patch release of the branch already in use, if that branch is supported. Same-branch updates are the lowest-risk remediation.
2. **Branch migration**: if the branch is EOL, or EOL within the project's planning horizon (8.2 ends 2026-12-31), choose the newest supported branch that **the framework version officially supports** (see the framework reference). If the framework does not support it, plan a framework upgrade stage or use the newest branch it supports.
3. Prefer branches in active support for long-lived systems. Security-only branches are acceptable short-term.
4. Never pick a pre-release (RC/beta) or a version not listed on php.net.
5. Record the source URL and date of every version claim in the plan.

## Vendor builds

Distribution packages (Debian/Ubuntu, RHEL/AlmaLinux/Rocky, SUSE, Alpine, cPanel EA-PHP, CloudLinux alt-php, Remi, Ondřej Surý PPA, TuxCare) carry their own version strings and may backport fixes without changing the upstream number. The upstream version alone is then **not** proof either way. See [vulnerability-verification.md](vulnerability-verification.md).

## Sources

- https://www.php.net/supported-versions.php
- https://www.php.net/releases/
- https://www.php.net/archive/
- https://www.php.net/eol.php
- https://endoflife.date/php (secondary)
