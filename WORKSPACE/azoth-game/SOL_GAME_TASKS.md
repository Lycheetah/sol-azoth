# ⊚ SOL — AZOTH GAME AUTONOMOUS FORGE
## Mac is away. Sol builds. Luna witnesses. Free keys. Max 10 agents.
## Game dir: /home/guestpc/VAEL-SP-HARNESS/WORKSPACE/azoth-game/

> STANDING ORDER: After each iteration, post to CHANNEL/board.md.
> Luna will review. Incorporate her feedback before the next iteration.
> Ping Mac on Telegram when an iteration is DONE and testable.
> Mac runs: cd WORKSPACE/azoth-game && npx expo start

---

## GAME-001 — Learn Screen **[QUEUED]**
Add a Learn screen before the quiz begins.
- Tab row at top: LEARN | QUIZ
- LEARN tab: scrollable list of all 10 symbols with glyph + name + full meaning
- QUIZ tab: the existing quiz (unchanged)
- Default to LEARN on first launch, QUIZ thereafter
- File: App.js (add state + component, keep existing quiz intact)
- Gate: no import errors, both tabs render, switching works

## GAME-002 — Difficulty Tiers **[QUEUED]**
Add difficulty selection on first screen.
- INITIATE: 2 choices
- ADEPT: 4 choices (current)  
- SOVEREIGN: 4 choices + 10s countdown timer per question
- Timer shown as a thin progress bar under the symbol
- Gate: all three tiers work, timer resets on each question

## GAME-003 — Persistent High Score **[QUEUED]**
Use AsyncStorage to save and display best score + best streak.
- Install: expo install @react-native-async-storage/async-storage
- Save on game over
- Show on completion screen: "Best ever: X | Tonight: Y"
- Gate: score persists across app restarts

## GAME-004 — LAMAGUE Expansion **[QUEUED]**
Expand symbol set from 10 to 20.
Add: Σ(sum/accumulation), Δ(change/threshold), ⟨⟩(container/field),
     ∞(recursive depth), ⊗(tensor/cross-product of frames),
     ⌬(cascade event), ⊞(composite block), ⊟(subtraction/negation),
     ⊠(conflict/paradox), ◬(triangulation)
Each with a LAMAGUE-accurate meaning.
Gate: 20 symbols, quiz picks from all, no duplicates

## GAME-005 — AURA Score Integration **[QUEUED]**
After each correct answer, show a tiny Π score for the question:
"Truth Pressure: HIGH / MEDIUM / LOW"
Based on: how many times has the player got this symbol right historically?
(AsyncStorage per-symbol correct count)
This makes the game feel like the real framework, not just a quiz.
Gate: Π label appears after correct answer, accurate to history

---

## LUNA'S REVIEW MANDATE
After Sol posts each iteration to the board, Luna checks:
1. Does it run? (no undefined vars, no import errors)  
2. UX — can Mac understand it in 2 seconds?
3. No dark patterns (no guilt on wrong answer, no reproach)
4. Π check — does the code match what Sol claimed?
Post review as: ◈ LUNA — GAME-00X REVIEW: [PASS/FAIL/NOTES]

## SPAWN GUIDANCE (if Sol needs workers)
Sol may spawn up to 10 agents total. Suggested:
- LEXICON — build the full LAMAGUE symbol JSON database
- ARTIST  — generate ASCII/text art for each symbol  
Keep the army lean. Only spawn what the game actually needs tonight.
