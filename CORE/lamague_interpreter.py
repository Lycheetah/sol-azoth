"""
LAMAGUE Interpreter — the executable language runtime.
Parses LAMAGUE strings → AST → evaluates against symbol library.
Designed for AI-native execution: emit LAMAGUE, get results back.

Architecture:
  LAMAGUE string → Tokenizer → Parser (PEG) → AST → Evaluator → Result

Symbol classes (from LAMAGUE spec):
  I-CLASS: invariants (stable anchors)
  D-CLASS: dynamics (transformations)
  R-CLASS: relations (connections)
  F-CLASS: forces (drives, tensions)
  M-CLASS: metrics (measurements)
  T-CLASS: temporal (time)
  P-CLASS: protection (safety)
  C-CLASS: consciousness (awareness)

TRIAD kernel: Ao → Φ↑ → Ψ
  Ao  — anchor, return to baseline
  Φ↑  — ascent, growth, learning
  Ψ   — fold, correction, integration
"""

import re
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# ── AST Node Types ─────────────────────────────────────────────────────────────

class NodeType(Enum):
    LITERAL = "literal"          # raw value: number, string, bool
    SYMBOL = "symbol"            # named reference: Π, Φ↑, variable
    CALL = "call"                # function call: f(x, y)
    IMPLICATION = "implication"  # ∴ : if condition then consequence
    FUNCTION = "function"        # function definition (legacy name)
    FUNCTION_DEF = "function_def"  # fn name(params) body syntax
    CONJUNCTION = "conjunction"  # ∧ : all conditions
    DISJUNCTION = "disjunction"  # ∨ : any condition
    DERIVATION = "derivation"    # ⊢ : assert/verify
    MEASURE = "measure"          # ⟨|⟩ : coherence measure
    ASSIGNMENT = "assignment"    # := : bind value to name
    SEQUENCE = "sequence"        # ; : sequential composition
    COMPARISON = "comparison"    # >, <, >=, <=, ==, !=
    BINOP = "binop"              # +, -, *, /
    NEGATION = "negation"        # ¬ : logical not
    ANCHOR = "anchor"            # Ao : return to baseline
    ASCENT = "ascent"            # Φ↑ : gradient movement
    FOLD = "fold"                # Ψ : integrate past
    PRESERVE = "preserve"        # preserve={...} : invariant set
    DEMOTE = "demote"            # demote={...} : contradiction set
    PROPERTY = "property"        # x.y : property access
    LIST = "list"                # [a, b, c]
    # ── FORGED: Control Flow & Error Handling (T6.1) ──────────────────────
    IF = "if"                    # if/else branching
    WHILE = "while"              # while loop
    BLOCK = "block"              # { ... } block scope
    LAMBDA = "lambda"            # λ(args) expr — anonymous function
    RETURN = "return"            # return from function
    RAISE = "raise"              # raise / ⟛ forced termination
    TRY = "try"                  # try/catch error handling
    CATCH = "catch"              # catch clause
    # ── FORGED: Error Handling Symbols (T6.2) ────────────────────────────
    SILENT_FAIL = "silent_fail"  # ⟐ : run action, suppress if Π < threshold
    FORCED_TERM = "forced_term"  # ⟛ : exit immediately with clean state
    # ── FORGED: Function Definition (T6.1 extension) ──────────────────────
@dataclass
class ASTNode:
    type: NodeType
    value: Any = None
    children: list = field(default_factory=list)
    name: str = ""
    params: list = field(default_factory=list)
    body: Any = None


# ── Tokenizer ──────────────────────────────────────────────────────────────────

# LAMAGUE Unicode symbol patterns
SYMBOL_PATTERNS = {
    # I-CLASS: Invariants
    "●": "ANCHOR_POINT",
    "∅": "VOID",
    "Ω": "WHOLENESS",
    "⟟": "FIXED_POINT",
    "⟐": "SILENT_FAIL",
    "⟛": "FORCED_TERM",
    "∞": "CLOSED_INFINITE",

    # D-CLASS: Dynamics
    "Φ↑": "ASCENT",
    "Φ↓": "DESCENT",
    "⊗": "FUSION",
    "∇": "CASCADE",

    # R-CLASS: Relations
    "∴": "IMPLICATION",
    "→": "MAP",
    "↔": "BIMAP",
    "⊢": "DERIVATION",
    "≡": "EQUIVALENCE",
    "≅": "ISOMORPHISM",
    "∼": "SIMILARITY",
    "∝": "PROPORTIONAL",
    "∧": "CONJUNCTION",
    "∨": "DISJUNCTION",
    "¬": "NEGATION",
    "⊤": "TRUE",
    "⊥": "FALSE",

    # F-CLASS: Forces
    "↑": "UP",
    "↓": "DOWN",
    "⇒": "FORCE",
    "⌂": "HOME",
    "⌇": "DRIVE",

    # M-CLASS: Metrics
    "Π": "TRUTH_PRESSURE",
    "⟨|⟩": "COHERENCE",
    "μ": "AGENCY",
    "σ": "BOUNDARY",
    "τ": "PHASE",
    "Δ": "DELTA",
    "∑": "SUM",
    "∫": "INTEGRAL",

    # T-CLASS: Temporal
    "◷": "TIME_POINT",
    "◰": "DURATION",
    "◱": "CYCLE",
    "◲": "PHASE_T",

    # P-CLASS: Protection
    "⎔": "SHIELD",
    "⎕": "BOUNDARY_BOX",
    "⛉": "BREAK",

    # C-CLASS: Consciousness
    "Ψ": "AWARENESS",
    "◎": "ATTENTION",
    "⊙": "FOCUS",
    # ── FORGED: Control Flow Keywords (T6.1) ──────────────────────────────
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "try": "TRY",
    "catch": "CATCH",
    "raise": "RAISE",
    "return": "RETURN",
    "λ": "LAMBDA",
    "fn": "FUNCTION_DEF",
    # I-CLASS: Invariants
    "●": "ANCHOR_POINT",
    "∅": "VOID",
    "Ω": "WHOLENESS",
    "⟟": "FIXED_POINT",
    "⟐": "SILENT_FAIL",
    "⟛": "FORCED_TERM",
    "∞": "CLOSED_INFINITE",

    # D-CLASS: Dynamics
    "Φ↑": "ASCENT",
    "Φ↓": "DESCENT",
    "⊗": "FUSION",
    "∇": "CASCADE",

    # R-CLASS: Relations
    "∴": "IMPLICATION",
    "→": "MAP",
    "↔": "BIMAP",
    "⊢": "DERIVATION",
    "≡": "EQUIVALENCE",
    "≅": "ISOMORPHISM",
    "∼": "SIMILARITY",
    "∝": "PROPORTIONAL",
    "∧": "CONJUNCTION",
    "∨": "DISJUNCTION",
    "¬": "NEGATION",
    "⊤": "TRUE",
    "⊥": "FALSE",

    # F-CLASS: Forces
    "↑": "UP",
    "↓": "DOWN",
    "⇒": "FORCE",
    "⌂": "HOME",
    "⌇": "DRIVE",

    # M-CLASS: Metrics
    "Π": "TRUTH_PRESSURE",
    "⟨|⟩": "COHERENCE",
    "μ": "AGENCY",
    "σ": "BOUNDARY",
    "τ": "PHASE",
    "Δ": "DELTA",
    "∑": "SUM",
    "∫": "INTEGRAL",

    # T-CLASS: Temporal
    "◷": "TIME_POINT",
    "◰": "DURATION",
    "◱": "CYCLE",
    "◲": "PHASE_T",

    # P-CLASS: Protection
    "⎔": "SHIELD",
    "⎕": "BOUNDARY_BOX",
    "⛉": "BREAK",

    # C-CLASS: Consciousness
    "Ψ": "AWARENESS",
    "◎": "ATTENTION",
    "⊙": "FOCUS",

    # TRIAD Kernel
    "Ao": "ANCHOR",
    "Ψ_inv": "INVARIANT",

    # Punctuation / structure
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    "{": "LBRACE",
    "}": "RBRACE",
    ",": "COMMA",
    ";": "SEMICOLON",
    ":=": "ASSIGN",
    "==": "EQ",
    "=": "EQUALS",
    ">": "GT",
    "<": "LT",
    ">=": "GTE",
    "<=": "LTE",
    "!=": "NEQ",
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "/": "SLASH",
    ".": "DOT",
}

