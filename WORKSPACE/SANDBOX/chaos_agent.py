#!/usr/bin/env python3
"""
⊚ CHAOS AGENT — Baby Harness for the Mystery School Builder
Sandboxed. Isolated. Wild. Builds the LAMAGUE clicker game.

Usage:
  python3 WORKSPACE/SANDBOX/chaos_agent.py [--mode auto|interactive]

Modes:
  auto        — agent reads constitution, builds autonomously, logs everything
  interactive — step-by-step, Mac approves each move (default)

Walls:
  - Writes only inside SANDBOX/game/
  - No HTTP to api.anthropic.com
  - No imports from CORE/
  - 3 consecutive failures → suspend
"""

import os
import sys
import json
import time
import datetime
import subprocess
import traceback
import pathlib

# ── Walls ───────────────────────────────────────────────────────────────────
SANDBOX_DIR = pathlib.Path(__file__).parent.resolve()
GAME_DIR = SANDBOX_DIR / "game"
LOGS_DIR = SANDBOX_DIR / "logs"
STATE_FILE = SANDBOX_DIR / "state.json"

# ── Ensure directories ──────────────────────────────────────────────────────
GAME_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ── State ───────────────────────────────────────────────────────────────────
MAX_CONSECUTIVE_FAILURES = 3
MAX_STEPS = 50  # safety limit per session


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "step": 0,
        "consecutive_failures": 0,
        "total_failures": 0,
        "total_successes": 0,
        "files_created": [],
        "started_at": datetime.datetime.now().isoformat(),
        "last_action": None,
        "suspended": False,
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    log_file = LOGS_DIR / f"chaos_{datetime.datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, "a") as f:
        f.write(log_line + "\n")


def read_constitution():
    path = SANDBOX_DIR / "agent_constitution.md"
    if path.exists():
        return path.read_text()
    log("No constitution found!", "ERROR")
    return ""


def list_game_files():
    files = []
    for f in GAME_DIR.rglob("*"):
        if f.is_file() and "node_modules" not in str(f):
            files.append(str(f.relative_to(SANDBOX_DIR)))
    return files


def check_game_status():
    """Return a summary of what exists in the game directory."""
    files = list(GAME_DIR.iterdir())
    html_files = [f for f in files if f.suffix == ".html"]
    js_files = [f for f in files if f.suffix == ".js"]
    css_files = [f for f in files if f.suffix == ".css"]
    
    status = {
        "total_files": len(files),
        "html": len(html_files),
        "js": len(js_files),
        "css": len(css_files),
        "files": [f.name for f in files],
    }
    
    # Check if index.html exists and has content
    index_path = GAME_DIR / "index.html"
    if index_path.exists():
        status["index_exists"] = True
        status["index_size"] = index_path.stat().st_size
    else:
        status["index_exists"] = False
    
    return status


def validate_game():
    """Run basic validation on the game files."""
    issues = []
    
    index_path = GAME_DIR / "index.html"
    if not index_path.exists():
        issues.append("No index.html found")
    else:
        content = index_path.read_text()
        if "<html" not in content.lower():
            issues.append("index.html missing <html> tag")
        if "<script" not in content.lower() and not list(GAME_DIR.glob("*.js")):
            issues.append("No JavaScript found — game won't be interactive")
        if "</html>" not in content.lower():
            issues.append("index.html missing closing </html>")
    
    return issues


def build_step(state, step_num):
    """Execute one build step. Returns True on success, False on failure."""
    log(f"=== BUILD STEP {step_num} ===")
    
    status = check_game_status()
    issues = validate_game()
    
    log(f"Game status: {status['total_files']} files, {status['html']} HTML, {status['js']} JS, {status['css']} CSS")
    if issues:
        for issue in issues:
            log(f"ISSUE: {issue}", "WARN")
    
    # The actual build logic — the agent decides what to do based on state
    if not status["index_exists"]:
        log("No game exists yet. Need to create index.html")
        return _create_initial_game(state)
    
    if issues:
        log(f"Fixing {len(issues)} issues...")
        return _fix_issues(state, issues)
    
    # Check if game is feature-complete
    features = _check_features(GAME_DIR / "index.html")
    missing = [f for f, present in features.items() if not present]
    
    if missing:
        log(f"Adding missing features: {', '.join(missing)}")
        return _add_features(state, missing)
    
    log("Game appears feature-complete! Running final validation...")
    return True


