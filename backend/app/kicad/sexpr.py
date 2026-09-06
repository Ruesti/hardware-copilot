"""Minimaler S-Expression-Parser/-Serialisierer für KiCad-Dateien.

Repräsentation: verschachtelte Listen; Atome sind str, Strings in
Anführungszeichen werden als Quoted (str-Subklasse) markiert, damit die
Serialisierung verlustfrei bleibt.
"""
from __future__ import annotations


class Quoted(str):
    """String, der beim Serialisieren in Anführungszeichen steht."""


def parse(text: str) -> list:
    tokens = _tokenize(text)
    pos = 0

    def read() -> object:
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        if tok == "(":
            node: list = []
            while tokens[pos] != ")":
                node.append(read())
            pos += 1
            return node
        if tok.startswith('"'):
            return Quoted(tok[1:-1].replace('\\"', '"').replace("\\\\", "\\"))
        return tok

    return read()


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif c in "()":
            tokens.append(c)
            i += 1
        elif c == '"':
            j = i + 1
            while text[j] != '"' or text[j - 1] == "\\":
                j += 1
            tokens.append(text[i:j + 1])
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in '()"':
                j += 1
            tokens.append(text[i:j])
            i = j
    return tokens


def dumps(node: object, indent: int = 0) -> str:
    if isinstance(node, Quoted):
        return '"' + str(node).replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(node, str):
        return node
    inner = " ".join(dumps(child) for child in node)
    if len(inner) <= 100:
        return f"({inner})"
    pad = "  " * (indent + 1)
    parts = [dumps(node[0]) if node else ""]
    for child in node[1:]:
        parts.append("\n" + pad + dumps(child, indent + 1))
    return "(" + parts[0] + "".join(parts[1:]) + ")"
