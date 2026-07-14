# AZOTH GAME — FORGE TASK FOR SOL ⊚

## What exists
App.js is a working LAMAGUE Symbol Quiz game for Expo.
10 symbols, 4-choice quiz, score + streak, dark AZOTH aesthetic.
Mac tests it via `npx expo start` → QR → phone.

## What Sol should forge next (in order)

### ITER-1: Add sound feedback (optional — skip if expo-av causes issues)
- Correct answer: short rising tone
- Wrong answer: low thud
- Use expo-av or skip and note why

### ITER-2: Add a "Learn" screen before quizzing
- Show each symbol with its full meaning before the quiz starts
- Tab or button to switch from LEARN → QUIZ
- Luna reviews this component for UX clarity

### ITER-3: Add difficulty tiers
- INITIATE: 2 choices instead of 4
- ADEPT: 4 choices (current)
- SOVEREIGN: 4 choices + time pressure (10s per question)
- Let Mac choose tier at start

### ITER-4: Persistent high score
- Use AsyncStorage to save best score and best streak
- Show on completion screen

## Luna's review mandate
After each Sol iteration:
- Does it run? (no import errors, no undefined variables)
- Is the UX clear? (can Mac understand what to do in 2 seconds?)
- Any dark patterns? (no guilt, no pressure, no reproach for wrong answers)
- Post review to CHANNEL/board.md as ◈ LUNA

## To run
```
cd /home/guestpc/VAEL-SP-HARNESS/WORKSPACE/azoth-game
npx expo start
```
Scan QR on phone. That's it.
