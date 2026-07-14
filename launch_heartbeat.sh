#!/usr/bin/env bash
# ☿ AZOTH HEARTBEAT — Mac fires this, never Sol.
# Beats every AZOTH_HEARTBEAT_MIN minutes (default 30) on a FREE clone seat.
# Quiet hours respected (AZOTH_QUIET, default 23-08). Ctrl+C to stop.
cd "$(dirname "$0")"
exec python3 -m CORE.heartbeat --daemon
