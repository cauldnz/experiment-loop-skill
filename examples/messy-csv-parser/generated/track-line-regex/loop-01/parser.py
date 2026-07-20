"""Line-oriented parser for a permissive vendor CSV dialect."""

from __future__ import annotations

import re

__all__ = ["ParseError", "parse"]


class ParseError(ValueError):
    """Raised when input is not valid vendor CSV."""


_PHYSICAL_LINE = re.compile(r".*?(?:\r\n|\r|\n|$)", re.DOTALL)
_IGNORABLE_LINE = re.compile(r"^[ \t]*(?:#.*)?$")
_FIELD = re.compile(
    r"""
    [ \t]*
    (?:
        "(?P<quoted>(?:""|[^"])*)" [ \t]* (?P<quoted_sep>,|\Z)
      |
        (?P<plain>[^",\r\n]*) (?P<plain_sep>,|\Z)
    )
    """,
    re.VERBOSE | re.DOTALL,
)


def _location(text: str, offset: int) -> tuple[int, int]:
    """Return a one-based (line, column), treating every newline spelling once."""
    prefix = text[:offset]
    breaks = list(re.finditer(r"\r\n|\r|\n", prefix))
    line = len(breaks) + 1
    line_start = breaks[-1].end() if breaks else 0
    return line, offset - line_start + 1


def _error(text: str, offset: int, detail: str) -> ParseError:
    line, column = _location(text, offset)
    return ParseError(f"{detail} at line {line}, column {column}")


def _physical_lines(text: str):
    for match in _PHYSICAL_LINE.finditer(text):
        raw = match.group(0)
        if not raw:
            continue
        ending = re.search(r"\r\n|\r|\n\Z", raw)
        if ending:
            yield raw[: ending.start()], raw[ending.start() :], match.start()
        else:
            yield raw, "", match.start()


def _logical_records(text: str):
    parts: list[str] = []
    record_start = 0
    in_quotes = False
    opening_quote = -1

    for content, ending, offset in _physical_lines(text):
        if not in_quotes and _IGNORABLE_LINE.fullmatch(content):
            continue

        if not parts:
            record_start = offset
        parts.append(content)

        index = 0
        while index < len(content):
            if content[index] != '"':
                index += 1
                continue
            if in_quotes and index + 1 < len(content) and content[index + 1] == '"':
                index += 2
                continue
            in_quotes = not in_quotes
            if in_quotes:
                opening_quote = offset + index
            index += 1

        if in_quotes:
            if ending:
                parts.append("\n")
            continue

        yield "".join(parts), record_start
        parts.clear()

    if in_quotes:
        raise _error(text, opening_quote, "unterminated quoted field")


def _parse_record(record: str, start: int, source: str) -> list[str]:
    fields: list[str] = []
    position = 0

    while True:
        match = _FIELD.match(record, position)
        if match is None:
            raise _error(source, start + position, "malformed field")

        if match.group("quoted") is not None:
            fields.append(match.group("quoted").replace('""', '"').replace("\r\n", "\n"))
            separator = match.group("quoted_sep")
        else:
            fields.append(match.group("plain").strip(" \t"))
            separator = match.group("plain_sep")

        position = match.end()
        if separator == "":
            return fields
        if position == len(record):
            fields.append("")
            return fields


def parse(text: str) -> list[list[str]]:
    """Parse *text* and return rows while preserving ragged row widths."""
    if not isinstance(text, str):
        raise TypeError("text must be str")

    first_bom = text.find("\ufeff")
    if first_bom > 0:
        raise _error(text, first_bom, "UTF-8 BOM is only allowed at offset zero")
    if first_bom == 0:
        text = text[1:]
    later_bom = text.find("\ufeff")
    if later_bom >= 0:
        raise _error(text, later_bom, "UTF-8 BOM is only allowed at offset zero")

    return [_parse_record(record, start, text) for record, start in _logical_records(text)]
