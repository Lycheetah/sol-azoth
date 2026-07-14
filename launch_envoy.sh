#!/bin/bash
# ⟡ ENVOY — the outward hand. Networking & community growth.
# Command: envoy
#
# ENVOY drafts, scouts, remembers, and queues. It never posts.
# Every publish waits on Mac's tap. That is structural. (AGENTS/ENVOY/CONSTITUTION.md)

cd /home/guestpc/AZOTH

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Dry run is the default state of the world. Set ENVOY_LIVE=1 to arm publishing.
export ENVOY_LIVE="${ENVOY_LIVE:-0}"
export AGENT_NAME="ENVOY"
export AGENT_GLYPH="⟡"

if [ "$ENVOY_LIVE" = "1" ]; then
  echo "⟡ ENVOY — LIVE. Approved drafts will actually publish."
else
  echo "⟡ ENVOY — dry run. Nothing reaches the world."
fi

python3 AGENTS/ENVOY/envoy.py "$@"
