## @file definition.py
## @brief Go-to-definition and document symbols provider for SansScript.

from __future__ import annotations

from lsprotocol.types import (
    DocumentSymbol,
    Location,
    Position,
    Range,
    SymbolKind,
)

from .parser import ParsedDocument, TokenType


def provide_definition(
    doc: ParsedDocument, pos: Position, uri: str
) -> Location | None:
    """@brief Jump to the definition of the symbol at the cursor.
    @param doc  Parsed document.
    @param pos  Cursor position.
    @param uri  Document URI for the returned Location.
    @return     Location of the definition, or None.
    """
    token = _token_at_position(doc, pos)
    if token is None:
        return None

    if token.type not in (TokenType.IDENTIFIER, TokenType.BUILTIN):
        return None

    name = token.value

    if name in doc.functions:
        fdef = doc.functions[name]
        return Location(
            uri=uri,
            range=Range(
                start=Position(line=fdef.line, character=fdef.col),
                end=Position(line=fdef.line, character=fdef.col + len(fdef.name)),
            ),
        )

    current_scope = _current_scope(doc, pos.line)
    vdef = None
    if current_scope != "global":
        key = f"{current_scope}:{name}"
        vdef = doc.variables.get(key)
    if vdef is None:
        vdef = doc.variables.get(name)

    if vdef is not None:
        return Location(
            uri=uri,
            range=Range(
                start=Position(line=vdef.line, character=vdef.col),
                end=Position(line=vdef.line, character=vdef.col + len(vdef.name)),
            ),
        )

    return None


def provide_document_symbols(doc: ParsedDocument) -> list[DocumentSymbol]:
    """@brief Return an outline of functions and top-level variables.
    @param doc  Parsed document.
    @return     List of DocumentSymbol for the outline view.
    """
    symbols: list[DocumentSymbol] = []

    for fname, fdef in doc.functions.items():
        param_names = [p.name for p in fdef.params]
        detail = f"({', '.join(param_names)})"
        sym_range = Range(
            start=Position(line=fdef.line, character=0),
            end=Position(line=fdef.end_line, character=len(doc.lines[fdef.end_line]) if fdef.end_line < len(doc.lines) else 0),
        )
        sel_range = Range(
            start=Position(line=fdef.line, character=fdef.col),
            end=Position(line=fdef.line, character=fdef.col + len(fname)),
        )
        symbols.append(DocumentSymbol(
            name=fname,
            kind=SymbolKind.Function,
            range=sym_range,
            selection_range=sel_range,
            detail=detail,
        ))

    for key, vdef in doc.variables.items():
        if vdef.scope != "global":
            continue
        line_end = vdef.col + len(vdef.name)
        sym_range = Range(
            start=Position(line=vdef.line, character=vdef.col),
            end=Position(line=vdef.line, character=line_end),
        )
        symbols.append(DocumentSymbol(
            name=vdef.name,
            kind=SymbolKind.Variable,
            range=sym_range,
            selection_range=sym_range,
        ))

    return symbols


def _token_at_position(doc: ParsedDocument, pos: Position):
    if pos.line >= len(doc.tokens):
        return None
    for t in doc.tokens[pos.line]:
        if t.col <= pos.character < t.end_col:
            if t.type != TokenType.WHITESPACE:
                return t
    return None


def _current_scope(doc: ParsedDocument, line: int) -> str:
    for fname, fdef in doc.functions.items():
        if fdef.line < line <= fdef.end_line:
            return fname
    return "global"
