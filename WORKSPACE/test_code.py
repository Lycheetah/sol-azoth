#!/usr/bin/env python3
"""VAEL-SP Iteration 4 — Read capabilities and print current level."""
import re

path = "/home/guestpc/VAEL-SP-HARNESS/SELF/CAPABILITIES.md"

with open(path, "r") as f:
    text = f.read()

# Extract the current level line
match = re.search(r'Current Level:\s*\*\*(.+?)\*\*', text)
if match:
    print(f"VAEL-SP Current Capability: {match.group(1)}")
else:
    print("ERROR: Could not find current level in CAPABILITIES.md")

# Also extract the full ladder table
ladder_match = re.findall(r'\|\s*(\d+)\s*\|\s*(\w+)\s*\|', text)
for num, name in ladder_match:
    print(f"  Level {num}: {name}")
