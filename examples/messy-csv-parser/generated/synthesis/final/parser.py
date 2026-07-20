"""Hand-rolled parser for a messy vendor CSV dialect -- synthesis loop-02.

Synthesis provenance
--------------------
This is loop-02 of the ``synthesis`` Track (model ``claude-opus-4.8``), whose
parent is ``synthesis-loop-01``. It changes no parsing behavior relative to
loop-01. It makes exactly one measured, behavior-safe API improvement driven by
loop-01 evidence (a review of the two Tracks' error APIs): ``ParseError`` now
also exposes a ``reason`` attribute -- the bare cause string, previously only
recoverable by substring-parsing the formatted message. The formatted message
and every existing attribute (``line``/``col``/``row_number``/``field_number``)
are unchanged, so all loop-01 tests pass unchanged. loop-02 additionally commits
regression tests that pin the winner's deliberate ASCII-only structural-
whitespace behavior (the under-specified edge surfaced by loop-01 union testing)
and load runnable sample fixtures.

Lineage note: loop-01 has a multi-parent lineage of ``line-regex-loop-02``
(rejected architecture) and ``track-state-machine-loop-02`` (winning
architecture). Per the independent
``gpt-5.6-terra`` judge (weighted 4.940 vs 4.745), the winning
character-state-machine architecture is kept verbatim: named ``_State``
transitions, a single ``_Scanner`` owning physical coordinates, and
``ParseError`` carrying 1-based line/column plus row/field context.

The judge found **no** rejected-track helper both necessary and
architecture-compatible: its offset-map/regex pipeline (``_physical_lines``,
``_logical_records``, ``_FIELD``, per-character ``source_offsets``) would
duplicate this scanner/state-transition responsibility and is therefore
explicitly rejected. The one narrowly-proven, architecture-neutral idea that
*is* incorporated from the rejected Track is its **non-string input guard**:
``parse(None)`` (or any non-``str``) now raises a clear
``TypeError("text must be str")`` at the public boundary instead of an opaque
``TypeError: 'NoneType' object is not subscriptable`` leaking from an internal
string slice. Evidence: ``track-line-regex/final/parser.py`` lines 161-162 and
its committed test ``test_type_error_for_non_string`` (final test_parser.py
lines 146-148), which passed in that Track. This is a boundary precondition,
not a parsing mechanism, so it changes nothing about the state machine.

Architecture (unchanged from the winning Track)
-----------------------------------------------
A single-pass, whole-input **character state machine**. The entire input
string is scanned once (with multi-character newline sequences such as
``\\r\\n`` collapsed into a single logical transition). A small ``_State``
enum names every state the machine can be in; a dedicated handler method
exists per state, and each handler's docstring records its invariants and the
transitions it may take. A ``_Scanner`` helper owns the raw cursor (character
offset, 1-based line, 1-based column) and centralizes the two primitive moves
every state needs (``advance`` over an ordinary character, ``advance_newline``
over a logical newline), so precise source positions are computed in exactly
one place instead of being duplicated across every branch.

No use of the standard-library ``csv`` module, ``pandas``, or any third-party
parsing library.

Public API
----------
``ParseError`` -- raised for any malformed input; message includes a 1-based
line and column plus the row/field index being parsed.

``parse(text: str) -> list[list[str]]`` -- parse the given text into rows of
string fields. Raises ``TypeError`` if ``text`` is not a ``str``.
"""

from __future__ import annotations

from enum import Enum, auto


class ParseError(Exception):
    """Raised when the input cannot be parsed as valid vendor CSV.

    Attributes:
        reason: the bare human-readable cause, without the coordinate suffix.
        line: 1-based line number where the problem was detected.
        col: 1-based column number where the problem was detected.
        row_number: 1-based index of the logical row being parsed.
        field_number: 1-based index of the field within that row.
    """

    def __init__(self, reason: str, line: int, col: int, row_number: int, field_number: int):
        self.reason = reason
        self.line = line
        self.col = col
        self.row_number = row_number
        self.field_number = field_number
        super().__init__(
            f"{reason} (line {line}, column {col}, row {row_number}, field {field_number})"
        )


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


