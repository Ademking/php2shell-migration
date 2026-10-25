#!/usr/bin/env python3
"""Install php2shell-migration where each AI coding agent discovers skills.

Discovery paths come from each vendor's documentation (verified 2026-10-24, see README
"Compatibility"). Because most tools also read the shared `.agents/skills` convention, the
default `--tool all` installs into the smallest set of directories that covers every
supported tool: `.agents/skills` plus `.claude/skills`.

Usage:
  install.py                                  # user scope, all supported tools
  install.py --scope project --project DIR    # inside a repository (commit it to share)
  install.py --tool codex --tool claude-code  # only some tools
  install.py --dir /path/to/skills            # any other tool's skills directory
  install.py --zip dist/php2shell-migration.zip   # package for claude.ai / Claude API upload
  install.py --uninstall [same selectors]     # remove what install.py installed
  install.py --list                           # show tools and paths
Options: --mode auto|copy|symlink (default auto), --dry-run.

Safety: existing directories are replaced only if their SKILL.md declares this skill's name;
anything else is left alone and reported. Standard library only; no network.
Exit codes: 0 ok, 1 refused/failed, 64 usage error.
"""
import argparse
import os
import shutil
import sys
import zipfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
NAME = "php2shell-migration"
# Per-tool skill directories, preferred first. Project paths are relative to the repository root,
# user paths to the home directory. Sources: README "Compatibility" table.
TOOLS = {
    "claude-code": {"project": [".claude/skills"], "user": [".claude/skills"]},
    "codex": {"project": [".agents/skills"], "user": [".agents/skills"]},
    "copilot": {"project": [".github/skills", ".claude/skills", ".agents/skills"], "user": [".copilot/skills", ".agents/skills"]},
    "cursor": {"project": [".cursor/skills", ".agents/skills", ".claude/skills", ".codex/skills"],
               "user": [".cursor/skills", ".agents/skills", ".claude/skills", ".codex/skills"]},
    "gemini": {"project": [".gemini/skills", ".agents/skills"], "user": [".gemini/skills", ".agents/skills"]},
    "opencode": {"project": [".opencode/skills", ".claude/skills", ".agents/skills"],
                 "user": [".config/opencode/skills", ".claude/skills", ".agents/skills"]},
}
PREFERENCE = [".agents/skills", ".claude/skills"]  # shared paths win ties in the cover
EXCLUDE = {".git", "__pycache__", "dist", ".pytest_cache"}
ZIP_EXCLUDE = EXCLUDE | {"tests"}


def skill_dirs(tools, scope):
    """Smallest set of skills directories such that every selected tool reads at least one (greedy cover)."""
    uncovered, chosen = set(tools), []
    while uncovered:
        cands = {d for t in uncovered for d in TOOLS[t][scope]}
        best = max(sorted(cands), key=lambda d: (sum(d in TOOLS[t][scope] for t in uncovered),
                                                  -PREFERENCE.index(d) if d in PREFERENCE else -99))
        chosen.append(best)
        uncovered = {t for t in uncovered if best not in TOOLS[t][scope]}
    return chosen


