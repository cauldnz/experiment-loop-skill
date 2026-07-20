"""Hand-rolled parser for a messy vendor CSV dialect.

Architecture
------------
This module implements a single-pass, whole-input **character state
machine**. The entire input string is scanned once, character by character
(with multi-character newline sequences such as ``\\r\\n`` collapsed into a
single logical transition). A small ``_State`` enum names every state the
machine can be in; each state's handler documents its invariants and the
exact transitions it may take. Precise 1-based ``(line, column)`` source
positions are tracked throughout so that malformed input can be reported
with an actionable location.

No use of the standard-library ``csv`` module, ``pandas``, or any
third-party parsing library.

Public API
----------
``ParseError`` -- raised for any malformed input, message includes a
1-based line and column.

``parse(text: str) -> list[list[str]]`` -- parse the given text into rows
of string fields.
"""

from __future__ import annotations

from enum import Enum, auto


class ParseError(Exception):
    """Raised when the input cannot be parsed as valid vendor CSV.

    Attributes:
        line: 1-based line number where the problem was detected.
        col: 1-based column number where the problem was detected.
    """

    def __init__(self, reason: str, line: int, col: int):
        self.line = line
        self.col = col
        super().__init__(f"{reason} (line {line}, column {col})")


class _State(Enum):
    """Named states of the whole-input character state machine.

    FIELD_START
        Positioned at the start of a field (either the first field of a
        row, right after a row boundary, or any later field right after a
        comma). Leading spaces/tabs are consumed here without being kept.
        When this is the *first* field attempt of a fresh row
        (``row_start_untouched`` is True) a ``#`` means "comment line" and
        an immediate newline/EOF means "blank line" -- neither produces a
        row.
    IN_UNQUOTED
        Accumulating characters of an unquoted field. Terminates on
        comma, newline, or EOF. A literal quote character here is
        malformed.
    IN_QUOTED
        Accumulating characters of a quoted field verbatim (interior
        whitespace preserved). Newlines are normalized to ``\\n``. A quote
        character transitions to QUOTE_PENDING to disambiguate an escaped
        quote from field closure.
    QUOTE_PENDING
        Just saw a ``"`` while inside a quoted field. If the next
        character is also ``"`` this is a doubled-quote escape and we
        return to IN_QUOTED. Otherwise the field is closed and we move to
        AFTER_QUOTE without consuming the next character.
    AFTER_QUOTE
        The quoted field's closing quote has been seen. Only spaces/tabs
        are permitted until the field/row terminator (comma, newline, or
        EOF); anything else is malformed.
    IN_COMMENT
        Consuming (and discarding) the remainder of a comment line, up to
        but not including its terminating newline.
    """

    FIELD_START = auto()
    IN_UNQUOTED = auto()
    IN_QUOTED = auto()
    QUOTE_PENDING = auto()
    AFTER_QUOTE = auto()
    IN_COMMENT = auto()


_BOM = "\ufeff"
_WS = (" ", "\t")


def _is_newline_start(ch: str) -> bool:
    return ch == "\r" or ch == "\n"


def _consume_newline(text: str, pos: int, line: int, col: int, n: int):
    """Consume one logical newline (\\r\\n, \\r, or \\n) at ``pos``.

    Returns the advanced (pos, line, col). Caller must have already
    verified that a newline starts at ``pos``.
    """
    if text[pos] == "\r":
        if pos + 1 < n and text[pos + 1] == "\n":
            return pos + 2, line + 1, 1
        return pos + 1, line + 1, 1
    # text[pos] == "\n"
    return pos + 1, line + 1, 1


