## @file completion.py
## @brief Autocompletion provider for SansScript.

from __future__ import annotations

from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    InsertTextFormat,
    Position,
)

from .parser import ParsedDocument, TokenType, _significant_tokens
from .symbols import (
    BUILTIN_MAP,
    BUILTINS,
    CONSTANTS,
    KEYWORDS,
    LOGICAL_OPS,
)


def provide_completions(doc: ParsedDocument, pos: Position) -> CompletionList:
    """@brief Return completion items for the given cursor position.
    @param doc  Parsed document.
    @param pos  Cursor position.
    @return     CompletionList with keywords, builtins, user symbols, and variables.
    """
    items: list[CompletionItem] = []
    prefix = _word_at_cursor(doc, pos)
    current_scope = _current_scope(doc, pos.line)

    for kw in KEYWORDS:
        if prefix and not kw.name.startswith(prefix):
            continue
        item = CompletionItem(
            label=kw.name,
            kind=CompletionItemKind.Keyword,
            detail=f"({kw.english})",
            documentation=kw.doc,
        )
        if kw.snippet:
            item.insert_text = kw.snippet
            item.insert_text_format = InsertTextFormat.Snippet
        items.append(item)

    for bi in BUILTINS:
        if prefix and not bi.name.startswith(prefix):
            continue
        sig = f"{bi.name}({', '.join(bi.params)})"
        snippet_params = ", ".join(f"${{{i+1}:{p}}}" for i, p in enumerate(bi.params))
        items.append(CompletionItem(
            label=bi.name,
            kind=CompletionItemKind.Function,
            detail=f"{bi.english}: {sig}",
            documentation=bi.doc,
            insert_text=f"{bi.name}({snippet_params})",
            insert_text_format=InsertTextFormat.Snippet,
        ))

    for name, doc_text in CONSTANTS.items():
        if prefix and not name.startswith(prefix):
            continue
        items.append(CompletionItem(
            label=name,
            kind=CompletionItemKind.Constant,
            detail=doc_text,
        ))

    for name, doc_text in LOGICAL_OPS.items():
        if prefix and not name.startswith(prefix):
            continue
        items.append(CompletionItem(
            label=name,
            kind=CompletionItemKind.Operator,
            detail=doc_text,
        ))

    for fname, fdef in doc.functions.items():
        if prefix and not fname.startswith(prefix):
            continue
        param_names = [p.name for p in fdef.params]
        sig = f"{fname}({', '.join(param_names)})"
        snippet_params = ", ".join(f"${{{i+1}:{p}}}" for i, p in enumerate(param_names))
        items.append(CompletionItem(
            label=fname,
            kind=CompletionItemKind.Function,
            detail=f"function {sig}",
            insert_text=f"{fname}({snippet_params})",
            insert_text_format=InsertTextFormat.Snippet,
        ))

    seen_vars: set[str] = set()
    for key, vdef in doc.variables.items():
        name = vdef.name
        if name in seen_vars:
            continue
        if prefix and not name.startswith(prefix):
            continue
        if vdef.scope == "global" or vdef.scope == current_scope:
            seen_vars.add(name)
            items.append(CompletionItem(
                label=name,
                kind=CompletionItemKind.Variable,
                detail=f"variable ({vdef.scope})",
            ))

    return CompletionList(is_incomplete=False, items=items)


def _word_at_cursor(doc: ParsedDocument, pos: Position) -> str:
    """@brief Extract the partial identifier being typed at the cursor."""
    if pos.line >= len(doc.lines):
        return ""
    line = doc.lines[pos.line]
    col = min(pos.character, len(line))
    start = col
    while start > 0 and _is_ident_char(line[start - 1]):
        start -= 1
    return line[start:col]


def _is_ident_char(ch: str) -> bool:
    cp = ord(ch)
    return (
        ch == '_'
        or ('a' <= ch <= 'z')
        or ('A' <= ch <= 'Z')
        or ('0' <= ch <= '9')
        or (0x0900 <= cp <= 0x097F)
    )


def _current_scope(doc: ParsedDocument, line: int) -> str:
    """@brief Return the enclosing function name, or 'global'."""
    for fname, fdef in doc.functions.items():
        if fdef.line < line <= fdef.end_line:
            return fname
    return "global"
