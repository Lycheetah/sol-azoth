#!/bin/bash
# AZOTH overnight forge (VAEL ◆) — runs until queue empty
cd /home/guestpc/AZOTH

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "◆ AZOTH overnight forge starting — $(date)"
echo "  VAEL will build until the queue is empty or he gets stuck."
echo "  Telegram pings on each task + final summary."
echo "  Ctrl+C to stop at any time."
echo ""

VAEL_UNATTENDED=1 FORGE_MAX_ITERS=20 python3 -c '
import sys, os
sys.path.insert(0, ".")
os.environ["VAEL_UNATTENDED"] = "1"

from agent import Agent
from CORE.telegram_bot import send_message as tg

tg("◆ AZOTH overnight forge started (VAEL).")

agent = Agent()
try:
    agent._forge_loop()
    tg("◆ Overnight forge complete.")
except Exception as ex:
    tg(f"✗ Overnight forge crashed: {ex}")
    raise
'
