# SansScript LSP

Language Server Protocol implementation for [SansScript](https://github.com/jaywyawhare/SansScript).

Provides IDE features for `.san` files in any LSP-compatible editor.

## Features

| Feature | Description |
|---------|-------------|
| Diagnostics | Missing `:`, orphaned `अथवा_यदि`/`अन्यथा`, unmatched parens, undefined functions |
| Autocompletion | Keywords with snippets, builtins with parameter placeholders, user functions, scoped variables |
| Hover | English translations for keywords, signatures for builtins and user functions, variable info |
| Go-to-definition | Jump to function definitions and variable first-assignments |
| Document symbols | Outline view of functions and top-level variables |
| Semantic highlighting | Keywords, functions, variables, numbers, strings, comments, operators, parameters, constants |

## Install

```sh
pip install -e .
```

This installs the `SansScript-LSP` command and the `SansScript_LSP` Python package.

Requires Python 3.9+ and installs `pygls` and `lsprotocol` as dependencies.

## Usage

Start the server on stdio (how LSP clients launch it):

```sh
SansScript-LSP
# or
python -m SansScript_LSP
```

### Neovim

```lua
vim.filetype.add({ extension = { san = "sanscript" } })

vim.api.nvim_create_autocmd("FileType", {
  pattern = "sanscript",
  callback = function()
    vim.lsp.start({
      name = "SansScript-LSP",
      cmd = { "SansScript-LSP" },
    })
  end,
})
```

### Emacs (eglot)

```elisp
(add-to-list 'auto-mode-alist '("\\.san\\'" . prog-mode))
(add-to-list 'eglot-server-programs '(prog-mode . ("SansScript-LSP")))
```

### VS Code

Use the [Generic LSP Client](https://marketplace.visualstudio.com/items?itemName=llllvvuu.glspc) extension:

```json
{
  "glspc.languageId": "sanscript",
  "glspc.serverCommand": "SansScript-LSP",
  "glspc.pathPattern": "**/*.san"
}
```

## Project Structure

```
SansScript_LSP/
  __init__.py
  __main__.py          # Entry point
  server.py            # LanguageServer subclass, feature wiring
  symbols.py           # Keywords, builtins, constants
  parser.py            # Tokenizer + document parser
  analyzer.py          # Diagnostics
  completion.py        # Autocompletion provider
  hover.py             # Hover information provider
  definition.py        # Go-to-definition + document symbols
  semantic_tokens.py   # Semantic token highlighting
```

## SansScript Language Reference

### Keywords

| Keyword | English | Description |
|---------|---------|-------------|
| `यदि` | if | Conditional branch |
| `अथवा_यदि` | elif | Else-if branch |
| `अन्यथा` | else | Else branch |
| `यावत्` | while | While loop |
| `कार्यम्` | function | Function definition |
| `प्रतिददाति` | return | Return from function |
| `विरम` | break | Break out of loop |
| `अनुवर्तय` | continue | Skip to next iteration |

### Builtins

| Function | English | Params |
|----------|---------|--------|
| `मुद्रय` | print | (value) |
| `निर्गम` | exit | (code) |
| `दीर्घता` | length | (value) |
| `योजय` | append | (list, element) |
| `उपपाठ` | substring | (value, start, end) |
| `अन्वेषय` | find | (haystack, needle) |
| `वर्णाङ्क` | char_code | (string) |
| `अंकवर्ण` | from_char_code | (code_point) |
| `पाठ्य` | to_string | (value) |
| `पूर्णाङ्क` | to_int | (value) |
| `पूर्णाङ्क_पाठ_से` | parse_int | (string) |
| `विभज` | split | (string, delimiter) |
| `सञ्चिका_पठ` | read_file | (path) |

### Constants and Operators

- `सत्यम्` (true), `असत्यम्` (false)
- `च` (and), `वा` (or), `न` (not)
- Arithmetic: `+` `-` `*` `/` `%`
- Comparison: `==` `!=` `<` `>` `<=` `>=`

### Example

```
कार्यम् क्रमगुणित(न्):
    यदि न् <= १:
        प्रतिददाति १
    प्रतिददाति न् * क्रमगुणित(न् - १)

मुद्रय(क्रमगुणित(१०))
```
