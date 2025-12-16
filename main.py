from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ucl_parser import parse_text, UclSyntaxError
from ucl_eval import evaluate_document, UclEvalError


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def dump_yaml(obj) -> str:
    import yaml
    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ucl2yaml",
        description="Транслятор учебного конфигурационного языка в YAML",
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Путь к входному файлу с конфигурацией",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    try:
        text = read_text(Path(args.input))
    except FileNotFoundError:
        print(f"Ошибка: файл не найден: {args.input}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Ошибка чтения файла {args.input}: {e}", file=sys.stderr)
        return 1

    try:
        ast = parse_text(text)
        obj = evaluate_document(ast, text)
    except (UclSyntaxError, UclEvalError) as e:
        print(str(e), file=sys.stderr)
        return 1

    sys.stdout.write(dump_yaml(obj))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
