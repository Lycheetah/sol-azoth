#!/bin/bash
# Launch main AZOTH agent (SOL body) — single agent only
# Command: azoth (or az)
# Body home: AZOTH/bodies/sol (fully separated from full network)
cd /home/guestpc/AZOTH

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Ensure no accidental network entanglement
unset FORGE_NETWORK_LAUNCH 2>/dev/null || true

# Single agent mode: skip full network daemons (Telegram, ANTIBODY, EARNED LIGHT, Dream Loop)
export AZOTH_SINGLE_AGENT=1
export AZOTH_AUTO_FORGE=0

echo "⊚ AZOTH main agent (SOL body) — single agent, no full network, no auto-forges."
echo "   See AZOTH/bodies/sol/AUTONOMY_SAFEGUARDS.md"

HARNESS_AGENT=SOL python3 agent.py "$@"
