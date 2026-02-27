## @file semantic_tokens.py
## @brief Semantic token highlighting for SansScript.

from __future__ import annotations

from lsprotocol.types import SemanticTokens

from .parser import ParsedDocument, TokenType

SEMANTIC_TOKEN_TYPES = [
    "keyword",
    "function",
    "variable",
    "number",
    "string",
    "comment",
    "operator",
    "parameter",
    "enumMember",
]

SEMANTIC_TOKEN_MODIFIERS: list[str] = [
    "declaration",
    "definition",
    "readonly",
]

_TYPE_MAP = {
    TokenType.KEYWORD: 0,
    TokenType.BUILTIN: 1,
    TokenType.IDENTIFIER: 2,
    TokenType.NUMBER: 3,
    TokenType.STRING: 4,
    TokenType.COMMENT: 5,
    TokenType.OPERATOR: 6,
    TokenType.LOGICAL_OP: 6,
    TokenType.CONSTANT: 8,
}

_SKIP = {
    TokenType.WHITESPACE,
    TokenType.PAREN_OPEN,
    TokenType.PAREN_CLOSE,
    TokenType.BRACKET_OPEN,
    TokenType.BRACKET_CLOSE,
    TokenType.COMMA,
    TokenType.COLON,
    TokenType.UNKNOWN,
}


def provide_semantic_tokens(doc: ParsedDocument) -> SemanticTokens:
    """@brief Produce the semantic tokens data array for the full document.
    @param doc  Parsed document.
    @return     SemanticTokens with the encoded data array.
    """
    data: list[int] = []
    prev_line = 0
    prev_col = 0

    param_names: set[str] = set()
    for fdef in doc.functions.values():
        for p in fdef.params:
            param_names.add(p.name)

    func_names: set[str] = set(doc.functions.keys())

    for line_tokens in doc.tokens:
        for tok in line_tokens:
            if tok.type in _SKIP:
                continue

            token_type = _TYPE_MAP.get(tok.type)
            if token_type is None:
                continue

            if tok.type == TokenType.IDENTIFIER:
                if tok.value in func_names:
                    token_type = 1
                elif tok.value in param_names:
                    token_type = 7

            length = tok.end_col - tok.col
            delta_line = tok.line - prev_line
            delta_col = tok.col if delta_line > 0 else tok.col - prev_col

            data.extend([delta_line, delta_col, length, token_type, 0])
            prev_line = tok.line
            prev_col = tok.col

    return SemanticTokens(data=data)
