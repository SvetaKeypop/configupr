import yaml
import pytest

from ucl_parser import parse_text, UclSyntaxError
from ucl_eval import evaluate_document, UclEvalError
from main import main


def _eval(text: str):
    ast = parse_text(text)
    return evaluate_document(ast, text)


def test_number_scientific_only_ok():
    assert _eval("$[ a: 1e+0, b: -2.5e-1, c: +3.e+2, ]") == {
        "a": 1.0, "b": -0.25, "c": 300.0
    }


def test_number_without_exponent_is_error():
    with pytest.raises(UclSyntaxError):
        parse_text("$[ a: 10, ]")


def test_string_basic_and_escapes():
    obj = _eval(r'$[ s: "a\nb\t\"c\"\\", ]')
    assert obj["s"] == 'a\nb\t"c"\\'


def test_empty_dict():
    assert _eval("$[ ]") == {}


def test_dict_nested_and_trailing_comma():
    text = r"""
$[
  outer: $[
    inner: $[ a: 1e+0, ],
  ],
]
"""
    assert _eval(text) == {"outer": {"inner": {"a": 1.0}}}


def test_def_and_ref():
    text = r"""
(def pi 3.14159e+0)
$[ x: {pi}, ]
"""
    assert _eval(text) == {"x": 3.14159}


def test_ref_inside_nested_dict():
    text = r"""
(def hp 1e+2)
$[ stats: $[ hp: {hp}, ], ]
"""
    assert _eval(text) == {"stats": {"hp": 100.0}}


def test_unknown_constant_error_has_location_and_pointer():
    text = r"$[ x: {nope}, ]"
    with pytest.raises(UclEvalError) as e:
        _eval(text)
    s = str(e.value)
    assert "Неизвестная константа" in s
    assert "строка" in s and "столбец" in s
    assert "^" in s


def test_duplicate_const_error():
    text = r"""
(def a 1e+0)
(def a 2e+0)
$[ x: {a}, ]
"""
    with pytest.raises(UclEvalError) as e:
        _eval(text)
    assert "Константа уже объявлена" in str(e.value)


def test_duplicate_key_error():
    with pytest.raises(UclSyntaxError) as e:
        parse_text("$[ a: 1e+0, a: 2e+0, ]")
    assert "Повтор ключа" in str(e.value)


def test_syntax_error_missing_bracket():
    with pytest.raises(UclSyntaxError) as e:
        parse_text("$[ a: 1e+0, ")
    assert "Синтаксическая ошибка" in str(e.value)


def test_extra_text_after_value_error():
    with pytest.raises(UclSyntaxError):
        parse_text('$[ a: 1e+0, ] "лишнее"')


def test_cli_outputs_yaml(tmp_path, capsys):
    text = r"""
(def pi 3e+0)
$[ x: {pi}, y: "ok", ]
"""
    p = tmp_path / "in.ucl"
    p.write_text(text, encoding="utf-8")

    code = main(["-i", str(p)])
    out = capsys.readouterr().out

    assert code == 0
    assert yaml.safe_load(out) == {"x": 3.0, "y": "ok"}


def test_cli_missing_file(capsys):
    code = main(["-i", "no_such_file.ucl"])
    err = capsys.readouterr().err.lower()
    assert code == 1
    assert "файл не найден" in err