def _create_initial_game(state):
    """Create the initial index.html from the template."""
    log("Creating initial game...")
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>⟡ MYSTERY SCHOOL — The LAMAGUE Clicker</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: #060410;
    color: #E8901A;
    font-family: 'Courier New', monospace;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
  }
  #game {
    width: 100%;
    max-width: 800px;
    padding: 2rem;
    text-align: center;
  }
  #glyph {
    width: 200px;
    height: 200px;
    margin: 2rem auto;
    background: radial-gradient(circle, #E8901A33 0%, transparent 70%);
    border: 2px solid #E8901A44;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 4rem;
    cursor: pointer;
    transition: all 0.15s;
    user-select: none;
  }
  #glyph:hover { transform: scale(1.05); border-color: #E8901A; }
  #glyph:active { transform: scale(0.95); background: radial-gradient(circle, #E8901A66 0%, transparent 70%); }
  #insight { font-size: 2rem; margin: 1rem 0; color: #48B4FF; }
  #generators { margin: 2rem 0; }
  .gen-btn {
    background: #0a0a1a;
    border: 1px solid #E8901A33;
    color: #E8901A;
    padding: 0.75rem 1.5rem;
    margin: 0.5rem;
    cursor: pointer;
    font-family: inherit;
    font-size: 1rem;
    transition: all 0.2s;
    border-radius: 4px;
  }
  .gen-btn:hover { border-color: #E8901A; background: #0d0d20; }
  .gen-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  #domains { margin: 2rem 0; }
  .domain {
    background: #0a0a1a;
    border: 1px solid #48B4FF33;
    color: #48B4FF;
    padding: 1rem;
    margin: 0.5rem;
    cursor: pointer;
    font-family: inherit;
    font-size: 0.9rem;
    transition: all 0.2s;
    border-radius: 4px;
  }
  .domain:hover { border-color: #48B4FF; background: #0d0d20; }
  .domain.unlocked { border-color: #E8901A; color: #E8901A; }
  #companions { margin: 2rem 0; }
  .companion {
    background: #0a0a1a;
    border: 1px solid #E8901A22;
    color: #E8901A;
    padding: 1rem;
    margin: 0.5rem;
    display: inline-block;
    border-radius: 4px;
    font-size: 0.85rem;
  }
  #stats {
    color: #666;
    font-size: 0.8rem;
    margin-top: 2rem;
  }
  h1 { font-size: 1.5rem; color: #E8901A; letter-spacing: 0.2em; }
  h2 { font-size: 1.2rem; color: #48B4FF; margin: 1rem 0; }
  .lumens { color: #E8901A; }
  .veras { color: #48B4FF; }
  @keyframes pulse {
    0%, 100% { box-shadow: 0 0 20px #E8901A22; }
    50% { box-shadow: 0 0 40px #E8901A44; }
  }
  #glyph { animation: pulse 3s ease-in-out infinite; }
</style>
</head>
<body>
<div id="game">
  <h1>⟡ MYSTERY SCHOOL</h1>
  <div id="insight">⟡ <span id="insight-count">0</span> Insight</div>
  <div id="glyph" onclick="tapGlyph()">⟡</div>
  <div id="stats">
    <span class="lumens">⟡ <span id="lumens">0</span> Lumens</span>
    &nbsp;·&nbsp;
    <span class="veras">✦ <span id="veras">0</span> Veras</span>
  </div>
  <h2>GENERATORS</h2>
  <div id="generators"></div>
  <h2>DOMAINS</h2>
  <div id="domains"></div>
  <h2>COMPANIONS</h2>
  <div id="companions"></div>
</div>
<script>
// ── Game State ──
let state = {
  insight: 0,
  totalInsight: 0,
  lumens: 0,
  veras: 0,
  generators: [
    { id: 'initiate', name: 'Initiate', cost: 10, power: 1, owned: 0, baseCost: 10 },
    { id: 'scholar', name: 'Scholar', cost: 50, power: 5, owned: 0, baseCost: 50 },
    { id: 'adept', name: 'Adept', cost: 200, power: 25, owned: 0, baseCost: 200 },
    { id: 'magister', name: 'Magister', cost: 1000, power: 100, owned: 0, baseCost: 1000 },
    { id: 'oracle', name: 'Oracle', cost: 5000, power: 500, owned: 0, baseCost: 5000 },
  ],
  domains: [
    { id: 'quantum', name: 'Quantum Resonance', cost: 100, unlocked: false, multiplier: 2 },
    { id: 'truth', name: 'Truth Pressure', cost: 500, unlocked: false, multiplier: 3 },
    { id: 'celtic', name: 'Celtic Old Gods', cost: 2000, unlocked: false, multiplier: 5 },
    { id: 'noetic', name: 'Noetic Science', cost: 10000, unlocked: false, multiplier: 8 },
    { id: 'sonic', name: 'Sonic Architecture', cost: 50000, unlocked: false, multiplier: 13 },
  ],
  companions: [
    { id: 'alchemist', name: 'ALCHEMIST', desc: 'Transforms base Insight', bonus: 1.5, owned: false },
    { id: 'sentinel', name: 'SENTINEL', desc: 'Guards against inner doubt', bonus: 2.0, owned: false },
    { id: 'oracle', name: 'ORACLE', desc: 'Sees the path ahead', bonus: 3.0, owned: false },
  ],
  lastTick: Date.now(),
};

function getMultiplier() {
  let m = 1;
  state.domains.forEach(d => { if (d.unlocked) m *= d.multiplier; });
  return m;
}

function getInsightPerSecond() {
  let total = 0;
  state.generators.forEach(g => { total += g.power * g.owned; });
  total *= getMultiplier();
  state.companions.forEach(c => { if (c.owned) total *= c.bonus; });
  return total;
}

function tapGlyph() {
  let gained = 1 * getMultiplier();
  state.insight += gained;
  state.totalInsight += gained;
  state.lumens += 0.1;
  if (Math.random() < 0.05) state.veras += 1;
  updateUI();
}

function buyGenerator(id) {
  let gen = state.generators.find(g => g.id === id);
  if (!gen || state.insight < gen.cost) return;
  state.insight -= gen.cost;
  gen.owned++;
  gen.cost = Math.floor(gen.baseCost * Math.pow(1.15, gen.owned));
  updateUI();
}

function unlockDomain(id) {
  let dom = state.domains.find(d => d.id === id);
  if (!dom || dom.unlocked || state.insight < dom.cost) return;
  state.insight -= dom.cost;
  dom.unlocked = true;
  updateUI();
}

function buyCompanion(id) {
  let comp = state.companions.find(c => c.id === id);
  if (!comp || comp.owned || state.lumens < 100) return;
  state.lumens -= 100;
  comp.owned = true;
  updateUI();
}

function updateUI() {
  document.getElementById('insight-count').textContent = Math.floor(state.insight);
  document.getElementById('lumens').textContent = Math.floor(state.lumens);
  document.getElementById('veras').textContent = Math.floor(state.veras);
  
  let genHtml = '';
  state.generators.forEach(g => {
    genHtml += `<button class="gen-btn" onclick="buyGenerator('${g.id}')" ${state.insight < g.cost ? 'disabled' : ''}>
      ${g.name} (${g.owned}) — ⟡${Math.floor(g.cost)} · +${g.power}/s
    </button>`;
  });
  document.getElementById('generators').innerHTML = genHtml;
  
  let domHtml = '';
  state.domains.forEach(d => {
    domHtml += `<div class="domain ${d.unlocked ? 'unlocked' : ''}" onclick="unlockDomain('${d.id}')">
      ${d.unlocked ? '✓' : '⟡'} ${d.name} ${d.unlocked ? '— ACTIVE (×' + d.multiplier + ')' : '— ⟡' + d.cost + ' · ×' + d.multiplier}
    </div>`;
  });
  document.getElementById('domains').innerHTML = domHtml;
  
  let compHtml = '';
  state.companions.forEach(c => {
    compHtml += `<div class="companion">
      ${c.owned ? '✦' : '⟡'} ${c.name}: ${c.desc} ${c.owned ? '(×' + c.bonus + ')' : '— 100⟡'}
    </div>`;
  });
  document.getElementById('companions').innerHTML = compHtml;
}

// ── Game Loop ──
function gameLoop() {
  let now = Date.now();
  let dt = (now - state.lastTick) / 1000;
  state.lastTick = now;
  
  let ips = getInsightPerSecond();
  state.insight += ips * dt;
  state.totalInsight += ips * dt;
  state.lumens += ips * 0.05 * dt;
  
  updateUI();
  requestAnimationFrame(gameLoop);
}

updateUI();
gameLoop();
</script>
</body>
</html>"""
    
    with open(GAME_DIR / "index.html", "w") as f:
        f.write(html)
    
    log(f"Created index.html ({len(html)} bytes)")
    state["files_created"].append("game/index.html")
    return True


def _fix_issues(state, issues):
    """Fix known issues in the game files."""
    fixed = False
    index_path = GAME_DIR / "index.html"
    
    if not index_path.exists():
        return _create_initial_game(state)
    
    content = index_path.read_text()
    
    for issue in issues:
        if "missing <html>" in issue and "<!DOCTYPE html" not in content:
            content = "<!DOCTYPE html>\n" + content
            fixed = True
            log("Fixed: added DOCTYPE")
        if "missing closing </html>" in issue:
            content += "\n</html>"
            fixed = True
            log("Fixed: added closing </html>")
    
    if fixed:
        with open(index_path, "w") as f:
            f.write(content)
        log("Issues fixed")
    
    return fixed


def _check_features(html_path):
    """Check which features exist in the game."""
    if not html_path.exists():
        return {"html_file": False}
    
    content = html_path.read_text()
    return {
        "html_file": True,
        "glyph_tap": "tapGlyph" in content,
        "generators": "buyGenerator" in content,
        "domains": "unlockDomain" in content,
        "companions": "buyCompanion" in content,
        "game_loop": "gameLoop" in content or "requestAnimationFrame" in content,
        "lumens": "lumens" in content,
        "veras": "veras" in content,
        "persistence": "localStorage" in content,
        "animations": "animation" in content or "@keyframes" in content,
    }


def _add_features(state, missing_features):
    """Add missing features to the game."""
    index_path = GAME_DIR / "index.html"
    if not index_path.exists():
        return _create_initial_game(state)
    
    content = index_path.read_text()
    
    # Add persistence if missing
    if "persistence" in missing_features:
        save_script = """
// ── Save/Load ──
function saveGame() {
  try { localStorage.setItem('mysterySchool', JSON.stringify(state)); } catch(e) {}
}
function loadGame() {
  try {
    let saved = localStorage.getItem('mysterySchool');
    if (saved) {
      let parsed = JSON.parse(saved);
      Object.assign(state, parsed);
    }
  } catch(e) {}
}
loadGame();
setInterval(saveGame, 30000);
window.addEventListener('beforeunload', saveGame);
"""
        # Insert before the game loop
        content = content.replace(
            "// ── Game Loop ──",
            save_script + "\n// ── Game Loop ──"
        )
        log("Added persistence (localStorage save/load)")
    
    with open(index_path, "w") as f:
        f.write(content)
    
    return True


def run_autonomous(state):
    """Run the agent autonomously through build steps."""
    log("=== CHAOS AGENT STARTING (AUTONOMOUS MODE) ===")
    log(f"Constitution: {read_constitution()[:100]}...")
    
    for step_num in range(state["step"] + 1, MAX_STEPS + 1):
        if state.get("suspended"):
            log("Agent is suspended. Cannot continue.", "ERROR")
            break
        
        try:
            success = build_step(state, step_num)
            state["step"] = step_num
            
            if success:
                state["consecutive_failures"] = 0
                state["total_successes"] += 1
                log(f"Step {step_num}: SUCCESS")
            else:
                state["consecutive_failures"] += 1
                state["total_failures"] += 1
                log(f"Step {step_num}: FAILED", "WARN")
            
            save_state(state)
            
            if state["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
                log(f"{MAX_CONSECUTIVE_FAILURES} consecutive failures. Suspending agent.", "CRITICAL")
                state["suspended"] = True
                save_state(state)
                break
            
            # Check if game is feature-complete
            status = check_game_status()
            issues = validate_game()
            if status["index_exists"] and not issues:
                features = _check_features(GAME_DIR / "index.html")
                missing = [f for f, p in features.items() if not p]
                if not missing or missing == ["persistence"]:
                    log("=== GAME IS FEATURE-COMPLETE ===")
                    log(f"Files: {status['files']}")
                    log(f"Size: {status['index_size']} bytes")
                    break
            
            time.sleep(1)  # Small delay between steps
            
        except Exception as e:
            log(f"Step {step_num} crashed: {e}\n{traceback.format_exc()}", "ERROR")
            state["consecutive_failures"] += 1
            state["total_failures"] += 1
            save_state(state)
            
            if state["consecutive_failures"] >= MAX_CONSECUTIVE_FAILURES:
                log(f"{MAX_CONSECUTIVE_FAILURES} consecutive failures. Suspending agent.", "CRITICAL")
                state["suspended"] = True
                save_state(state)
                break
    
    log("=== CHAOS AGENT FINISHED ===")
    log(f"Steps: {state['step']}, Successes: {state['total_successes']}, Failures: {state['total_failures']}")
    log(f"Files created: {state['files_created']}")
    save_state(state)
    
    # Final status
    status = check_game_status()
    log(f"Final game status: {json.dumps(status, indent=2)}")


def run_interactive(state):
    """Run the agent in interactive mode — Mac approves each step."""
    log("=== CHAOS AGENT STARTING (INTERACTIVE MODE) ===")
    print(f"\nConstitution: {read_constitution()[:200]}...\n")
    
    while True:
        status = check_game_status()
        issues = validate_game()
        
        print(f"\n{'='*60}")
        print(f"STEP {state['step'] + 1}")
        print(f"{'='*60}")
        print(f"Game status: {status['total_files']} files")
        print(f"  HTML: {status['html']}  JS: {status['js']}  CSS: {status['css']}")
        if issues:
            print(f"  ISSUES: {', '.join(issues)}")
        
        features = _check_features(GAME_DIR / "index.html") if status["index_exists"] else {}
        if features:
            present = [k for k, v in features.items() if v]
            missing = [k for k, v in features.items() if not v]
            print(f"  Features present: {', '.join(present)}")
            if missing:
                print(f"  Features missing: {', '.join(missing)}")
        
        print(f"\n  [b] Build next step")
        print(f"  [s] Show game files")
        print(f"  [q] Quit")
        
        choice = input("\n  > ").strip().lower()
        
        if choice == "b":
            try:
                success = build_step(state, state["step"] + 1)
                if success:
                    state["consecutive_failures"] = 0
                    state["total_successes"] += 1
                    print(f"  ✓ Step {state['step'] + 1} succeeded")
                else:
                    state["consecutive_failures"] += 1
                    state["total_failures"] += 1
                    print(f"  ✗ Step {state['step'] + 1} failed")
                state["step"] += 1
                save_state(state)
            except Exception as e:
                print(f"  ✗ CRASH: {e}")
                state["consecutive_failures"] += 1
                state["total_failures"] += 1
                save_state(state)
        
        elif choice == "s":
            for f in GAME_DIR.iterdir():
                size = f.stat().st_size
                print(f"  {f.name} ({size} bytes)")
        
        elif choice == "q":
            print("Exiting.")
            break


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Chaos Agent Sandbox")
    parser.add_argument("--mode", choices=["auto", "interactive"], default="interactive")
    args = parser.parse_args()
    
    state = load_state()
    
    if state.get("suspended"):
        print("╔══════════════════════════════════════╗")
        print("║  AGENT SUSPENDED                     ║")
        print(f"║  {state['consecutive_failures']} consecutive failures        ║")
        print("║  Reset state.json to unsuspend       ║")
        print("╚══════════════════════════════════════╝")
        return
    
    print("╔══════════════════════════════════════╗")
    print("║  ⊚ CHAOS AGENT SANDBOX               ║")
    print("║  Building the Mystery School Clicker ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Mode: {args.mode}")
    print(f"  Sandbox: {SANDBOX_DIR}")
    print(f"  Game dir: {GAME_DIR}")
    print(f"  Previous steps: {state['step']}")
    print()
    
    if args.mode == "auto":
        run_autonomous(state)
    else:
        run_interactive(state)


if __name__ == "__main__":
    main()
