#!/usr/bin/env python3
"""Print the today's progress brief.

Running this script will output the contents of `today_brief.md` to STDOUT.
"""
import pathlib, sys

def main():
    brief_path = pathlib.Path(__file__).with_name('today_brief.md')
    if not brief_path.is_file():
        sys.stderr.write(f"Error: {brief_path} not found\n")
        sys.exit(1)
    print(brief_path.read_text(encoding='utf-8'))

if __name__ == "__main__":
    main()
