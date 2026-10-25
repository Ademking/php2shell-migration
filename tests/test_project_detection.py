import contextlib
import datetime
import io
import json
import os
import shutil
import socket
import tempfile
import unittest
import urllib.request
from unittest import mock

from helpers import FIXTURES, fixture, load_script

detect = load_script("detect-project.py")
TODAY = datetime.date(2026, 10, 24)  # pin lifecycle evaluation to the data verification date

# Fake secrets planted in fixtures; none may ever appear in detector output.
PLANTED_SECRETS = ["FIXTURESECRETAPPKEYDONOTLEAK", "laravel-fixture-db-pass", "ghp_FIXTURETOKENDONOTLEAK",
                   "symfony-fixture-compose-secret", "symfony-url-secret", "wp-fixture-password-123",
                   "wp-fixture-auth-key-xyz", "legacy-fixture-pass"]


def scan(name):
    return detect.scan(fixture(name), today=TODAY)


def project(report, path="."):
    return next(p for p in report["projects"] if p["path"] == path)


def fw_ids(proj):
    return [f["id"] for f in proj["frameworks"]]


def categories(report):
    return [f["category"] for f in report["findings"]]


class FrameworkDetection(unittest.TestCase):
    def test_laravel_from_lock_with_high_confidence(self):
        p = project(scan("laravel"))
        self.assertEqual(fw_ids(p), ["laravel"])
        fw = p["frameworks"][0]
        self.assertEqual((fw["version"], fw["confidence"]), ("12.70.1", "high"))
        self.assertIn("composer.lock", fw["version_source"])
        self.assertTrue(any("artisan" in e for e in fw["evidence"]))

    def test_laravel_embeds_symfony_components_not_reported_as_app(self):
        p = project(scan("laravel"))
        self.assertNotIn("symfony", fw_ids(p))

    def test_symfony_installed_php_wins_over_lock(self):
        fw = project(scan("symfony"))["frameworks"][0]
        self.assertEqual(fw["id"], "symfony")
        self.assertEqual(fw["version"], "7.4.21")
        self.assertIn("installed.php", fw["version_source"])

    def test_wordpress_version_file(self):
        fw = project(scan("wordpress"))["frameworks"][0]
        self.assertEqual((fw["id"], fw["version"], fw["confidence"]), ("wordpress", "6.9.1", "high"))

    def test_legacy_php_is_unrecognized_custom_project(self):
        p = project(scan("legacy-php"))
        self.assertEqual(p["frameworks"], [])
        self.assertIn("other-php-projects.md", p["note"])

    def test_slim_detected_by_package_only(self):
        fw = project(scan("no-test-runner"))["frameworks"][0]
        self.assertEqual((fw["id"], fw["version"]), ("slim", "4.14.0"))
        self.assertEqual(fw["lifecycle"]["status"], "unknown")

    def test_unsupported_framework_version_flagged(self):
        r = scan("unsupported-framework")
        fw = project(r)["frameworks"][0]
        self.assertEqual(fw["version"], "8.83.27")
        self.assertEqual(fw["lifecycle"]["status"], "unsupported")
        self.assertIn("framework_outdated", categories(r))

    def test_supported_framework_not_flagged(self):
        self.assertNotIn("framework_outdated", categories(scan("laravel")))

    def test_marker_only_detection_is_medium_confidence(self):
        fw = project(scan("malformed-composer"))["frameworks"][0]
        self.assertEqual((fw["id"], fw["confidence"], fw["version"]), ("laravel", "medium", None))


