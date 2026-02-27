## @file symbols.py
## @brief SansScript keyword, builtin, and constant definitions with documentation.

from dataclasses import dataclass, field


@dataclass
class KeywordInfo:
    name: str
    english: str
    doc: str
    snippet: str = ""


@dataclass
class BuiltinInfo:
    name: str
    english: str
    doc: str
    params: list[str] = field(default_factory=list)
    return_type: str = ""


KEYWORDS: list[KeywordInfo] = [
    KeywordInfo(
        "यदि", "if",
        "Conditional branch. Body must be indented.",
        snippet="यदि ${1:condition}:\n\t${2:body}",
    ),
    KeywordInfo(
        "अथवा_यदि", "elif",
        "Else-if branch. Must follow a यदि or another अथवा_यदि block.",
        snippet="अथवा_यदि ${1:condition}:\n\t${2:body}",
    ),
    KeywordInfo(
        "अन्यथा", "else",
        "Else branch. Must follow a यदि or अथवा_यदि block.",
        snippet="अन्यथा:\n\t${1:body}",
    ),
    KeywordInfo(
        "यावत्", "while",
        "While loop. Body must be indented.",
        snippet="यावत् ${1:condition}:\n\t${2:body}",
    ),
    KeywordInfo(
        "कार्यम्", "function",
        "Function definition. Parameters in parentheses, body indented.",
        snippet="कार्यम् ${1:name}(${2:params}):\n\t${3:body}",
    ),
    KeywordInfo(
        "प्रतिददाति", "return",
        "Return a value from a function.",
        snippet="प्रतिददाति ${1:value}",
    ),
    KeywordInfo(
        "विरम", "break",
        "Break out of the current loop.",
    ),
    KeywordInfo(
        "अनुवर्तय", "continue",
        "Skip to the next iteration of the current loop.",
    ),
]

KEYWORD_MAP: dict[str, KeywordInfo] = {kw.name: kw for kw in KEYWORDS}
KEYWORD_NAMES: set[str] = {kw.name for kw in KEYWORDS}

CONSTANTS: dict[str, str] = {
    "सत्यम्": "true  — Boolean true",
    "असत्यम्": "false — Boolean false",
}

LOGICAL_OPS: dict[str, str] = {
    "च": "and — Logical AND",
    "वा": "or  — Logical OR",
    "न": "not — Logical NOT (prefix)",
}

BUILTINS: list[BuiltinInfo] = [
    BuiltinInfo(
        "मुद्रय", "print",
        "Print a value followed by a newline.",
        params=["value"],
        return_type="none",
    ),
    BuiltinInfo(
        "निर्गम", "exit",
        "Exit the programme with the given status code.",
        params=["code"],
        return_type="none",
    ),
    BuiltinInfo(
        "दीर्घता", "length",
        "Return the length of a string (in characters) or list.",
        params=["value"],
        return_type="int",
    ),
    BuiltinInfo(
        "योजय", "append",
        "Append an element to a list (mutates the list).",
        params=["list", "element"],
        return_type="none",
    ),
    BuiltinInfo(
        "उपपाठ", "substring / sublist",
        "Return a substring (by character indices) or sublist. End is exclusive.",
        params=["value", "start", "end"],
        return_type="str|list",
    ),
    BuiltinInfo(
        "अन्वेषय", "find",
        "Find the character offset of needle in haystack (-1 if not found).",
        params=["haystack", "needle"],
        return_type="int",
    ),
    BuiltinInfo(
        "वर्णाङ्क", "char_code",
        "Return the Unicode code-point of the first character of a string.",
        params=["string"],
        return_type="int",
    ),
    BuiltinInfo(
        "अंकवर्ण", "from_char_code",
        "Return a one-character string from a Unicode code-point.",
        params=["code_point"],
        return_type="str",
    ),
    BuiltinInfo(
        "पाठ्य", "to_string",
        "Convert a value to its string representation.",
        params=["value"],
        return_type="str",
    ),
    BuiltinInfo(
        "पूर्णाङ्क", "to_int",
        "Convert a value to an integer.",
        params=["value"],
        return_type="int",
    ),
    BuiltinInfo(
        "पूर्णाङ्क_पाठ_से", "parse_int",
        "Parse an integer from a string (supports Devanagari digits).",
        params=["string"],
        return_type="int",
    ),
    BuiltinInfo(
        "विभज", "split",
        "Split a string by a delimiter, returning a list of strings.",
        params=["string", "delimiter"],
        return_type="list",
    ),
    BuiltinInfo(
        "सञ्चिका_पठ", "read_file",
        "Read the entire contents of a file as a string.",
        params=["path"],
        return_type="str",
    ),
]

BUILTIN_MAP: dict[str, BuiltinInfo] = {b.name: b for b in BUILTINS}
BUILTIN_NAMES: set[str] = {b.name for b in BUILTINS}

OPERATORS = {
    "+", "-", "*", "/", "%",
    "==", "!=", "<", ">", "<=", ">=",
    "=",
}

BLOCK_OPENERS: set[str] = {"यदि", "अथवा_यदि", "अन्यथा", "यावत्", "कार्यम्"}

CONSTANT_NAMES: set[str] = set(CONSTANTS)
LOGICAL_OP_NAMES: set[str] = set(LOGICAL_OPS)
ALL_KNOWN: set[str] = KEYWORD_NAMES | BUILTIN_NAMES | CONSTANT_NAMES | LOGICAL_OP_NAMES
