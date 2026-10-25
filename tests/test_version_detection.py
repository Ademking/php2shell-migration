import contextlib
import datetime
import io
import unittest

from helpers import load_script

chk = load_script("check-php-version.py")
detect = load_script("detect-project.py")
DATA = chk.load_data()
D = datetime.date(2026, 10, 24)


def classify(v, today=D, **kw):
    return chk.classify(v, data=DATA, today=today, **kw)


class ParseVersion(unittest.TestCase):
    def test_plain_and_php_v_output(self):
        self.assertEqual(chk.parse_version("8.3.30")["version"], "8.3.30")
        v = chk.parse_version("PHP 8.4.27 (cli) (built: Oct 21 2026 10:00:00) (NTS)")
        self.assertEqual((v["branch"], v["patch"]), ("8.4", 27))

    def test_branch_only_and_garbage(self):
        self.assertIsNone(chk.parse_version("8.2")["patch"])
        self.assertIsNone(chk.parse_version("no version here"))
        self.assertIsNone(chk.parse_version(""))

    def test_docker_variant_is_not_vendor_suffix(self):
        self.assertEqual(chk.parse_version("8.3.36-fpm-alpine")["suffix"], "")

    def test_sapi_extracted_from_php_v(self):
        self.assertEqual(classify("PHP 8.3.36 (cli) (built: x)")["sapi"], "cli")


class AdvisoryClassification(unittest.TestCase):
    def test_fixed_versions_are_patched(self):
        for v in ("8.2.35", "8.3.36", "8.4.27", "8.5.12", "8.5.13"):
            self.assertEqual(classify(v)["classification"], "runtime_patched", v)

    def test_one_below_fixed_is_affected(self):
        for v in ("8.2.34", "8.3.35", "8.4.26", "8.5.11", "8.3.30"):
            r = classify(v)
            self.assertEqual(r["classification"], "runtime_affected", v)
            self.assertEqual({a["status"] for a in r["advisories"]}, {"affected"})

    def test_both_cves_reported(self):
        self.assertEqual([a["id"] for a in classify("8.4.1")["advisories"]], ["CVE-2026-109618", "CVE-2026-109619"])

    def test_eol_branches_are_unsupported_and_affected(self):
        for v in ("8.1.34", "8.0.30", "7.4.33", "5.6.40"):
            r = classify(v)
            self.assertEqual(r["classification"], "runtime_unsupported", v)
            self.assertEqual(r["branch_status"], "eol")
            self.assertTrue(all(a["status"] == "affected_unless_vendor_backport" for a in r["advisories"]))

    def test_branch_becomes_eol_after_security_support_date(self):
        self.assertEqual(classify("8.2.35", today=datetime.date(2026, 12, 31))["classification"], "runtime_patched")
        self.assertEqual(classify("8.2.35", today=datetime.date(2027, 1, 1))["classification"], "runtime_unsupported")

    def test_vendor_build_below_fixed_is_unknown_not_affected(self):
        for v in ("8.1.2-1ubuntu2.20", "8.2.20-1+deb12u1", "8.3.30-1.el9.remi"):
            r = classify(v)
            self.assertTrue(r["vendor_build"], v)
            self.assertTrue(any("vendor security notice" in n for n in r["notes"]) or r["branch_status"] == "eol", v)
        self.assertEqual(classify("8.2.20-1+deb12u1")["classification"], "status_unknown")
        self.assertEqual(classify("8.3.36-1+deb12u1")["classification"], "runtime_patched")

    def test_branch_only_is_unknown(self):
        r = classify("8.4")
        self.assertEqual(r["classification"], "status_unknown")
        self.assertTrue(any("No patch level" in n for n in r["notes"]))

    def test_future_branch_and_prerelease_are_unknown(self):
        r = classify("8.6.0RC4")
        self.assertEqual(r["classification"], "status_unknown")
        self.assertTrue(r["prerelease"])
        self.assertEqual(classify("8.5.12RC1")["classification"], "status_unknown")

    def test_unparseable_is_unknown(self):
        self.assertEqual(classify("unknown")["classification"], "status_unknown")

    def test_cli_note_never_claims_web(self):
        r = classify("8.3.36", sapi="cli")
        self.assertTrue(any("does not verify the PHP version serving web requests" in n for n in r["notes"]))

    def test_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(chk.main(["8.3.36", "--today", "2026-10-24"]), 0)
            self.assertEqual(chk.main(["8.3.30", "--today", "2026-10-24"]), 2)
            self.assertEqual(chk.main(["7.4.33", "--today", "2026-10-24"]), 2)
            self.assertEqual(chk.main(["8.4", "--today", "2026-10-24"]), 3)

    def test_advisory_data_is_dated_and_sourced(self):
        self.assertRegex(DATA["verified_on"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(any("php.net" in s for s in DATA["sources"]))
        self.assertTrue(all(a["ghsa"].startswith("GHSA-") for a in DATA["advisories"]))


class ComposerConstraints(unittest.TestCase):
    CASES = [("^8.1", "8.1", True), ("^8.1", "8.0", False), ("^8.1", "9.0", False), (">=7.4 <8.3", "8.3", False),
             (">=7.4 <8.3", "8.2.1", True), ("~8.2.0", "8.3", False), ("~8.2.0", "8.2.5", True), ("~8.2", "8.4", True),
             ("8.1.*", "8.1", True), ("8.1.*", "8.2", False), ("^7.4|^8.0", "8.3", True), ("^7.4 || ^8.0", "7.3", False),
             (">=8.2", "8.4", True), ("7.4 - 8.1", "8.1.3", True), ("7.4 - 8.1", "8.2", False), (">=8.2,<8.5", "8.5", False)]

    def test_constraints(self):
        for c, v, want in self.CASES:
            self.assertEqual(detect.constraint_allows(c, v), want, f"{c} vs {v}")

    def test_unparseable_constraint_is_none(self):
        self.assertIsNone(detect.constraint_allows("dev-main", "8.2"))
        self.assertIsNone(detect.constraint_allows("^8.1", "latest"))


class FrameworkLifecycle(unittest.TestCase):
    LC = {"verified_on": "2026-10-24", "products": {"demo": {"source": "x", "releases": [
        {"cycle": "3", "eol": "2027-01-01", "is_eol": False, "latest": "3.9"},
        {"cycle": "2.5", "eol": "2026-01-01", "is_eol": True, "latest": "2.5.9"},
        {"cycle": "2", "eol": True, "is_eol": True, "latest": "2.4"}]}}}

    def test_most_specific_cycle_wins(self):
        self.assertEqual(detect.lifecycle_for("demo", "2.5.1", self.LC, D)["cycle"], "2.5")
        self.assertEqual(detect.lifecycle_for("demo", "2.4.1", self.LC, D)["cycle"], "2")

    def test_status(self):
        self.assertEqual(detect.lifecycle_for("demo", "3.1", self.LC, D)["status"], "supported")
        self.assertEqual(detect.lifecycle_for("demo", "3.1", self.LC, datetime.date(2027, 2, 1))["status"], "unsupported")
        self.assertEqual(detect.lifecycle_for("demo", "1.0", self.LC, D)["status"], "unsupported")

    def test_unknown_product_or_version(self):
        self.assertEqual(detect.lifecycle_for("nope", "1.0", self.LC, D)["status"], "unknown")
        self.assertEqual(detect.lifecycle_for("demo", None, self.LC, D)["status"], "unknown")


if __name__ == "__main__":
    unittest.main()