class MultipleProjects(unittest.TestCase):
    def test_monorepo_reports_each_application(self):
        r = scan("monorepo")
        self.assertTrue(r["monorepo"])
        paths = {p["path"]: fw_ids(p) for p in r["projects"]}
        self.assertEqual(paths["apps/shop"], ["laravel"])
        self.assertEqual(paths["apps/blog"], ["wordpress"])
        self.assertEqual(paths["packages/shared"], [])
        self.assertEqual(project(r, "apps/shop")["frameworks"][0]["version"], "13.38.0")
        self.assertEqual(project(r, "apps/blog")["frameworks"][0]["version"], "7.0.7")

    def test_unattributable_runtime_stays_repository_level(self):
        r = scan("monorepo")
        self.assertEqual([x["source"] for x in r["runtimes"]], ["docker-compose.yml"])

    def test_single_app_is_not_monorepo(self):
        self.assertFalse(scan("laravel")["monorepo"])


class MalformedInput(unittest.TestCase):
    def test_malformed_composer_does_not_crash_and_warns(self):
        r = scan("malformed-composer")
        self.assertEqual(len([w for w in r["warnings"] if "malformed JSON" in w]), 2)
        p = project(r)
        self.assertTrue(p["composer"]["composer_json_malformed"])
        self.assertTrue(p["composer"]["lock_malformed"])
        self.assertTrue(any(f["category"] == "dependency_inconsistent" and f["severity"] == "high" for f in r["findings"]))

    def test_empty_and_missing_directories(self):
        with tempfile.TemporaryDirectory() as d:
            r = detect.scan(d, today=TODAY)
            self.assertEqual(r["projects"], [])
            self.assertEqual(r["findings"], [])
        r = detect.scan(os.path.join(FIXTURES, "does-not-exist"), today=TODAY)
        self.assertIn("path is not a directory", r["warnings"])

    def test_binary_and_non_object_json(self):
        with tempfile.TemporaryDirectory() as d:
            with open(os.path.join(d, "composer.json"), "w") as fh:
                fh.write("[1, 2, 3]")
            with open(os.path.join(d, "Dockerfile"), "wb") as fh:
                fh.write(b"\x00\xff\xfe\nFROM php:8.2.35-fpm\n")
            r = detect.scan(d, today=TODAY)
            self.assertTrue(any("not a JSON object" in w for w in r["warnings"]))
            self.assertEqual(r["projects"][0]["runtimes"][0]["version"], "8.2.35")

    def test_cli_usage_error_exit_code(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(detect.main([os.path.join(FIXTURES, "nope")]), 64)


class RuntimeDistinction(unittest.TestCase):
    def test_web_ci_and_cli_runtimes_are_kept_separate(self):
        rts = project(scan("laravel"))["runtimes"]
        kinds = {r["source"]: r["kind"] for r in rts}
        self.assertEqual(kinds, {"Dockerfile": "web", ".github/workflows/tests.yml": "ci"})
        for r in rts:
            self.assertIn("verify" if r["kind"] == "web" else "does not prove the web runtime", r["note"])

    def test_cli_toolchain_pin_is_cli_not_web(self):
        r = scan("legacy-php")
        self.assertEqual([x["kind"] for x in project(r)["runtimes"]], ["cli"])
        self.assertTrue(any("No web runtime declaration" in f["message"] for f in r["findings"]))

    def test_declared_vs_deployed_mismatch(self):
        r = scan("vulnerable-runtime-config")
        msgs = [f["message"] for f in r["findings"] if f["category"] == "deployment_mismatch"]
        self.assertTrue(any("requires php >=8.2" in m and "PHP 8.1" in m for m in msgs))
        self.assertTrue(any("web runtime branch differs" in m for m in msgs))

    def test_runtime_security_classification(self):
        r = scan("vulnerable-runtime-config")
        by_src = {x["source"]: x for x in project(r)["runtimes"]}
        self.assertEqual(by_src["Dockerfile"]["security"]["classification"], "runtime_unsupported")
        self.assertEqual(by_src[".github/workflows/ci.yml"]["security"]["classification"], "runtime_affected")
        self.assertIn("runtime_affected", categories(r))
        self.assertTrue(any("mod_php" in f["message"] for f in r["findings"]))

    def test_patched_web_runtime_produces_no_runtime_finding(self):
        r = scan("laravel")
        self.assertEqual(project(r)["runtimes"][0]["security"]["classification"], "runtime_patched")
        self.assertNotIn("runtime_affected", categories(r))

    def test_branch_only_runtime_is_unknown(self):
        r = scan("symfony")
        self.assertEqual(project(r)["runtimes"][0]["security"]["classification"], "status_unknown")

    def test_web_server_config_detection(self):
        rt = project(scan("wordpress"))["runtimes"][0]
        self.assertEqual((rt["kind"], rt["version"], rt["source"]), ("web", "8.1", "deploy/nginx.conf"))


class TestTooling(unittest.TestCase):
    def test_runner_present(self):
        tt = project(scan("laravel"))["test_tooling"]
        self.assertTrue(tt["has_test_runner"])
        self.assertIn("phpunit/phpunit", tt["packages"])

    def test_no_runner(self):
        tt = project(scan("no-test-runner"))["test_tooling"]
        self.assertFalse(tt["has_test_runner"])
        self.assertIn("no test runner", detect.summary(scan("no-test-runner")))


class SafetyProperties(unittest.TestCase):
    def all_outputs(self):
        for name in sorted(os.listdir(FIXTURES)):
            r = detect.scan(fixture(name), today=TODAY)
            yield name, json.dumps(r) + detect.summary(r)

    def test_no_secret_leaks_in_any_output(self):
        for name, out in self.all_outputs():
            for secret in PLANTED_SECRETS:
                self.assertNotIn(secret, out, f"{secret} leaked from fixture {name}")

    def test_redact_patterns(self):
        cases = {
            "define('DB_PASSWORD', 'hunter2');": "hunter2",
            "MYSQL_PASSWORD: s3cret": "s3cret",
            "DATABASE_URL=mysql://user:pa55@db/app": "pa55",
            "api_key = 'abc123def'": "abc123def",
            "token ghp_abcdefghijklmnopqrstuvwxyz0123": "ghp_abcdefghijklmnopqrstuvwxyz0123",
            "AWS AKIAABCDEFGHIJKLMNOP": "AKIAABCDEFGHIJKLMNOP",
        }
        for text, secret in cases.items():
            self.assertNotIn(secret, detect.redact(text), text)
        self.assertEqual(detect.redact("FROM php:8.3.36-fpm"), "FROM php:8.3.36-fpm")

    def test_no_network_access(self):
        def deny(*a, **k):
            raise AssertionError("detector attempted network access")
        with mock.patch.object(socket, "socket", deny), mock.patch.object(socket, "create_connection", deny), \
                mock.patch.object(urllib.request, "urlopen", deny):
            for name, _ in self.all_outputs():
                pass
        self.assertFalse(detect.scan(fixture("laravel"), today=TODAY)["network_used"])

    def test_detector_source_has_no_network_or_exec_imports(self):
        with open(detect.__file__, encoding="utf-8") as fh:
            src = fh.read()
        for forbidden in ("import socket", "import urllib", "import http", "import subprocess", "os.system", "eval(", "exec("):
            self.assertNotIn(forbidden, src)

    def test_does_not_modify_scanned_tree(self):
        with tempfile.TemporaryDirectory() as d:
            dst = os.path.join(d, "app")
            shutil.copytree(fixture("laravel"), dst)
            before = {os.path.join(r, f): os.path.getmtime(os.path.join(r, f)) for r, _, fs in os.walk(dst) for f in fs}
            detect.scan(dst, today=TODAY)
            after = {os.path.join(r, f): os.path.getmtime(os.path.join(r, f)) for r, _, fs in os.walk(dst) for f in fs}
            self.assertEqual(before, after)

    def test_json_cli_output(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(detect.main([fixture("wordpress"), "--json"]), 0)
        self.assertEqual(json.loads(buf.getvalue())["projects"][0]["frameworks"][0]["id"], "wordpress")


if __name__ == "__main__":
    unittest.main()
