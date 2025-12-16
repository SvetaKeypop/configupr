import argparse
import sys
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_args(argv):
    parser = argparse.ArgumentParser(
        prog="ucl2yaml",
        description="Транслятор учебного конфигурационного языка в YAML",
    )
    parser.add_argument(
        "-i", "--input",
        help="Путь к входному файлу с конфигурацией",
    )
    return parser.parse_args(argv)


def resolve_input_path(arg_value: str | None) -> Path:
    if arg_value:
        return Path(arg_value)

    default_path = Path(__file__).resolve().parent / "config.ucl"
    return default_path


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    input_path = resolve_input_path(args.input)

    try:
        text = read_text(input_path)
    except FileNotFoundError:
        print(
            "Ошибка: входной файл не найден.\n"
            f"Передай путь через -i/--input или создай файл по умолчанию: {input_path}",
            file=sys.stderr,
        )
        return 1
    except OSError as e:
        print(f"Ошибка чтения файла {input_path}: {e}", file=sys.stderr)
        return 1

    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
