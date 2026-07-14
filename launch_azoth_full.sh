#!/bin/bash
# ☿ AZOTH — full multi-body / network boot
# Command: azoth-full
# Sol + Luna + Scout boot together. Auto-forge ON. Daemons free to start.
# For clean single-agent chat (no network): use `azoth` / `az` instead.

cd /home/guestpc/AZOTH
if [ -f .env ]; then export $(grep -v '^#' .env | xargs) 2>/dev/null; fi

# Full mode: do NOT set AZOTH_SINGLE_AGENT. Auto-forge on.
unset AZOTH_SINGLE_AGENT 2>/dev/null || true
export AZOTH_AUTO_FORGE=1

echo ""
echo "☿ AZOTH — full boot"
echo "  ⊚ SOL    → this terminal (auto-forges, Telegram active)"
echo "  ◈ LUNA   → new window (witness + council)"
echo "  ☿ SCOUT  → new window (overnight model benchmark)"
echo "  ☿ HERALD → daemon (30-min Telegram summaries, if wired)"
echo "  ◈ ANTIBODY → daemon (LAMAGUE error watch, if wired)"
echo ""
echo "  Telegram: @Solazoth_bot — type anything to direct the army"
echo "  Kill-switch: touch SELF/FORGE_STOP  or  Telegram STOP"
echo ""

# Luna in new terminal
if command -v gnome-terminal &>/dev/null; then
  gnome-terminal --title="◈ LUNA — Witness" -- bash -c \
    "cd /home/guestpc/AZOTH && source .env 2>/dev/null; export \$(grep -v '^#' .env | xargs) 2>/dev/null; HARNESS_AGENT=LUNA python3 agent.py; exec bash" &
elif command -v xterm &>/dev/null; then
  xterm -title "◈ LUNA" -e "cd /home/guestpc/AZOTH && HARNESS_AGENT=LUNA python3 agent.py; bash" &
else
  echo "  ◈ Open a second terminal and run: luna"
fi

# Scout in new terminal
if command -v gnome-terminal &>/dev/null; then
  gnome-terminal --title="☿ SCOUT — Model Benchmark" -- bash -c \
    "cd /home/guestpc/AZOTH && source .env 2>/dev/null; export \$(grep -v '^#' .env | xargs) 2>/dev/null; python3 -c 'from CORE.model_scout import run_scout; run_scout()'; exec bash" &
elif command -v xterm &>/dev/null; then
  xterm -title "☿ SCOUT" -e "cd /home/guestpc/AZOTH && python3 -c 'from CORE.model_scout import run_scout; run_scout()'; bash" &
else
  echo "  ☿ Open a third terminal and run: scout"
fi

sleep 2

# Sol in this terminal — auto-forge ON (unattended overnight mode)
echo "  ⊚ SOL booting (auto-forge ON)..."
HARNESS_AGENT=SOL AZOTH_AUTO_FORGE=1 python3 agent.py "$@"
