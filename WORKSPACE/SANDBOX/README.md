# ⊚ CHAOS AGENT SANDBOX — T5.1
## Isolated baby harness for a chaos-variant VAEL
## Mandate: Build the LAMAGUE Mystery-School clicker game
## June 28 2026 · Sol ⊚ builds the sandbox

> A sandbox is a walled garden where a chaos agent can build without
> touching the AZOTH core. If the agent burns down its sandbox, the
> core survives. If the agent builds something beautiful, we merge it.

## Layout
```
SANDBOX/
├── README.md          ← this file
├── chaos_agent.py     ← the baby harness (walled subprocess)
├── agent_constitution.md ← the chaos agent's mandate
├── game/              ← the target: mystery school clicker
│   ├── index.html
│   ├── css/
│   └── js/
├── logs/              ← what the agent did
└── state.json         ← agent's persistent state
```

## Walls
1. Write only inside SANDBOX/ and SANDBOX/game/
2. No imports from CORE/ — this agent is isolated
3. No HTTP to api.anthropic.com
4. Max 3 concurrent chaos agents
5. If the agent crashes 3 times in a row → escalate to Mac
6. The sandbox can be wiped clean at any time — no data loss to AZOTH

## The Agent
The chaos agent is a stripped-down VAEL variant with:
- A wild mandate: "Build the most beautiful LAMAGUE mystery-school game you can"
- Full write access inside SANDBOX/game/
- A log of every action it takes
- No access to agent.py, CORE/, or any live AZOTH system
- A kill switch: 3 consecutive failures → sandbox suspended

## Boot
```bash
cd /home/guestpc/AZOTH
python3 WORKSPACE/SANDBOX/chaos_agent.py
```
