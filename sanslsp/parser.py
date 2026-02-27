## @file parser.py
## @brief Tokenizer and document parser for SansScript.
##
## Produces tokens, function definitions, variable assignments, and indent info
## without executing anything.

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto

from .symbols import (
    ALL_KNOWN,
    BLOCK_OPENERS,
    BUILTIN_NAMES,
    CONSTANT_NAMES,
    KEYWORD_NAMES,
    LOGICAL_OP_NAMES,
)


class TokenType(Enum):
    KEYWORD = auto()
    BUILTIN = auto()
    CONSTANT = auto()
    LOGICAL_OP = auto()
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    OPERATOR = auto()
    PAREN_OPEN = auto()
    PAREN_CLOSE = auto()
    BRACKET_OPEN = auto()
    BRACKET_CLOSE = auto()
    COMMA = auto()
    COLON = auto()
    COMMENT = auto()
    WHITESPACE = auto()
    UNKNOWN = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int
    end_col: int


@dataclass
class ParamInfo:
    name: str
    line: int
    col: int


@dataclass
class FuncDef:
    name: str
    line: int
    col: int
    end_line: int
    params: list[ParamInfo] = field(default_factory=list)
    body_indent: int = 0


@dataclass
class VarDef:
    name: str
    line: int
    col: int
    scope: str = "global"


@dataclass
class ParsedDocument:
    tokens: list[list[Token]]
    functions: dict[str, FuncDef]
    variables: dict[str, VarDef]
    line_indents: list[int]
    lines: list[str]


_IDENT_START = re.compile(r'[\u0900-\u097F_a-zA-Z]')
_IDENT_PART = re.compile(r'[\u0900-\u097F_a-zA-Z0-9\u0966-\u096F]')
_DIGIT_START = re.compile(r'[0-9\u0966-\u096F]')
_DIGIT_PART = re.compile(r'[0-9\u0966-\u096F]')

_OPERATORS_DOUBLE = {"==", "!=", "<=", ">="}
_OPERATORS_SINGLE = {"+", "-", "*", "/", "%", "=", "<", ">"}


def _is_ident_start(ch: str) -> bool:
    return bool(_IDENT_START.match(ch))


def _is_ident_part(ch: str) -> bool:
    return bool(_IDENT_PART.match(ch))


def tokenize_line(text: str, line_no: int) -> list[Token]:
    """@brief Tokenize a single line of SansScript source.
    @param text     The source line to tokenize.
    @param line_no  0-based line number.
    @return         List of tokens found on this line.
    """
    tokens: list[Token] = []
    i = 0
    length = len(text)

    while i < length:
        ch = text[i]

        if ch == '#':
            tokens.append(Token(TokenType.COMMENT, text[i:], line_no, i, length))
            break

        if ch in (' ', '\t'):
            start = i
            while i < length and text[i] in (' ', '\t'):
                i += 1
            tokens.append(Token(TokenType.WHITESPACE, text[start:i], line_no, start, i))
            continue

        if ch == '"':
            start = i
            i += 1
            while i < length and text[i] != '"':
                i += 1
            if i < length:
                i += 1
            tokens.append(Token(TokenType.STRING, text[start:i], line_no, start, i))
            continue

        if _DIGIT_START.match(ch):
            start = i
            while i < length and _DIGIT_PART.match(text[i]):
                i += 1
            tokens.append(Token(TokenType.NUMBER, text[start:i], line_no, start, i))
            continue

        if _is_ident_start(ch):
            start = i
            i += 1
            while i < length and _is_ident_part(text[i]):
                i += 1
            word = text[start:i]
            if word in KEYWORD_NAMES:
                tt = TokenType.KEYWORD
            elif word in BUILTIN_NAMES:
                tt = TokenType.BUILTIN
            elif word in CONSTANT_NAMES:
                tt = TokenType.CONSTANT
            elif word in LOGICAL_OP_NAMES:
                tt = TokenType.LOGICAL_OP
            else:
                tt = TokenType.IDENTIFIER
            tokens.append(Token(tt, word, line_no, start, i))
            continue

        if i + 1 < length and text[i:i+2] in _OPERATORS_DOUBLE:
            tokens.append(Token(TokenType.OPERATOR, text[i:i+2], line_no, i, i + 2))
            i += 2
            continue

        if ch in _OPERATORS_SINGLE:
            tokens.append(Token(TokenType.OPERATOR, ch, line_no, i, i + 1))
            i += 1
            continue

        if ch == '(':
            tokens.append(Token(TokenType.PAREN_OPEN, ch, line_no, i, i + 1))
            i += 1
            continue
        if ch == ')':
            tokens.append(Token(TokenType.PAREN_CLOSE, ch, line_no, i, i + 1))
            i += 1
            continue
        if ch == '[':
            tokens.append(Token(TokenType.BRACKET_OPEN, ch, line_no, i, i + 1))
            i += 1
            continue
        if ch == ']':
            tokens.append(Token(TokenType.BRACKET_CLOSE, ch, line_no, i, i + 1))
            i += 1
            continue
        if ch == ',':
            tokens.append(Token(TokenType.COMMA, ch, line_no, i, i + 1))
            i += 1
            continue
        if ch == ':':
            tokens.append(Token(TokenType.COLON, ch, line_no, i, i + 1))
            i += 1
            continue

        tokens.append(Token(TokenType.UNKNOWN, ch, line_no, i, i + 1))
        i += 1

    return tokens


