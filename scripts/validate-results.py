#!/usr/bin/env python3
"""Validate a php2shell-migration test-results report and optionally render a Markdown summary.

Checks the JSON Schema in templates/test-results.schema.json (a small built-in subset of
JSON Schema: type, required, properties, items, enum, minLength, $ref) and the semantic
rules R1-R14 from references/testing/results-report-format.md. The rules exist so that a
report cannot claim more than its recorded evidence supports.

Usage:
  validate-results.py REPORT.json [--markdown OUT.md] [--quiet]
Exit codes: 0 valid, 1 invalid, 64 usage error.
"""
import argparse
import json
import os
import re
import sys

SCHEMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "templates", "test-results.schema.json")
REQUIRED_FOR_VERIFIED = ("syntax_check", "dependency_audit", "test_suite", "runtime_version_check", "web_runtime_check")
OVERCLAIM = re.compile(r"(?i)\b(fully|completely|100\s*%|totally)\s+secure\b|\bguaranteed\s+secure\b|\bno\s+vulnerabilities\b")
TYPES = {"string": str, "boolean": bool, "array": list, "object": dict, "null": type(None)}


def _is_type(value, t):
    if t == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return isinstance(value, TYPES[t])


def check_schema(value, schema, root, path="$"):
    if "$ref" in schema:
        schema = root["$defs"][schema["$ref"].split("/")[-1]]
    errors = []
    types = schema.get("type")
    if types:
        types = types if isinstance(types, list) else [types]
        if not any(_is_type(value, t) for t in types):
            return [f"{path}: expected {'/'.join(types)}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in {schema['enum']}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        errors.append(f"{path}: must not be empty")
    if isinstance(value, dict):
        errors += [f"{path}: missing required key '{k}'" for k in schema.get("required", []) if k not in value]
        for k, sub in schema.get("properties", {}).items():
            if k in value:
                errors += check_schema(value[k], sub, root, f"{path}.{k}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors += check_schema(item, schema["items"], root, f"{path}[{i}]")
    return errors


def derive_overall(report):
    """The only overall_result a report's own evidence permits (rule R10)."""
    tests = report["tests"]
    statuses = [t["status"] for t in tests]
    if "failed" in statuses:
        return "failed"
    if "passed" not in statuses:
        return "blocked" if "blocked" in statuses else "not_verified"
    sec, mig = report["security"], report["migration"]
    passed = {t["name"] for t in tests if t["status"] == "passed"}
    advisories = sec["advisories_checked"]
    if (not any(s in ("blocked", "not_run") for s in statuses)
            and all(n in passed for n in REQUIRED_FOR_VERIFIED)
            and sec["runtime_patch_verified"] and sec["web_runtime_verified"]
            and not sec["remaining_findings"]
            and mig["status"] in ("completed", "not_required")
            and advisories and all(a["result"] == "verified" for a in advisories)):
        return "verified"
    return "partially_verified"


def check_semantics(report):
    errors, warnings = [], []
    tests = report["tests"]
    names = [t["name"] for t in tests]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        errors.append(f"R2: duplicate test names {dupes}")
    for t in tests:
        n, st, cmd, code = t["name"], t["status"], t["command"], t["exit_code"]
        if st in ("passed", "failed") and (not isinstance(cmd, str) or not cmd.strip() or code is None):
            errors.append(f"R3: test '{n}' is {st} but has no executed command and exit code")
        if st == "passed" and code not in (None, 0):
            errors.append(f"R4: test '{n}' is passed with non-zero exit code {code}")
        if st == "passed" and not t["evidence"]:
            errors.append(f"R4: test '{n}' is passed without evidence (output excerpt, log path or artifact)")
        if st == "not_run" and (cmd is not None or code is not None):
            errors.append(f"R5: test '{n}' is not_run but records a command or exit code; use passed/failed/blocked")
        if st in ("skipped", "blocked", "failed") and not t["summary"].strip():
            errors.append(f"R6/R7: test '{n}' is {st} without a summary/reason")
    passed = {t["name"] for t in tests if t["status"] == "passed"}
    sec = report["security"]
    if sec["runtime_patch_verified"] and "runtime_version_check" not in passed:
        errors.append("R8: runtime_patch_verified is true without a passed 'runtime_version_check' test")
    if sec["web_runtime_verified"] and not (sec["runtime_patch_verified"] and "web_runtime_check" in passed):
        errors.append("R9: web_runtime_verified is true without runtime_patch_verified and a passed 'web_runtime_check' test")
    expected = derive_overall(report)
    if report["overall_result"] != expected:
        errors.append(f"R10: overall_result is '{report['overall_result']}' but the recorded evidence permits only '{expected}'")
    if report["overall_result"] == "verified" and not sec["advisories_checked"]:
        errors.append("R11: verified requires advisories_checked entries")
    if report["migration"]["status"] == "completed" and not report["migration"]["rollback_available"]:
        warnings.append("R12: migration completed but rollback_available is false")
    texts = [report.get("summary", "")] + [t["summary"] for t in tests]
    if any(OVERCLAIM.search(x or "") for x in texts):
        errors.append("R13: report claims the application is fully/completely secure; tests cannot establish that")
    if any(t["status"] in ("skipped", "blocked", "not_run") for t in tests) and not report["limitations"]:
        errors.append("R14: skipped/blocked/not_run tests require at least one entry in limitations")
    return errors, warnings


def validate(report, schema=None):
    """Return (errors, warnings)."""
    if schema is None:
        with open(SCHEMA, encoding="utf-8") as fh:
            schema = json.load(fh)
    errors = check_schema(report, schema, schema)
    if errors:
        return errors, []  # semantic rules assume a structurally valid report
    return check_semantics(report)


def to_markdown(report):
    p, s, m = report["project"], report["security"], report["migration"]
    yes = lambda b: "yes" if b else "**no**"
    auto = [t for t in report["tests"] if t.get("layer") == "automated_tests" or t["name"] == "test_suite"]
    out = [f"# Migration test results: {p['name']}", "",
           f"**Overall result:** `{report['overall_result']}`", "",
           "| Question | Answer |", "|---|---|",
           f"| Runtime patch verified | {yes(s['runtime_patch_verified'])} |",
           f"| Application migration completed | {yes(m['status'] in ('completed', 'not_required'))} (`{m['status']}`) |",
           f"| Automated tests passed | {yes(auto and all(t['status'] == 'passed' for t in auto))} |",
           f"| Deployment (web) runtime verified | {yes(s['web_runtime_verified'])} |",
           f"| Remaining security findings | {len(s['remaining_findings'])} |", "",
           f"Framework: {p['framework']} {p['framework_version_before'] or '?'} -> {p['framework_version_after'] or '?'}; "
           f"PHP: {p['php_version_before'] or '?'} -> {p['php_version_after'] or '?'}", "",
           "## Tests", "", "| Test | Layer | Status | Exit | Command | Summary |", "|---|---|---|---|---|---|"]
    for t in report["tests"]:
        cmd = f"`{t['command']}`" if t["command"] else "-"
        out.append(f"| {t['name']} | {t.get('layer', '-')} | {t['status']} | {t['exit_code'] if t['exit_code'] is not None else '-'} | {cmd} | {t['summary'].replace('|', '/')} |")
    out += ["", "## Advisories checked", ""] + ([f"- {a['id']}: {a['result']} ({a['source']}, {a.get('checked_on') or 'date not recorded'})" for a in s["advisories_checked"]] or ["- none"])
    out += ["", "## Remaining findings", ""] + ([f"- [{f['severity']}] {f['id']} ({f['category']}): {f['description']}" for f in s["remaining_findings"]] or ["- none recorded"])
    out += ["", "## Limitations", ""] + ([f"- {x}" for x in report["limitations"]] or ["- none recorded"])
    out += ["", "_A passing test suite does not prove the runtime is patched, and a patched runtime does not prove the application is secure._", ""]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report")
    ap.add_argument("--markdown", help="write a Markdown summary here (only if the report is valid)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    try:
        with open(a.report, encoding="utf-8") as fh:
            report = json.load(fh)
    except (OSError, ValueError) as exc:
        print(f"error: cannot read report: {exc}", file=sys.stderr)
        return 64
    errors, warnings = validate(report)
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"error: {e}")
    if errors:
        print(f"INVALID: {len(errors)} error(s)")
        return 1
    if a.markdown:
        with open(a.markdown, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(report))
    if not a.quiet:
        print(f"VALID: overall_result={report['overall_result']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