def declared_name(path):
    """`name` from a SKILL.md frontmatter, or None."""
    try:
        text = (Path(path) / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return None
    if not text.startswith("---"):
        return None
    for line in text[3:text.find("\n---", 3)].splitlines():
        key, _, value = line.partition(":")
        if key.strip() == "name":
            return value.strip().strip("'\"")
    return None


def is_ours(path):
    return declared_name(path) == NAME


def _ignore(exclude):
    return lambda d, names: [n for n in names if n in exclude or n.endswith(".pyc")]


def remove(path):
    if path.is_symlink() or (os.name == "nt" and _is_junction(path)):
        path.unlink() if path.is_symlink() else os.rmdir(path)
    else:
        shutil.rmtree(path)


def _is_junction(path):
    try:
        return path.is_junction()  # Python 3.12+
    except AttributeError:
        return False


def place(dest, mode, link_to, log, dry):
    """Install one copy/link at dest (…/skills/php2shell-migration)."""
    if dest.exists() or dest.is_symlink():
        if dest.resolve() == SKILL_ROOT:
            log(f"skip   {dest} (this is the source checkout)")
            return True
        if not is_ours(dest):
            log(f"REFUSE {dest} exists and is not a {NAME} install; move it away first")
            return False
        log(f"update {dest}")
        if not dry:
            remove(dest)
    else:
        log(f"create {dest}")
    if dry:
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    if mode in ("symlink", "auto") and link_to is not None:
        try:
            os.symlink(link_to, dest, target_is_directory=True)
            log(f"       -> symlink to {link_to}")
            return True
        except (OSError, NotImplementedError) as exc:
            if mode == "symlink":
                log(f"FAILED symlink {dest}: {exc} (on Windows enable Developer Mode, or use --mode copy)")
                return False
    shutil.copytree(SKILL_ROOT, dest, ignore=_ignore(EXCLUDE))
    log("       copied")
    return True


def install(dirs, base, mode, dry, log):
    ok, first = True, None
    for d in dirs:
        dest = base / d / NAME
        link_to = SKILL_ROOT if mode == "symlink" else first
        placed = place(dest, mode, link_to, log, dry)
        ok &= placed
        if placed and first is None:
            first = dest  # later locations link to this copy, never to a refused foreign directory
    return ok


def uninstall(dirs, base, dry, log):
    for d in reversed(dirs):  # links to the first copy go before the copy, so none is left dangling
        dest = base / d / NAME
        if not (dest.exists() or dest.is_symlink()):
            log(f"absent {dest}")
        elif dest.resolve() == SKILL_ROOT and not dest.is_symlink():
            log(f"skip   {dest} (this is the source checkout)")
        elif is_ours(dest) or (dest.is_symlink() and not dest.exists()):
            log(f"remove {dest}")
            if not dry:
                remove(dest)
        else:
            log(f"REFUSE {dest} is not a {NAME} install")
    return True


def build_zip(out, log):
    """claude.ai / Claude API layout: the skill folder at the archive root, named after the skill."""
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirnames, files in os.walk(SKILL_ROOT):
            dirnames[:] = sorted(d for d in dirnames if d not in ZIP_EXCLUDE)
            for f in sorted(files):
                p = Path(root) / f
                if p.suffix == ".pyc" or p.resolve() == out:
                    continue
                zf.write(p, Path(NAME) / p.relative_to(SKILL_ROOT))
    log(f"wrote {out} (upload it in claude.ai or via the Claude Skills API)")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tool", action="append", choices=sorted(TOOLS) + ["all"], help="repeatable; default all")
    ap.add_argument("--scope", choices=["user", "project"], default="user")
    ap.add_argument("--project", default=".", help="repository root for --scope project")
    ap.add_argument("--home", help=argparse.SUPPRESS)  # tests
    ap.add_argument("--dir", action="append", help="extra skills directory for any other tool (repeatable)")
    ap.add_argument("--mode", choices=["auto", "copy", "symlink"], default="auto",
                    help="auto: copy once, symlink the other locations (falls back to copy); symlink: link all to this checkout")
    ap.add_argument("--zip", help="write a claude.ai/API upload archive and exit")
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    log = print
    if a.list:
        for t, scopes in sorted(TOOLS.items()):
            log(f"{t:12} project: {', '.join(scopes['project'])}\n{'':12} user:    {', '.join('~/' + p for p in scopes['user'])}")
        return 0
    if a.zip:
        build_zip(a.zip, log)
        return 0
    tools = sorted(TOOLS) if not a.tool or "all" in a.tool else sorted(set(a.tool))
    base = Path(a.project).resolve() if a.scope == "project" else Path(a.home or Path.home()).resolve()
    if a.scope == "project" and not base.is_dir():
        print(f"error: project directory not found: {base}", file=sys.stderr)
        return 64
    dirs = skill_dirs(tools, a.scope)
    extra = [Path(d).expanduser().resolve() for d in a.dir or []]
    log(f"{'uninstall' if a.uninstall else 'install'} {NAME} ({a.scope} scope, tools: {', '.join(tools)}){' [dry run]' if a.dry_run else ''}")
    ok = True
    if a.uninstall:
        uninstall(dirs, base, a.dry_run, log)
        for e in extra:
            uninstall(["."], e, a.dry_run, log)
    else:
        ok = install(dirs, base, a.mode, a.dry_run, log)
        for e in extra:
            ok &= install(["."], e, "copy" if a.mode == "auto" else a.mode, a.dry_run, log)
        if ok and not a.dry_run:
            log("done. Restart the agent if it does not pick up new skills automatically.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
