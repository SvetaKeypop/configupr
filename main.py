import argparse
import sys
from pathlib import Path

from ucl_parser import parse_text, UclSyntaxError
from ucl_eval import evaluate_document, UclEvalError


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ucl2yaml",
        description="Транслятор учебного конфигурационного языка в YAML",
    )
    parser.add_argument(
        "-i", "--input",
        help="Путь к входному файлу",
    )
    return parser.parse_args(argv)


def resolve_input_path(arg_value):
    if arg_value:
        return Path(arg_value)
    return Path(__file__).resolve().parent / "config.ucl"


def dump_yaml(obj) -> str:
    try:
        import yaml
    except ImportError:
        print("Ошибка: не установлен пакет pyyaml.", file=sys.stderr)
        raise SystemExit(1)

    return yaml.safe_dump(obj, allow_unicode=True, sort_keys=False)


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
        result_obj = evaluate_document(ast)
    except (UclSyntaxError, UclEvalError) as e:
        print(str(e), file=sys.stderr)
        return 1

    sys.stdout.write(dump_yaml(result_obj))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
