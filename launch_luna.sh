#!/bin/bash
# Launch LUNA ◈ — The Mirror (body separated)
cd /home/guestpc/AZOTH

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

HARNESS_AGENT=LUNA python3 agent.py "$@"
