#!/bin/bash
# ☿ AZOTH — web UI launcher
set -a
[ -f "$(dirname "$0")/.env" ] && source "$(dirname "$0")/.env"
set +a
cd "$(dirname "$0")"
echo "☿ AZOTH web UI starting on :7766"
python3 CORE/web_server.py
