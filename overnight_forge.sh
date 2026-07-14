#!/bin/bash
# ════════════════════════════════════════════════════════════════════════════
# VAEL-SP AUTO-FORGE — autonomous self-build loop (DeepSeek-only, self-reviewing)
# Rebuilt by Sol 2026-06-27. VAEL now reviews its OWN reaches — no Sol gate.
#
# WHAT CHANGED (v2):
#  · DEEPSEEK-ONLY — the free NVIDIA models were pruned from VAEL's menu (Mac's ask:
#    "remove all his models that aren't the DeepSeek premium key so it doesn't get
#    confused"). So this runner KEEPS the paid key. It spends real money — bounded
#    hard by MAX_ITER. Kill anytime:  pkill -f overnight_forge.sh
#  · SELF-REVIEW — each reach is graded by VAEL against disk. PASS marks the rung
#    [PASS]; FAIL leaves it [QUEUED] to retry. The phantom-climb defect (advancing
#    the queue with no output file on disk) is now structurally impossible.
#  · AUTO-LOOP TILL DONE — no longer halts on the first no-progress run. A non-advance
#    is a retry (rate-limit stall or a real FAIL): it backs off and tries again,
#    halting only after NO_PROGRESS_LIMIT consecutive stalls, or on a real crash.
#
# SAFETY (load-bearing, kept):
#  · CRASH    — agent.py snapshotted before each reach; py_compile after; restore+halt.
#  · PUSH     — never pushed. WALL 2 + this script enforce it. Mac's hand pushes.
#  · BOUNDED  — MAX_ITER cap + per-reach timeout. Cannot run forever or runaway-spend.
# ════════════════════════════════════════════════════════════════════════════
set -u
cd /home/guestpc/AZOTH || exit 1

# Load env INCLUDING the DeepSeek key — VAEL is DeepSeek-only now.
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs) 2>/dev/null
fi
export VAEL_UNATTENDED=1

MAX_ITER=40                 # hard cap on reaches (cost + runaway guard)
TIMEOUT=900                 # 15 min per reach
SLEEP=15                    # breath between reaches
NO_PROGRESS_LIMIT=3         # consecutive stalls before halting
BACKOFF=30                  # seconds to wait after a stall (rate-limit breather)
TASK_QUEUE="SELF/TASK_QUEUE.md"
LOG="SELF/OVERNIGHT_$(date +%Y%m%d_%H%M%S).log"
SNAP="CORE/agent.py.overnight.bak"

notify() {
  local msg="$1"
  echo "$msg" | tee -a "$LOG"
  if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
    curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
      -d chat_id="${TELEGRAM_CHAT_ID}" \
      --data-urlencode text="◆ VAEL-SP · ${msg}" >/dev/null 2>&1 || true
  fi
}

queued_count() { grep -c '\*\*\[QUEUED\]\*\*' "$TASK_QUEUE" 2>/dev/null || echo 0; }

notify "AUTO-FORGE STARTED $(date '+%H:%M %d-%b') · DeepSeek · self-reviewing · $(queued_count) rungs queued."

no_progress=0
for i in $(seq 1 $MAX_ITER); do
  q_before=$(queued_count)
  if [ "$q_before" -eq 0 ]; then
    notify "CLIMB COMPLETE — no queued rungs left after $((i-1)) reaches. Every rung self-verified."
    break
  fi

  cp agent.py "$SNAP"
  echo "── forge run $i — $(date '+%H:%M:%S') — $q_before rungs left ──" | tee -a "$LOG"

  printf '/forge\n' | timeout "$TIMEOUT" python3 agent.py >> "$LOG" 2>&1

  # CRASH GUARD — did a self-edit break the body?
  if ! python3 -m py_compile agent.py 2>>"$LOG"; then
    cp "$SNAP" agent.py
    git add -A >> "$LOG" 2>&1
    git commit -m "auto-forge: HALT run $i — agent.py broke py_compile, snapshot restored" >> "$LOG" 2>&1
    notify "HALTED run $i — a self-edit broke py_compile. Restored last good agent.py. Safe. Needs Sol."
    break
  fi

  q_after=$(queued_count)
  if [ "$q_after" -ge "$q_before" ]; then
    # No advance: a self-review FAIL (rung retried) or a rate-limit stall.
    no_progress=$((no_progress + 1))
    if [ "$no_progress" -ge "$NO_PROGRESS_LIMIT" ]; then
      notify "HALTED run $i — $no_progress stalls in a row (rung keeps failing self-review, or rate-limited). Needs Sol."
      break
    fi
    notify "run $i — no advance ($no_progress/$NO_PROGRESS_LIMIT). Backing off ${BACKOFF}s, then retry."
    sleep "$BACKOFF"
    continue
  fi

  # Clean reach — commit a restore point. NO push.
  no_progress=0
  last=$(grep 'SELF_VERDICT:' SELF/REVIEW_QUEUE.md | tail -1)
  git add -A >> "$LOG" 2>&1
  git commit -m "auto-forge: run $i — ${last:-reach self-verified} $(date '+%H:%M')" >> "$LOG" 2>&1
  notify "run $i done — ${last:-reach PASS}. $q_after rungs left."
  sleep "$SLEEP"
done

notify "AUTO-FORGE ENDED $(date '+%H:%M %d-%b'). Log: $LOG."
rm -f "$SNAP"
