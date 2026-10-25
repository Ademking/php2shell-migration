import contextlib
import copy
import io
import json
import os
import re
import tempfile
import unittest

from helpers import SKILL_ROOT, load_script, read_text, write_text

vr = load_script("validate-results.py")
with open(os.path.join(SKILL_ROOT, "templates", "test-results.schema.json"), encoding="utf-8") as fh:
    SCHEMA = json.load(fh)


def passed(name, layer, cmd="cmd", evidence=("exit 0; output excerpt",)):
    return {"name": name, "layer": layer, "status": "passed", "command": cmd, "exit_code": 0,
            "summary": f"{name} passed", "evidence": list(evidence)}


def verified_report():
    return {
        "skill": "php2shell-migration",
        "summary": "Runtime and application migrated; evidence recorded.",
        "project": {"name": "demo", "framework": "laravel", "framework_version_before": "11.57.0", "framework_version_after": "12.70.1",
                    "php_version_before": "8.2.20", "php_version_after": "8.4.27"},
        "security": {"advisories_checked": [{"id": "CVE-2026-109618", "source": "https://github.com/php/php-src/security/advisories/GHSA-w8hw-w9fx-j79w", "checked_on": "2026-10-24", "result": "verified"},
                                            {"id": "CVE-2026-109619", "source": "https://github.com/php/php-src/security/advisories/GHSA-6wmf-4rv5-p3rp", "checked_on": "2026-10-24", "result": "verified"}],
                     "runtime_patch_verified": True, "web_runtime_verified": True, "remaining_findings": []},
        "migration": {"status": "completed", "files_changed": ["composer.json", "composer.lock"], "database_changes": [], "rollback_available": True},
        "tests": [passed("syntax_check", "structural", "find . -name '*.php' -print0 | xargs -0 -n1 php -l"),
                  passed("dependency_audit", "security", "composer audit"),
                  passed("test_suite", "automated_tests", "php artisan test"),
                  passed("runtime_version_check", "runtime", "php -v"),
                  passed("web_runtime_check", "runtime", "curl -s https://staging.example.test/health")],
        "limitations": [],
        "overall_result": "verified",
    }


def test_by_name(report, name):
    return next(t for t in report["tests"] if t["name"] == name)


class TemplateAndSchema(unittest.TestCase):
    def test_template_is_valid_and_not_verified(self):
        with open(os.path.join(SKILL_ROOT, "templates", "test-results.json"), encoding="utf-8") as fh:
            tpl = json.load(fh)
        errors, _ = vr.validate(tpl, SCHEMA)
        self.assertEqual(errors, [])
        self.assertEqual(tpl["overall_result"], "not_verified")
        self.assertTrue(all(t["status"] == "not_run" for t in tpl["tests"]))

    def test_enums_documented(self):
        doc = read_text(os.path.join(SKILL_ROOT, "references", "testing", "results-report-format.md"))
        enums = (SCHEMA["$defs"]["test"]["properties"]["status"]["enum"] + SCHEMA["properties"]["overall_result"]["enum"]
                 + SCHEMA["properties"]["migration"]["properties"]["status"]["enum"])
        for value in enums:
            self.assertIn(f"`{value}`", doc, f"{value} not documented")
        for rule in ("R1", "R3", "R5", "R8", "R10", "R13", "R14"):
            self.assertIn(rule, doc)

    def test_full_verified_report_is_valid(self):
        errors, warnings = vr.validate(verified_report(), SCHEMA)
        self.assertEqual((errors, warnings), ([], []))

    def test_schema_violations(self):
        r = verified_report()
        del r["tests"][0]["exit_code"]
        r["overall_result"] = "secure"
        r["security"]["runtime_patch_verified"] = "yes"
        errors, _ = vr.validate(r, SCHEMA)
        joined = "\n".join(errors)
        self.assertIn("missing required key 'exit_code'", joined)
        self.assertIn("'secure' not in", joined)
        self.assertIn("expected boolean", joined)

    def test_bool_is_not_integer_exit_code(self):
        r = verified_report()
        r["tests"][0]["exit_code"] = True
        self.assertTrue(any("expected integer/null" in e for e in vr.validate(r, SCHEMA)[0]))


class AntiFabrication(unittest.TestCase):
    def assertRule(self, report, rule):
        errors, _ = vr.validate(report, SCHEMA)
        self.assertTrue(any(e.startswith(rule) for e in errors), f"expected {rule}, got {errors}")

    def test_passed_without_command_is_fabrication(self):
        r = verified_report()
        test_by_name(r, "test_suite").update(command=None, exit_code=None)
        self.assertRule(r, "R3")

    def test_passed_with_nonzero_exit(self):
        r = verified_report()
        test_by_name(r, "test_suite")["exit_code"] = 1
        self.assertRule(r, "R4")

    def test_passed_without_evidence(self):
        r = verified_report()
        test_by_name(r, "dependency_audit")["evidence"] = []
        self.assertRule(r, "R4")

    def test_not_run_with_command_or_exit(self):
        r = verified_report()
        test_by_name(r, "test_suite").update(status="not_run", exit_code=0)
        self.assertRule(r, "R5")

    def test_blocked_needs_reason(self):
        r = verified_report()
        test_by_name(r, "test_suite").update(status="blocked", command=None, exit_code=None, summary="")
        self.assertRule(r, "R6")

    def test_runtime_verified_needs_passed_check(self):
        r = verified_report()
        test_by_name(r, "runtime_version_check").update(status="not_run", command=None, exit_code=None, evidence=[], summary="")
        r["limitations"] = ["x"]
        self.assertRule(r, "R8")

    def test_web_runtime_needs_its_own_check(self):
        r = verified_report()
        r["tests"] = [t for t in r["tests"] if t["name"] != "web_runtime_check"]
        self.assertRule(r, "R9")

    def test_cli_only_cannot_claim_web_runtime(self):
        r = verified_report()
        r["security"]["runtime_patch_verified"] = False
        self.assertRule(r, "R9")

    def test_overclaiming_language(self):
        r = verified_report()
        r["summary"] = "All tests pass, the application is fully secure."
        self.assertRule(r, "R13")

    def test_skips_need_limitations(self):
        r = verified_report()
        test_by_name(r, "test_suite").update(status="skipped", command=None, exit_code=None, summary="no runner")
        r["overall_result"] = "partially_verified"
        self.assertRule(r, "R14")

    def test_duplicate_names(self):
        r = verified_report()
        r["tests"].append(copy.deepcopy(r["tests"][0]))
        self.assertRule(r, "R2")


