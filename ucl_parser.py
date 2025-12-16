from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any

from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput, VisitError



class UclSyntaxError(Exception):
    def __init__(self, message: str, line: int, col: int, text: str | None = None):
        self.message = message
        self.line = line
        self.col = col
        self.text = text
        super().__init__(self._format())

    def _format(self) -> str:
        base = f"{self.message} (строка {self.line}, столбец {self.col})"
        if not self.text:
            return base

        lines = self.text.splitlines()
        if 1 <= self.line <= len(lines):
            src = lines[self.line - 1]
            caret_pos = max(1, self.col)
            pointer = " " * (caret_pos - 1) + "^"
            return base + "\n" + src + "\n" + pointer
        return base


@dataclass(frozen=True)
class Ref:
    name: str
    line: int
    col: int


@dataclass(frozen=True)
class Def:
    name: str
    value: Any
    line: int
    col: int


_GRAMMAR = r"""
?start: document

document: def_stmt* value

def_stmt: "(" "def" NAME value ")"

?value: dict
      | ref
      | SIGNED_SCI_NUMBER   -> number
      | ESCAPED_STRING      -> string

dict: "$[" [pair ("," pair)* [","]] "]"
pair: NAME ":" value

ref: "{" NAME "}"

NAME: /[a-z]+/
SIGNED_SCI_NUMBER: /[+-]?\d+\.?\d*[eE][+-]?\d+/

%import common.ESCAPED_STRING
%import common.WS
%ignore WS
"""

_PARSER = Lark(_GRAMMAR, parser="lalr", maybe_placeholders=False)



class _ToModel(Transformer):
    def document(self, items):
        defs: list[Def] = []
        value = None
        for x in items:
            if isinstance(x, Def):
                defs.append(x)
            else:
                value = x
        return ("document", defs, value)

    def def_stmt(self, items):
        name_tok = items[0]
        val = items[1]
        return Def(str(name_tok), val, name_tok.line, name_tok.column)

    def number(self, items):
        return float(str(items[0]))

    def string(self, items):
        return ast.literal_eval(str(items[0]))

    def ref(self, items):
        name_tok = items[0]
        return Ref(str(name_tok), name_tok.line, name_tok.column)

    def pair(self, items):
        key_tok = items[0]
        val = items[1]
        return (str(key_tok), val, key_tok.line, key_tok.column)

    def dict(self, items):
        pairs = []
        for it in items:
            if it is None:
                continue
            if isinstance(it, list):
                pairs.extend(it)
            else:
                pairs.append(it)

        d = {}
        for key, val, line, col in pairs:
            if key in d:
                raise UclSyntaxError(f"Повтор ключа в словаре: {key}", line, col)
            d[key] = val
        return d


def parse_text(text: str):
    try:
        tree = _PARSER.parse(text)
        return _ToModel().transform(tree)

    except VisitError as e:
        orig = e.orig_exc
        if isinstance(orig, UclSyntaxError):
            raise UclSyntaxError(orig.message, orig.line, orig.col, text)
        raise

    except UclSyntaxError as e:
        raise UclSyntaxError(e.message, e.line, e.col, text)

    except UnexpectedInput as e:
        raise UclSyntaxError("Синтаксическая ошибка", e.line, e.column, text)
