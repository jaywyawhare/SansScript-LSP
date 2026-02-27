## @file hover.py
## @brief Hover information provider for SansScript.

from __future__ import annotations

from lsprotocol.types import Hover, MarkupContent, MarkupKind, Position, Range

from .parser import ParsedDocument, TokenType
from .symbols import BUILTIN_MAP, CONSTANTS, KEYWORD_MAP, LOGICAL_OPS


def provide_hover(doc: ParsedDocument, pos: Position) -> Hover | None:
    """@brief Return hover information for the token at the cursor.
    @param doc  Parsed document.
    @param pos  Cursor position.
    @return     Hover with markdown content, or None.
    """
    token = _token_at_position(doc, pos)
    if token is None:
        return None

    content: str | None = None

    if token.type == TokenType.KEYWORD:
        kw = KEYWORD_MAP.get(token.value)
        if kw:
            content = f"**{kw.name}** — `{kw.english}`\n\n{kw.doc}"

    elif token.type == TokenType.BUILTIN:
        bi = BUILTIN_MAP.get(token.value)
        if bi:
            sig = f"{bi.name}({', '.join(bi.params)})"
            content = (
                f"**{bi.name}** — `{bi.english}`\n\n"
                f"```\n{sig}\n```\n\n"
                f"{bi.doc}\n\n"
                f"Returns: `{bi.return_type}`"
            )

    elif token.type == TokenType.CONSTANT:
        desc = CONSTANTS.get(token.value)
        if desc:
            content = f"**{token.value}** — {desc}"

    elif token.type == TokenType.LOGICAL_OP:
        desc = LOGICAL_OPS.get(token.value)
        if desc:
            content = f"**{token.value}** — {desc}"

    elif token.type == TokenType.IDENTIFIER:
        if token.value in doc.functions:
            fdef = doc.functions[token.value]
            param_names = [p.name for p in fdef.params]
            sig = f"{fdef.name}({', '.join(param_names)})"
            content = f"**function** `{sig}`\n\nDefined at line {fdef.line + 1}"
        else:
            vdef = _find_variable(doc, token.value, pos.line)
            if vdef:
                content = (
                    f"**variable** `{vdef.name}`\n\n"
                    f"Scope: {vdef.scope}  \n"
                    f"First assigned: line {vdef.line + 1}"
                )

    elif token.type == TokenType.STRING:
        content = f"String literal: `{token.value}`"

    elif token.type == TokenType.NUMBER:
        content = f"Number: `{token.value}`"

    if content is None:
        return None

    return Hover(
        contents=MarkupContent(kind=MarkupKind.Markdown, value=content),
        range=Range(
            start=Position(line=token.line, character=token.col),
            end=Position(line=token.line, character=token.end_col),
        ),
    )


def _token_at_position(doc: ParsedDocument, pos: Position):
    if pos.line >= len(doc.tokens):
        return None
    for t in doc.tokens[pos.line]:
        if t.col <= pos.character < t.end_col:
            if t.type != TokenType.WHITESPACE:
                return t
    return None


def _find_variable(doc: ParsedDocument, name: str, line: int):
    """@brief Find the best-matching variable definition for a name at a given line.
    @param doc   Parsed document.
    @param name  Variable name to look up.
    @param line  Line number for scope resolution.
    @return      VarDef or None.
    """
    current_scope = "global"
    for fname, fdef in doc.functions.items():
        if fdef.line < line <= fdef.end_line:
            current_scope = fname
            break

    if current_scope != "global":
        key = f"{current_scope}:{name}"
        if key in doc.variables:
            return doc.variables[key]
    if name in doc.variables:
        return doc.variables[name]
    return None
