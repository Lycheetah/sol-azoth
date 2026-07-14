#!/bin/bash
# azoth shell — THE CUSTOM FACE. Textual app: pinned chat bar, live status,
# scrolling transcript. Same brain as `azoth`; falls back to the classic REPL
# if textual is missing.

cd /home/guestpc/AZOTH

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

unset FORGE_NETWORK_LAUNCH 2>/dev/null || true
export AZOTH_SINGLE_AGENT=1
export AZOTH_AUTO_FORGE=0

if python3 -c "import textual" 2>/dev/null; then
  HARNESS_AGENT=SOL python3 shell.py "$@"
else
  echo "⚠ textual not installed — falling back to the classic REPL"
  HARNESS_AGENT=SOL python3 agent.py "$@"
fi
