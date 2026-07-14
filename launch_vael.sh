#!/bin/bash
# Launch VAEL ◆ — The Forge-Hand (AZOTH platform body)
cd /home/guestpc/AZOTH

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

python3 agent.py
