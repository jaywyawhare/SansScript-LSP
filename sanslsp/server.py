## @file server.py
## @brief SansScript Language Server wiring.
##
## Connects parsing, diagnostics, completion, hover, definition,
## document symbols, and semantic tokens to pygls.

from __future__ import annotations

import logging

from lsprotocol.types import (
    TEXT_DOCUMENT_COMPLETION,
    TEXT_DOCUMENT_DEFINITION,
    TEXT_DOCUMENT_DID_CHANGE,
    TEXT_DOCUMENT_DID_CLOSE,
    TEXT_DOCUMENT_DID_OPEN,
    TEXT_DOCUMENT_DOCUMENT_SYMBOL,
    TEXT_DOCUMENT_HOVER,
    TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    CompletionList,
    CompletionParams,
    DefinitionParams,
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentSymbolParams,
    Hover,
    HoverParams,
    Location,
    PublishDiagnosticsParams,
    SemanticTokens,
    SemanticTokensLegend,
    SemanticTokensParams,
)
from pygls.lsp.server import LanguageServer

from .analyzer import analyze
from .completion import provide_completions
from .definition import provide_definition
from .hover import provide_hover
from .parser import ParsedDocument, parse_document
from .semantic_tokens import SEMANTIC_TOKEN_MODIFIERS, SEMANTIC_TOKEN_TYPES, provide_semantic_tokens

log = logging.getLogger(__name__)

_doc_cache: dict[str, ParsedDocument] = {}


def _publish_diagnostics(ls: LanguageServer, uri: str, diags) -> None:
    ls.text_document_publish_diagnostics(
        PublishDiagnosticsParams(uri=uri, diagnostics=diags)
    )


def _reparse(ls: LanguageServer, uri: str, text: str) -> None:
    """@brief Parse document, cache result, and publish diagnostics."""
    doc = parse_document(text)
    _doc_cache[uri] = doc
    diags = analyze(doc)
    _publish_diagnostics(ls, uri, diags)


def get_parsed(uri: str) -> ParsedDocument | None:
    return _doc_cache.get(uri)


def create_server() -> LanguageServer:
    """@brief Create and configure the SansScript language server.
    @return Configured LanguageServer ready to start.
    """
    server = LanguageServer("sanslsp", "v0.1.0")

    @server.feature(TEXT_DOCUMENT_DID_OPEN)
    def did_open(ls: LanguageServer, params: DidOpenTextDocumentParams):
        _reparse(ls, params.text_document.uri, params.text_document.text)

    @server.feature(TEXT_DOCUMENT_DID_CHANGE)
    def did_change(ls: LanguageServer, params: DidChangeTextDocumentParams):
        if params.content_changes:
            text = params.content_changes[-1].text
            _reparse(ls, params.text_document.uri, text)

    @server.feature(TEXT_DOCUMENT_DID_CLOSE)
    def did_close(ls: LanguageServer, params: DidCloseTextDocumentParams):
        uri = params.text_document.uri
        _doc_cache.pop(uri, None)
        _publish_diagnostics(ls, uri, [])

    @server.feature(TEXT_DOCUMENT_COMPLETION)
    def completion(ls: LanguageServer, params: CompletionParams) -> CompletionList:
        doc = get_parsed(params.text_document.uri)
        if doc is None:
            return CompletionList(is_incomplete=False, items=[])
        return provide_completions(doc, params.position)

    @server.feature(TEXT_DOCUMENT_HOVER)
    def hover(ls: LanguageServer, params: HoverParams) -> Hover | None:
        doc = get_parsed(params.text_document.uri)
        if doc is None:
            return None
        return provide_hover(doc, params.position)

    @server.feature(TEXT_DOCUMENT_DEFINITION)
    def definition(ls: LanguageServer, params: DefinitionParams) -> Location | None:
        doc = get_parsed(params.text_document.uri)
        if doc is None:
            return None
        return provide_definition(doc, params.position, params.text_document.uri)

    @server.feature(TEXT_DOCUMENT_DOCUMENT_SYMBOL)
    def document_symbol(ls: LanguageServer, params: DocumentSymbolParams):
        from .definition import provide_document_symbols
        doc = get_parsed(params.text_document.uri)
        if doc is None:
            return []
        return provide_document_symbols(doc)

    @server.feature(
        TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
        SemanticTokensLegend(
            token_types=SEMANTIC_TOKEN_TYPES,
            token_modifiers=SEMANTIC_TOKEN_MODIFIERS,
        ),
    )
    def semantic_tokens_full(ls: LanguageServer, params: SemanticTokensParams) -> SemanticTokens:
        doc = get_parsed(params.text_document.uri)
        if doc is None:
            return SemanticTokens(data=[])
        return provide_semantic_tokens(doc)

    return server