def measure_indent(line: str) -> int:
    """@brief Count indentation in spaces (tab = 4 spaces), matching C interpreter.
    @param line  Raw source line.
    @return      Number of equivalent spaces of indentation.
    """
    indent = 0
    for ch in line:
        if ch == ' ':
            indent += 1
        elif ch == '\t':
            indent += 4
        else:
            break
    return indent


def _significant_tokens(toks: list[Token]) -> list[Token]:
    """@brief Filter out whitespace and comment tokens.
    @param toks  Token list for a line.
    @return      Tokens that carry semantic meaning.
    """
    return [t for t in toks if t.type not in (TokenType.WHITESPACE, TokenType.COMMENT)]


def parse_document(source: str) -> ParsedDocument:
    """@brief Parse a complete SansScript document.
    @param source  Full document source text.
    @return        ParsedDocument with tokens, functions, variables, and indent info.
    """
    raw_lines = source.split('\n')
    if raw_lines and raw_lines[-1] == '':
        raw_lines = raw_lines[:-1]
    if not raw_lines:
        raw_lines = ['']

    all_tokens: list[list[Token]] = []
    line_indents: list[int] = []
    functions: dict[str, FuncDef] = {}
    variables: dict[str, VarDef] = {}

    for lineno, line in enumerate(raw_lines):
        toks = tokenize_line(line, lineno)
        all_tokens.append(toks)
        line_indents.append(measure_indent(line))

    current_func: FuncDef | None = None
    func_indent: int = -1

    for lineno, toks in enumerate(all_tokens):
        sig = _significant_tokens(toks)
        if not sig:
            continue

        indent = line_indents[lineno]

        if current_func is not None:
            if indent <= func_indent:
                current_func.end_line = lineno - 1
                current_func = None
                func_indent = -1
            else:
                current_func.end_line = lineno

        if sig[0].type == TokenType.KEYWORD and sig[0].value == "कार्यम्":
            func_def = _parse_func_header(sig, lineno, indent)
            if func_def:
                functions[func_def.name] = func_def
                current_func = func_def
                func_indent = indent
                for p in func_def.params:
                    key = f"{func_def.name}:{p.name}"
                    if key not in variables:
                        variables[key] = VarDef(p.name, p.line, p.col, scope=func_def.name)
                continue

        _extract_assignment(sig, lineno, indent, variables, current_func)

    if current_func is not None:
        current_func.end_line = len(raw_lines) - 1

    return ParsedDocument(
        tokens=all_tokens,
        functions=functions,
        variables=variables,
        line_indents=line_indents,
        lines=raw_lines,
    )


def _parse_func_header(sig: list[Token], lineno: int, indent: int) -> FuncDef | None:
    """@brief Parse 'कार्यम् name(p1, p2):' from significant tokens.
    @param sig     Significant tokens on the line.
    @param lineno  0-based line number.
    @param indent  Indentation level of the definition line.
    @return        FuncDef if valid, None otherwise.
    """
    if len(sig) < 4:
        return None
    if sig[1].type != TokenType.IDENTIFIER:
        return None

    name_tok = sig[1]
    params: list[ParamInfo] = []

    paren_idx = None
    for idx, t in enumerate(sig[2:], start=2):
        if t.type == TokenType.PAREN_OPEN:
            paren_idx = idx
            break
    if paren_idx is None:
        return None

    j = paren_idx + 1
    while j < len(sig):
        if sig[j].type == TokenType.PAREN_CLOSE:
            break
        if sig[j].type == TokenType.IDENTIFIER:
            params.append(ParamInfo(sig[j].value, sig[j].line, sig[j].col))
        j += 1

    return FuncDef(
        name=name_tok.value,
        line=lineno,
        col=name_tok.col,
        end_line=lineno,
        params=params,
        body_indent=indent + 4,
    )


def _extract_assignment(
    sig: list[Token],
    lineno: int,
    indent: int,
    variables: dict[str, VarDef],
    current_func: FuncDef | None,
) -> None:
    """@brief Detect `name = expr` and record the variable if first occurrence.
    @param sig           Significant tokens on the line.
    @param lineno        0-based line number.
    @param indent        Indentation level.
    @param variables     Variable registry to update.
    @param current_func  Enclosing function, or None for global scope.
    """
    if len(sig) < 3:
        return

    if (sig[0].type == TokenType.IDENTIFIER
            and sig[1].type == TokenType.OPERATOR
            and sig[1].value == '='):
        name = sig[0].value
        scope = current_func.name if current_func else "global"
        key = f"{scope}:{name}" if current_func else name
        if key not in variables:
            variables[key] = VarDef(name, lineno, sig[0].col, scope=scope)
