#!/bin/bash
# ☿ AZOTH MODEL SCOUT — overnight model benchmarking
# Tests every NVIDIA model: availability, speed, context limits, LAMAGUE quality
# Results → KNOWLEDGE/model_catalog.md + Telegram updates every 30 min
# Mac kicks this off. It runs until done. Sol and Luna wake smarter.

cd /home/guestpc/AZOTH
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs) 2>/dev/null
fi

echo ""
echo "☿ AZOTH MODEL SCOUT"
echo "  Testing all NVIDIA models overnight."
echo "  Telegram will update every 30 minutes."
echo "  Results → KNOWLEDGE/model_catalog.md"
echo "  Press Ctrl-C to stop."
echo ""

python3 -c "from CORE.model_scout import run_scout; run_scout()"