def parse(text: str) -> list[list[str]]:
    """Parse ``text`` (already-decoded str) into a list of rows of fields.

    See module docstring for the dialect rules enforced.
    """
    n = len(text)
    pos = 0
    line = 1
    col = 1

    # A UTF-8 BOM is only legal at absolute offset zero. It is consumed
    # silently and does not occupy a column of its own.
    if n > 0 and text[0] == _BOM:
        pos = 1

    rows: list[list[str]] = []
    row: list[str] = []
    field_chars: list[str] = []
    state = _State.FIELD_START
    row_start_untouched = True
    quote_start_line = 0
    quote_start_col = 0

    def commit_field(value: str) -> None:
        row.append(value)

    def commit_row() -> None:
        rows.append(row.copy())
        row.clear()

    while pos < n:
        ch = text[pos]

        if ch == _BOM:
            raise ParseError(
                "Byte-order mark is only permitted at the start of input", line, col
            )

        if state == _State.FIELD_START:
            if ch in _WS:
                pos += 1
                col += 1
                continue
            if row_start_untouched and ch == "#":
                state = _State.IN_COMMENT
                pos += 1
                col += 1
                continue
            if row_start_untouched and _is_newline_start(ch):
                # Blank line: consume it and stay ready for a new row.
                pos, line, col = _consume_newline(text, pos, line, col, n)
                continue
            row_start_untouched = False
            if ch == '"':
                quote_start_line, quote_start_col = line, col
                field_chars = []
                state = _State.IN_QUOTED
                pos += 1
                col += 1
                continue
            if ch == ",":
                commit_field("")
                pos += 1
                col += 1
                continue
            if _is_newline_start(ch):
                commit_field("")
                commit_row()
                pos, line, col = _consume_newline(text, pos, line, col, n)
                row_start_untouched = True
                continue
            # First real character of an unquoted field.
            field_chars = [ch]
            state = _State.IN_UNQUOTED
            pos += 1
            col += 1
            continue

        if state == _State.IN_UNQUOTED:
            if ch == ",":
                commit_field("".join(field_chars).rstrip(" \t"))
                field_chars = []
                state = _State.FIELD_START
                pos += 1
                col += 1
                continue
            if _is_newline_start(ch):
                commit_field("".join(field_chars).rstrip(" \t"))
                field_chars = []
                commit_row()
                pos, line, col = _consume_newline(text, pos, line, col, n)
                state = _State.FIELD_START
                row_start_untouched = True
                continue
            if ch == '"':
                raise ParseError(
                    "Unexpected quote character inside an unquoted field",
                    line,
                    col,
                )
            field_chars.append(ch)
            pos += 1
            col += 1
            continue

        if state == _State.IN_QUOTED:
            if ch == '"':
                state = _State.QUOTE_PENDING
                pos += 1
                col += 1
                continue
            if _is_newline_start(ch):
                pos, line, col = _consume_newline(text, pos, line, col, n)
                field_chars.append("\n")
                continue
            field_chars.append(ch)
            pos += 1
            col += 1
            continue

        if state == _State.QUOTE_PENDING:
            if ch == '"':
                # Doubled quote: escaped literal quote.
                field_chars.append('"')
                state = _State.IN_QUOTED
                pos += 1
                col += 1
                continue
            # Field is closed; re-process this character in AFTER_QUOTE
            # without consuming it.
            state = _State.AFTER_QUOTE
            continue

        if state == _State.AFTER_QUOTE:
            if ch in _WS:
                pos += 1
                col += 1
                continue
            if ch == ",":
                commit_field("".join(field_chars))
                field_chars = []
                state = _State.FIELD_START
                pos += 1
                col += 1
                continue
            if _is_newline_start(ch):
                commit_field("".join(field_chars))
                field_chars = []
                commit_row()
                pos, line, col = _consume_newline(text, pos, line, col, n)
                state = _State.FIELD_START
                row_start_untouched = True
                continue
            raise ParseError(
                f"Unexpected character {ch!r} after closing quote; "
                "expected a comma or a newline",
                line,
                col,
            )

        if state == _State.IN_COMMENT:
            if _is_newline_start(ch):
                pos, line, col = _consume_newline(text, pos, line, col, n)
                state = _State.FIELD_START
                row_start_untouched = True
                continue
            pos += 1
            col += 1
            continue

    # End of input reached. Finalize any pending field/row.
    if state == _State.FIELD_START:
        if not (row_start_untouched and not row):
            commit_field("")
            commit_row()
    elif state == _State.IN_UNQUOTED:
        commit_field("".join(field_chars).rstrip(" \t"))
        commit_row()
    elif state == _State.AFTER_QUOTE or state == _State.QUOTE_PENDING:
        commit_field("".join(field_chars))
        commit_row()
    elif state == _State.IN_QUOTED:
        raise ParseError(
            "Unterminated quoted field (opening quote never closed)",
            quote_start_line,
            quote_start_col,
        )
    # IN_COMMENT at EOF: nothing to commit, comment simply ends.

    return rows
