"""Shared test helpers: load the hyphen-named scripts as modules."""
import importlib.util
import os

SKILL_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
FIXTURES = os.path.join(SKILL_ROOT, "tests", "fixtures")


def load_script(name):
    path = os.path.join(SKILL_ROOT, "scripts", name)
    spec = importlib.util.spec_from_file_location(name.replace("-", "_").removesuffix(".py"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fixture(name):
    return os.path.join(FIXTURES, name)


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write_text(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
