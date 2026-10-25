#!/usr/bin/env python3
"""Classify a PHP version string against the PHP2Shell advisories and PHP lifecycle data.

Offline: reads references/security/php-advisory-data.json (refresh that file from
php.net before trusting the result). Never executes PHP.

Usage:
  check-php-version.py "8.3.30"
  check-php-version.py "$(php -v | head -n1)" --sapi cli
  check-php-version.py "8.1.2-1ubuntu2.20" --json

Exit codes: 0 runtime_patched, 2 runtime_affected/runtime_unsupported, 3 status_unknown, 64 usage error.
"""
import argparse
import datetime
import json
import os
import re
import sys

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "references", "security", "php-advisory-data.json")
VERSION_RE = re.compile(r"(?<![\d.])(\d+)\.(\d+)(?:\.(\d+))?((?:-|~|\+|RC|alpha|beta)[0-9A-Za-z.+~\-]*)?")
SAPI_RE = re.compile(r"\((cli|fpm-fcgi|cgi-fcgi|apache2handler|litespeed|frankenphp|embed|phpdbg)\)", re.I)
# Version suffixes that indicate a distribution/vendor build which may carry backported fixes.
VENDOR_RE = re.compile(r"^-\d|^\+|ubuntu|deb\d*u|\.el\d|remi|amzn|suse|cloudlinux|tuxcare|ppa|\.fc\d+", re.I)
# Official Docker image variant tags (php:8.3.36-fpm-alpine) are upstream builds, not vendor patches.
DOCKER_TAG_RE = re.compile(r"^-(fpm|apache|cli|zts|alpine|bookworm|bullseye|buster|trixie)(?![a-z])", re.I)
PRERELEASE_RE = re.compile(r"RC|alpha|beta|dev", re.I)


def load_data(path=DATA):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def parse_version(text):
    m = VERSION_RE.search(text or "")
    if not m:
        return None
    major, minor, patch, suffix = m.group(1), m.group(2), m.group(3), m.group(4) or ""
    if DOCKER_TAG_RE.match(suffix):
        suffix = ""
    return {
        "major": int(major), "minor": int(minor),
        "patch": int(patch) if patch is not None else None,
        "suffix": suffix, "branch": f"{major}.{minor}",
        "version": f"{major}.{minor}" + (f".{patch}" if patch is not None else ""),
    }


def classify(text, sapi=None, data=None, today=None):
    data = data or load_data()
    today = today or datetime.date.today()
    out = {"input": text, "parsed": None, "sapi": sapi, "vendor_build": False, "prerelease": False,
           "branch_status": "unknown", "advisories": [], "classification": "status_unknown",
           "notes": [], "data_verified_on": data.get("verified_on")}
    m = SAPI_RE.search(text or "")
    if m and not sapi:
        out["sapi"] = m.group(1).lower()
    v = parse_version(text)
    if not v:
        out["notes"].append("Could not parse a PHP version from the input.")
        return out
    out["parsed"] = v
    out["vendor_build"] = bool(v["suffix"] and VENDOR_RE.search(v["suffix"]))
    out["prerelease"] = bool(v["suffix"] and PRERELEASE_RE.search(v["suffix"]))
    key = (v["major"], v["minor"])
    branches = {tuple(map(int, b.split("."))): info for b, info in data["branches"].items()}

    if key in branches:
        eol = datetime.date.fromisoformat(branches[key]["security_support_until"])
        out["branch_status"] = "supported" if today <= eol else "eol"
        out["security_support_until"] = branches[key]["security_support_until"]
    elif key < min(branches):
        out["branch_status"] = "eol"
    else:
        out["branch_status"] = "unknown"
        out["notes"].append(f"Branch {v['branch']} is newer than the advisory data (verified {data.get('verified_on')}); refresh php-advisory-data.json from php.net.")

    affected = False
    unknown = False
    for adv in data["advisories"]:
        fixed = adv["fixed_in"].get(v["branch"])
        entry = {"id": adv["id"], "fixed_in": fixed}
        if fixed is None:
            if out["branch_status"] == "eol":
                entry["status"] = "affected_unless_vendor_backport"
                affected = True
            else:
                entry["status"] = "unknown"
                unknown = True
        elif v["patch"] is None:
            entry["status"] = "unknown"
            unknown = True
        elif out["prerelease"]:
            entry["status"] = "unknown"
            unknown = True
        elif v["patch"] >= int(fixed.split(".")[2]):
            entry["status"] = "fixed"
        elif out["vendor_build"]:
            entry["status"] = "vendor_backport_possible"
            unknown = True
        else:
            entry["status"] = "affected"
            affected = True
        out["advisories"].append(entry)

    if v["patch"] is None:
        out["notes"].append("No patch level given (branch only, e.g. a floating Docker tag): resolve the exact running version.")
    if out["vendor_build"] and any(a["status"] == "vendor_backport_possible" for a in out["advisories"]):
        out["notes"].append("Vendor/distribution build below the upstream fixed version: check the vendor security notice and package changelog before concluding it is affected or patched.")
    elif out["vendor_build"] and out["branch_status"] == "eol":
        out["notes"].append("Vendor/distribution build of an EOL branch: a vendor backport may exist; collect the vendor notice as evidence, then still plan a branch migration.")
    if out["prerelease"]:
        out["notes"].append("Pre-release build: never a production remediation target.")

    if out["branch_status"] == "eol":
        out["classification"] = "runtime_unsupported"
        out["notes"].append("Branch receives no official PHP security releases: migrate to a supported branch (vendor backports are a temporary measure only).")
    elif affected:
        out["classification"] = "runtime_affected"
    elif unknown:
        out["classification"] = "status_unknown"
    else:
        out["classification"] = "runtime_patched"
    if out["sapi"] == "cli":
        out["notes"].append("CLI runtime only: this does not verify the PHP version serving web requests (FPM/mod_php/CGI).")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version", help="Version string or the first line of `php -v`")
    ap.add_argument("--sapi", help="SAPI the version was observed from (cli, fpm-fcgi, apache2handler, ...)")
    ap.add_argument("--data", default=DATA, help="Advisory data JSON")
    ap.add_argument("--today", help="Override today's date (YYYY-MM-DD) for lifecycle checks")
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    a = ap.parse_args(argv)
    try:
        data = load_data(a.data)
        today = datetime.date.fromisoformat(a.today) if a.today else None
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 64
    r = classify(a.version, a.sapi, data, today)
    if a.json:
        print(json.dumps(r, indent=2))
    else:
        ver = r["parsed"]["version"] + r["parsed"]["suffix"] if r["parsed"] else "?"
        print(f"PHP {ver}{' (' + r['sapi'] + ')' if r['sapi'] else ''}: {r['classification']} [branch {r['branch_status']}]")
        for adv in r["advisories"]:
            print(f"  {adv['id']}: {adv['status']} (fixed in {adv['fixed_in'] or 'no official release'})")
        for n in r["notes"]:
            print(f"  note: {n}")
        print(f"  advisory data verified on {r['data_verified_on']}")
    return {"runtime_patched": 0, "runtime_affected": 2, "runtime_unsupported": 2}.get(r["classification"], 3)


if __name__ == "__main__":
    sys.exit(main())
