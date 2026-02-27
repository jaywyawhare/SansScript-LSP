## @file analyzer.py
## @brief Diagnostics provider for SansScript documents.
##
## Reports syntax errors, indentation issues, undefined variables/functions,
## and orphaned elif/else blocks.

from __future__ import annotations

from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from .parser import ParsedDocument, TokenType, _significant_tokens, measure_indent
from .symbols import (
    BLOCK_OPENERS,
    BUILTIN_MAP,
    BUILTIN_NAMES,
    KEYWORD_NAMES,
    CONSTANT_NAMES,
    LOGICAL_OP_NAMES,
)


def _line_range(line: int, col: int = 0, end_col: int | None = None) -> Range:
    if end_col is None:
        end_col = col + 1
    return Range(
        start=Position(line=line, character=col),
        end=Position(line=line, character=end_col),
    )


def _whole_line_range(line: int, text: str) -> Range:
    return Range(
        start=Position(line=line, character=0),
        end=Position(line=line, character=len(text)),
    )


def analyze(doc: ParsedDocument) -> list[Diagnostic]:
    """@brief Produce diagnostics for a parsed SansScript document.
    @param doc  Parsed document to analyze.
    @return     List of LSP diagnostics.
    """
    diags: list[Diagnostic] = []

    _check_indentation(doc, diags)
    _check_block_structure(doc, diags)
    _check_orphaned_elif_else(doc, diags)
    _check_unmatched_parens(doc, diags)
    _check_undefined_references(doc, diags)

    return diags


def _check_indentation(doc: ParsedDocument, diags: list[Diagnostic]) -> None:
    """@brief Warn when a block opener is not followed by an indented line."""
    prev_indent = 0
    prev_is_block_opener = False

    for lineno, line in enumerate(doc.lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        indent = doc.line_indents[lineno]

        if prev_is_block_opener and indent <= prev_indent:
            diags.append(Diagnostic(
                range=_whole_line_range(lineno, line),
                message="Expected indented block after previous statement.",
                severity=DiagnosticSeverity.Warning,
            ))

        prev_indent = indent
        prev_is_block_opener = stripped.endswith(':') and _line_opens_block(stripped)


def _line_opens_block(stripped: str) -> bool:
    for kw in BLOCK_OPENERS:
        if stripped.startswith(kw):
            return True
    return False


def _check_block_structure(doc: ParsedDocument, diags: list[Diagnostic]) -> None:
    """@brief Check function definitions and block openers for structural errors."""
    for lineno, toks in enumerate(doc.tokens):
        sig = _significant_tokens(toks)
        if not sig:
            continue

        if sig[0].type == TokenType.KEYWORD and sig[0].value == "कार्यम्":
            line_text = doc.lines[lineno].strip()
            if '(' not in line_text or not line_text.endswith(':'):
                diags.append(Diagnostic(
                    range=_whole_line_range(lineno, doc.lines[lineno]),
                    message="Function definition must be: कार्यम् name(params):",
                    severity=DiagnosticSeverity.Error,
                ))
            elif ')' not in line_text:
                diags.append(Diagnostic(
                    range=_whole_line_range(lineno, doc.lines[lineno]),
                    message="Missing closing parenthesis in function definition.",
                    severity=DiagnosticSeverity.Error,
                ))

        if sig[0].type == TokenType.KEYWORD and sig[0].value in ("यदि", "यावत्", "अथवा_यदि"):
            line_text = doc.lines[lineno].strip()
            if not line_text.endswith(':'):
                diags.append(Diagnostic(
                    range=_whole_line_range(lineno, doc.lines[lineno]),
                    message=f"'{sig[0].value}' statement must end with ':'",
                    severity=DiagnosticSeverity.Error,
                ))

        if sig[0].type == TokenType.KEYWORD and sig[0].value == "अन्यथा":
            line_text = doc.lines[lineno].strip()
            if not line_text.endswith(':'):
                diags.append(Diagnostic(
                    range=_whole_line_range(lineno, doc.lines[lineno]),
                    message="'अन्यथा' must end with ':'",
                    severity=DiagnosticSeverity.Error,
                ))


def _check_orphaned_elif_else(doc: ParsedDocument, diags: list[Diagnostic]) -> None:
    """@brief Detect अथवा_यदि / अन्यथा without a preceding यदि at the same indent."""
    last_if_indent: dict[int, int] = {}

    for lineno, line in enumerate(doc.lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        indent = doc.line_indents[lineno]

        if stripped.startswith("यदि") and stripped.endswith(':'):
            last_if_indent[indent] = lineno
        elif stripped.startswith("अथवा_यदि"):
            if indent not in last_if_indent:
                diags.append(Diagnostic(
                    range=_whole_line_range(lineno, line),
                    message="'अथवा_यदि' without a preceding 'यदि' at the same indentation.",
                    severity=DiagnosticSeverity.Error,
                ))
            else:
                last_if_indent[indent] = lineno
        elif stripped.startswith("अन्यथा") and stripped.endswith(':'):
            if indent not in last_if_indent:
                diags.append(Diagnostic(
                    range=_whole_line_range(lineno, line),
                    message="'अन्यथा' without a preceding 'यदि' at the same indentation.",
                    severity=DiagnosticSeverity.Error,
                ))
            else:
                del last_if_indent[indent]
        else:
            last_if_indent.pop(indent, None)


def _check_unmatched_parens(doc: ParsedDocument, diags: list[Diagnostic]) -> None:
    """@brief Check for unmatched ( ) [ ] on each line."""
    for lineno, toks in enumerate(doc.tokens):
        paren_depth = 0
        bracket_depth = 0
        for t in toks:
            if t.type == TokenType.PAREN_OPEN:
                paren_depth += 1
            elif t.type == TokenType.PAREN_CLOSE:
                paren_depth -= 1
            elif t.type == TokenType.BRACKET_OPEN:
                bracket_depth += 1
            elif t.type == TokenType.BRACKET_CLOSE:
                bracket_depth -= 1

        if paren_depth != 0:
            diags.append(Diagnostic(
                range=_whole_line_range(lineno, doc.lines[lineno]),
                message="Unmatched parentheses on this line.",
                severity=DiagnosticSeverity.Error,
            ))
        if bracket_depth != 0:
            diags.append(Diagnostic(
                range=_whole_line_range(lineno, doc.lines[lineno]),
                message="Unmatched brackets on this line.",
                severity=DiagnosticSeverity.Error,
            ))


def _check_undefined_references(doc: ParsedDocument, diags: list[Diagnostic]) -> None:
    """@brief Warn when a called function is not defined and not a builtin."""
    for lineno, toks in enumerate(doc.tokens):
        for idx, t in enumerate(toks):
            if t.type != TokenType.IDENTIFIER:
                continue
            next_tok = _next_significant(toks, idx)
            if next_tok and next_tok.type == TokenType.PAREN_OPEN:
                name = t.value
                if (name not in doc.functions
                        and name not in BUILTIN_NAMES
                        and name not in KEYWORD_NAMES):
                    diags.append(Diagnostic(
                        range=_line_range(lineno, t.col, t.end_col),
                        message=f"Undefined function '{name}'.",
                        severity=DiagnosticSeverity.Warning,
                    ))


def _next_significant(toks: list, start_idx: int):
    """@brief Return the next non-whitespace token after start_idx, or None."""
    for t in toks[start_idx + 1:]:
        if t.type != TokenType.WHITESPACE:
            return t
    return None
