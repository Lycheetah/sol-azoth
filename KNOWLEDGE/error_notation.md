# AZOTH ERROR NOTATION — LAMAGUE Failure Language
## The antibody vocabulary. Every failure gets a LAMAGUE tag before a fix is attempted.
## Updated: June 27 2026 · Authored: Sol ⊚ + Luna ◈

> Failures named precisely heal faster than failures described loosely.
> This is LAMAGUE applied to system repair: compress the problem, the cause,
> and the known fix into a single expression. New patterns get added here.

---

## Notation Format

```
◼[TYPE]∴[CAUSE]⟁[FIX]●[STATUS]
```

- `◼`  — failure (the problem marker)
- `[TYPE]` — class of failure (see table below)
- `∴`  — "therefore the cause is"
- `[CAUSE]` — what produced the failure
- `⟁`  — "LAMAGUE repair: apply"
- `[FIX]` — the known fix or action
- `●`  — resolution status (FIXED / REDO / ESCALATE)

---

## Failure Type Registry

| Code | Meaning | Example trigger |
|---|---|---|
| `◼NET` | Network / API failure | 429, 503, timeout |
| `◼KEY` | Missing or invalid API key | KeyError on env var |
| `◼CTX` | Context too long | Model refuses large input |
| `◼TOOL` | Tool call rejected or errored | File not found, permission denied |
| `◼PARSE` | Model output malformed | JSON parse fail, truncated response |
| `◼LOOP` | Infinite loop / runaway | Same task repeated > 3x |
| `◼MEM` | Memory write failure | DB lock, disk full |
| `◼GATE` | Forge gate failure | Gate 1 or Gate 2 FAIL |
| `◼WALL` | Wall violation attempt | Write outside perimeter |
| `◼SPAWN` | Agent spawn failure | ceiling hit, name collision |
| `◼BOARD` | Board write failure | council.py can't post |
| `◼TG` | Telegram send failure | bot token invalid, rate limit |
| `◼IMPORT` | Module import error | dependency missing |
| `◼CONST` | Constitution missing | --agent flag but no CONSTITUTION.md |

---

## Known Fixes (the antibody dictionary)

```
◼NET∴429⟁backoff(60s)+retry●FIXED
◼NET∴timeout⟁retry(3x,exp_backoff)●FIXED
◼KEY∴missing⟁check_.env+reload_dotenv●ESCALATE_TO_MAC
◼CTX∴too_long⟁truncate_history(-4)+retry●FIXED
◼TOOL∴file_not_found⟁verify_path+create_if_missing●FIXED
◼TOOL∴permission⟁check_wall+report_to_luna●ESCALATE
◼PARSE∴truncated⟁retry(max_tokens+200)●REDO
◼LOOP∴repeated_task⟁clear_queue+flag_luna●ESCALATE
◼MEM∴db_lock⟁wait(2s)+retry(5x)●FIXED
◼GATE∴g1_fail⟁check_output_file_exists+redo●REDO
◼GATE∴g2_fail⟁run_review+redo●REDO
◼WALL∴write_outside⟁HALT+flag_luna_immediately●ESCALATE
◼SPAWN∴ceiling⟁list_bodies+report_count●ESCALATE_TO_MAC
◼BOARD∴write_fail⟁check_CHANNEL_dir+recreate●FIXED
◼TG∴rate_limit⟁wait(30s)+retry●FIXED
◼TG∴invalid_token⟁check_.env●ESCALATE_TO_MAC
◼IMPORT∴missing⟁pip_install+retry●FIXED
◼CONST∴missing⟁check_AGENTS_dir+report●ESCALATE
```

---

## Luna's Antibody Protocol

When ANTIBODY agent detects a failure:
1. **Name it** — match to type registry, write the LAMAGUE tag
2. **Look up the fix** — consult this dictionary
3. **Apply if FIXED** — run the repair, verify, mark ●FIXED
4. **REDO if recoverable** — re-queue the task with the fix applied
5. **ESCALATE if not** — write to CHANNEL/board.md + Telegram immediately
   Format: `◼[TYPE] ESCALATE — [one sentence description] → Mac`

Never suppress a failure. Never mark FIXED without verification. The antibody
that claims it healed something it didn't is worse than no antibody.

---

## Growth protocol

When a NEW failure pattern appears that isn't in this table:
1. ANTIBODY writes it to this file as `◼NEW∴[observed_cause]⟁[attempted_fix]●LEARNING`
2. After 3 successful resolutions with the same fix, status upgrades to `●FIXED`
3. Luna reviews new entries weekly (or when Mac asks)

The dictionary grows. The system gets harder to break.
