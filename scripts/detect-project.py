#!/usr/bin/env python3
"""Identify PHP applications, frameworks, versions and declared runtimes in a directory tree.

Safe by construction:
  * never executes PHP or application code, never imports network modules;
  * reads only the small set of files it needs and extracts version strings with regexes;
  * never prints file contents, only paths, package names and parsed versions (all redacted).

Detection results are *signals with confidence*, not proof. The CLI runtime, CI runtime and
deployed web runtime are reported separately; a web runtime found in source is still only a
declaration until it is verified on the target host.

Usage:
  detect-project.py PATH [--json] [--output FILE] [--max-depth N]
Exit codes: 0 scan completed (even with warnings), 64 usage error.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIFECYCLE = os.path.join(HERE, "..", "references", "frameworks", "framework-lifecycle.json")
SKIP_DIRS = {"vendor", "node_modules", ".git", ".svn", ".hg", "bower_components", "cache", ".idea", ".vscode", "uploads"}
MAX_READ = 2 * 1024 * 1024  # never read huge files

# ---------------------------------------------------------------- signatures
# strong: any one marker detects the framework (medium confidence)
# weak: supporting evidence only
# packages: composer packages whose installed/locked version is the framework version (high confidence)
# version_files: (relative path, regex) -> version (high confidence)
FRAMEWORKS = [
    dict(id="laravel", name="Laravel", packages=["laravel/framework"], strong=["artisan"], weak=["bootstrap/app.php", "routes/web.php"],
         version_files=[("vendor/laravel/framework/src/Illuminate/Foundation/Application.php", r"const VERSION = '([^']+)'")]),
    dict(id="symfony", name="Symfony", packages=["symfony/framework-bundle"], strong=["symfony.lock", "config/bundles.php"], weak=["bin/console"], version_files=[]),
    dict(id="wordpress", name="WordPress", packages=["johnpbloch/wordpress-core", "roots/wordpress", "roots/wordpress-no-content"],
         strong=["wp-includes/version.php", "wp-load.php"], weak=["wp-config.php", "wp-content"],
         version_files=[("wp-includes/version.php", r"\$wp_version\s*=\s*'([^']+)'"), ("wp/wp-includes/version.php", r"\$wp_version\s*=\s*'([^']+)'")]),
    dict(id="drupal", name="Drupal", packages=["drupal/core", "drupal/core-recommended", "drupal/drupal"], strong=["core/lib/Drupal.php", "web/core/lib/Drupal.php", "includes/bootstrap.inc"], weak=["sites/default"],
         version_files=[("core/lib/Drupal.php", r"const VERSION = '([^']+)'"), ("web/core/lib/Drupal.php", r"const VERSION = '([^']+)'"), ("includes/bootstrap.inc", r"define\('VERSION', '([^']+)'\)")]),
    dict(id="codeigniter", name="CodeIgniter", packages=["codeigniter4/framework", "codeigniter4/codeigniter4", "codeigniter/framework"],
         strong=["spark", "system/CodeIgniter.php", "system/core/CodeIgniter.php"], weak=["app/Config/App.php", "application/config/config.php"],
         version_files=[("system/CodeIgniter.php", r"CI_VERSION = '([^']+)'"), ("system/core/CodeIgniter.php", r"define\('CI_VERSION', '([^']+)'\)"),
                        ("vendor/codeigniter4/framework/system/CodeIgniter.php", r"CI_VERSION = '([^']+)'")]),
    dict(id="yii", name="Yii", packages=["yiisoft/yii2", "yiisoft/yii", "yiisoft/yii-web"], strong=["yii", "protected/yiic.php"], weak=["protected/config/main.php", "config/web.php"], version_files=[]),
    dict(id="cakephp", name="CakePHP", packages=["cakephp/cakephp"], strong=["bin/cake", "bin/cake.php", "lib/Cake/VERSION.txt"], weak=["cake", "config/app.php", "src/Application.php"],
         version_files=[("vendor/cakephp/cakephp/VERSION.txt", r"^(\d+\.\d+\.\d+[^\s]*)\s*$"), ("lib/Cake/VERSION.txt", r"^(\d+\.\d+\.\d+[^\s]*)\s*$")]),
    dict(id="joomla", name="Joomla", packages=["joomla/joomla-cms"], strong=["libraries/src/Version.php", "administrator/manifests/files/joomla.xml"], weak=["configuration.php", "administrator"],
         version_files=[("administrator/manifests/files/joomla.xml", r"<version>([^<]+)</version>")]),
    dict(id="october-cms", name="October CMS", packages=["october/system", "october/rain", "october/october"], strong=["modules/system/ServiceProvider.php"], weak=["plugins", "themes"], version_files=[]),
    dict(id="suitecrm", name="SuiteCRM", packages=["salesagility/suitecrm"], strong=["suitecrm_version.php", "public/legacy/suitecrm_version.php"], weak=["sugar_version.php"],
         version_files=[("suitecrm_version.php", r"\$suitecrm_version\s*=\s*'([^']+)'"), ("public/legacy/suitecrm_version.php", r"\$suitecrm_version\s*=\s*'([^']+)'")]),
    dict(id="espocrm", name="EspoCRM", packages=["espocrm/espocrm"], strong=["application/Espo/Core/Application.php"], weak=["client/src", "data/config.php"],
         version_files=[("data/config.php", r"'version'\s*=>\s*'([^']+)'")]),
    dict(id="nextcloud", name="Nextcloud", packages=[], strong=["occ", "lib/private/Server.php"], weak=["apps", "core/Command"],
         version_files=[("version.php", r"\$OC_VersionString\s*=\s*'([^']+)'")]),
    dict(id="magento", name="Magento / Adobe Commerce", packages=["magento/product-community-edition", "magento/product-enterprise-edition", "magento/magento2-base", "magento/framework"],
         strong=["bin/magento", "app/etc/di.xml"], weak=["pub/index.php", "app/etc/env.php"], version_files=[]),
    dict(id="prestashop", name="PrestaShop", packages=["prestashop/prestashop"], strong=["classes/PrestaShopAutoload.php", "config/defines.inc.php"], weak=["app/AppKernel.php", "modules"],
         version_files=[("app/AppKernel.php", r"const VERSION = '([^']+)'"), ("install/install_version.php", r"_PS_INSTALL_VERSION_', '([^']+)'")]),
    dict(id="opencart", name="OpenCart", packages=["opencart/opencart"], strong=["system/startup.php", "catalog/controller"], weak=["system/library", "admin/config.php"],
         version_files=[("index.php", r"define\('VERSION', '([^']+)'\)"), ("upload/index.php", r"define\('VERSION', '([^']+)'\)")]),
    dict(id="slim", name="Slim Framework", packages=["slim/slim"], strong=[], weak=[], version_files=[]),
    dict(id="dolibarr", name="Dolibarr", packages=["dolibarr/dolibarr"], strong=["htdocs/main.inc.php", "htdocs/filefunc.inc.php"], weak=["htdocs/conf"],
         version_files=[("htdocs/filefunc.inc.php", r"define\('DOL_VERSION', '([^']+)'\)")]),
    dict(id="typo3", name="TYPO3", packages=["typo3/cms-core"], strong=["typo3/sysext/core", "typo3conf"], weak=["config/system/settings.php"],
         version_files=[("typo3/sysext/core/Classes/Information/Typo3Version.php", r"const VERSION = '([^']+)'"),
                        ("vendor/typo3/cms-core/Classes/Information/Typo3Version.php", r"const VERSION = '([^']+)'")]),
    dict(id="moodle", name="Moodle", packages=["moodle/moodle"], strong=["lib/moodlelib.php", "config-dist.php"], weak=["admin/cli", "version.php"],
         version_files=[("version.php", r"\$release\s*=\s*'([\d.]+)"), ("public/version.php", r"\$release\s*=\s*'([\d.]+)")]),
    dict(id="mediawiki", name="MediaWiki", packages=["mediawiki/core"], strong=["includes/Defines.php", "maintenance/run.php"], weak=["LocalSettings.php", "extensions", "skins"],
         version_files=[("includes/Defines.php", r"define\(\s*'MW_VERSION',\s*'([^']+)'")]),
    dict(id="laminas", name="Laminas / Zend Framework", packages=["laminas/laminas-mvc", "laminas/laminas-mvc-skeleton", "mezzio/mezzio", "zendframework/zendframework", "zendframework/zend-mvc"],
         strong=["config/application.config.php"], weak=["module"], version_files=[]),
    dict(id="phalcon", name="Phalcon", packages=["phalcon/devtools", "phalcon/ide-stubs", "phalcon/incubator"], strong=[".phalcon"], weak=[], version_files=[], ext="ext-phalcon"),
    dict(id="phpmyadmin", name="phpMyAdmin", packages=["phpmyadmin/phpmyadmin"], strong=["libraries/classes/Version.php", "src/Version.php", "libraries/Config.php"], weak=["config.sample.inc.php", "themes"],
         version_files=[("libraries/classes/Version.php", r"VERSION = '([^']+)'"), ("src/Version.php", r"VERSION = '([^']+)'")]),
]
FW_BY_ID = {f["id"]: f for f in FRAMEWORKS}

# ------------------------------------------------------------------- redaction
SECRET_RES = [
    (re.compile(r"(?i)((?:password|passwd|pwd|secret|token|api[_-]?key|private[_-]?key|auth|salt|credential|access[_-]?key)[\w-]*['\"]?\s*(?:=>|=|:|,)\s*)(['\"]?)([^'\"\s,;)]+)"), r"\1\2[REDACTED]"),
    (re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://[^:/\s@]+:)([^@\s]+)(@)"), r"\1[REDACTED]\3"),
    (re.compile(r"\b(AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|xox[abpr]-[A-Za-z0-9-]{10,})\b"), "[REDACTED]"),
]


def redact(text):
    text = str(text)
    for rx, repl in SECRET_RES:
        text = rx.sub(repl, text)
    return text


# ---------------------------------------------------------------------- helpers
def read_text(path):
    try:
        if os.path.getsize(path) > MAX_READ:
            return None
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def read_json(path, warnings, rel):
    text = read_text(path)
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError as exc:
        warnings.append(f"{rel}: malformed JSON ({exc.msg} at line {exc.lineno}); ignored")
        return None


def norm_version(v):
    return v[1:] if isinstance(v, str) and v[:1] in "vV" and v[1:2].isdigit() else v


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:3])


# ------------------------------------------------- composer constraint matching
def _satisfies_one(ver, part):
    m = re.match(r"^(\^|~|>=|<=|>|<|==|=|!=)?\s*v?(\d+(?:\.(?:\d+|\*|x))*)(?:[-@].*)?$", part)
    if not m:
        return None
    op, raw = m.group(1) or "=", m.group(2)
    nums = [x for x in raw.split(".") if x not in ("*", "x")]
    want = tuple(int(x) for x in nums)
    wildcard = len(nums) < len(raw.split("."))
    v = ver[:3] + (0,) * (3 - len(ver))
    w = want + (0,) * (3 - len(want))
    if op == "^":
        upper = (want[0] + 1, 0, 0) if want[0] > 0 else (0, (want[1] if len(want) > 1 else 0) + 1, 0)
        return w <= v < upper
    if op == "~":
        prefix = want[:-1] if len(want) > 1 else want
        return v >= w and v[:len(prefix)] == prefix
    if op in ("=", "==") and (wildcard or len(want) < 3):
        return v[:len(want)] == want
    return {"=": v == w, "==": v == w, "!=": v != w, ">=": v >= w, "<=": v <= w, ">": v > w, "<": v < w}[op]


def constraint_allows(constraint, version):
    """True/False if `version` (e.g. '8.1' or '8.1.27') satisfies a Composer constraint, None if unparseable.
    A branch-only version is allowed if any patch in that branch could satisfy it."""
    vt = vtuple(version)
    if not vt:
        return None
    candidates = [vt] if len(vt) >= 3 else [vt[:2] + (0,), vt[:2] + (999,)]
    any_parsed = False
    for alt in re.split(r"\s*\|\|?\s*", constraint.strip()):
        parts = [p for p in re.split(r"\s*,\s*|\s+", alt.replace(">= ", ">=").replace("<= ", "<=").replace("> ", ">").replace("< ", "<")) if p]
        if " - " in alt:
            lo, hi = alt.split(" - ", 1)
            hi_nums = [int(x) for x in re.findall(r"\d+", hi)]
            # composer: a partial upper bound is exclusive of the next component ("8.1" -> "<8.2")
            upper = "<=" + hi.strip() if len(hi_nums) >= 3 else "<" + ".".join(map(str, hi_nums[:-1] + [hi_nums[-1] + 1]))
            parts = [">=" + lo.strip(), upper]
        for cand in candidates:
            results = [_satisfies_one(cand, p) for p in parts]
            if None in results or not results:
                continue
            any_parsed = True
            if all(results):
                return True
    return False if any_parsed else None


# ------------------------------------------------------------------ composer
def composer_info(root, rel_root, warnings):
    info = {"composer_json": False, "name": None, "php_constraint": None, "platform_php": None, "extensions": [],
            "require": {}, "composer_json_malformed": False, "lock_malformed": False, "lock_present": False, "installed_present": False, "lock_missing_packages": [], "packages": {}}
    cj_path = os.path.join(root, "composer.json")
    if os.path.isfile(cj_path):
        info["composer_json"] = True
        cj = read_json(cj_path, warnings, os.path.join(rel_root, "composer.json"))
        info["composer_json_malformed"] = not isinstance(cj, dict)
        if isinstance(cj, dict):
            req = cj.get("require") if isinstance(cj.get("require"), dict) else {}
            info["name"] = cj.get("name") if isinstance(cj.get("name"), str) else None
            info["php_constraint"] = req.get("php") if isinstance(req.get("php"), str) else None
            info["extensions"] = sorted(k for k in req if k.startswith("ext-"))
            info["require"] = {k: v for k, v in req.items() if "/" in k and isinstance(v, str)}
            plat = (cj.get("config") or {}).get("platform") if isinstance(cj.get("config"), dict) else None
            if isinstance(plat, dict) and isinstance(plat.get("php"), str):
                info["platform_php"] = plat["php"]
        elif cj is not None:
            warnings.append(f"{os.path.join(rel_root, 'composer.json')}: not a JSON object; ignored")
    lock = read_json(os.path.join(root, "composer.lock"), warnings, os.path.join(rel_root, "composer.lock")) if os.path.isfile(os.path.join(root, "composer.lock")) else None
    if os.path.isfile(os.path.join(root, "composer.lock")) and not isinstance(lock, dict):
        info["lock_malformed"] = True
    if isinstance(lock, dict):
        info["lock_present"] = True
        for pkg in (lock.get("packages") or []) + (lock.get("packages-dev") or []):
            if isinstance(pkg, dict) and isinstance(pkg.get("name"), str):
                info["packages"][pkg["name"]] = {"version": norm_version(pkg.get("version")), "source": "composer.lock"}
        info["lock_missing_packages"] = sorted(n for n in info["require"] if n not in info["packages"])
    installed_json = os.path.join(root, "vendor", "composer", "installed.json")
    inst = read_json(installed_json, warnings, os.path.join(rel_root, "vendor/composer/installed.json")) if os.path.isfile(installed_json) else None
    if inst is not None:
        pkgs = inst.get("packages") if isinstance(inst, dict) else inst
        if isinstance(pkgs, list):
            info["installed_present"] = True
            for pkg in pkgs:
                if isinstance(pkg, dict) and isinstance(pkg.get("name"), str):
                    info["packages"][pkg["name"]] = {"version": norm_version(pkg.get("version")), "source": "vendor/composer/installed.json"}
    installed_php = os.path.join(root, "vendor", "composer", "installed.php")
    text = read_text(installed_php) if os.path.isfile(installed_php) else None
    if text:
        info["installed_present"] = True
        for name, ver in re.findall(r"'([a-z0-9_.-]+/[a-z0-9_.-]+)'\s*=>\s*(?:array\(|\[)\s*'pretty_version'\s*=>\s*'([^']+)'", text):
            info["packages"][name] = {"version": norm_version(ver), "source": "vendor/composer/installed.php"}
    return info


# ------------------------------------------------------------------- runtimes
DOCKER_FROM = re.compile(r"(?im)^\s*FROM\s+(?:--platform=\S+\s+)?(\S*php\S*?):([\w.-]+)")
COMPOSE_IMAGE = re.compile(r"(?im)^\s*image:\s*['\"]?(\S*php\S*?):([\w.-]+)")
PKG_FPM = re.compile(r"(?i)\bphp(\d\.\d)-(fpm|cli|common)\b|\bphp(\d)(\d)-(fpm|cli)\b")
FPM_SOCK = re.compile(r"(?i)php(\d\.\d)-fpm\.sock|/php/(\d\.\d)/fpm|php-fpm(\d\.\d)|ea-php(\d)(\d)|x-httpd-php(\d)(\d)|alt-php(\d)(\d)")
MOD_PHP = re.compile(r"(?im)^\s*LoadModule\s+php(\d)?_module")
CI_PHP = re.compile(r"(?i)php[-_ ]?versions?['\"]?\s*[:=]\s*\[?\s*['\"]?(\d+\.\d+(?:\.\d+)?)|image:\s*['\"]?(?:\S*/)?php:(\d+\.\d+(?:\.\d+)?)|setup-php@\S+")
PLATFORM_TYPE = re.compile(r"(?im)^\s*(?:type|runtime):\s*['\"]?php:?(\d+\.?\d+(?:\.\d+)?)")
CI_FILES = (".gitlab-ci.yml", "bitbucket-pipelines.yml", ".travis.yml", "azure-pipelines.yml", "Jenkinsfile")


def _ver(*groups):
    g = [x for x in groups if x]
    if len(g) == 2 and len(g[0]) == 1 and len(g[1]) == 1:  # ea-php81 style
        return f"{g[0]}.{g[1]}"
    return g[0] if g else None


def _sapi(text):
    t = text.lower()
    return "apache2handler" if "apache" in t else "fpm-fcgi" if "fpm" in t else "frankenphp" if "frankenphp" in t else None


def runtime_from_file(path, rel, name):
    text = read_text(path)
    if not text:
        return []
    out = []
    low = name.lower()
    rel_dir = os.path.dirname(rel).replace("\\", "/")
    if low.startswith(("dockerfile", "containerfile")) or low.endswith(".dockerfile"):
        for image, tag in DOCKER_FROM.findall(text):
            m = re.match(r"(\d+\.\d+(?:\.\d+)?)", tag)
            variant = "web" if re.search(r"fpm|apache|nginx|frankenphp|litespeed|unit", image + tag, re.I) else "cli"
            out.append(dict(kind=variant, version=m.group(1) if m else None, source=rel, detail=redact(f"FROM {image}:{tag}"), sapi=_sapi(image + tag)))
        for g in PKG_FPM.findall(text):
            v = _ver(g[0], g[2], g[3])
            out.append(dict(kind="web" if "fpm" in g else "cli", version=v, source=rel, detail=f"OS package php{v} ({g[1] or g[4]})"))
    elif re.match(r"(docker-)?compose.*\.ya?ml$", low):
        for image, tag in COMPOSE_IMAGE.findall(text):
            m = re.match(r"(\d+\.\d+(?:\.\d+)?)", tag)
            variant = "web" if re.search(r"fpm|apache|nginx|frankenphp|litespeed|unit", image + tag, re.I) else "cli"
            out.append(dict(kind=variant, version=m.group(1) if m else None, source=rel, detail=redact(f"image {image}:{tag}"), sapi=_sapi(image + tag)))
    elif rel_dir.endswith(".github/workflows") or name in CI_FILES or rel_dir.endswith(".circleci"):
        for g in CI_PHP.findall(text):
            if g[0] or g[1]:
                out.append(dict(kind="ci", version=g[0] or g[1], source=rel, detail="CI PHP version"))
    elif name in (".php-version",):
        v = text.strip().splitlines()[0] if text.strip() else None
        out.append(dict(kind="cli", version=v, source=rel, detail="local toolchain pin (.php-version)"))
    elif name == ".tool-versions":
        m = re.search(r"(?m)^php\s+(\S+)", text)
        if m:
            out.append(dict(kind="cli", version=m.group(1), source=rel, detail="local toolchain pin (.tool-versions)"))
    elif name in (".platform.app.yaml", ".upsun.yaml", "app.yaml") or rel_dir.endswith(".platform") or rel_dir.endswith(".upsun"):
        for v in PLATFORM_TYPE.findall(text):
            v = v if "." in v else f"{v[0]}.{v[1:]}"
            out.append(dict(kind="web", version=v, source=rel, detail="PaaS runtime declaration"))
    elif low.endswith((".conf", ".htaccess", ".ini", ".vhost")) or low in ("www.conf", "nginx.conf", "httpd.conf"):
        for g in FPM_SOCK.findall(text):
            v = _ver(*g)
            out.append(dict(kind="web", version=v, source=rel, detail=f"web server/FPM config references PHP {v}"))
        for g in MOD_PHP.findall(text):
            out.append(dict(kind="web", version=g or None, source=rel, detail="Apache mod_php (highest PHP2Shell risk SAPI per php.net)", sapi="apache2handler"))
    return out


def classify_runtime(version, checker):
    if not version or not checker:
        return None
    r = checker.classify(version)
    return {"classification": r["classification"], "branch_status": r["branch_status"],
            "advisories": {a["id"]: a["status"] for a in r["advisories"]}}


def load_checker():
    try:
        spec = importlib.util.spec_from_file_location("check_php_version", os.path.join(HERE, "check-php-version.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.load_data()
        return mod
    except (OSError, ValueError, AttributeError):
        return None


def load_lifecycle():
    try:
        with open(LIFECYCLE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def lifecycle_for(fid, version, lc, today):
    if not lc or not version:
        return {"status": "unknown", "reason": "no version or lifecycle data"}
    prod = lc.get("products", {}).get(fid)
    if not prod:
        return {"status": "unknown", "reason": "no lifecycle data for this project; check the official release policy"}
    vt = vtuple(version)
    best = None
    for rel in prod["releases"]:
        ct = vtuple(rel["cycle"])
        if ct and vt[:len(ct)] == ct and (best is None or len(ct) > len(vtuple(best["cycle"]))):
            best = rel
    if not best:
        oldest = min((vtuple(r["cycle"]) for r in prod["releases"]), default=None)
        if oldest and vt and vt < oldest:
            return {"status": "unsupported", "reason": "older than every tracked release", "source": prod["source"], "verified_on": lc.get("verified_on")}
        return {"status": "unknown", "reason": "release cycle not found", "source": prod["source"]}
    eol = best["eol"]
    if isinstance(eol, str):
        is_eol = datetime.date.fromisoformat(eol) < today
    else:
        is_eol = bool(best.get("is_eol"))
    return {"status": "unsupported" if is_eol else "supported", "cycle": best["cycle"], "eol": eol, "latest": best["latest"],
            "supported_php": best.get("supported_php"), "source": prod["source"], "verified_on": lc.get("verified_on")}


# ---------------------------------------------------------------- test tooling
TEST_CONFIGS = {"phpunit.xml": "PHPUnit", "phpunit.xml.dist": "PHPUnit", "phpunit.dist.xml": "PHPUnit", "tests/Pest.php": "Pest",
                "codeception.yml": "Codeception", "codeception.dist.yml": "Codeception", "behat.yml": "Behat", "behat.yml.dist": "Behat",
                "phpstan.neon": "PHPStan", "phpstan.neon.dist": "PHPStan", "phpstan.dist.neon": "PHPStan", "psalm.xml": "Psalm",
                "rector.php": "Rector", "phpcs.xml": "PHP_CodeSniffer", "phpcs.xml.dist": "PHP_CodeSniffer", ".phpcs.xml.dist": "PHP_CodeSniffer"}


def test_tooling(root, comp):
    tools = sorted({f"{name} ({rel})" for rel, name in TEST_CONFIGS.items() if os.path.isfile(os.path.join(root, *rel.split("/")))})
    dev = [p for p in ("phpunit/phpunit", "pestphp/pest", "codeception/codeception", "phpstan/phpstan", "rector/rector",
                       "phpcompatibility/php-compatibility", "squizlabs/php_codesniffer", "vimeo/psalm") if p in comp["packages"]]
    return {"configs": tools, "packages": dev, "has_test_runner": any(t.split()[0] in ("PHPUnit", "Pest", "Codeception", "Behat") for t in tools)
            or any(p in dev for p in ("phpunit/phpunit", "pestphp/pest", "codeception/codeception"))}


# ----------------------------------------------------------------- detection
# Host applications that embed other frameworks: the embedded one is reported as a component.
EMBEDS = {"october-cms": {"laravel"}, "laravel": {"symfony"}, "drupal": {"symfony"}, "prestashop": {"symfony"},
          "magento": {"laminas", "symfony"}, "suitecrm": {"symfony"}, "nextcloud": {"symfony"}, "typo3": {"symfony"},
          "espocrm": {"slim"}, "mediawiki": {"symfony"}, "moodle": {"symfony"}}


def detect_frameworks(root, comp, rel_root):
    found = []
    for fw in FRAMEWORKS:
        evidence, version, vsource, conf = [], None, None, None
        strong = [m for m in fw["strong"] if os.path.exists(os.path.join(root, *m.split("/")))]
        weak = [m for m in fw["weak"] if os.path.exists(os.path.join(root, *m.split("/")))]
        for pkg in fw["packages"]:
            if pkg in comp["packages"]:
                p = comp["packages"][pkg]
                version, vsource, conf = p["version"], f"{p['source']} ({pkg})", "high"
                evidence.append(f"package {pkg} {p['version']} in {p['source']}")
                break
        if not version:
            for pkg in fw["packages"]:
                if pkg in comp["require"]:
                    conf = "medium"
                    evidence.append(f"composer.json requires {pkg} {comp['require'][pkg]} (constraint, not installed version)")
                    break
        if fw.get("ext") and fw["ext"] in comp["extensions"]:
            conf = conf or "medium"
            evidence.append(f"composer.json requires {fw['ext']}")
        if not (conf or strong or weak):
            continue  # version files are only trusted alongside another signal
        for rel, rx in fw["version_files"]:
            path = os.path.join(root, *rel.split("/"))
            if not version and os.path.isfile(path):
                m = re.search(rx, read_text(path) or "", re.M)
                if m:
                    version, vsource, conf = m.group(1), rel, "high"
                    evidence.append(f"version string in {rel}")
        if fw["id"] == "joomla" and not version and strong:
            text = read_text(os.path.join(root, "libraries", "src", "Version.php")) or ""
            parts = [re.search(rf"{k}_VERSION\s*=\s*(\d+)", text) for k in ("MAJOR", "MINOR", "PATCH")]
            if all(parts):
                version, vsource, conf = ".".join(x.group(1) for x in parts), "libraries/src/Version.php", "high"
                evidence.append("version constants in libraries/src/Version.php")
        evidence += [f"marker {m}" for m in strong] + [f"supporting marker {m}" for m in weak]
        if strong and not conf:
            conf = "medium"
        if not conf and len(weak) >= 2:
            conf = "low"
        if conf:
            found.append({"id": fw["id"], "name": fw["name"], "version": version, "version_source": vsource,
                          "confidence": conf, "evidence": [redact(e) for e in evidence], "components": []})
    ids = {f["id"] for f in found}
    embedded = set().union(*(EMBEDS.get(i, set()) for i in ids)) - {i for i in ids if i in EMBEDS and not any(i in EMBEDS.get(j, ()) for j in ids)}
    hosts = [f for f in found if f["id"] not in embedded]
    for f in found:
        if f["id"] in embedded:
            host = next((h for h in hosts if f["id"] in EMBEDS.get(h["id"], ())), None)
            if host:
                host["components"].append(f"{f['name']} {f['version'] or ''}".strip())
    found = hosts
    if any(f["confidence"] in ("high", "medium") for f in found):
        found = [f for f in found if f["confidence"] != "low"]
    return found


def scan(path, max_depth=8, today=None):
    today = today or datetime.date.today()
    path = os.path.abspath(path)
    report = {"tool": "php2shell-migration/detect-project", "scanned_path": path, "network_used": False,
              "generated_on": today.isoformat(), "projects": [], "runtimes": [], "findings": [], "warnings": [], "monorepo": False}
    if not os.path.isdir(path):
        report["warnings"].append("path is not a directory")
        return report
    checker, lifecycle = load_checker(), load_lifecycle()
    if not checker:
        report["warnings"].append("advisory data unavailable: runtime security classification skipped")
    roots, runtime_hits = [], []
    base_depth = path.rstrip(os.sep).count(os.sep)
    for dirpath, dirnames, filenames in os.walk(path):
        depth = dirpath.count(os.sep) - base_depth
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not (d.startswith(".") and d not in (".github", ".circleci", ".platform", ".upsun", ".docker", ".phalcon")))
        if depth >= max_depth:
            dirnames[:] = []
        rel_dir = os.path.relpath(dirpath, path).replace("\\", "/")
        rel_dir = "" if rel_dir == "." else rel_dir
        for name in filenames:
            rel = f"{rel_dir}/{name}" if rel_dir else name
            runtime_hits += runtime_from_file(os.path.join(dirpath, name), rel, name)
        is_root = "composer.json" in filenames or any(
            os.path.exists(os.path.join(dirpath, *m.split("/"))) for fw in FRAMEWORKS for m in fw["strong"])
        if is_root:
            roots.append(rel_dir)

    for rel_root in roots:
        root = os.path.join(path, *rel_root.split("/")) if rel_root else path
        comp = composer_info(root, rel_root, report["warnings"])
        fws = detect_frameworks(root, comp, rel_root)
        for fw in fws:
            fw["lifecycle"] = lifecycle_for(fw["id"], fw["version"], lifecycle, today)
        parent = max((r for r in roots if r != rel_root and (r == "" or rel_root.startswith(r + "/"))), key=len, default=None)
        proj = {"path": rel_root or ".", "parent": (parent or ".") if parent is not None else None, "frameworks": fws,
                "composer": {k: v for k, v in comp.items() if k not in ("packages", "require")},
                "package_count": len(comp["packages"]), "test_tooling": test_tooling(root, comp), "runtimes": []}
        if not fws:
            proj["frameworks"] = []
            proj["note"] = "No known framework signature: treat as custom/unrecognized PHP (references/frameworks/other-php-projects.md)"
        report["projects"].append(proj)

    # assign runtime declarations to the deepest enclosing project
    for hit in runtime_hits:
        owner = max((p for p in report["projects"] if p["path"] == "." or hit["source"].startswith(p["path"] + "/")),
                    key=lambda p: len(p["path"]) if p["path"] != "." else 0, default=None)
        hit["security"] = classify_runtime(hit["version"], checker) if hit["version"] and re.match(r"\d+\.\d+", hit["version"]) else None
        hit["note"] = {"web": "declared in source; verify on the serving host before claiming it is the deployed runtime",
                       "cli": "CLI/toolchain runtime; does not prove the web runtime",
                       "ci": "CI runtime; does not prove the web runtime"}[hit["kind"]]
        (owner["runtimes"] if owner else report["runtimes"]).append(hit)

    report["monorepo"] = sum(1 for p in report["projects"] if p["frameworks"] or p["composer"]["composer_json"]) > 1
    _findings(report)
    return report


def _findings(report):
    f = report["findings"]
    all_rt = report["runtimes"] + [r for p in report["projects"] for r in p["runtimes"]]
    for p in report["projects"]:
        rts = p["runtimes"] + (report["runtimes"] if p["path"] == "." else [])
        constraint = p["composer"].get("php_constraint")
        for rt in rts:
            sec = rt.get("security") or {}
            cls = sec.get("classification")
            if cls in ("runtime_affected", "runtime_unsupported"):
                f.append({"category": cls, "severity": "critical" if cls == "runtime_affected" else "high", "project": p["path"],
                          "message": f"{rt['kind']} runtime PHP {rt['version']} declared in {rt['source']} is {cls.replace('_', ' ')}",
                          "evidence": [rt["source"]]})
            elif rt["version"] and cls == "status_unknown":
                f.append({"category": "status_unknown", "severity": "medium", "project": p["path"],
                          "message": f"{rt['kind']} runtime PHP {rt['version']} in {rt['source']}: patch level cannot be established from source",
                          "evidence": [rt["source"]]})
            if constraint and rt["version"] and constraint_allows(constraint, rt["version"]) is False:
                f.append({"category": "deployment_mismatch", "severity": "high", "project": p["path"],
                          "message": f"composer.json requires php {constraint} but {rt['source']} declares {rt['kind']} PHP {rt['version']}",
                          "evidence": ["composer.json", rt["source"]]})
        for rt in rts:
            if rt.get("sapi") == "apache2handler":
                f.append({"category": "other", "severity": "high", "project": p["path"],
                          "message": f"{rt['source']} uses Apache mod_php, the SAPI php.net rates highest risk for PHP2Shell; prioritise patching it",
                          "evidence": [rt["source"]]})
        web = {vtuple(r["version"])[:2] for r in rts if r["kind"] == "web" and r["version"]}
        other = {vtuple(r["version"])[:2] for r in rts if r["kind"] in ("cli", "ci") and r["version"]}
        if web and other and not (web & other):
            f.append({"category": "deployment_mismatch", "severity": "medium", "project": p["path"],
                      "message": "web runtime branch differs from CLI/CI runtime branch: tests may not exercise the deployed runtime",
                      "evidence": sorted({r["source"] for r in rts})})
        for fw in p["frameworks"]:
            if fw["lifecycle"].get("status") == "unsupported":
                f.append({"category": "framework_outdated", "severity": "high", "project": p["path"],
                          "message": f"{fw['name']} {fw['version']} is past end of life (source: {fw['lifecycle'].get('source')}, data {fw['lifecycle'].get('verified_on')})",
                          "evidence": [fw["version_source"] or "markers"]})
        if p["composer"].get("lock_missing_packages"):
            f.append({"category": "dependency_inconsistent", "severity": "medium", "project": p["path"],
                      "message": "composer.lock does not contain: " + ", ".join(p["composer"]["lock_missing_packages"][:10]),
                      "evidence": ["composer.json", "composer.lock"]})
        if p["composer"]["composer_json_malformed"] or p["composer"]["lock_malformed"]:
            f.append({"category": "dependency_inconsistent", "severity": "high", "project": p["path"],
                      "message": "malformed Composer metadata: run `composer validate` and repair before any upgrade", "evidence": ["composer.json", "composer.lock"]})
        elif p["composer"]["composer_json"] and not p["composer"]["lock_present"]:
            f.append({"category": "dependency_inconsistent", "severity": "low", "project": p["path"],
                      "message": "composer.json without composer.lock: installed dependency versions cannot be established", "evidence": ["composer.json"]})
    if report["projects"] and not any(r["kind"] == "web" for r in all_rt):
        f.append({"category": "status_unknown", "severity": "high", "project": ".",
                  "message": "No web runtime declaration found in source: the PHP version serving requests must be verified on the host",
                  "evidence": []})
    for item in f:
        item["message"] = redact(item["message"])


# -------------------------------------------------------------------- output
def summary(report):
    lines = [f"Scanned: {report['scanned_path']} (network used: no)"]
    if report["monorepo"]:
        lines.append("Multiple PHP applications/components detected (monorepo).")
    if not report["projects"]:
        lines.append("No PHP project roots found.")
    for p in report["projects"]:
        lines.append(f"\n[{p['path']}]" + (f" (inside {p['parent']})" if p["parent"] else ""))
        for fw in p["frameworks"]:
            lc = fw["lifecycle"]
            lines.append(f"  {fw['name']} {fw['version'] or '(version unknown)'} - confidence {fw['confidence']}; lifecycle {lc.get('status')}"
                         + (f" (cycle {lc['cycle']}, latest {lc['latest']}, PHP {lc.get('supported_php') or 'see docs'})" if lc.get("cycle") else ""))
            for e in fw["evidence"][:4]:
                lines.append(f"    - {e}")
        if not p["frameworks"]:
            lines.append("  " + p["note"])
        c = p["composer"]
        if c["composer_json"]:
            lines.append(f"  composer: php {c['php_constraint'] or '(no constraint)'}; lock {'yes' if c['lock_present'] else 'no'}; vendor {'yes' if c['installed_present'] else 'no'}; ext {', '.join(c['extensions']) or '-'}")
        tt = p["test_tooling"]
        lines.append(f"  test tooling: {', '.join(tt['configs'] + tt['packages']) or 'none found'}"
                     + ("" if tt["has_test_runner"] else " -> no test runner: automated tests will be 'blocked' until one exists"))
        for r in p["runtimes"]:
            sec = (r.get("security") or {}).get("classification", "unclassified")
            lines.append(f"  runtime[{r['kind']}] PHP {r['version'] or '?'} from {r['source']}: {sec}")
    if report["runtimes"]:
        lines.append("\n[repository level: not attributable to one application]")
    for r in report["runtimes"]:
        lines.append(f"  runtime[{r['kind']}] PHP {r['version'] or '?'} from {r['source']}")
    if report["findings"]:
        lines.append("\nFindings:")
        for x in report["findings"]:
            lines.append(f"  [{x['severity']}] {x['category']}: {x['message']}")
    if report["warnings"]:
        lines.append("\nWarnings:")
        lines += [f"  - {w}" for w in report["warnings"]]
    lines.append("\nDetection is evidence, not proof. Verify the serving runtime on the host; see references/security/vulnerability-verification.md.")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true", help="print JSON instead of the human summary")
    ap.add_argument("--output", help="also write the JSON report to this file")
    ap.add_argument("--max-depth", type=int, default=8)
    a = ap.parse_args(argv)
    if not os.path.isdir(a.path):
        print(f"error: not a directory: {a.path}", file=sys.stderr)
        return 64
    report = scan(a.path, a.max_depth)
    if a.output:
        with open(a.output, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    print(json.dumps(report, indent=2) if a.json else summary(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
