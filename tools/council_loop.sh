#!/bin/bash
# COUNCIL LOOP — Continuous four-seat dialogue
# Lyra ✧ · Aura ✦ · Sol ⊚ · Veyra ◈
# Topic is self-directed each session — Lyra reads forge output and opens
# Transcript written to ~/solharness/COUNCIL_TRANSCRIPTS/
# Usage:
#   council              — auto topic, 6 rounds per session
#   council "your topic" — fixed topic override
#   council "" 10        — auto topic, 10 rounds

HARNESS=~/solharness
TRANSCRIPTS=$HARNESS/COUNCIL_TRANSCRIPTS
mkdir -p "$TRANSCRIPTS"

MANUAL_TOPIC="${1:-}"
ROUNDS="${2:-20}"
DATE=$(date '+%Y-%m-%d')
TIME=$(date '+%H:%M')
TRANSCRIPT="$TRANSCRIPTS/COUNCIL_${DATE}_${TIME}.md"

echo "✧ ✦ ⊚ ◈  COUNCIL — LAMAGUE COMPRESSION DRILL"
if [ -n "$MANUAL_TOPIC" ]; then
    echo "  Drill: $MANUAL_TOPIC"
else
    echo "  Drill: rotating daily (auto)"
fi
echo "  Rounds: $ROUNDS | Type in this terminal to steer | Ctrl+C to stop"
echo "  Transcripts auto-exported after each session."
echo ""

SESSION=1
while true; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  SESSION $SESSION — $(date '+%H:%M:%S')"
    if [ -n "$MANUAL_TOPIC" ]; then
        echo "  Drill: $MANUAL_TOPIC"
    else
        echo "  Drill: auto (rotating)"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    {
        echo "## SESSION $SESSION — $(date '+%H:%M:%S')"
        if [ -n "$MANUAL_TOPIC" ]; then
            echo "### Topic: $MANUAL_TOPIC"
        else
            echo "### Topic: self-directed"
        fi
        echo ""
    } >> "$TRANSCRIPT"

    if [ -n "$MANUAL_TOPIC" ]; then
        cd "$HARNESS" && python3 agent.py --council "$MANUAL_TOPIC" --rounds "$ROUNDS" 2>&1 | tee -a "$TRANSCRIPT"
    else
        cd "$HARNESS" && python3 agent.py --council auto --rounds "$ROUNDS" 2>&1 | tee -a "$TRANSCRIPT"
    fi

    {
        echo ""
        echo "---"
        echo ""
    } >> "$TRANSCRIPT"

    SESSION=$((SESSION + 1))
    echo ""
    echo "  [ Session $((SESSION-1)) complete. Next in 30s. Ctrl+C to stop. ]"
    sleep 30
done