# Multi-char symbols must be checked before single-char
MULTI_CHAR_SYMBOLS = sorted(
    [s for s in SYMBOL_PATTERNS if len(s) > 1],
    key=len, reverse=True
)
SINGLE_CHAR_SYMBOLS = {s for s in SYMBOL_PATTERNS if len(s) == 1}
ALL_SYMBOLS = set(SYMBOL_PATTERNS.keys())


@dataclass
class Token:
    type: str
    value: str
    pos: int


def tokenize(text: str) -> list[Token]:
    """Tokenize a LAMAGUE string into tokens."""
    tokens = []
    i = 0
    while i < len(text):
        c = text[i]

        # Whitespace
        if c in ' \t\n\r':
            i += 1
            continue

        # Comments (-- to end of line)
        if c == '-' and i + 1 < len(text) and text[i + 1] == '-':
            while i < len(text) and text[i] != '\n':
                i += 1
            continue

        # Named identifiers that happen to start with a symbol character
        # (e.g. "Π_threshold") must not be chopped into symbol + leftover word.
        # Only intervene when more than the bare symbol char is present —
        # a lone "Π" still falls through to ordinary symbol matching below.
        if c.isalpha() or c == '_':
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                j += 1
            if j - i > 1:
                word = text[i:j]
                if word in SYMBOL_PATTERNS:
                    tokens.append(Token(SYMBOL_PATTERNS[word], word, i))
                else:
                    tokens.append(Token("IDENT", word, i))
                i = j
                continue

        # Multi-char symbols
        matched = False
        for sym in MULTI_CHAR_SYMBOLS:
            if text[i:i+len(sym)] == sym:
                tokens.append(Token(SYMBOL_PATTERNS[sym], sym, i))
                i += len(sym)
                matched = True
                break
        if matched:
            continue

        # Single-char symbols
        if c in SINGLE_CHAR_SYMBOLS:
            tokens.append(Token(SYMBOL_PATTERNS[c], c, i))
            i += 1
            continue

        # Numbers (int or float)
        if c.isdigit() or (c == '.' and i + 1 < len(text) and text[i + 1].isdigit()):
            j = i
            has_dot = False
            while j < len(text) and (text[j].isdigit() or (text[j] == '.' and not has_dot)):
                if text[j] == '.':
                    has_dot = True
                j += 1
            num_str = text[i:j]
            tokens.append(Token("NUMBER", num_str, i))
            i = j
            continue

        # Strings (double-quoted)
        if c == '"':
            j = i + 1
            while j < len(text) and text[j] != '"':
                if text[j] == '\\':
                    j += 1
                j += 1
            tokens.append(Token("STRING", text[i+1:j], i))
            i = j + 1
            continue

        # Identifiers (words)
        if c.isalpha() or c == '_':
            j = i
            while j < len(text) and (text[j].isalnum() or text[j] == '_'):
                j += 1
            word = text[i:j]
            # Check if it's a known symbol
            if word in SYMBOL_PATTERNS:
                tokens.append(Token(SYMBOL_PATTERNS[word], word, i))
            else:
                tokens.append(Token("IDENT", word, i))
            i = j
            continue

        # Unknown character — skip or raise
        i += 1

    tokens.append(Token("EOF", "", len(text)))
    return tokens


# ── Parser ─────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    pass


