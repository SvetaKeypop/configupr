import argparse
import sys
from pathlib import Path

from ucl_parser import parse_text, UclSyntaxError


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ucl2yaml",
        description="Транслятор учебного конфигурационного языка в YAML",
    )
    parser.add_argument(
        "-i", "--input",
        help="Путь к входному файлу (по умолчанию: config.ucl рядом с main.py)",
    )
    return parser.parse_args(argv)


def resolve_input_path(arg_value):
    if arg_value:
        return Path(arg_value)
    return Path(__file__).resolve().parent / "config.ucl"


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    input_path = resolve_input_path(args.input)

    try:
        text = read_text(input_path)
    except FileNotFoundError:
        print(f"Ошибка: файл не найден: {input_path}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Ошибка чтения файла {input_path}: {e}", file=sys.stderr)
        return 1

    try:
        ast = parse_text(text)
    except UclSyntaxError as e:
        print(f"{e}", file=sys.stderr)
        return 1

    print(ast)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
