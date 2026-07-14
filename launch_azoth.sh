#!/bin/bash
# azoth — main single SOL agent (AZOTH)
# Pure chat by default. Tools only on explicit /forge (or other / commands).
# No network, no daemons, no auto-forges.

cd /home/guestpc/AZOTH

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Hard isolation from full network / army
unset FORGE_NETWORK_LAUNCH 2>/dev/null || true

export AZOTH_SINGLE_AGENT=1
export AZOTH_AUTO_FORGE=0

# No pre-boot chatter — the wake screen inside agent.py carries the identity now.
HARNESS_AGENT=SOL python3 agent.py "$@"

# For the old full multi-body/network boot, use the previous full launcher
# (or azoth-full if you set it up). This script is now the canonical `azoth`.
