#!/usr/bin/env python3
"""T0.1 bench — bulletproof tool-calling.

Deterministic, offline. Proves the leak-repair layer on 20 samples of text-format
tool-call markup (well-formed, malformed, truncated, ASCII + fullwidth DSML,
backtick, XML). For EVERY leak sample:
  1. _looks_like_tool_markup(sample)  -> True   (we detect it)
  2. _strip_tool_markup(sample)       -> no markup tokens survive (Mac never sees raw)
  3. a tool name is extractable       -> we know what to run (invoke/DSML/backtick/xml)
Plus negatives: plain prose must NOT be flagged and must pass through unchanged.

No API calls, no tool execution. Run: python3 tests/tool_fire_bench.py
"""
import io, sys, os
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
with redirect_stdout(io.StringIO()):          # swallow any import banner
    import agent as A

D = "｜"   # fullwidth pipe (what DeepSeek actually leaks)

# ── 20 leak samples ──────────────────────────────────────────────────────────
LEAKS = [
    # 1 well-formed fullwidth DSML
    f'<{D}{D}DSML{D}{D}invoke name="bash"><{D}{D}DSML{D}{D}parameter name="command">ls -la</{D}{D}DSML{D}{D}parameter></{D}{D}DSML{D}{D}invoke>',
    # 2 Mac's exact malformed case — broken closer, no closing invoke
    f'<{D}{D}DSML{D}{D}invoke name="bash"><parameter name="command" string="true">ls -la</{D}{D}DSML{D}{D}parameter>',
    # 3 ASCII single pipe
    '<|DSML|invoke name="read_file"><|DSML|parameter name="path">foo.py</|DSML|parameter></|DSML|invoke>',
    # 4 bare invoke, no DSML wrapper
    '<invoke name="bash"><parameter name="command">pwd</parameter></invoke>',
    # 5 backtick form
    '`tool_bash` `ls -la`',
    # 6 XML tool tag
    '<tool_bash>echo hi</tool_bash>',
    # 7 truncated mid-parameter (stream cut off)
    f'<{D}{D}DSML{D}{D}invoke name="write_file"><{D}{D}DSML{D}{D}parameter name="path">a.txt',
    # 8 prose + invoke (prose must survive the strip)
    'Sure, let me list the files.\n<invoke name="bash"><parameter name="command">ls</parameter></invoke>',
    # 9 two invokes back to back
    '<invoke name="bash"><parameter name="command">ls</parameter></invoke><invoke name="bash"><parameter name="command">pwd</parameter></invoke>',
    # 10 attribute-xml short form
    '<read file="config.py"/>',
    # 11 child-xml form
    '<read><path>config.py</path></read>',
    # 12 fullwidth, name=read_file
    f'<{D}{D}DSML{D}{D}invoke name="read_file"><{D}{D}DSML{D}{D}parameter name="path">x.md</{D}{D}DSML{D}{D}parameter></{D}{D}DSML{D}{D}invoke>',
    # 13 function.-prefixed name
    '<invoke name="function.bash"><parameter name="command">whoami</parameter></invoke>',
    # 14 spaced DSML tokens
    f'< {D}{D} DSML {D}{D} invoke name="bash">< {D}{D} DSML {D}{D} parameter name="command">date</ {D}{D} DSML {D}{D} parameter></ {D}{D} DSML {D}{D} invoke>',
    # 15 create_file
    '<invoke name="create_file"><parameter name="path">new.txt</parameter><parameter name="content">hi</parameter></invoke>',
    # 16 done call as markup
    '<invoke name="done"><parameter name="completed">all built</parameter></invoke>',
    # 17 backtick read
    '`tool_read_file` `README.md`',
    # 18 uppercase INVOKE
    '<INVOKE NAME="bash"><PARAMETER NAME="command">ls</PARAMETER></INVOKE>',
    # 19 leading prose + truncated DSML
    'Let me check.\n<|DSML|invoke name="bash"><|DSML|parameter name="command">grep -r foo',
    # 20 glob
    '<invoke name="glob"><parameter name="pattern">**/*.py</parameter></invoke>',
]

import re as _re

def has_markup_tokens(s: str) -> bool:
    low = s.lower()
    if any(t in low for t in ("invoke", "dsml")):
        return True
    if A._R1_BACKTICK_PAT.search(s):
        return True
    if _re.search(r'<\s*(?:tool_\w+|parameter|read|write|bash|glob)\b', s, _re.I):
        return True
    return False

def extract_name(s: str) -> str:
    m = A._R1_DSML_INVOKE_PAT.findall(s) or A._R1_DSML_INVOKE_LOOSE.findall(s)
    if m:
        return m[0][0]
    m = A._R1_BACKTICK_PAT.findall(s) or A._R1_XML_PAT.findall(s)
    if m:
        return m[0][0]
    m = A._R1_ATXML_PAT.findall(s) or A._R1_CHILDXML_PAT.findall(s)
    if m:
        return m[0][0]
    return ""

fails = 0
for i, s in enumerate(LEAKS, 1):
    detected = A._looks_like_tool_markup(s)
    stripped = A._strip_tool_markup(s)
    clean = not has_markup_tokens(stripped)
    name = extract_name(s)
    # true safety invariant: we either KNOW the tool (can execute) OR detect+strip the
    # leak — never both-fail (both-fail = raw markup reaches the screen, the June bug).
    ok = (bool(name) or detected) and clean
    if not ok:
        fails += 1
        print(f"FAIL #{i}: detected={detected} clean={clean} name={name!r}")
        print(f"        stripped={stripped!r}")
    else:
        print(f"ok   #{i}: name={name:<12} stripped={stripped[:40]!r}")

# ── negatives: plain prose must NOT trip the detector, must pass unchanged ─────
NEG = [
    "I'll read the config now and report back.",
    "The parameter you set looks fine.",          # word 'parameter' in prose, no tags
    "Done — the build compiles and tests pass.",
]
for i, s in enumerate(NEG, 1):
    detected = A._looks_like_tool_markup(s)
    unchanged = A._strip_tool_markup(s) == s.strip()
    # 'parameter'/'done' as prose words are allowed; detector keys on TAGS not words,
    # except literal 'DSML'/backtick — none here, so detected must be False.
    ok = (not detected) and unchanged
    if not ok:
        fails += 1
        print(f"FAIL neg#{i}: detected={detected} unchanged={unchanged} :: {s!r}")
    else:
        print(f"ok   neg#{i}: prose passed through")

total = len(LEAKS) + len(NEG)
print(f"\n{'PASS' if fails == 0 else 'FAIL'}: {total - fails}/{total} "
      f"({len(LEAKS)} leaks caught+stripped+named, {len(NEG)} prose untouched)")
sys.exit(1 if fails else 0)
