# Deployment and rollback

**Last verified: 2026-10-24.** The agent prepares changes and runbooks; humans deploy.

## Runtime declarations to update together

| Where | Example change |
|---|---|
| Dockerfile | `FROM php:8.4.27-fpm-bookworm` (pin the patch release; avoid floating `php:8.4-fpm` for reproducibility, or pin by digest) |
| Compose / Kubernetes | image tags, digests |
| CI | workflow `php-version` matrices; CI images |
| PaaS | `.platform.app.yaml` / `.upsun/config.yaml` `type: 'php:8.4'`, Heroku `composer.json` `require.php`, App Engine `runtime` |
| OS packages | `apt install php8.4-fpm` / `dnf module` streams / `apk add php84-fpm` plus FPM pool paths and the web server `fastcgi_pass` socket |
| Shared hosting | control-panel PHP selector (cPanel MultiPHP, CloudLinux selector, Plesk): document the setting and owner |
| Composer | `require.php`, `config.platform.php` |
| Local | `.php-version`, `.tool-versions` |

Re-run `scripts/detect-project.py` afterwards: there should be no `deployment_mismatch` findings.

## After deploying a runtime patch (runbook for the operator)

1. Restart **all** PHP workers (FPM master reload, Apache restart for mod_php, LiteSpeed lsphp restart, container recreate). php.net stresses restarting every worker when changing mitigations, and the same holds for binary updates.
2. Verify the serving version ([../security/vulnerability-verification.md](../security/vulnerability-verification.md)).
3. Watch error logs and health checks for one full traffic cycle.
4. Clear OPcache and framework caches if the deploy procedure doesn't.

## Rollback

| Change type | Rollback |
|---|---|
| Code/config | `git revert <stage commits>` and redeploy the previous artefact |
| Container image | redeploy the previous image digest (keep it pinned in the runbook) |
| OS package | **avoid rolling back a security patch**. If the patch itself breaks the app, roll back the application change instead, or apply the mitigations while fixing forward |
| Database | restore the verified backup taken before migration; most CMS schema upgrades are irreversible otherwise |
| Composer | revert `composer.json` + `composer.lock` together, then `composer install` |

Rolling back to a vulnerable runtime re-opens PHP2Shell. If unavoidable, it must be time-boxed, apply all interim mitigations, and appear as an open finding.

## Checkpoints the plan must name

- Git branch/commit before the change.
- Previous image digest or package version.
- DB backup location and restore test result.
- Config files changed (FPM pools, vhosts, php.ini) with copies of the originals.
