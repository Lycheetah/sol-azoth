"""
Simple LAMAGUE parser prototype.
Parses a LAMAGUE source file and prints tokenized intents.
This is a minimal example to demonstrate tooling support.
"""
import sys
import re

def tokenize(line: str):
    # Very naive tokenization: split on whitespace, keep @ and % prefixes
    tokens = []
    for part in line.strip().split():
        if part.startswith('@') or part.startswith('%'):
            tokens.append(part)
        else:
            # split on punctuation like commas, parentheses
            sub = re.split(r'([,()])', part)
            tokens.extend([s for s in sub if s])
    return tokens

def parse_file(path: str):
    try:
        with open(path, 'r') as f:
            for lineno, line in enumerate(f, 1):
                if line.strip() == '' or line.lstrip().startswith('#'):
                    continue
                tokens = tokenize(line)
                print(f"{lineno}: {tokens}")
    except FileNotFoundError:
        print(f"Error: file {path} not found", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python lamague_parser.py <source.lam>', file=sys.stderr)
        sys.exit(1)
    parse_file(sys.argv[1])
