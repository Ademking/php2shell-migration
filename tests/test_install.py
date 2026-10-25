import contextlib
import io
import os
import tempfile
import unittest
import zipfile
from pathlib import Path

from helpers import SKILL_ROOT, load_script, write_text

inst = load_script("install.py")


def run(*args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = inst.main(list(args))
    return code, out.getvalue()


class Coverage(unittest.TestCase):
    def test_default_dirs_cover_every_tool_in_both_scopes(self):
        for scope in ("user", "project"):
            dirs = inst.skill_dirs(sorted(inst.TOOLS), scope)
            self.assertEqual(dirs, [".agents/skills", ".claude/skills"], scope)
            for tool, paths in inst.TOOLS.items():
                self.assertTrue(set(dirs) & set(paths[scope]), f"{tool} not covered in {scope} scope")

    def test_single_tool_uses_its_own_path(self):
        self.assertEqual(inst.skill_dirs(["codex"], "user"), [".agents/skills"])
        self.assertEqual(inst.skill_dirs(["claude-code"], "project"), [".claude/skills"])
        self.assertEqual(inst.skill_dirs(["codex", "claude-code"], "user"), [".agents/skills", ".claude/skills"])

    def test_documented_tools(self):
        self.assertEqual(sorted(inst.TOOLS), ["claude-code", "codex", "copilot", "cursor", "gemini", "opencode"])
        readme = (Path(SKILL_ROOT) / "README.md").read_text(encoding="utf-8")
        for tool, paths in inst.TOOLS.items():
            for p in paths["project"]:
                self.assertIn(p, readme, f"{tool} path {p} missing from README compatibility table")


class InstallLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.proj = Path(self.tmp.name) / "proj"
        self.home.mkdir()
        self.proj.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def installed(self, base, d):
        return base / d / inst.NAME

    def test_dry_run_changes_nothing(self):
        code, out = run("--home", str(self.home), "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn("create", out)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_user_install_is_discoverable_and_complete(self):
        code, _ = run("--home", str(self.home), "--mode", "copy")
        self.assertEqual(code, 0)
        for d in (".agents/skills", ".claude/skills"):
            dest = self.installed(self.home, d)
            self.assertEqual(inst.declared_name(dest), "php2shell-migration")
            for f in ("scripts/detect-project.py", "references/frameworks/laravel.md", "templates/test-results.schema.json"):
                self.assertTrue((dest / f).is_file(), f)
            self.assertFalse(any(p.name == "__pycache__" for p in dest.rglob("*")))

    def test_project_install_and_reinstall_updates(self):
        self.assertEqual(run("--scope", "project", "--project", str(self.proj), "--tool", "codex", "--mode", "copy")[0], 0)
        dest = self.installed(self.proj, ".agents/skills")
        write_text(dest / "stale.txt", "old")
        code, out = run("--scope", "project", "--project", str(self.proj), "--tool", "codex", "--mode", "copy")
        self.assertEqual(code, 0)
        self.assertIn("update", out)
        self.assertFalse((dest / "stale.txt").exists())

    def test_refuses_foreign_directory(self):
        foreign = self.installed(self.proj, ".claude/skills")
        foreign.mkdir(parents=True)
        write_text(foreign / "SKILL.md", "---\nname: something-else\ndescription: x\n---\n")
        code, out = run("--scope", "project", "--project", str(self.proj), "--tool", "claude-code")
        self.assertEqual(code, 1)
        self.assertIn("REFUSE", out)
        self.assertTrue((foreign / "SKILL.md").read_text().startswith("---\nname: something-else"))
        code, out = run("--scope", "project", "--project", str(self.proj), "--tool", "claude-code", "--uninstall")
        self.assertIn("REFUSE", out)
        self.assertTrue(foreign.exists())

    def test_auto_mode_links_or_copies(self):
        self.assertEqual(run("--home", str(self.home))[0], 0)
        second = self.installed(self.home, ".claude/skills")
        self.assertEqual(inst.declared_name(second), "php2shell-migration")  # symlink or fallback copy, either works
        if second.is_symlink():
            self.assertEqual(second.resolve(), self.installed(self.home, ".agents/skills").resolve())

    def test_symlink_mode_links_to_checkout(self):
        probe = Path(self.tmp.name) / "probe"
        try:
            os.symlink(self.home, probe, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlinks unavailable here: {exc}")
        self.assertEqual(run("--home", str(self.home), "--mode", "symlink", "--tool", "codex")[0], 0)
        self.assertEqual(self.installed(self.home, ".agents/skills").resolve(), Path(SKILL_ROOT).resolve())

    def test_uninstall_removes_only_ours(self):
        run("--home", str(self.home))
        other = self.home / ".agents/skills/other-skill"
        other.mkdir(parents=True)
        code, _ = run("--home", str(self.home), "--uninstall")
        self.assertEqual(code, 0)
        self.assertFalse(self.installed(self.home, ".agents/skills").exists())
        self.assertFalse(os.path.lexists(self.installed(self.home, ".claude/skills")))
        self.assertTrue(other.exists())

    def test_custom_dir_for_other_tools(self):
        custom = Path(self.tmp.name) / "windsurf-skills"
        self.assertEqual(run("--home", str(self.home), "--tool", "codex", "--dir", str(custom))[0], 0)
        self.assertEqual(inst.declared_name(custom / inst.NAME), "php2shell-migration")

    def test_zip_layout_for_claude_upload(self):
        out = Path(self.tmp.name) / "dist" / "skill.zip"
        self.assertEqual(run("--zip", str(out))[0], 0)
        names = zipfile.ZipFile(out).namelist()
        self.assertIn("php2shell-migration/SKILL.md", names)
        self.assertTrue(all(n.startswith("php2shell-migration/") for n in names))
        self.assertFalse(any("/tests/" in n or n.endswith(".pyc") for n in names))
        self.assertIn("php2shell-migration/agents/openai.yaml", names)

    def test_bad_project_dir(self):
        self.assertEqual(run("--scope", "project", "--project", str(self.proj / "missing"))[0], 64)


if __name__ == "__main__":
    unittest.main()
