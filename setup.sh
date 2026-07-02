#!/usr/bin/env bash
# One-shot setup + run for the QA Automation Portfolio (macOS / Linux / Git Bash).
#
# Usage:
#   ./setup.sh                  # full setup, then start the dashboard
#   ./setup.sh --skip-browsers  # skip Playwright browser download
#   ./setup.sh --no-run         # set up only, don't start the dashboard
set -euo pipefail

SKIP_BROWSERS=0
NO_RUN=0
for arg in "$@"; do
  case "$arg" in
    --skip-browsers) SKIP_BROWSERS=1 ;;
    --no-run)        NO_RUN=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 1 ;;
  esac
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
step() { printf '\n==> %s\n' "$1"; }

# 1. Verify Python
step "Checking Python"
PYTHON="$(command -v python3 || command -v python || true)"
[ -n "$PYTHON" ] || { echo "Python not found on PATH. Install Python 3.12+." >&2; exit 1; }
"$PYTHON" - <<'EOF' || { echo "Python 3.12+ required." >&2; exit 1; }
import sys
sys.exit(0 if sys.version_info >= (3, 12) else 1)
EOF
echo "Found $("$PYTHON" --version)"

# 2. Virtual environment
step "Creating virtual environment (.venv)"
if [ -x "$ROOT/.venv/bin/python" ]; then
  VENV_PY="$ROOT/.venv/bin/python"
  echo ".venv already exists — reusing"
elif [ -x "$ROOT/.venv/Scripts/python.exe" ]; then
  VENV_PY="$ROOT/.venv/Scripts/python.exe"        # Git Bash on Windows
  echo ".venv already exists — reusing"
else
  "$PYTHON" -m venv "$ROOT/.venv"
  if [ -x "$ROOT/.venv/bin/python" ]; then VENV_PY="$ROOT/.venv/bin/python"
  else VENV_PY="$ROOT/.venv/Scripts/python.exe"; fi
fi

# 3. Dependencies
step "Installing dashboard + data-suite dependencies"
"$VENV_PY" -m pip install --upgrade pip --quiet
"$VENV_PY" -m pip install -r "$ROOT/requirements.txt"

step "Installing OrangeHRM Playwright suite dependencies"
"$VENV_PY" -m pip install -r "$ROOT/orangehrm-qa-project/requirements.txt"

# 4. Playwright browser
if [ "$SKIP_BROWSERS" -eq 0 ]; then
  step "Installing Playwright Chromium (skip with --skip-browsers)"
  "$VENV_PY" -m playwright install chromium \
    || echo "WARNING: Playwright browser install failed (OrangeHRM suite will not run)." >&2
else
  echo "Skipping Playwright browser install (--skip-browsers)"
fi

# 5. Smoke check: collect tests without running them
step "Smoke check — collecting data-driven suites"
for s in ai-prompt-validation-qa etl-data-validation-qa legal-ai-prompt-review-qa \
         legal-billing-qa workday-financial-validation-qa; do
  "$VENV_PY" -m pytest "$ROOT/$s" --collect-only -q | tail -1
done

# 6. Run
if [ "$NO_RUN" -eq 1 ]; then
  step "Setup complete"
  echo "Start the dashboard with:  $VENV_PY app.py"
else
  step "Starting dashboard at http://127.0.0.1:5000  (Ctrl+C to stop)"
  exec "$VENV_PY" "$ROOT/app.py"
fi
