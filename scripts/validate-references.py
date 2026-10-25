#!/usr/bin/env python3
"""Validate the skill's documentation, references and links.

Offline checks (default, no network):
  * SKILL.md frontmatter follows the Agent Skills specification (name, description, compatibility);
  * all required files exist;
  * every framework reference has sections A-G, a "Last verified" date and official sources;
  * framework references are not near-identical copies of each other;
  * relative Markdown links resolve; URLs are well formed and carry no tracking parameters;
  * every CVE identifier mentioned anywhere is registered in references/security/php2shell-advisories.md.

Online check (--online): requests every external URL and reports reachable / blocked / broken /
unreachable. Nothing is rewritten: an unreachable source must be fixed or marked by a human/agent.

Usage: validate-references.py [SKILL_DIR] [--online] [--report FILE] [--strict]
Exit codes: 0 ok, 1 offline errors (or broken URLs with --strict), 64 usage error.
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FRAMEWORK_DOCS = ["laravel", "symfony", "wordpress", "drupal", "codeigniter", "yii", "cakephp", "joomla", "october-cms",
                  "suitecrm", "espocrm", "nextcloud", "magento", "prestashop", "opencart", "slim", "dolibarr", "typo3",
                  "moodle", "mediawiki", "laminas", "phalcon", "phpmyadmin"]
REQUIRED = (["SKILL.md", "README.md", "LICENSE",
             "references/security/php2shell-advisories.md", "references/security/php-supported-versions.md",
             "references/security/vulnerability-verification.md", "references/security/remediation-policy.md",
             "references/security/php-advisory-data.json", "references/frameworks/framework-lifecycle.json",
             "references/frameworks/other-php-projects.md",
             "references/migration/migration-workflow.md", "references/migration/composer-dependencies.md",
             "references/migration/php-language-compatibility.md", "references/migration/database-migrations.md",
             "references/migration/deployment-and-rollback.md", "references/migration/legacy-applications.md",
             "references/testing/testing-strategy.md", "references/testing/framework-test-commands.md",
             "references/testing/security-verification.md", "references/testing/results-report-format.md",
             "scripts/detect-project.py", "scripts/check-php-version.py", "scripts/validate-references.py",
             "scripts/validate-results.py", "scripts/run-validation.sh", "scripts/install.py",
             "templates/migration-plan.md", "templates/migration-report.md", "templates/test-results.json",
             "templates/test-results.schema.json",
             "examples/laravel-migration.md", "examples/wordpress-migration.md", "examples/legacy-php-migration.md",
             "tests/README.md"]
            + [f"references/frameworks/{f}.md" for f in FRAMEWORK_DOCS])
SECTIONS = ["A. Project identification", "B. PHP compatibility", "C. Upgrade strategy", "D. Automated migration tooling",
            "E. Test plan", "F. Recovery and rollback", "G. Sources"]
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BARE_URL_RE = re.compile(r"(?<![(<\[])\bhttps?://[^\s)>\]`'\"]+")
CVE_RE = re.compile(r"\bCVE-\d{4}-\d{4,}\b")
SIMILARITY_LIMIT = 0.5


def md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "fixtures", "__pycache__")]
        for n in filenames:
            if n.endswith(".md"):
                yield os.path.join(dirpath, n)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def parse_frontmatter(text):
    if not text.startswith("---"):
        return None, "SKILL.md must start with YAML frontmatter (---)"
    end = text.find("\n---", 3)
    if end < 0:
        return None, "unterminated frontmatter"
    fm, current = {}, None
    for line in text[3:end].strip("\n").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")) and current:
            k, _, v = line.strip().partition(":")
            fm[current][k.strip()] = v.strip().strip("'\"")
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v in ("", "|", ">"):
            fm[k], current = {}, k
        else:
            fm[k], current = v.strip("'\""), None
    return fm, None


def check_skill_md(root, errors, warnings=None):
    warnings = [] if warnings is None else warnings
    text = read(os.path.join(root, "SKILL.md"))
    fm, err = parse_frontmatter(text)
    if err:
        errors.append(f"SKILL.md: {err}")
        return
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name or "") or len(name) > 64:
        errors.append(f"SKILL.md: invalid name {name!r} (1-64 chars, a-z 0-9 and single hyphens)")
    if name != os.path.basename(os.path.abspath(root)):
        errors.append(f"SKILL.md: name {name!r} must match directory {os.path.basename(os.path.abspath(root))!r}")
    if not isinstance(desc, str) or not 1 <= len(desc) <= 1024:
        errors.append("SKILL.md: description must be 1-1024 characters")
    # Portability rules beyond the spec, from client docs (README "Compatibility").
    if re.search(r"anthropic|claude", name or ""):
        errors.append("SKILL.md: name must not contain 'anthropic' or 'claude' (rejected by Claude surfaces)")
    if any(re.search(r"<[^>]+>", str(fm.get(k, ""))) for k in ("name", "description")):
        errors.append("SKILL.md: name/description must not contain XML tags (rejected by Claude surfaces)")
    for k, v in fm.items():
        if isinstance(v, str) and ": " in v:
            errors.append(f"SKILL.md: unquoted ': ' in '{k}' breaks strict YAML parsers used by some clients")
    if isinstance(desc, str) and len(desc) > 500:
        warnings.append("SKILL.md: description over 500 characters; keep it short for conservative cross-client portability")
    if "compatibility" in fm and not 1 <= len(fm["compatibility"]) <= 500:
        errors.append("SKILL.md: compatibility must be 1-500 characters")
    if "metadata" in fm and not isinstance(fm["metadata"], dict):
        errors.append("SKILL.md: metadata must be a mapping")
    if text.count("\n") > 500:
        errors.append("SKILL.md: body should stay under 500 lines (move detail to references/)")


def check_framework_doc(rel, text, errors):
    pos = -1
    for s in SECTIONS:
        m = re.search(rf"(?m)^##\s+{re.escape(s)}\b", text)
        if not m:
            errors.append(f"{rel}: missing section '## {s}'")
        elif m.start() < pos:
            errors.append(f"{rel}: section '{s}' out of order")
        else:
            pos = m.start()
    if not re.search(r"(?mi)^\**last verified:?\**:?\s*\d{4}-\d{2}-\d{2}", text):
        errors.append(f"{rel}: missing 'Last verified: YYYY-MM-DD' line")
    sources = text[text.find("## G. Sources"):] if "## G. Sources" in text else ""
    if "https://" not in sources:
        errors.append(f"{rel}: G. Sources has no https links")


def body_lines(text, fid):
    """Normalised content lines used for the duplicate-document check."""
    out = set()
    for line in text.splitlines():
        line = line.strip()
        if len(line) < 25 or line.startswith(("#", "|---", "```")):
            continue
        out.add(re.sub(r"\s+", " ", line.lower().replace(fid.replace("-", " "), "<fw>")))
    return out


def check_similarity(docs, errors):
    items = list(docs.items())
    for i, (a, la) in enumerate(items):
        for b, lb in items[i + 1:]:
            if la and lb:
                j = len(la & lb) / len(la | lb)
                if j > SIMILARITY_LIMIT:
                    errors.append(f"framework docs {a} and {b} are {j:.0%} identical: write project-specific content")


def check_url(url):
    p = urllib.parse.urlparse(url)
    if p.scheme not in ("http", "https") or "." not in p.netloc or " " in url:
        return "malformed URL"
    if any(k.lower().startswith("utm_") for k in urllib.parse.parse_qs(p.query)):
        return "tracking parameters (utm_*) must be removed"
    return None


def collect(root):
    errors, warnings, urls, docs = [], [], {}, {}
    for rel in REQUIRED:
        if not os.path.isfile(os.path.join(root, *rel.split("/"))):
            errors.append(f"missing required file {rel}")
    if os.path.isfile(os.path.join(root, "SKILL.md")):
        check_skill_md(root, errors, warnings)
    adv_path = os.path.join(root, "references", "security", "php2shell-advisories.md")
    known_cves = set(CVE_RE.findall(read(adv_path))) if os.path.isfile(adv_path) else set()
    for path in md_files(root):
        rel = os.path.relpath(path, root).replace("\\", "/")
        text = read(path)
        for _, target in LINK_RE.findall(text):
            if target.startswith(("http://", "https://")):
                urls.setdefault(target, set()).add(rel)
            elif not target.startswith(("#", "mailto:")):
                dest = os.path.normpath(os.path.join(os.path.dirname(path), urllib.parse.unquote(target.split("#")[0])))
                if not os.path.exists(dest):
                    errors.append(f"{rel}: broken relative link {target}")
        # Bare URLs inside code are illustrative commands (localhost, example hosts), not references.
        prose = re.sub(r"`[^`\n]*`", "", re.sub(r"(?s)```.*?```", "", text))
        for u in BARE_URL_RE.findall(prose):
            urls.setdefault(u.rstrip(".,;:"), set()).add(rel)
        for cve in set(CVE_RE.findall(text)) - known_cves:
            errors.append(f"{rel}: {cve} is not registered (with its source) in references/security/php2shell-advisories.md")
        fid = os.path.splitext(os.path.basename(rel))[0]
        if rel.startswith("references/frameworks/") and fid in FRAMEWORK_DOCS:
            check_framework_doc(rel, text, errors)
            docs[rel] = body_lines(text, fid)
    check_similarity(docs, errors)
    for u, where in sorted(urls.items()):
        problem = check_url(u)
        if problem:
            errors.append(f"{sorted(where)[0]}: {problem}: {u}")
        elif u.startswith("http://"):
            warnings.append(f"{sorted(where)[0]}: non-HTTPS URL {u}")
    return errors, warnings, urls


def probe(url, timeout=20):
    headers = {"User-Agent": "Mozilla/5.0 (php2shell-migration reference validator)"}
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return {"url": url, "status": "reachable", "http": resp.status, "final_url": resp.geturl()}
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in (403, 405, 400, 404, 429, 500, 501, 503):
                continue  # many servers reject HEAD: retry with GET
            kind = "blocked" if exc.code in (401, 403, 429, 503) else "broken"
            return {"url": url, "status": kind, "http": exc.code}
        except (urllib.error.URLError, OSError, ValueError) as exc:
            if method == "HEAD":
                continue
            return {"url": url, "status": "unreachable", "error": str(getattr(exc, "reason", exc))[:200]}
    return {"url": url, "status": "unreachable", "error": "no response"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=ROOT)
    ap.add_argument("--online", action="store_true", help="check every external URL (network)")
    ap.add_argument("--report", help="write a JSON report here")
    ap.add_argument("--strict", action="store_true", help="fail on broken URLs (online mode)")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.root):
        print(f"error: not a directory: {a.root}", file=sys.stderr)
        return 64
    errors, warnings, urls = collect(a.root)
    result = {"root": os.path.abspath(a.root), "errors": errors, "warnings": warnings, "url_count": len(urls), "online": None}
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    print(f"offline checks: {len(errors)} error(s), {len(warnings)} warning(s), {len(urls)} unique external URLs")
    broken = []
    if a.online:
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
            results = sorted(ex.map(probe, sorted(urls)), key=lambda r: (r["status"], r["url"]))
        for r in results:
            r["used_in"] = sorted(urls[r["url"]])
        counts = {}
        for r in results:
            counts[r["status"]] = counts.get(r["status"], 0) + 1
            if r["status"] != "reachable":
                print(f"{r['status']}: {r['url']} ({r.get('http') or r.get('error')}) in {', '.join(r['used_in'][:3])}")
        broken = [r for r in results if r["status"] in ("broken", "unreachable")]
        result["online"] = {"counts": counts, "results": results}
        print(f"online checks: {counts}")
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1)
    return 1 if errors or (a.strict and broken) else 0


if __name__ == "__main__":
    sys.exit(main())