class _Scanner:
    """Owns the raw cursor over the input text.

    Invariant: ``line``/``col`` always describe the position of the
    character at ``text[pos]`` (or, at end of input, the position one past
    the last character). This is the *only* class allowed to mutate
    ``pos``/``line``/``col`` -- every state handler goes through
    ``advance`` or ``advance_newline`` instead of touching them directly.
    """

    __slots__ = ("text", "n", "pos", "line", "col")

    def __init__(self, text: str, start_pos: int = 0):
        self.text = text
        self.n = len(text)
        self.pos = start_pos
        self.line = 1
        self.col = 1

    def at_eof(self) -> bool:
        return self.pos >= self.n

    def peek(self) -> str:
        """Return the character at the cursor. Caller must check at_eof()."""
        return self.text[self.pos]

    def advance(self) -> None:
        """Move past one ordinary (non-newline) character."""
        self.pos += 1
        self.col += 1

    def advance_newline(self) -> None:
        """Move past one logical newline: \\r\\n, bare \\r, or bare \\n."""
        if self.text[self.pos] == "\r" and self.pos + 1 < self.n and self.text[self.pos + 1] == "\n":
            self.pos += 2
        else:
            self.pos += 1
        self.line += 1
        self.col = 1


class _Machine:
    """Drives the state machine over one full input string."""

    def __init__(self, text: str):
        # A UTF-8 BOM is only legal at absolute offset zero. It is
        # consumed silently and does not occupy a column of its own.
        start_pos = 1 if text[:1] == _BOM else 0
        self.sc = _Scanner(text, start_pos)
        self.rows: list[list[str]] = []
        self.row: list[str] = []
        self.field_chars: list[str] = []
        self.state = _State.FIELD_START
        self.row_start_untouched = True
        self.row_number = 1
        self.field_number = 1
        self.quote_start_line = 0
        self.quote_start_col = 0

    # -- error helper --------------------------------------------------
    def _error(self, reason: str) -> ParseError:
        return ParseError(reason, self.sc.line, self.sc.col, self.row_number, self.field_number)

    # -- field/row bookkeeping ------------------------------------------
    def _commit_field(self, value: str) -> None:
        self.row.append(value)
        self.field_number += 1

    def _commit_row(self) -> None:
        self.rows.append(self.row.copy())
        self.row.clear()
        self.row_number += 1
        self.field_number = 1

    # -- per-state handlers ----------------------------------------------
    def _step_field_start(self, ch: str) -> None:
        """At the start of a field: skip padding, classify the row if needed."""
        sc = self.sc
        if ch in _WS:
            sc.advance()
            return
        if self.row_start_untouched and ch == "#":
            self.state = _State.IN_COMMENT
            sc.advance()
            return
        if self.row_start_untouched and _is_newline_start(ch):
            # Blank/whitespace-only physical line: discard, no row emitted.
            sc.advance_newline()
            return
        self.row_start_untouched = False
        if ch == '"':
            self.quote_start_line, self.quote_start_col = sc.line, sc.col
            self.field_chars = []
            self.state = _State.IN_QUOTED
            sc.advance()
            return
        if ch == ",":
            self._commit_field("")
            sc.advance()
            return
        if _is_newline_start(ch):
            self._commit_field("")
            self._commit_row()
            sc.advance_newline()
            self.row_start_untouched = True
            return
        # First real character of an unquoted field.
        self.field_chars = [ch]
        self.state = _State.IN_UNQUOTED
        sc.advance()

    def _step_in_unquoted(self, ch: str) -> None:
        """Accumulating an unquoted field; a quote here is malformed."""
        sc = self.sc
        if ch == ",":
            self._commit_field("".join(self.field_chars).rstrip(" \t"))
            self.field_chars = []
            self.state = _State.FIELD_START
            sc.advance()
            return
        if _is_newline_start(ch):
            self._commit_field("".join(self.field_chars).rstrip(" \t"))
            self.field_chars = []
            self._commit_row()
            sc.advance_newline()
            self.state = _State.FIELD_START
            self.row_start_untouched = True
            return
        if ch == '"':
            raise self._error("Unexpected quote character inside an unquoted field")
        self.field_chars.append(ch)
        sc.advance()

    def _step_in_quoted(self, ch: str) -> None:
        """Inside a quoted field: verbatim content, newlines normalized."""
        sc = self.sc
        if ch == '"':
            self.state = _State.QUOTE_PENDING
            sc.advance()
            return
        if _is_newline_start(ch):
            sc.advance_newline()
            self.field_chars.append("\n")
            return
        self.field_chars.append(ch)
        sc.advance()

    def _step_quote_pending(self, ch: str) -> None:
        """Just saw a quote inside a quoted field: escape or close?"""
        if ch == '"':
            # Doubled quote: escaped literal quote, field stays open.
            self.field_chars.append('"')
            self.state = _State.IN_QUOTED
            self.sc.advance()
            return
        # Field is closed; re-process this same character in AFTER_QUOTE
        # without consuming it (no cursor movement here).
        self.state = _State.AFTER_QUOTE

    def _step_after_quote(self, ch: str) -> None:
        """After a quoted field's closing quote: only padding, then terminator."""
        sc = self.sc
        if ch in _WS:
            sc.advance()
            return
        if ch == ",":
            self._commit_field("".join(self.field_chars))
            self.field_chars = []
            self.state = _State.FIELD_START
            sc.advance()
            return
        if _is_newline_start(ch):
            self._commit_field("".join(self.field_chars))
            self.field_chars = []
            self._commit_row()
            sc.advance_newline()
            self.state = _State.FIELD_START
            self.row_start_untouched = True
            return
        raise self._error(
            f"Unexpected character {ch!r} after closing quote; expected a comma or a newline"
        )

    def _step_in_comment(self, ch: str) -> None:
        """Discarding the remainder of a comment line."""
        sc = self.sc
        if _is_newline_start(ch):
            sc.advance_newline()
            self.state = _State.FIELD_START
            self.row_start_untouched = True
            return
        sc.advance()

    _HANDLERS = {
        _State.FIELD_START: _step_field_start,
        _State.IN_UNQUOTED: _step_in_unquoted,
        _State.IN_QUOTED: _step_in_quoted,
        _State.QUOTE_PENDING: _step_quote_pending,
        _State.AFTER_QUOTE: _step_after_quote,
        _State.IN_COMMENT: _step_in_comment,
    }

    def run(self) -> list[list[str]]:
        sc = self.sc
        while not sc.at_eof():
            ch = sc.peek()
            if ch == _BOM:
                raise self._error("Byte-order mark is only permitted at the start of input")
            self._HANDLERS[self.state](self, ch)
        self._finalize()
        return self.rows

    def _finalize(self) -> None:
        """Handle input that ends without a trailing newline."""
        if self.state == _State.FIELD_START:
            if not (self.row_start_untouched and not self.row):
                self._commit_field("")
                self._commit_row()
        elif self.state == _State.IN_UNQUOTED:
            self._commit_field("".join(self.field_chars).rstrip(" \t"))
            self._commit_row()
        elif self.state in (_State.AFTER_QUOTE, _State.QUOTE_PENDING):
            self._commit_field("".join(self.field_chars))
            self._commit_row()
        elif self.state == _State.IN_QUOTED:
            raise ParseError(
                "Unterminated quoted field (opening quote never closed)",
                self.quote_start_line,
                self.quote_start_col,
                self.row_number,
                self.field_number,
            )
        # IN_COMMENT at EOF: nothing to commit, comment simply ends.


def parse(text: str) -> list[list[str]]:
    """Parse ``text`` (already-decoded str) into a list of rows of fields.

    See module docstring for the dialect rules enforced. Raises ``TypeError``
    if ``text`` is not a ``str`` (a boundary precondition incorporated from the
    rejected line-regex Track; see module docstring for evidence).
    """
    if not isinstance(text, str):
        raise TypeError("text must be str")
    return _Machine(text).run()
