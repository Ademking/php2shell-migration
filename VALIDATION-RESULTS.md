# Validation results (skill development run)

Recorded on 2026-10-24, updated 2026-10-25 after adding cross-tool installation, on Windows 11 with Python 3.12.10 (Git Bash for `run-validation.sh`). These results cover **the skill's own scripts and documents only**. They are not evidence about any PHP application.

## Commands and actual results

| Command | Exit | Result |
|---|---|---|
| `python -m unittest discover -s tests -v` | 0 | **109 tests, all passed**: test_project_detection 31, test_validation_reporting 31, test_version_detection 21, test_install 13, test_reference_integrity 13. 0 skipped (the symlink test ran: symlinks are available on this machine), 0 failures, 0 ResourceWarnings. |
| `python scripts/validate-references.py` | 0 | Offline: 0 errors, 0 warnings, 248 unique external URLs, all 23 framework references with sections A–G. |
| `python scripts/validate-references.py --online` | 0 | 240 reachable, **8 blocked** (HTTP 403 to automated clients), 0 broken (see below). |
| `sh scripts/run-validation.sh` | 0 | Unit tests OK, references OK, `templates/test-results.json` VALID (`not_verified`). "ALL VALIDATION PASSED". |

### Fixed during development (failures found by the checks)

- Version checker: a stray control character in a regex broke Docker-tag handling; release candidates of a fixed version were classified `runtime_affected` (now `status_unknown`).
- Detector: a test fixture with binary bytes before `FROM` was unrealistic, so the fixture was corrected; the code path still handles undecodable bytes.
- Reference validator: illustrative `http://localhost` URLs inside code were flagged; code spans/blocks are now excluded from the bare-URL scan.
- Online check, first run: 3 broken links (TYPO3 upgrade guide, Nextcloud advisories, MediaWiki version lifecycle). Replaced with the URLs the projects now use, and confirmed reachable.

### URLs blocked to automated clients (403), marked in the documents

`https://core.trac.wordpress.org`, `https://docs.joomla.org` (+ `/Portal:Upgrading_Versions`), `https://docs.moodle.org` (+ `/en/Upgrading`; its content was read through a fetch tool), `https://moodle.org`, `https://helpx.adobe.com/security/products/magento.html`, the CISA alert URL. Each is annotated in the relevant document or has an alternative official source next to it.

### Reachable vs verified

"Reachable" means the URL answered HTTP 2xx/3xx. The **content** of these primary sources was read and used for factual claims:

- php.net archive 2026, php.net supported versions, GHSA-w8hw-w9fx-j79w, GHSA-6wmf-4rv5-p3rp
- CVE Services API records for both CVEs (state PUBLISHED, assigner `php`, published 2026-10-21); NVD API status "Analyzed"
- Agent Skills specification; endoflife.date API (lifecycle data)
- MediaWiki Version lifecycle, Nextcloud security page, TYPO3 major upgrade page, Moodle Upgrading page, Joomla 5.4 → 6.0 notes and guide

The other framework facts come from the official documentation as known at writing time, are hedged where uncertain, and must be rechecked at use (each document says so).

## Cross-tool installation (2026-10-25)

- Skill discovery paths were read from the official docs of Claude Code, OpenAI Codex, VS Code / GitHub Copilot, GitHub Copilot CLI, Cursor, Gemini CLI, OpenCode, the Claude platform and the Claude Help Center (links in the README "Compatibility" table).
- `scripts/install.py` was exercised against a throwaway home and project directory: copy into `~/.agents/skills`, symlink from `~/.claude/skills`, re-install (update), refusal of a foreign directory, uninstall, and zip packaging. All of this is also covered by `tests/test_install.py`.
- Not done: loading the installed skill inside each product. Compatibility rests on the vendors' documented paths and format rules.

## Environment observation

The CLI PHP on the development machine is **PHP 8.3.30**, which `scripts/check-php-version.py` classifies as `runtime_affected` (fixed in 8.3.36). This is a CLI-only observation of a developer workstation, not a web runtime.

## Not performed

- `skills-ref validate` (the spec authors' reference validator) was not installed or run; the spec rules are checked by `validate-references.py` instead.
- No end-to-end run inside a specific agent product (Claude Code, Codex, ...). Compatibility rests on the vendors' documented paths and the spec.
- No production systems, credentials or databases were touched.
