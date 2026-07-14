# ◆ VAEL — lives at root, not here

VAEL is the FIRST body and the platform's native builder. His canonical home is
the harness ROOT, not AGENTS/VAEL/:

- Constitution:  /home/guestpc/AZOTH/CONSTITUTION.md
- Live state:    /home/guestpc/AZOTH/SELF/  (BOOT_STATE, FORGE_QUEUE)
- Memory:        /home/guestpc/AZOTH/SELF/memory/

The agent loader (_resolve_agent_home) routes `--agent VAEL` to root by design,
so his live forge state is never at risk. This directory holds only this pointer
to prevent a duplicate constitution from forking and rotting (Single Truth Rule).

VAEL does not inherit ARCHITECTURE.md. The hand builds; it does not architect.
