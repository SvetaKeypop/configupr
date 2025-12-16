class UclEvalError(Exception):
    def __init__(self, message: str, line: int, col: int):
        super().__init__(f"{message} (строка {line}, столбец {col})")
        self.message = message
        self.line = line
        self.col = col


def evaluate_document(ast):
    kind, defs, value = ast
    if kind != "document":
        raise ValueError("Ожидался document")

    env = {}

    for item in defs:
        if item[0] != "def":
            continue
        _, name, raw_value, line, col = item
        if name in env:
            raise UclEvalError(f"Константа уже объявлена: {name}", line, col)
        env[name] = eval_value(raw_value, env)

    return eval_value(value, env)


def eval_value(node, env):
    if isinstance(node, (int, float, str)):
        return node

    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            out[k] = eval_value(v, env)
        return out

    if isinstance(node, tuple):
        if len(node) >= 1 and node[0] == "ref":
            _, name, line, col = node
            if name not in env:
                raise UclEvalError(f"Неизвестная константа: {name}", line, col)
            return env[name]

    raise ValueError("Неизвестный узел AST")
