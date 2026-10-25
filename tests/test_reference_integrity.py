import os
import shutil
import tempfile
import unittest

from helpers import SKILL_ROOT, load_script, read_text, write_text

ref = load_script("validate-references.py")
SECTIONS = "\n\n".join(f"## {s}\n\ncontent" for s in ref.SECTIONS)


class RealSkillTree(unittest.TestCase):
    """The shipped skill must pass every offline documentation check."""

    @classmethod
    def setUpClass(cls):
        cls.errors, cls.warnings, cls.urls = ref.collect(SKILL_ROOT)

    def test_no_offline_errors(self):
        self.assertEqual(self.errors, [])

    def test_every_framework_has_a_reference(self):
        for fid in ref.FRAMEWORK_DOCS:
            self.assertTrue(os.path.isfile(os.path.join(SKILL_ROOT, "references", "frameworks", f"{fid}.md")), fid)
        self.assertEqual(len(ref.FRAMEWORK_DOCS), 23)

    def test_official_php_sources_are_referenced(self):
        for u in ("https://www.php.net/supported-versions.php", "https://github.com/php/php-src/security/advisories",
                  "https://getcomposer.org/doc/03-cli.md#audit", "https://agentskills.io/specification"):
            self.assertIn(u, self.urls)

    def test_skill_md_frontmatter(self):
        fm, err = ref.parse_frontmatter(read_text(os.path.join(SKILL_ROOT, "SKILL.md")))
        self.assertIsNone(err)
        self.assertEqual(fm["name"], "php2shell-migration")
        self.assertLessEqual(len(fm["description"]), 1024)


class Checks(unittest.TestCase):
    def test_url_validation(self):
        self.assertIsNone(ref.check_url("https://www.php.net/releases/"))
        self.assertEqual(ref.check_url("https://php.net/x?utm_source=chatgpt.com"), "tracking parameters (utm_*) must be removed")
        for bad in ("ftp://example.com/x", "https://localhost/x", "https:///nohost", "htps://example.com"):
            self.assertEqual(ref.check_url(bad), "malformed URL", bad)

    def test_framework_doc_sections(self):
        errors = []
        ref.check_framework_doc("x.md", "# X\nLast verified: 2026-10-24\n" + SECTIONS.replace("content", "https://example.org", 7), errors)
        self.assertEqual(errors, [])
        errors = []
        ref.check_framework_doc("x.md", "# X\n## A. Project identification\n## C. Upgrade strategy\n", errors)
        self.assertTrue(any("B. PHP compatibility" in e for e in errors))
        self.assertTrue(any("Last verified" in e for e in errors))
        self.assertTrue(any("G. Sources" in e for e in errors))

    def test_section_order(self):
        errors = []
        text = "Last verified: 2026-10-24\n## B. PHP compatibility\n## A. Project identification\n" + SECTIONS + "\nhttps://x.org"
        ref.check_framework_doc("x.md", text, errors)
        self.assertTrue(any("out of order" in e for e in errors))

    def test_duplicate_generic_docs_detected(self):
        generic = "\n".join(f"This is a generic sentence number {i} about upgrading the framework safely." for i in range(30))
        a = ref.body_lines(generic.replace("the framework", "laravel"), "laravel")
        b = ref.body_lines(generic.replace("the framework", "symfony"), "symfony")
        errors = []
        ref.check_similarity({"laravel.md": a, "symfony.md": b}, errors)
        self.assertEqual(len(errors), 1)
        errors = []
        ref.check_similarity({"a.md": {"one unique line of real content here"}, "b.md": {"another unique line of real content"}}, errors)
        self.assertEqual(errors, [])

    def test_frontmatter_rules(self):
        cases = {"PHP2Shell": "invalid name", "-bad": "invalid name", "a--b": "invalid name"}
        for name, msg in cases.items():
            with tempfile.TemporaryDirectory() as d:
                skill = os.path.join(d, "php2shell-migration")
                os.makedirs(skill)
                write_text(os.path.join(skill, "SKILL.md"), f"---\nname: {name}\ndescription: test\n---\nbody\n")
                errors = []
                ref.check_skill_md(skill, errors)
                self.assertTrue(any(msg in e for e in errors), name)
        with tempfile.TemporaryDirectory() as d:
            skill = os.path.join(d, "other-dir")
            os.makedirs(skill)
            write_text(os.path.join(skill, "SKILL.md"), "---\nname: php2shell-migration\ndescription: \"\"\n---\n")
            errors = []
            ref.check_skill_md(skill, errors)
            self.assertTrue(any("must match directory" in e for e in errors))
            self.assertTrue(any("description" in e for e in errors))

    def test_cross_client_portability_rules(self):
        cases = {"name: claude-helper\ndescription: ok": "anthropic' or 'claude'",
                 "name: php2shell-migration\ndescription: Use <b>this</b>": "XML tags",
                 "name: php2shell-migration\ndescription: Use when: PHP breaks": "unquoted ': '"}
        for fm, msg in cases.items():
            with tempfile.TemporaryDirectory() as d:
                name = fm.split("\n")[0].split(": ")[1]
                skill = os.path.join(d, name)
                os.makedirs(skill)
                write_text(os.path.join(skill, "SKILL.md"), f"---\n{fm}\n---\nbody\n")
                errors = []
                ref.check_skill_md(skill, errors)
                self.assertTrue(any(msg in e for e in errors), (fm, errors))

    def test_shipped_description_is_portable(self):
        fm, _ = ref.parse_frontmatter(read_text(os.path.join(SKILL_ROOT, "SKILL.md")))
        self.assertLessEqual(len(fm["description"]), 500)
        self.assertLessEqual(len(fm["compatibility"]), 500)

    def test_broken_link_unregistered_cve_and_missing_files(self):
        with tempfile.TemporaryDirectory() as d:
            root = os.path.join(d, "php2shell-migration")
            shutil.copytree(SKILL_ROOT, root, ignore=shutil.ignore_patterns("fixtures", "__pycache__"))
            with open(os.path.join(root, "references", "frameworks", "laravel.md"), "a", encoding="utf-8") as fh:
                fh.write("\nSee [missing](does-not-exist.md) and CVE-2099-0001 and https://example.org/?utm_source=x\n")
            os.remove(os.path.join(root, "references", "frameworks", "moodle.md"))
            errors, _, _ = ref.collect(root)
            joined = "\n".join(errors)
            self.assertIn("broken relative link does-not-exist.md", joined)
            self.assertIn("CVE-2099-0001 is not registered", joined)
            self.assertIn("tracking parameters", joined)
            self.assertIn("missing required file references/frameworks/moodle.md", joined)


class Probe(unittest.TestCase):
    def test_probe_reports_unreachable_without_raising(self):
        # Reserved TLD: never resolves, so this needs no network and must not raise.
        r = ref.probe("https://unreachable.invalid/", timeout=2)
        self.assertEqual(r["status"], "unreachable")


if __name__ == "__main__":
    unittest.main()
