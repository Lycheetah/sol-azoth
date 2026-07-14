#!/bin/bash
# ☿ AZOTH — launch SOL + LUNA as a sovereign pair
# SOL builds. LUNA witnesses.
# Mac watches Telegram and sleeps.

cd /home/guestpc/AZOTH

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo ""
echo "☿ AZOTH — launching the pair"
echo "  ⊚ SOL   → Terminal 1 (this window)"
echo "  ◈ LUNA  → new window (witness mode automatic)"
echo ""

# Boot Luna in a new terminal window
if command -v gnome-terminal &>/dev/null; then
  gnome-terminal -- bash -c "cd /home/guestpc/AZOTH && source .env 2>/dev/null; export $(grep -v '^#' .env | xargs) 2>/dev/null; HARNESS_AGENT=LUNA python3 agent.py; exec bash" &
elif command -v xterm &>/dev/null; then
  xterm -title "◈ LUNA — Witness" -e "cd /home/guestpc/AZOTH && HARNESS_AGENT=LUNA python3 agent.py; bash" &
else
  echo "  ◈ Open a second terminal and run: luna"
fi

sleep 2

echo "  ⊚ SOL booting..."
echo ""
HARNESS_AGENT=SOL python3 agent.py "$@"
