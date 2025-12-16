from __future__ import annotations

from typing import Any
from ucl_parser import Ref, Def


class UclEvalError(Exception):
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


def evaluate_document(ast, source_text: str):
    kind, defs, value = ast
    if kind != "document":
        raise ValueError("Ожидался document")

    env: dict[str, Any] = {}

    # def разрешены только сверху (как в грамматике): (def ...)* value
    for d in defs:
        if d.name in env:
            raise UclEvalError(f"Константа уже объявлена: {d.name}", d.line, d.col, source_text)
        env[d.name] = eval_value(d.value, env, source_text)

    return eval_value(value, env, source_text)


def eval_value(node: Any, env: dict[str, Any], source_text: str):
    if isinstance(node, (int, float, str)):
        return node

    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            out[k] = eval_value(v, env, source_text)
        return out

    if isinstance(node, Ref):
        if node.name not in env:
            raise UclEvalError(f"Неизвестная константа: {node.name}", node.line, node.col, source_text)
        return env[node.name]

    # На случай, если кто-то случайно передал Def внутрь (не по грамматике)
    if isinstance(node, Def):
        raise UclEvalError("Объявление def допустимо только в начале документа", node.line, node.col, source_text)

    raise ValueError("Неизвестный тип узла")
