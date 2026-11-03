from __future__ import annotations

import argparse
import csv
import io
import sys
from collections.abc import Sequence
from typing import TextIO

from prettytable import PrettyTable, TableStyle


def _delimiter(value: str) -> str:
    if len(value) != 1:
        msg = "delimiter must be a single character"
        raise argparse.ArgumentTypeError(msg)
    return value


def _style(value: str) -> TableStyle:
    try:
        return TableStyle[value.upper().replace("-", "_")]
    except KeyError:
        styles = ", ".join(style.name.lower() for style in TableStyle)
        msg = f"unknown style {value!r}; choose from: {styles}"
        raise argparse.ArgumentTypeError(msg) from None


def _parse_table(source: TextIO, delimiter: str) -> PrettyTable:
    reader = csv.reader(source, delimiter=delimiter, strict=True)
    try:
        field_names = next(reader)
    except StopIteration:
        msg = "input does not contain a header row"
        raise ValueError(msg) from None

    if not field_names or any(not field_name.strip() for field_name in field_names):
        msg = "header row contains a blank column name"
        raise ValueError(msg)

    table = PrettyTable(field_names)
    for row in reader:
        if len(row) != len(field_names):
            msg = (
                f"CSV row {reader.line_num} has {len(row)} columns; "
                f"expected {len(field_names)}"
            )
            raise ValueError(msg)
        table.add_row(row)

    return table


def _read_table(input_path: str, delimiter: str) -> PrettyTable:
    if input_path == "-":
        source = io.StringIO(sys.stdin.read().removeprefix("\ufeff"), newline="")
        return _parse_table(source, delimiter)

    with open(input_path, encoding="utf-8-sig", newline="") as source:
        return _parse_table(source, delimiter)


def main(args: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Format CSV data as a readable table.")
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        metavar="FILE",
        help="CSV file to read, or - for standard input (the default)",
    )
    parser.add_argument(
        "-d",
        "--delimiter",
        type=_delimiter,
        default=",",
        help="CSV delimiter (default: comma)",
    )
    parser.add_argument(
        "--style",
        type=_style,
        default=TableStyle.DEFAULT,
        metavar="STYLE",
        help="table style (for example: single_border, markdown, msword_friendly)",
    )
    parser.add_argument(
        "--output-format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parsed_args = parser.parse_args(args)

    try:
        table = _read_table(parsed_args.input, parsed_args.delimiter)
        table.set_style(parsed_args.style)
    except (OSError, csv.Error, ValueError) as exc:
        parser.error(str(exc))

    print(table.get_formatted_string(parsed_args.output_format))
    return 0
