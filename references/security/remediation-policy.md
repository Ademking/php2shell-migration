# Remediation policy

**Last verified: 2026-10-24.** How to decide what to do, and in which order.

## Six situations

| # | Category id | Evidence | Required action | Urgency |
|---|---|---|---|---|
| 1 | `runtime_affected` | Supported branch, upstream version below the fixed release | Update the runtime within the branch (e.g. 8.3.30 → 8.3.36). Restart **all** workers. Verify. | Immediate. Apply interim mitigations until done. |
| 2 | `runtime_unsupported` | Branch past security support (≤8.1 today; 8.2 after 2026-12-31) | Short term: vendor backport or php.net source backport plus mitigations. Then migrate to a supported branch (framework work may be required). | Immediate containment, planned migration. |
| 3 | `framework_outdated` | Runtime patched; framework/CMS past EOL or behind security releases | Upgrade the framework through its supported path. Separate from runtime work. | High; schedule. |
| 4 | `dependency_vulnerable` | `composer audit`, CMS update screens, extension advisories | Update the package within constraints, or replace/patch it. Never ignore advisories silently. | By severity. |
| 5 | `deployment_mismatch` | Source declares one runtime, deployment config/host another (detector or on-host check) | Align the declarations (Dockerfile, compose, CI, PaaS config, FPM pools) and verify on the host. | High: tests may not cover production. |
| 6 | `status_unknown` | Branch-only tag, vendor build without notice, no host access, sources unreachable | Report what is unknown and which evidence would resolve it. Do not guess. | Treat as possibly affected. |

A project can be in several categories at once; record each as a finding.

## Ordering rules

1. **Runtime before application.** A same-branch patch (category 1) requires no code change and must not wait for framework work.
2. **Containment before migration** for category 2: get a patched build (vendor or backport) or mitigations in place, then migrate.
3. **One variable at a time.** Change the runtime, test, then the framework, test, then dependencies. Don't combine a PHP major/minor jump with a framework major jump in one step unless the framework requires it; if it does, document why.
4. **Supported targets only.** Never move to an EOL branch, a pre-release, or an unofficial build as the end state.
5. **No feature removal** to make an upgrade pass, unless the user decides so explicitly.

## Interim mitigations

Listed in [php2shell-advisories.md](php2shell-advisories.md#interim-mitigations-not-fixes). Record each applied mitigation as a finding with category `runtime_affected` that stays open until the runtime is updated.

## Definition of done (per category)

- 1/2: `runtime_patch_verified` and `web_runtime_verified` true in the report, with evidence.
- 3/4: target versions installed, lock file committed, `composer audit` (or CMS equivalent) clean or remaining items listed as findings, application tests executed.
- 5: declarations aligned, plus on-host evidence.
- 6: either resolved into another category with evidence, or still listed with the missing evidence named.
