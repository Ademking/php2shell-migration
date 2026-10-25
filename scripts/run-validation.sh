#!/bin/sh
# Run the skill's own test suite and documentation/reference validation.
# POSIX sh; on Windows run the same python commands directly (see README).
#   scripts/run-validation.sh            offline (default)
#   scripts/run-validation.sh --online   also probe every external URL
set -u
cd "$(dirname "$0")/.." || exit 64
PY=${PYTHON:-python3}
command -v "$PY" >/dev/null 2>&1 || PY=python
status=0

echo "== 1/3 unit tests (python -m unittest discover -s tests -v)"
"$PY" -m unittest discover -s tests -v || status=1

echo "== 2/3 reference validation"
"$PY" scripts/validate-references.py . "$@" || status=1

echo "== 3/3 template report validation"
"$PY" scripts/validate-results.py templates/test-results.json || status=1

[ "$status" -eq 0 ] && echo "ALL VALIDATION PASSED" || echo "VALIDATION FAILED"
exit "$status"
