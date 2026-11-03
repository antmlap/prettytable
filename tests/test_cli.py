from __future__ import annotations

import io
import json
import tomllib
from pathlib import Path

import pytest

from prettytable.cli import main


def test_reads_csv_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO('name,city\nAlice,"New York, NY"\n'))

    assert main([]) == 0
    assert capsys.readouterr().out == (
        "+-------+--------------+\n"
        "|  name |     city     |\n"
        "+-------+--------------+\n"
        "| Alice | New York, NY |\n"
        "+-------+--------------+\n"
    )


def test_reads_single_column_csv(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("name\nAlice\n"))

    assert main([]) == 0
    assert "Alice" in capsys.readouterr().out


def test_reads_csv_from_file_with_delimiter(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    input_file = tmp_path / "table.tsv"
    input_file.write_text("name\tcity\nAlice\tParis\n", encoding="utf-8")

    assert main(["--delimiter", "\t", str(input_file)]) == 0
    output = capsys.readouterr().out
    assert "Alice" in output
    assert "Paris" in output


def test_selects_table_style(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("name,city\nAlice,Paris\n"))

    assert main(["--style", "markdown"]) == 0
    output = capsys.readouterr().out
    assert output.startswith("|")
    assert "+" not in output


def test_outputs_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("name,city\nAlice,Paris\n"))

    assert main(["--output-format", "json"]) == 0
    assert json.loads(capsys.readouterr().out) == [
        ["name", "city"],
        {"name": "Alice", "city": "Paris"},
    ]


def test_json_preserves_spaces_inside_quoted_fields(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        "sys.stdin", io.StringIO('name,city\nAlice,"  New York, NY  "\n')
    )

    assert main(["--output-format", "json"]) == 0
    assert json.loads(capsys.readouterr().out) == [
        ["name", "city"],
        {"name": "Alice", "city": "  New York, NY  "},
    ]


@pytest.mark.parametrize(
    ("args", "stdin"),
    [
        ([], ""),
        (["--delimiter", ","], ""),
    ],
)
def test_reports_input_without_header(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    args: list[str],
    stdin: str,
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))

    with pytest.raises(SystemExit, match="2"):
        main(args)

    assert "header row" in capsys.readouterr().err


def test_reports_unreadable_file(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    with pytest.raises(SystemExit, match="2"):
        main([str(tmp_path / "missing.csv")])

    assert "missing.csv" in capsys.readouterr().err


def test_reports_csv_row_with_too_many_columns(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO("name,city\nAlice,Paris,Extra\n"))

    with pytest.raises(SystemExit, match="2"):
        main([])

    error = capsys.readouterr().err
    assert "CSV row 2 has 3 columns; expected 2" in error


@pytest.mark.parametrize("header", ["", ",city", '"",city', "   ,city"])
def test_rejects_blank_headers(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    header: str,
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(f"{header}\nAlice,Paris\n"))

    with pytest.raises(SystemExit, match="2"):
        main([])

    assert "header row contains a blank column name" in capsys.readouterr().err


def test_rejects_unclosed_quoted_field(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO('name,city\nAlice,"New York\n'))

    with pytest.raises(SystemExit, match="2"):
        main([])

    assert "unexpected end of data" in capsys.readouterr().err


def test_registers_pretty_table_script() -> None:
    with open("pyproject.toml", "rb") as pyproject_file:
        project = tomllib.load(pyproject_file)

    assert project["project"]["scripts"]["pretty-table"] == "prettytable.cli:main"
    assert (
        project["project"]["urls"]["Homepage"]
        == "https://github.com/prettytable/prettytable"
    )
    assert "urls" not in project["project"]["scripts"]