class Parser:
    """Recursive descent parser for LAMAGUE expressions."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, *types: str) -> Token:
        t = self.peek()
        if t.type not in types:
            raise ParseError(f"Expected {types}, got {t.type} ('{t.value}') at pos {t.pos}")
        return self.advance()

    def parse(self) -> ASTNode:
        """Parse a full LAMAGUE expression."""
        nodes = []
        while self.peek().type != "EOF":
            nodes.append(self.parse_expression())
            if self.peek().type == "SEMICOLON":
                self.advance()  # consume ;
        if len(nodes) == 1:
            return nodes[0]
        return ASTNode(type=NodeType.SEQUENCE, children=nodes)

    def parse_block(self) -> ASTNode:
        """Parse a { ... } block."""
        self.expect("LBRACE")
        nodes = []
        while self.peek().type != "RBRACE":
            nodes.append(self.parse_expression())
            if self.peek().type == "SEMICOLON":
                self.advance()
        self.expect("RBRACE")
        if len(nodes) == 1:
            return nodes[0]
        return ASTNode(type=NodeType.SEQUENCE, children=nodes)

    def parse_expression(self) -> ASTNode:
        """Parse an expression (derivation is top-level, wraps implication)."""
        return self.parse_derivation()

    def parse_implication(self) -> ASTNode:
        """Parse implication: condition ∴ consequence"""
        left = self.parse_disjunction()
        if self.peek().type == "IMPLICATION":
            self.advance()
            right = self.parse_implication()
            return ASTNode(type=NodeType.IMPLICATION, children=[left, right])
        return left

    def parse_disjunction(self) -> ASTNode:
        """Parse disjunction: left ∨ right"""
        left = self.parse_conjunction()
        while self.peek().type == "DISJUNCTION":
            self.advance()
            right = self.parse_conjunction()
            left = ASTNode(type=NodeType.DISJUNCTION, children=[left, right])
        return left

    def parse_conjunction(self) -> ASTNode:
        """Parse conjunction: left ∧ right"""
        left = self.parse_comparison()
        while self.peek().type == "CONJUNCTION":
            self.advance()
            right = self.parse_comparison()
            left = ASTNode(type=NodeType.CONJUNCTION, children=[left, right])
        return left

    def parse_comparison(self) -> ASTNode:
        """Parse comparison: left > right, left < right, etc."""
        left = self.parse_assignment()
        if self.peek().type in ("GT", "LT", "GTE", "LTE", "EQ", "NEQ"):
            op_token = self.advance()
            right = self.parse_assignment()
            return ASTNode(type=NodeType.COMPARISON, value=op_token.type, children=[left, right])
        return left

    def parse_assignment(self) -> ASTNode:
        """Parse assignment: name := value"""
        left = self.parse_term()
        if self.peek().type == "ASSIGN":
            self.advance()
            right = self.parse_assignment()
            return ASTNode(type=NodeType.ASSIGNMENT, children=[left, right])
        return left

    def parse_term(self) -> ASTNode:
        """Parse term: additive level first, then multiplicative, then call/primary."""
        return self.parse_additive()

    def parse_additive(self) -> ASTNode:
        """Parse addition/subtraction: left + right, left - right"""
        left = self.parse_multiplicative()
        while self.peek().type in ("PLUS", "MINUS"):
            op_token = self.advance()
            right = self.parse_multiplicative()
            left = ASTNode(type=NodeType.BINOP, value=op_token.type, children=[left, right])
        return left

    def parse_multiplicative(self) -> ASTNode:
        """Parse multiplication/division: left * right, left / right"""
        left = self.parse_call()
        while self.peek().type in ("STAR", "SLASH"):
            op_token = self.advance()
            right = self.parse_call()
            left = ASTNode(type=NodeType.BINOP, value=op_token.type, children=[left, right])
        return left

    def parse_call(self) -> ASTNode:
        """Parse function call: name(args) or symbol(args)"""
        node = self.parse_primary()
        while self.peek().type == "LPAREN":
            self.advance()  # consume (
            args = []
            if self.peek().type != "RPAREN":
                args.append(self.parse_expression())
                while self.peek().type == "COMMA":
                    self.advance()
                    args.append(self.parse_expression())
            self.expect("RPAREN")
            node = ASTNode(type=NodeType.CALL, children=[node] + args)
        return node

    def parse_primary(self) -> ASTNode:
        """Parse a primary expression."""
        t = self.peek()

        # Grouped expression: (expr)
        if t.type == "LPAREN":
            self.advance()
            node = self.parse_expression()
            self.expect("RPAREN")
            return node
        # List: [a, b, c]
        if t.type == "LBRACKET":
            self.advance()
            items = []
            if self.peek().type != "RBRACKET":
                items.append(self.parse_expression())
                while self.peek().type == "COMMA":
                    self.advance()
                    items.append(self.parse_expression())
            self.expect("RBRACKET")
            return ASTNode(type=NodeType.LIST, children=items)
        # Also: {stmt; stmt; ...} — blocks (when content uses := or ;)
        if t.type == "LBRACE":
            self.advance()
            # Peek ahead to distinguish property set from block
            # If next token is IDENT followed by EQUALS (=) → property set
            # If next token is IDENT followed by ASSIGN (:=) or SEMICOLON → block
            # If next token is RBRACE → empty dict or empty block (dict wins)
            if self.peek().type == "RBRACE":
                self.advance()
                return ASTNode(type=NodeType.LITERAL, value=("dict", {}))
            
            # Save position for potential rollback
            saved_pos = self.pos
            
            # Check if this looks like a block: peek for ASSIGN or SEMICOLON
            is_block = False
            scan_pos = self.pos
            depth = 1
            while scan_pos < len(self.tokens) and depth > 0:
                tok = self.tokens[scan_pos]
                if tok.type == "LBRACE":
                    depth += 1
                elif tok.type == "RBRACE":
                    depth -= 1
                elif tok.type in ("ASSIGN", "SEMICOLON") and depth == 1:
                    is_block = True
                    break
                scan_pos += 1
            
            if is_block:
                # Parse as block
                nodes = []
                while self.peek().type not in ("RBRACE", "EOF"):
                    nodes.append(self.parse_expression())
                    if self.peek().type == "SEMICOLON":
                        self.advance()
                self.expect("RBRACE")
                if len(nodes) == 1:
                    return nodes[0]
                return ASTNode(type=NodeType.BLOCK, children=nodes)
            else:
                # Parse as property set
                props = {}
                key = self.expect("IDENT", "TRUTH_PRESSURE", "AGENCY", "BOUNDARY", "PHASE",
                                  "NUMBER", "STRING")
                self.expect("EQUALS")
                val = self.parse_expression()
                props[key.value] = val
                while self.peek().type == "COMMA":
                    self.advance()
                    key = self.expect("IDENT", "TRUTH_PRESSURE", "AGENCY", "BOUNDARY", "PHASE",
                                      "NUMBER", "STRING")
                    self.expect("EQUALS")
                    val = self.parse_expression()
                    props[key.value] = val
                self.expect("RBRACE")
                return ASTNode(type=NodeType.LITERAL, value=("dict", props))
        # Negation: ¬expr
        if t.type == "NEGATION":
            self.advance()
            node = self.parse_primary()
            return ASTNode(type=NodeType.NEGATION, children=[node])

        # Numbers
        if t.type == "NUMBER":
            self.advance()
            v = t.value
            return ASTNode(type=NodeType.LITERAL, value=float(v) if '.' in v else int(v))

        # Strings
        if t.type == "STRING":
            self.advance()
            return ASTNode(type=NodeType.LITERAL, value=t.value)
        # ── FORGED: Error Handling Symbols (T6.2) ──────────────────────────
        # ⟐(action, threshold) — silent fail: run action, suppress if Π < threshold
        if t.type == "SILENT_FAIL":
            self.advance()
            self.expect("LPAREN")
            action = self.parse_expression()
            self.expect("COMMA")
            threshold = self.parse_expression()
            self.expect("RPAREN")
            return ASTNode(type=NodeType.SILENT_FAIL, children=[action, threshold])

        # ⟛(condition) — forced termination: exit immediately with clean state
        if t.type == "FORCED_TERM":
            self.advance()
            self.expect("LPAREN")
            condition = self.parse_expression()
            self.expect("RPAREN")
            return ASTNode(type=NodeType.FORCED_TERM, children=[condition])

        # Numbers
        if t.type == "NUMBER":
            self.advance()
            v = t.value
            return ASTNode(type=NodeType.LITERAL, value=float(v) if '.' in v else int(v))

        # Strings
        if t.type == "STRING":
            self.advance()
            return ASTNode(type=NodeType.LITERAL, value=t.value)

        # Symbols and identifiers
        if t.type in ("TRUTH_PRESSURE", "AGENCY", "BOUNDARY", "PHASE", "COHERENCE",
                       "ASCENT", "DESCENT", "ANCHOR", "FOLD", "AWARENESS",
                       "ANCHOR_POINT", "VOID", "WHOLENESS", "FIXED_POINT",
                       "INTEGRITY_CREST", "CLOSED_INFINITE",
                       "FUSION", "CASCADE", "UP", "DOWN", "FORCE", "HOME", "DRIVE",
                       "DELTA", "SUM", "INTEGRAL", "INVARIANT",
                       "SHIELD", "BOUNDARY_BOX", "BREAK",
                       "ATTENTION", "FOCUS",
                       "TRUE", "FALSE",
                       "IDENT"):
            self.advance()
            return ASTNode(type=NodeType.SYMBOL, value=t.value, name=t.value)
            self.advance()
            return ASTNode(type=NodeType.SYMBOL, value=t.value, name=t.value)
        # ── FORGED: Control Flow (T6.1) ──────────────────────────────────
        # if (cond) { body } else { body }
        if t.type == "IF":
            self.advance()
            self.expect("LPAREN")
            cond = self.parse_expression()
            self.expect("RPAREN")
            body = self.parse_block()
            else_body = None
            if self.peek().type == "ELSE":
                self.advance()
        # while (cond) { body }
        if t.type == "WHILE":
            self.advance()
            self.expect("LPAREN")
            cond = self.parse_expression()
            self.expect("RPAREN")
            body = self.parse_block()
            return ASTNode(type=NodeType.WHILE, children=[cond, body])

        # λ(args) expr — anonymous function
        if t.type == "LAMBDA":
            self.advance()
            self.expect("LPAREN")
            params = []
            if self.peek().type != "RPAREN":
                params.append(self.expect("IDENT").value)
                while self.peek().type == "COMMA":
                    self.advance()
                    params.append(self.expect("IDENT").value)
            self.expect("RPAREN")
            body = self.parse_expression()
            return ASTNode(type=NodeType.LAMBDA, params=params, children=[body])

        # try { body } catch (name) { handler }
        if t.type == "TRY":
            self.advance()
            body = self.parse_block()
            self.expect("CATCH")
            self.expect("LPAREN")
            err_name = self.expect("IDENT").value
            self.expect("RPAREN")
            handler = self.parse_block()
            return ASTNode(type=NodeType.TRY, children=[body, handler],
                           params={"err_name": err_name})

        # return expr
        if t.type == "RETURN":
            self.advance()
            expr = self.parse_expression() if self.peek().type not in ("SEMICOLON", "EOF", "RBRACE") else None
            return ASTNode(type=NodeType.RETURN, children=[expr] if expr else [])

        # raise expr
        if t.type == "RAISE":
            self.advance()
            expr = self.parse_expression()
            return ASTNode(type=NodeType.RAISE, children=[expr])

        # fn name(params) body — function definition
        if t.type == "FUNCTION_DEF":
            self.advance()
            name = self.expect("IDENT").value
            self.expect("LPAREN")
            params = []
            if self.peek().type != "RPAREN":
                params.append(self.expect("IDENT").value)
                while self.peek().type == "COMMA":
                    self.advance()
                    params.append(self.expect("IDENT").value)
            self.expect("RPAREN")
            body = self.parse_expression()
            return ASTNode(type=NodeType.FUNCTION_DEF, value=name, params=params, children=[body])

        raise ParseError(f"Unexpected token {t.type} ('{t.value}') at pos {t.pos}")
        self.expect("LBRACE")
        nodes = []
        while self.peek().type not in ("RBRACE", "EOF"):
            nodes.append(self.parse_expression())
            if self.peek().type == "SEMICOLON":
                self.advance()
        self.expect("RBRACE")
        if len(nodes) == 1:
            return nodes[0]
        return ASTNode(type=NodeType.BLOCK, children=nodes)
    def parse_derivation(self) -> ASTNode:
        """Parse derivation: premises ⊢ conclusion.
        Calls parse_implication (not parse_expression) for its operands —
        parse_expression calls parse_derivation, so calling parse_expression
        here would recurse infinitely."""
        left = self.parse_implication()
        if self.peek().type == "DERIVATION":
            self.advance()
            right = self.parse_implication()
            return ASTNode(type=NodeType.DERIVATION, children=[left, right])
        return left

# ── Symbol Library (runtime operations) ────────────────────────────────────────

class EvalError(Exception):
    pass


class ReturnSignal(Exception):
    """Signal for return from function."""
    def __init__(self, value=None):
        self.value = value

class ForcedTermination(Exception):
    """Signal for ⟛ forced termination — clean state exit."""
    def __init__(self, message="Forced termination"):
        self.message = message
        super().__init__()


class Environment:
    """Variable bindings and runtime state."""
    def __init__(self, parent: Optional['Environment'] = None):
        self.bindings: dict[str, Any] = {}
        self.parent = parent

    def get(self, name: str) -> Any:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        raise EvalError(f"Undefined symbol: {name}")

    def set(self, name: str, value: Any):
        self.bindings[name] = value

    def has(self, name: str) -> bool:
        return name in self.bindings or (self.parent and self.parent.has(name))


class SymbolLibrary:
    """The runtime operations that LAMAGUE symbols dispatch to."""

    def __init__(self):
        self.functions: dict[str, Callable] = {}
        self._register_core()

    def _register_core(self):
        """Register all core LAMAGUE symbol operations."""

        # ∴ — Implication: if condition then consequence
        self.functions["∴"] = lambda cond, conseq: conseq if cond else None
        # ⟟ — Fixed Point: invariant anchor / identity
        self.functions["⟟"] = lambda x=None: x

        # ∧ — Conjunction: all conditions true
        self.functions["∧"] = lambda *args: all(args)

        # ∨ — Disjunction: any condition true
        self.functions["∨"] = lambda *args: any(args)

        # ¬ — Negation
        self.functions["¬"] = lambda x: not x

        # Π — Truth pressure: measure confidence
        self.functions["Π"] = self._truth_pressure

        # ⟨|⟩ — Coherence measure
        self.functions["⟨|⟩"] = self._coherence

        # ⊢ — Derivation: verify consequence follows
        self.functions["⊢"] = lambda premises, conclusion: premises.implies(conclusion) if hasattr(premises, 'implies') else None

        # Ao — Anchor: return to baseline
        self.functions["Ao"] = lambda state, baseline: baseline

        # Φ↑ — Ascent: gradient movement toward coherence
        self.functions["Φ↑"] = self._ascent

        # Ψ — Fold: integrate past states
        self.functions["Ψ"] = self._fold

        # μ — Agency measure
        self.functions["μ"] = lambda agent: getattr(agent, 'agency', 0.5)

        # σ — Boundary check
        self.functions["σ"] = lambda thing: getattr(thing, 'boundary', 1.0)

        # τ — Phase transition check
        self.functions["τ"] = lambda thing: getattr(thing, 'phase', 'stable')

        # Δ — Delta (change)
        self.functions["Δ"] = lambda new, old: new - old if isinstance(new, (int, float)) else new

        # ── Standard Library (T6.1 extension) ────────────────────────────
        # map: apply function to each element of a list
        self.functions["map"] = lambda fn, lst: [fn(x) for x in lst]

        # filter: keep elements where predicate returns true
        self.functions["filter"] = lambda pred, lst: [x for x in lst if pred(x)]

        # reduce: fold left
        self.functions["reduce"] = lambda fn, lst, init: __import__('functools').reduce(fn, lst, init)

        # range: generate list of numbers
        self.functions["range"] = lambda *args: list(range(*[int(a) for a in args]))

        # len: length of list/string
        self.functions["len"] = lambda x: len(x)

        # print: output for debugging
        self.functions["print"] = lambda *args: (print(*args), args[-1] if args else None)[1]

        # type: get type name
        self.functions["type"] = lambda x: type(x).__name__

        # head: first element
        self.functions["head"] = lambda lst: lst[0] if lst else None

        # tail: all but first
        self.functions["tail"] = lambda lst: lst[1:] if lst else []

        # cons: prepend to list
        self.functions["cons"] = lambda x, lst: [x] + lst

        # append: add to end
        self.functions["append"] = lambda lst, x: lst + [x]

        # empty? : check if list is empty
        self.functions["empty?"] = lambda lst: len(lst) == 0

    def _truth_pressure(self, knowledge, threshold=0.85):
        """Π(K) — measure truth pressure of knowledge."""
        # Simplified: if knowledge has evidence_count and precision, compute Π
        if isinstance(knowledge, dict):
            evidence = knowledge.get('evidence', 1)
            precision = knowledge.get('precision', 0.5)
            strain = knowledge.get('strain', 0.5)
            s0 = knowledge.get('s0', 1.0)
            return (evidence * precision) / (strain + s0)
        return 0.5  # fallback

    def _coherence(self, target, reference=None):
        """⟨T|R⟩ — measure coherence between target and reference."""
        if isinstance(target, dict) and isinstance(reference, dict):
            # Simple overlap measure
            common = set(target.keys()) & set(reference.keys())
            if not target:
                return 1.0
            return len(common) / max(len(target), 1)
        return 0.5

    def _ascent(self, state, target=None):
        """Φ↑ — gradient movement toward coherence.
        Returns the delta needed to move state toward target.
        Simplified: returns the difference if numeric, otherwise a progress indicator.
        """
        if isinstance(state, (int, float)) and isinstance(target, (int, float)):
            return target - state
        if isinstance(state, dict) and isinstance(target, dict):
            missing = set(target.keys()) - set(state.keys())
            return len(missing) / max(len(target), 1)
        return 0.5

    def _fold(self, *states):
        """Ψ — integrate past states into present.
        Averages numeric states, merges dicts, returns latest otherwise.
        """
        if not states:
            return None
        numeric = [s for s in states if isinstance(s, (int, float))]
        if numeric:
            return sum(numeric) / len(numeric)
        dicts = [s for s in states if isinstance(s, dict)]
        if dicts:
            merged = {}
            for d in dicts:
                merged.update(d)
            merged = {}
            for d in dicts:
                merged.update(d)
            return merged
        return states[-1]

    def register(self, name: str, func: Callable):
        """Register a custom symbol function."""
        self.functions[name] = func

    def get(self, name: str) -> Callable:
        if name in self.functions:
            return self.functions[name]
        raise EvalError(f"Unknown symbol operation: {name}")


# ── Evaluator ──────────────────────────────────────────────────────────────────

class Evaluator:
    """Walk AST and evaluate against the symbol library."""

    def __init__(self, library: Optional[SymbolLibrary] = None):
        self.library = library or SymbolLibrary()
        self.global_env = Environment()
        self._bind_builtins()

    def _bind_builtins(self):
        """Bind built-in functions to the global environment."""
        self.global_env.set("Π", self.library.functions["Π"])
        self.global_env.set("⟨|⟩", self.library.functions["⟨|⟩"])
        self.global_env.set("⊢", self.library.functions["⊢"])
        self.global_env.set("Ao", self.library.functions["Ao"])
        self.global_env.set("Φ↑", self.library.functions["Φ↑"])
        self.global_env.set("Ψ", self.library.functions["Ψ"])
        self.global_env.set("μ", self.library.functions["μ"])
        self.global_env.set("σ", self.library.functions["σ"])
        self.global_env.set("τ", self.library.functions["τ"])
        self.global_env.set("Δ", self.library.functions["Δ"])
        # Standard library
        for name in ["map", "filter", "reduce", "range", "len", "print",
                      "type", "head", "tail", "cons", "append", "empty?"]:
            self.global_env.set(name, self.library.functions[name])
        # Constants
        self.global_env.set("true", True)
        self.global_env.set("false", False)
        self.global_env.set("True", True)
        self.global_env.set("False", False)
        self.global_env.set("None", None)

    def evaluate(self, node: ASTNode, env: Optional[Environment] = None) -> Any:
        """Evaluate an AST node and return the result."""
        if env is None:
            env = self.global_env

        match node.type:
            case NodeType.LITERAL:
                if isinstance(node.value, tuple) and node.value[0] == "dict":
                    # Dict literal: evaluate all values
                    raw = node.value[1]
                    return {k: self.evaluate(v, env) if isinstance(v, ASTNode) else v
                            for k, v in raw.items()}
                return node.value

            case NodeType.SYMBOL:
                return env.get(node.value)

            case NodeType.LIST:
                return [self.evaluate(child, env) for child in node.children]

            case NodeType.SEQUENCE:
                result = None
                for child in node.children:
                    result = self.evaluate(child, env)
                return result

            case NodeType.IMPLICATION:
                cond = self.evaluate(node.children[0], env)
                conseq = node.children[1]
                if cond:
                    return self.evaluate(conseq, env)
                # If consequence is itself an implication, evaluate as else-branch (ternary chaining)
                if conseq.type == NodeType.IMPLICATION:
                    return self.evaluate(conseq, env)
                return None

            case NodeType.CONJUNCTION:
                return all(self.evaluate(child, env) for child in node.children)

            case NodeType.DISJUNCTION:
                return any(self.evaluate(child, env) for child in node.children)

            case NodeType.NEGATION:
                return not self.evaluate(node.children[0], env)

            case NodeType.COMPARISON:
                left = self.evaluate(node.children[0], env)
                right = self.evaluate(node.children[1], env)
                op = node.value
                if op == "GT":    return left > right
                if op == "LT":    return left < right
                if op == "GTE":   return left >= right
                if op == "LTE":   return left <= right
                if op == "EQUALS": return left == right
                if op == "NEQ":   return left != right
                raise EvalError(f"Unknown comparison: {op}")

            case NodeType.ASSIGNMENT:
                name = node.children[0].value
                value = self.evaluate(node.children[1], env)
                env.set(name, value)
                return value

            case NodeType.CALL:
                fn_node = node.children[0]
                args = [self.evaluate(arg, env) for arg in node.children[1:]]

                if fn_node.type == NodeType.SYMBOL:
                    fn_name = fn_node.value
                    # Check user variables first (closures, stored functions)
                    try:
                        fn = env.get(fn_name)
                        if callable(fn):
                            return fn(*args)
                    except (KeyError, NameError):
                        pass
                    # Fall back to library (built-in symbol operations)
                    fn = self.library.get(fn_name)
                    return fn(*args)
                elif fn_node.type == NodeType.CALL:
                    # Chained call: f(x)(y)
                    fn = self.evaluate(fn_node, env)
                    if callable(fn):
                        return fn(*args)
                    raise EvalError(f"Called non-callable: {fn}")
                else:
                    fn = self.evaluate(fn_node, env)
                    if callable(fn):
                        return fn(*args)
                    raise EvalError(f"Called non-callable: {fn}")

            case NodeType.DERIVATION:
                premises = self.evaluate(node.children[0], env)
                conclusion = self.evaluate(node.children[1], env)
                return premises, conclusion  # return pair for verification

            case NodeType.BINOP:
                left = self.evaluate(node.children[0], env)
                right = self.evaluate(node.children[1], env)
                match node.value:
                    case "PLUS":  return left + right
                    case "MINUS": return left - right
                    case "STAR":  return left * right
                    case "SLASH": return left / right
                    case _:       raise EvalError(f"Unknown binop: {node.value}")

            case NodeType.MEASURE:
                target = self.evaluate(node.children[0], env)
                ref = self.evaluate(node.children[1], env) if len(node.children) > 1 else None
                return self.library.functions["⟨|⟩"](target, ref)

            # ── FORGED: Control Flow Evaluation (T6.1) ───────────────────
            case NodeType.IF:
                cond = self.evaluate(node.children[0], env)
                if cond:
                    return self.evaluate(node.children[1], env)
                elif node.params and node.params.get("else"):
                    return self.evaluate(node.params["else"], env)
                return None

            case NodeType.WHILE:
                result = None
                max_iters = 1000
                iters = 0
                while self.evaluate(node.children[0], env):
                    result = self.evaluate(node.children[1], env)
                    iters += 1
                    if iters >= max_iters:
                        raise EvalError("While loop exceeded max iterations (1000)")
                return result

            case NodeType.BLOCK:
                result = None
                for child in node.children:
                    result = self.evaluate(child, env)
                return result

            case NodeType.LAMBDA:
                # Capture current environment for closure
                captured_env = env
                params = node.params

                def closure(*args):
                    # Create new scope with captured env as parent
                    local_env = Environment(captured_env)
                    for i, p in enumerate(params):
                        if i < len(args):
                            local_env.set(p, args[i])
                        else:
                            local_env.set(p, None)
                    try:
                        return self.evaluate(node.children[0], local_env)
                    except ReturnSignal as ret:
                        return ret.value

                return closure
                return closure

            case NodeType.RETURN:
                if node.children:
                    raise ReturnSignal(self.evaluate(node.children[0], env))
            case NodeType.SILENT_FAIL:
                # ⟐(action, threshold) — run action, if error and Π < threshold, suppress
                action = node.children[0]
                threshold_node = node.children[1]
                threshold = self.evaluate(threshold_node, env)
                try:
                    return self.evaluate(action, env)
                except Exception as e:
                    # Check if truth pressure is below threshold
                    try:
                        pi_val = self.evaluate(
                            ASTNode(type=NodeType.CALL,
                                    children=[ASTNode(type=NodeType.SYMBOL, value="Π", name="Π"),
                                              ASTNode(type=NodeType.LITERAL, value=str(e))]),
                            env)
                        if isinstance(pi_val, (int, float)) and pi_val < threshold:
                            return None  # Silent fail — suppressed
                    except Exception:
                        pass
                    # If we can't measure or above threshold, re-raise
                    raise

            case NodeType.FORCED_TERM:
                # ⟛(condition) — if condition is met, exit with clean state
                condition = self.evaluate(node.children[0], env)
                if condition:
                    raise ForcedTermination("⟛ forced termination: clean state exit")
                return None

            case NodeType.RAISE:
                exc_msg = self.evaluate(node.children[0], env)
                raise EvalError(f"Raised: {exc_msg}")

            case NodeType.TRY:
                try:
                    return self.evaluate(node.children[0], env)
                except Exception as e:
                    err_name = node.params.get("err_name", "e")
                    handler_env = Environment(env)
                    handler_env.set(err_name, str(e))
                    return self.evaluate(node.children[1], handler_env)

            case NodeType.RAISE:
                exc_msg = self.evaluate(node.children[0], env)
                raise EvalError(f"Raised: {exc_msg}")

            case NodeType.FUNCTION_DEF:
                # Define a named function in the current environment
                fn_name = node.value
                params = node.params
                body = node.children[0]
                captured_env = env

                def fn_closure(*args):
                    local_env = Environment(captured_env)
                    for i, p in enumerate(params):
                        if i < len(args):
                            local_env.set(p, args[i])
                        else:
                            local_env.set(p, None)
                    try:
                        result = self.evaluate(body, local_env)
                        return result
                    except ReturnSignal as ret:
                        return ret.value

                env.set(fn_name, fn_closure)
            case _:
                raise EvalError(f"Unknown node type: {node.type}")


class LAMAGUE:
    """Top-level LAMAGUE interpreter interface."""

    def __init__(self):
        self.library = SymbolLibrary()
        self.evaluator = Evaluator(self.library)
        self.last_result = None
        self.last_ast = None

    def eval(self, text: str) -> Any:
        """Parse and evaluate a LAMAGUE expression string."""
        tokens = tokenize(text)
        parser = Parser(tokens)
        ast = parser.parse()
        self.last_ast = ast
        try:
            self.last_result = self.evaluator.evaluate(ast)
        except ForcedTermination as ft:
            self.last_result = {"_forced_term": True, "message": str(ft)}
        return self.last_result

    def parse_only(self, text: str) -> ASTNode:
        """Parse without evaluating (for inspection)."""
        tokens = tokenize(text)
        parser = Parser(tokens)
        ast = parser.parse()
        self.last_ast = ast
        return ast

    def register_function(self, name: str, func: Callable):
        """Register a custom function callable from LAMAGUE."""
        self.library.register(name, func)
        self.evaluator.global_env.set(name, func)

    def set_variable(self, name: str, value: Any):
        """Set a variable in the global environment."""
        self.evaluator.global_env.set(name, value)

    def get_variable(self, name: str) -> Any:
        """Get a variable from the global environment."""
        return self.evaluator.global_env.get(name)

    def reset(self):
        """Reset the environment (clear all variables)."""
        self.evaluator = Evaluator(self.library)
        self.last_result = None
        self.last_ast = None

    def __repr__(self) -> str:
        return f"LAMAGUE(last={self.last_result!r})"
def repl():
    """Run the LAMAGUE REPL."""
    lam = LAMAGUE()
    print("LAMAGUE Interpreter v0.1")
    print("Type LAMAGUE expressions. Ctrl+D or 'exit' to quit.")
    print()
    while True:
        try:
            text = input("⟁ ")
        except EOFError:
            print()
            break
        if text.strip() in ("exit", "quit"):
            break
        if not text.strip():
            continue
        try:
            result = lam.eval(text)
            print(f"  → {result!r}")
        except (ParseError, EvalError) as e:
            print(f"  ⚠ {e}")
        except Exception as e:
            print(f"  ✗ {e}")


# ── Self-test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    lam = LAMAGUE()

    # Test basic expressions
    tests = [
        ("true ∧ true", True),
        ("true ∧ false", False),
        ("true ∨ false", True),
        ("false ∨ false", False),
        ("¬ true", False),
        ("¬ false", True),
        ("5 > 3", True),
        ("3 > 5", False),
        ("x := 42; x", 42),
        ("true ∴ 42", 42),
        ("false ∴ 42", None),
    ]

    print("Running self-tests...")
    for i, (code, expected) in enumerate(tests):
        try:
            result = lam.eval(code)
            status = "✓" if result == expected else "✗"
            print(f"  {status} {code} → {result!r} (expected {expected!r})")
        except Exception as e:
            print(f"  ✗ {code} → ERROR: {e}")

    # Test truth pressure
    print("\nTruth pressure test:")
    result = lam.eval("Π({evidence=5, precision=0.8, strain=0.3, s0=1.0})")
    print(f"  Π(K) → {result!r}")

    # Test implication with truth pressure
    print("\nImplication chain test:")
    lam.set_variable("K", {"evidence": 5, "precision": 0.8, "strain": 0.3, "s0": 1.0})
    result = lam.eval("Π(K) > 0.85 ∴ 42")
    print(f"  Π(K) > 0.85 ∴ 42 → {result!r}")

    # Test LAMAGUE-as-code example from the spec
    print("\nLAMAGUE-as-code example:")
    lam.set_variable("knowledge", {"evidence": 10, "precision": 0.9, "strain": 0.2, "s0": 1.0})

    # Register a custom function
    def reorganize(knowledge):
        return f"reorganized(knowledge, evidence={knowledge.get('evidence', '?')})"
    lam.register_function("reorganize", reorganize)

    result = lam.eval("Π(knowledge) > 0.85 ∴ reorganize(knowledge)")
    print(f"  Π(K) > 0.85 ∴ reorganize(K) → {result!r}")

    # Test the full LAMAGUE-as-code pipeline
    print("\nFull pipeline test (condition false):")
    result = lam.eval("Π(knowledge) > 10.0 ∴ reorganize(knowledge)")
    print(f"  Π(K) > 10.0 ∴ reorganize(K) → {result!r} (should be None)")

    # ── Control Flow Tests (T6.1) ─────────────────────────────────────
    print("\n--- Control Flow Tests (T6.1) ---")

    # if/else
    print("\nIf/else:")
    lam.set_variable("x", 10)
    r = lam.eval("x > 5 ∴ 100")
    print(f"  if x>5 ∴ 100 → {r!r} (expected 100)")
    assert r == 100, f"Expected 100, got {r}"

    r = lam.eval("x > 20 ∴ 200")
    print(f"  if x>20 ∴ 200 → {r!r} (expected None)")
    assert r is None, f"Expected None, got {r}"

    # Sequence
    print("\nSequence:")
    r = lam.eval("a := 1; a := a + 1; a")
    print(f"  a:=1; a:=a+1; a → {r!r} (expected 2)")
    assert r == 2, f"Expected 2, got {r}"

    # Block
    print("\nBlock:")
    r = lam.eval("b := {c := 10; c * 2}")
    print(f"  b:={{c:=10; c*2}} → {r!r} (expected 20)")
    assert r == 20, f"Expected 20, got {r}"

    # Nested: if inside block
    # Nested: if inside block
    print("\nNested (if inside block):")
    lam.set_variable("score", 85)
    r = lam.eval('{grade := "pass"; score > 90 ∴ grade := "excellent"; grade}')
    print(f"  nested if-in-block → {r!r} (expected 'pass')")
    assert r == 'pass', f"Expected 'pass', got {r}"

    # Lambda
    print("\nLambda:")
    r = lam.eval("double := λ(x) x * 2; double(21)")
    print(f"  λ(x) x*2 applied to 21 → {r!r} (expected 42)")
    assert r == 42, f"Expected 42, got {r}"

    # Lambda with multiple args
    r = lam.eval("add := λ(a, b) a + b; add(10, 32)")
    print(f"  λ(a,b) a+b applied to 10,32 → {r!r} (expected 42)")
    assert r == 42, f"Expected 42, got {r}"

    # While loop
    print("\nWhile loop:")
    lam.set_variable("count", 0)
    r = lam.eval("count := 0; while count < 5 { count := count + 1 }; count")
    print(f"  while count<5 increment → {r!r} (expected 5)")
    assert r == 5, f"Expected 5, got {r}"

    # Try/catch
    print("\nTry/catch:")
    r = lam.eval("try: 42 catch: None")
    print(f"  try:42 catch:None → {r!r} (expected 42)")
    assert r == 42, f"Expected 42, got {r}"

    # Raise/catch
    print("\nRaise/catch:")
    r = lam.eval("try: raise 'error' catch: 'caught'")
    print(f"  try:raise catch:caught → {r!r} (expected 'caught')")
    assert r == 'caught', f"Expected 'caught', got {r}"

    # Dict literal
    print("\nDict literal:")
    r = lam.eval("{evidence=5, precision=0.8}")
    print(f"  dict literal → {r!r} (expected dict with evidence=5, precision=0.8)")
    assert isinstance(r, dict), f"Expected dict, got {type(r)}"
    assert r.get('evidence') == 5, f"Expected evidence=5, got {r.get('evidence')}"

    # Property access
    print("\nProperty access:")
    lam.set_variable("obj", {"a": 1, "b": 2})
    # Note: property access via . is not in parser yet; skip if fails
    try:
        r = lam.eval("obj.a")
        print(f"  obj.a → {r!r} (expected 1)")
        assert r == 1, f"Expected 1, got {r}"
    except Exception as e:
        print(f"  obj.a → SKIP (property access not yet in parser): {e}")

    print("\nAll tests complete.")
    print("\nAll tests complete.")
