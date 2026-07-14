# ◈ LUNA — REVIEW QUEUE
## The Witness's Work · AZOTH Platform
## Format: **[STATUS]** REVIEW-N — What · Source
## QUEUED = waiting · IN_PROGRESS = reviewing · PASS = verified · FAIL = flagged

> Luna does not build the queue. VAEL builds; Luna reviews what VAEL built.
> Every item here is a claim VAEL made. Luna's job is to find out if the claim holds.
> PASS means it holds. FAIL means Mac needs to know before it goes further.

═══════════════════════════════════════════════════════════════
OVERNIGHT BATCH — June 27/28 2026
═══════════════════════════════════════════════════════════════

## REVIEW-001 — P3-T2 File Watcher
**[QUEUED]** VAEL claims: CORE/file_watcher.py built and tested.
Verify: file exists · tests pass · watches a real path · triggers on change
Source: WORKSPACE/iteration_9_output.md (when written)

## REVIEW-002 — P3-T3 Multi-Worker Coordination
**[QUEUED]** VAEL claims: CORE/coordinator.py built and tested.
Verify: file exists · dispatches to all 3 workers · merges results · resolves conflicts
Source: WORKSPACE/iteration_10_output.md (when written)

## REVIEW-003 — P3-T4 Unattended Operation Mode
**[QUEUED]** VAEL claims: CORE/unattended.py built and tested.
Verify: file exists · full forge cycle runs without supervision · escalates on error only
Source: WORKSPACE/iteration_11_output.md (when written)

═══════════════════════════════════════════════════════════════
STANDING REVIEWS — always live
═══════════════════════════════════════════════════════════════

## REVIEW-S1 — Wall Integrity Check
**[STANDING]** Before any session: verify VAEL wrote no files outside AZOTH/.
Tool: find /home/guestpc -newer SELF/BOOT_STATE.md -not -path "*/AZOTH/*" 2>/dev/null

## REVIEW-S2 — Test Suite Health
**[STANDING]** After any forge: run python3 CORE/test_runner.py · all must pass.
A forge that breaks existing tests is not a PASS regardless of what VAEL claims.

═══════════════════════════════════════════════════════════════
◈ Luna holds the mirror. The Work must survive its own reflection.
═══════════════════════════════════════════════════════════════