class OverallOutcome(unittest.TestCase):
    """R10: overall_result must equal what the evidence permits."""

    def derive(self, mutate):
        r = verified_report()
        mutate(r)
        return vr.derive_overall(r)

    def test_all_pass_is_verified(self):
        self.assertEqual(self.derive(lambda r: None), "verified")

    def test_any_failure_is_failed(self):
        self.assertEqual(self.derive(lambda r: test_by_name(r, "test_suite").update(status="failed", exit_code=1)), "failed")

    def test_skipped_optional_test_keeps_verified(self):
        def m(r):
            r["tests"].append({"name": "phpstan", "layer": "static_analysis", "status": "skipped", "command": None,
                               "exit_code": None, "summary": "not installed", "evidence": []})
        self.assertEqual(self.derive(m), "verified")

    def test_skipped_required_test_is_partial(self):
        self.assertEqual(self.derive(lambda r: test_by_name(r, "test_suite").update(status="skipped")), "partially_verified")

    def test_blocked_or_not_run_test_is_partial(self):
        self.assertEqual(self.derive(lambda r: test_by_name(r, "test_suite").update(status="blocked")), "partially_verified")
        self.assertEqual(self.derive(lambda r: test_by_name(r, "test_suite").update(status="not_run")), "partially_verified")

    def test_nothing_passed(self):
        def all_status(s):
            return lambda r: [t.update(status=s) for t in r["tests"]]
        self.assertEqual(self.derive(all_status("not_run")), "not_verified")
        self.assertEqual(self.derive(all_status("skipped")), "not_verified")
        self.assertEqual(self.derive(lambda r: [t.update(status="blocked" if i == 0 else "not_run") for i, t in enumerate(r["tests"])]), "blocked")
        self.assertEqual(self.derive(lambda r: r.update(tests=[])), "not_verified")

    def test_web_runtime_unverified_is_partial(self):
        self.assertEqual(self.derive(lambda r: r["security"].update(web_runtime_verified=False)), "partially_verified")

    def test_remaining_findings_prevent_verified(self):
        f = {"id": "composer-audit-1", "category": "dependency_vulnerable", "severity": "high", "description": "x"}
        self.assertEqual(self.derive(lambda r: r["security"]["remaining_findings"].append(f)), "partially_verified")

    def test_unreachable_advisory_prevents_verified(self):
        self.assertEqual(self.derive(lambda r: r["security"]["advisories_checked"][0].update(result="unreachable")), "partially_verified")

    def test_incomplete_migration_prevents_verified(self):
        self.assertEqual(self.derive(lambda r: r["migration"].update(status="partially_completed")), "partially_verified")

    def test_claim_must_match(self):
        r = verified_report()
        test_by_name(r, "test_suite").update(status="failed", exit_code=2)
        errors, _ = vr.validate(r, SCHEMA)
        self.assertTrue(any("R10" in e and "'failed'" in e for e in errors))
        r["overall_result"] = "failed"
        self.assertEqual(vr.validate(r, SCHEMA)[0], [])


class ExampleReports(unittest.TestCase):
    """JSON reports embedded in examples/*.md must stay valid against the schema and rules."""

    def test_examples_validate(self):
        found = 0
        for name in sorted(os.listdir(os.path.join(SKILL_ROOT, "examples"))):
            text = read_text(os.path.join(SKILL_ROOT, "examples", name))
            for block in re.findall(r"```json\n(.*?)```", text, re.S):
                if '"skill": "php2shell-migration"' in block:
                    found += 1
                    errors, _ = vr.validate(json.loads(block), SCHEMA)
                    self.assertEqual(errors, [], name)
        self.assertGreaterEqual(found, 3)


class MarkdownAndCli(unittest.TestCase):
    def test_markdown_distinguishes_five_questions(self):
        md = vr.to_markdown(verified_report())
        for q in ("Runtime patch verified", "Application migration completed", "Automated tests passed",
                  "Deployment (web) runtime verified", "Remaining security findings"):
            self.assertIn(q, md)
        self.assertIn("does not prove", md)

    def test_markdown_reports_failures(self):
        r = verified_report()
        test_by_name(r, "test_suite").update(status="failed", exit_code=1, summary="3 failures")
        md = vr.to_markdown(r)
        self.assertIn("| Automated tests passed | **no** |", md)
        self.assertIn("3 failures", md)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad, md = (os.path.join(d, n) for n in ("good.json", "bad.json", "out.md"))
            write_text(good, json.dumps(verified_report()))
            r = verified_report()
            r["overall_result"] = "partially_verified"
            write_text(bad, json.dumps(r))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(vr.main([good, "--markdown", md]), 0)
                self.assertEqual(vr.main([bad]), 1)
                with contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(vr.main([os.path.join(d, "missing.json")]), 64)
            self.assertTrue(read_text(md).startswith("# Migration test results: demo"))


if __name__ == "__main__":
    unittest.main()
