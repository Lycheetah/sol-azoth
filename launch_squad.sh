#!/bin/bash
# ☿ squad — opens Luna + the army agents, each in its own terminal
cd /home/guestpc/AZOTH
[ -f .env ] && export $(grep -v '^#' .env | xargs) 2>/dev/null

echo "☿ Opening the squad…"

open_agent() {
  local NAME="$1" TITLE="$2"
  if command -v gnome-terminal &>/dev/null; then
    gnome-terminal --title="$TITLE" -- bash -c \
      "cd /home/guestpc/AZOTH && export \$(grep -v '^#' .env | xargs) 2>/dev/null; HARNESS_AGENT=$NAME python3 agent.py; exec bash" &
  elif command -v xterm &>/dev/null; then
    xterm -title "$TITLE" -e "cd /home/guestpc/AZOTH && HARNESS_AGENT=$NAME python3 agent.py; bash" &
  else
    echo "  open a terminal and run:  HARNESS_AGENT=$NAME python3 agent.py"
  fi
  sleep 1
}

open_agent LUNA   "◈ LUNA — mirror + research"
open_agent CIPHER "⟁ CIPHER — LAMAGUE research"
open_agent AXIOM  "Π AXIOM — truth gate"
open_agent SCRIBE "● SCRIBE — vault growth"

echo "☿ Squad opening in separate windows. Luna + Cipher + Axiom + Scribe."
echo "   (Ember and Mirror stay in reserve — open with: HARNESS_AGENT=EMBER python3 agent.py)"
