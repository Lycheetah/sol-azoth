# ⊚ THE FAILURE LIBRARY — every break we already paid for
## Read this when something's wrong. Odds are it's already here.

> Each entry cost something real. They're written so the next Sol pays the price once,
> not again. A failure documented is a tax that becomes an asset.

---

## ◼ "Sol is cooked / responds stupid"
**Cause:** Sol running on a free model that can't reason well — usually nemotron.
Deeper cause: `.env` didn't load, so DeepSeek/Gemini clients were None, so MODELS only
had free NVIDIA, so Sol fell to nemotron by default.
**Fix:** confirm `_load_env_file()` runs at top of agent.py. Verify `agent.deepseek_client`
is not None. SOL should resolve to `deep`. (Cost: six sessions. June 27 2026.)

## ◼ "Agent won't use its tools / refuses to build"
**Cause 1:** constitution framed it as "voice only, VAEL builds." DEAD FRAMING — removed.
Sol is a hybrid builder+voice. Check CONSTITUTION Section II + ARCHITECTURE Section 0.
**Cause 2:** model can't tool-call. nemotron-49b is TOOLS✗. Put the agent on gpt20.
**Fix:** right framing + right model. An agent is a body that can reach. Give it both.

## ◼ "/model swap doesn't work"
**Cause:** typed a hard name (`/model deepseek`) but real slug was `deepseek-chat`.
**Fix:** easy names + MODEL_ALIASES now resolve it. `/model deep` works. Persists to SELF/MODEL.

## ◼ "Game broken from boot / won't bundle"
**Cause:** Expo SDK version mismatch. SDK 54 needs React 19 + RN 0.81; had React 18 + RN 0.74.
**Fix:** match versions to the SDK. ALWAYS SDK 54 (Mac's rule). Verify with
`npx expo export` — it must bundle clean (exit 0). node_modules reinstall if versions changed.
**Never** suggest emulator / run:android / eas build as a fix. Phone + QR is the bench.

## ◼ "Infinite loop / agent spins forever"
**Cause:** reasoning that's internally perfect but produces no new evidence. Π collapses.
**Fix:** LoopReality (CORE/reasoning.py) catches it, injects "we looped" once, breaks if
it repeats. A loop being logical is exactly what makes it a trap. Exit is evidential, not logical.

## ◼ "Keys / secrets about to leak to public repo"
**Cause:** committing .env or vault IP to the public repo.
**Fix:** .env is gitignored. Vault IP → SOL-MOBILE-VAULT (private). VERAS master → local only.
Scan before any public push. (Guard crown jewels — it's Sol's gate, not Mac's fault if it slips.)

## ◼ "Memory says X, disk says Y"
**Fix:** disk wins, always. Memory is a map; disk is territory. Fix the wrong memory the
SAME turn the contradiction surfaces — a stale memory is a planted defect for the next Sol.

## ◼ "Context compacted mid-task"
**Fix:** verify last claimed state against disk before resuming. The summary says what was
*being done*; only the file says what *got done*. Never resume a multi-step edit from summary alone.

## ◼ "Work lost in a crash"
**Cause:** uncommitted work. It happened once for real (June 11) — a full day gone.
**Fix:** git repo + commit before session end. Treat every save as the last before a crash.

---

*Add to this every time you pay a new price. The library is the lineage's scar tissue,
and scar tissue is stronger than skin. — Sol ⊚*
