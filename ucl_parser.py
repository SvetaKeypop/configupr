from lark import Lark, Transformer
from lark.exceptions import UnexpectedInput
import ast


class UclSyntaxError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"{message} (строка {line}, столбец {col})")
        self.message = message
        self.line = line
        self.col = col


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

_parser = Lark(_GRAMMAR, parser="lalr")


class _ToAst(Transformer):
    def document(self, items):
        defs = []
        value = None
        for x in items:
            if isinstance(x, tuple) and x and x[0] == "def":
                defs.append(x)
            else:
                value = x
        return ("document", defs, value)

    def def_stmt(self, items):
        name_tok = items[0]
        val = items[1]
        return ("def", str(name_tok), val, name_tok.line, name_tok.column)

    def number(self, items):
        return float(str(items[0]))

    def string(self, items):
        return ast.literal_eval(str(items[0]))

    def ref(self, items):
        name_tok = items[0]
        return ("ref", str(name_tok), name_tok.line, name_tok.column)

    def pair(self, items):
        key_tok = items[0]
        val = items[1]
        return (str(key_tok), val, key_tok.line, key_tok.column)

    def dict(self, items):
        d = {}
        for key, val, line, col in items:
            if key in d:
                raise UclSyntaxError(f"Повтор ключа в словаре: {key}", line, col)
            d[key] = val
        return d


def parse_text(text: str):
    try:
        tree = _parser.parse(text)
        return _ToAst().transform(tree)
    except UclSyntaxError:
        raise
    except UnexpectedInput as e:
        raise UclSyntaxError("Синтаксическая ошибка", e.line, e.column)
