"""Objective tests for the synthesis loop-02 parser.

Inherits the entire loop-01 union suite verbatim (winning state-machine suite +
local shared bakeoff + non-string guard) and adds loop-02's evidence-driven
additions, all behavior-safe:

  * ``TestParseErrorReasonAttribute`` -- the measured API-clarity improvement:
    ``ParseError.reason`` exposes the bare cause; the formatted message and all
    other attributes are unchanged.
  * ``TestUnicodeWhitespacePinned`` -- pins the winner's deliberate ASCII-only
    structural-whitespace behavior for Unicode-whitespace-only lines (the
    under-specified edge surfaced by loop-01 union testing). No behavior change;
    this closes the coverage/documentation gap.
  * ``TestFixtures`` -- loads the runnable sample fixtures under ``fixtures/``.

Run with: python test_parser.py
"""

import re
import unittest
from pathlib import Path

from parser import ParseError, parse


# ---------------------------------------------------------------------------
# Winning track-state-machine loop-02 suite (reproduced verbatim)
# ---------------------------------------------------------------------------
class TestBasicShapeAndAPI(unittest.TestCase):
    def test_empty_input_returns_no_rows(self):
        self.assertEqual(parse(""), [])

    def test_simple_two_row(self):
        self.assertEqual(parse("a,b,c\n1,2,3\n"), [["a", "b", "c"], ["1", "2", "3"]])

    def test_no_trailing_newline(self):
        self.assertEqual(parse("a,b,c"), [["a", "b", "c"]])


class TestBomCommentsBlanks(unittest.TestCase):
    def test_bom_at_start_is_stripped(self):
        text = "\ufeffa,b\n1,2\n"
        self.assertEqual(parse(text), [["a", "b"], ["1", "2"]])

    def test_comment_lines_ignored(self):
        text = "# a comment\na,b\n   # indented comment\n1,2\n"
        self.assertEqual(parse(text), [["a", "b"], ["1", "2"]])

    def test_blank_lines_ignored(self):
        text = "a,b\n\n   \n\t\n1,2\n"
        self.assertEqual(parse(text), [["a", "b"], ["1", "2"]])

    def test_bom_comments_and_blanks_combined(self):
        text = "\ufeff# header comment\n\na,b,c\n\n# mid comment\n1,2,3\n"
        self.assertEqual(parse(text), [["a", "b", "c"], ["1", "2", "3"]])

    def test_hash_not_at_start_of_line_is_literal(self):
        # '#' only introduces a comment when it is the first non-whitespace
        # character of the physical line -- not mid-field.
        self.assertEqual(parse("a#b,c\n"), [["a#b", "c"]])

    def test_comment_with_no_trailing_newline_at_eof(self):
        self.assertEqual(parse("a,b\n#trailing comment"), [["a", "b"]])

    def test_comment_only_file_produces_no_rows(self):
        self.assertEqual(parse("# just a comment\n"), [])

    def test_all_blank_and_comment_file_produces_no_rows(self):
        self.assertEqual(parse("\n \n#c\n\t\n"), [])

    def test_comment_immediately_after_bom_no_blank_line(self):
        self.assertEqual(parse("\ufeff#comment\na,b\n"), [["a", "b"]])


class TestQuotedFields(unittest.TestCase):
    def test_quoted_comma(self):
        self.assertEqual(parse('a,"b,c",d\n'), [["a", "b,c", "d"]])

    def test_embedded_lf(self):
        self.assertEqual(parse('a,"line1\nline2",b\n'), [["a", "line1\nline2", "b"]])

    def test_embedded_crlf_normalized(self):
        self.assertEqual(
            parse('a,"line1\r\nline2",b\n'), [["a", "line1\nline2", "b"]]
        )

    def test_embedded_bare_cr_normalized(self):
        self.assertEqual(
            parse('a,"line1\rline2",b\n'), [["a", "line1\nline2", "b"]]
        )

    def test_doubled_quote_escape(self):
        self.assertEqual(parse('a,"He said ""hi""",b\n'), [["a", 'He said "hi"', "b"]])

    def test_comment_and_blank_look_alikes_retained_inside_quotes(self):
        text = 'a,"# not a comment\n\nstill quoted",b\n'
        self.assertEqual(
            parse(text), [["a", "# not a comment\n\nstill quoted", "b"]]
        )

    def test_quoted_field_padding_spaces_trimmed_outside_quotes(self):
        text = 'a,  "value"  ,b\n'
        self.assertEqual(parse(text), [["a", "value", "b"]])

    def test_quoted_field_preserves_interior_whitespace(self):
        text = 'a,"  spaced out  ",b\n'
        self.assertEqual(parse(text), [["a", "  spaced out  ", "b"]])

    def test_empty_quoted_pair(self):
        self.assertEqual(parse('"",""\n'), [["", ""]])

    def test_quoted_field_flush_at_eof_without_trailing_delimiter(self):
        self.assertEqual(parse('a,"b"'), [["a", "b"]])

    def test_quote_immediately_reopened_yields_literal_quote_field(self):
        # '""""' == open, doubled-quote (one literal '"'), close.
        self.assertEqual(parse('a,"""",b\n'), [["a", '"', "b"]])

    def test_quoted_field_then_eof_right_after_comma(self):
        self.assertEqual(parse('a,"b",'), [["a", "b", ""]])


class TestRaggedRowsAndEmptyFields(unittest.TestCase):
    def test_ragged_rows_preserved(self):
        text = "a,b,c\n1,2\nx,y,z,w\n"
        self.assertEqual(
            parse(text), [["a", "b", "c"], ["1", "2"], ["x", "y", "z", "w"]]
        )

    def test_many_ragged_rows(self):
        text = "a\nb,c\nd,e,f\ng\n"
        self.assertEqual(parse(text), [["a"], ["b", "c"], ["d", "e", "f"], ["g"]])

    def test_empty_fields_and_trailing_comma(self):
        text = "a,,b,\n"
        self.assertEqual(parse(text), [["a", "", "b", ""]])

    def test_leading_comma_produces_empty_first_field(self):
        text = ",a\n"
        self.assertEqual(parse(text), [["", "a"]])

    def test_lone_comma_row(self):
        text = ",\n"
        self.assertEqual(parse(text), [["", ""]])


class TestTrimming(unittest.TestCase):
    def test_unquoted_surrounding_whitespace_trimmed(self):
        text = "  a  ,  b b  ,c\n"
        self.assertEqual(parse(text), [["a", "b b", "c"]])

    def test_unquoted_all_whitespace_field_becomes_empty(self):
        text = "a,   ,b\n"
        self.assertEqual(parse(text), [["a", "", "b"]])

    def test_unquoted_tabs_only_field_becomes_empty(self):
        text = "a,\t \t,b\n"
        self.assertEqual(parse(text), [["a", "", "b"]])

    def test_non_trim_whitespace_chars_preserved_in_unquoted_field(self):
        # Vertical tab / form feed are not part of the trim set (only
        # space and tab are); they must be preserved as literal content.
        text = "a,\x0bx\x0c,b\n"
        self.assertEqual(parse(text), [["a", "\x0bx\x0c", "b"]])


class TestCrOnlyLines(unittest.TestCase):
    def test_cr_only_physical_lines(self):
        text = "a,b\r1,2\r"
        self.assertEqual(parse(text), [["a", "b"], ["1", "2"]])

    def test_mixed_crlf_and_lf_row_separators(self):
        text = "a,b\r\nc,d\n"
        self.assertEqual(parse(text), [["a", "b"], ["c", "d"]])


class TestUnicode(unittest.TestCase):
    def test_unicode_content_preserved(self):
        self.assertEqual(
            parse("a,h\u00e9llo w\u00f6rld \U0001F600,c\n"),
            [["a", "h\u00e9llo w\u00f6rld \U0001F600", "c"]],
        )


class TestCoreBlockingSamples(unittest.TestCase):
    """Blocking core samples: a Loop failing any of these must be rejected."""

    def test_core_embedded_comma(self):
        self.assertEqual(parse('name,"Doe, John",age\n'), [["name", "Doe, John", "age"]])

    def test_core_embedded_newline(self):
        self.assertEqual(
            parse('a,"multi\nline",c\n'), [["a", "multi\nline", "c"]]
        )

    def test_core_doubled_quote_escaping(self):
        self.assertEqual(parse('"a""b",c\n'), [['a"b', "c"]])


class TestMalformedInputs(unittest.TestCase):
    def test_quote_in_unquoted_field_raises_with_position(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,b"c,d\n')
        err = ctx.exception
        self.assertEqual(err.line, 1)
        self.assertEqual(err.col, 4)
        self.assertIn("line 1", str(err))
        self.assertIn("column 4", str(err))

    def test_quote_in_unquoted_field_reports_row_and_field(self):
        with self.assertRaises(ParseError) as ctx:
            parse('x,y\na,b"c,d\n')
        err = ctx.exception
        self.assertEqual(err.line, 2)
        self.assertEqual(err.col, 4)
        self.assertEqual(err.row_number, 2)
        self.assertEqual(err.field_number, 2)

    def test_non_whitespace_after_closing_quote_raises_with_position(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,"b"c,d\n')
        err = ctx.exception
        self.assertEqual(err.line, 1)
        self.assertEqual(err.col, 6)

    def test_unterminated_quote_raises_with_open_position(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,"b,c\n')
        err = ctx.exception
        self.assertEqual(err.line, 1)
        self.assertEqual(err.col, 3)

    def test_unterminated_quote_after_odd_trailing_quotes(self):
        # 'b""' is 'b' followed by an escaped literal quote: the field is
        # still open and needs one more real closing quote.
        with self.assertRaises(ParseError) as ctx:
            parse('a,"b""')
        err = ctx.exception
        self.assertEqual(err.line, 1)
        self.assertEqual(err.col, 3)

    def test_still_open_field_after_quote_then_comma_inside_quotes(self):
        # 'b"",c\n' inside quotes: the pair after b is a doubled quote, so
        # the comma and 'c' are literal content and the field never closes.
        with self.assertRaises(ParseError):
            parse('a,"b"",c\n')

    def test_multiline_quoted_field_error_position_tracks_embedded_newlines(self):
        # Two embedded newlines inside the quoted field must advance the
        # line counter correctly before the error is raised on line 3.
        with self.assertRaises(ParseError) as ctx:
            parse('a,"line1\nline2\nline3"X,d\n')
        err = ctx.exception
        self.assertEqual(err.line, 3)
        self.assertEqual(err.col, 7)

    def test_bom_away_from_start_raises_with_position(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,b\n\ufeffc,d\n')
        err = ctx.exception
        self.assertEqual(err.line, 2)
        self.assertEqual(err.col, 1)

    def test_bom_as_last_character_of_file_raises(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,b\n\ufeff')
        err = ctx.exception
        self.assertEqual(err.line, 2)
        self.assertEqual(err.col, 1)

    def test_bom_inside_unquoted_field_raises(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a\ufeffb,c\n')
        err = ctx.exception
        self.assertEqual(err.line, 1)
        self.assertEqual(err.col, 2)

    def test_bom_inside_comment_line_raises(self):
        with self.assertRaises(ParseError):
            parse('a,b\n#comment \ufeffwith bom\n')

    def test_error_message_mentions_line_and_column_words(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,"b,c\n')
        msg = str(ctx.exception)
        self.assertIn("line", msg)
        self.assertIn("column", msg)

    def test_error_message_mentions_row_and_field_words(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,"b,c\n')
        msg = str(ctx.exception)
        self.assertIn("row", msg)
        self.assertIn("field", msg)


class TestNoStdlibCsvImport(unittest.TestCase):
    def test_source_does_not_import_csv(self):
        with open("parser.py", "r", encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("import csv", source)
        self.assertNotIn("from csv", source)


# ---------------------------------------------------------------------------
# Shared architecture-neutral bakeoff cases, copied from
# generated/cross-evaluation/test_bakeoff.py and run against THIS parser.
# ---------------------------------------------------------------------------
_SHARED_VALID_CASES = [
    ("blocking_quoted_comma", 'id,"Doe, Jane"\n', [["id", "Doe, Jane"]]),
    ("blocking_embedded_lf", 'id,"first\nsecond"\n', [["id", "first\nsecond"]]),
    ("blocking_embedded_crlf", 'id,"first\r\nsecond"\r\n', [["id", "first\nsecond"]]),
    ("blocking_doubled_quote", '"say ""hello""",ok\n', [['say "hello"', "ok"]]),
    ("bom_comments_blanks", "\ufeff # vendor\n\n a , b \n", [["a", "b"]]),
    ("padded_comment", "\t  # ignored\r\nx,y\r\n", [["x", "y"]]),
    ("comment_at_eof", "# ignored", []),
    ("quoted_hash_is_data", '"#not comment",x\n', [["#not comment", "x"]]),
    ("hash_in_later_field", "x,#not comment\n", [["x", "#not comment"]]),
    ("blank_inside_quote", '"a\n\nb",c\n', [["a\n\nb", "c"]]),
    ("comment_inside_quote", '"a\n#still data\nb",c\n', [["a\n#still data\nb", "c"]]),
    ("bare_cr_normalized", '"a\rb",c\r', [["a\nb", "c"]]),
    ("mixed_newlines", "a,b\r\nc,d\re,f\n", [["a", "b"], ["c", "d"], ["e", "f"]]),
    ("ragged_rows", "a,b,c\n1\n2,3\n", [["a", "b", "c"], ["1"], ["2", "3"]]),
    ("empty_fields", ",a,,\n", [["", "a", "", ""]]),
    ("quoted_empty", '"",x\n', [["", "x"]]),
    ("ascii_padding", ' \tplain \t, \t" quoted " \t\n', [["plain", " quoted "]]),
    ("unicode_not_padding", "\u00a0x\u00a0,y\n", [["\u00a0x\u00a0", "y"]]),
    ("padded_quoted_field", '\t "x,y"\t,z\n', [["x,y", "z"]]),
    ("data_without_final_newline", "a,b", [["a", "b"]]),
    ("empty_input", "", []),
    ("blank_only_input", " \t\r\n\t\n", []),
    ("four_quotes", '"""",x\n', [['"', "x"]]),
    ("multiline_doubled_quote", '"a\n""b""\nc",z\n', [['a\n"b"\nc', "z"]]),
]

_SHARED_ERROR_CASES = [
    ("quote_in_unquoted", 'a,b"c\n', 1, 4, "quote"),
    ("junk_after_quote", '"a"x\n', 1, 4, "after"),
    ("unterminated", 'a,"b\nc', 1, 3, "unterminated"),
    ("junk_second_lf", 'ok\n"x"z\n', 2, 4, "after"),
    ("junk_second_crlf", 'ok\r\n"x"z\r\n', 2, 4, "after"),
    ("interior_bom", "a,\ufeffb\n", 1, 3, "BOM|Byte-order"),
    ("second_bom", "\ufeffa,b\n\ufeffc,d\n", 2, 1, "BOM|Byte-order"),
]


class TestSharedBakeoffSuite(unittest.TestCase):
    """Local re-run of the architecture-neutral shared bakeoff cases."""

    maxDiff = None


def _install_shared_cases() -> None:
    for name, text, expected in _SHARED_VALID_CASES:
        def valid_test(self, text=text, expected=expected):
            self.assertEqual(parse(text), expected)

        setattr(TestSharedBakeoffSuite, f"test_shared_valid_{name}", valid_test)

    for name, text, line, column, pattern in _SHARED_ERROR_CASES:
        def error_test(self, text=text, line=line, column=column, pattern=pattern):
            with self.assertRaises(ParseError) as caught:
                parse(text)
            message = str(caught.exception)
            self.assertRegex(message, rf"line\s+{line}\b")
            self.assertRegex(message, rf"column\s+{column}\b")
            self.assertRegex(message, re.compile(pattern, re.IGNORECASE))

        setattr(TestSharedBakeoffSuite, f"test_shared_error_{name}", error_test)


_install_shared_cases()


# ---------------------------------------------------------------------------
# Incorporated helper from the rejected line-regex Track: non-string guard.
# Evidence: track-line-regex/final/parser.py lines 161-162 and its committed
# test test_type_error_for_non_string.
# ---------------------------------------------------------------------------
class TestNonStringInput(unittest.TestCase):
    def test_none_raises_type_error(self):
        with self.assertRaisesRegex(TypeError, "text must be str"):
            parse(None)

    def test_bytes_raises_type_error(self):
        with self.assertRaisesRegex(TypeError, "text must be str"):
            parse(b"a,b\n")

    def test_list_raises_type_error(self):
        with self.assertRaisesRegex(TypeError, "text must be str"):
            parse(["a", "b"])


# ---------------------------------------------------------------------------
# loop-02 additions (behavior-safe; driven by loop-01 evidence)
# ---------------------------------------------------------------------------
class TestParseErrorReasonAttribute(unittest.TestCase):
    """The measured error-API clarity improvement: ParseError.reason."""

    def test_reason_exposed_for_unterminated_quote(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,"b,c\n')
        err = ctx.exception
        self.assertEqual(
            err.reason, "Unterminated quoted field (opening quote never closed)"
        )
        # Message is unchanged: it still begins with the bare reason and still
        # carries the full coordinate suffix.
        self.assertTrue(str(err).startswith(err.reason))
        self.assertIn("line 1", str(err))
        self.assertIn("column 3", str(err))

    def test_reason_exposed_for_quote_in_unquoted(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,b"c,d\n')
        err = ctx.exception
        self.assertEqual(
            err.reason, "Unexpected quote character inside an unquoted field"
        )
        self.assertTrue(str(err).startswith(err.reason))

    def test_reason_exposed_for_bom(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,b\n\ufeffc,d\n')
        err = ctx.exception
        self.assertEqual(
            err.reason, "Byte-order mark is only permitted at the start of input"
        )

    def test_existing_attributes_unchanged(self):
        with self.assertRaises(ParseError) as ctx:
            parse('x,y\na,b"c,d\n')
        err = ctx.exception
        self.assertEqual((err.line, err.col, err.row_number, err.field_number), (2, 4, 2, 2))


class TestUnicodeWhitespacePinned(unittest.TestCase):
    """Pin the winner's deliberate ASCII-only structural-whitespace behavior.

    Only U+0020 (space) and U+0009 (tab) are structural/trim whitespace. A line
    containing only *Unicode* whitespace is therefore data, not a blank line,
    and a '#' after a leading Unicode space is literal content. This is
    consistent with the shared suite's ``unicode_not_padding`` case. These tests
    lock down the edge that loop-01 union testing surfaced (no behavior change).
    """

    def test_nbsp_only_line_is_a_data_row(self):
        self.assertEqual(
            parse("\u00a0\na,b\n"), [["\u00a0"], ["a", "b"]]
        )

    def test_unicode_space_before_hash_is_literal_not_comment(self):
        self.assertEqual(
            parse("\u2003# ignored\nx,y\n"), [["\u2003# ignored"], ["x", "y"]]
        )

    def test_ascii_whitespace_only_line_is_still_blank(self):
        # Contrast: ASCII space/tab-only lines remain ignorable blanks.
        self.assertEqual(parse(" \t\n\na,b\n"), [["a", "b"]])


class TestFixtures(unittest.TestCase):
    """Runnable sample fixtures under fixtures/ (resolved relative to this file)."""

    fixtures = Path(__file__).parent / "fixtures"

    def test_sample_fixture_parses(self):
        rows = parse((self.fixtures / "sample.csv").read_text(encoding="utf-8"))
        self.assertEqual(
            rows,
            [
                ["a", "b", "c"],
                ["1", "Doe, John", "line one\nline two"],
                ["x", 'quote "inside" text', "y"],
                ["ragged", "row"],
            ],
        )

    def test_malformed_unterminated_quote_fixture_raises(self):
        with self.assertRaises(ParseError) as ctx:
            parse((self.fixtures / "malformed_unterminated_quote.csv").read_text(encoding="utf-8"))
        self.assertIn("Unterminated", ctx.exception.reason)

    def test_malformed_quote_in_unquoted_fixture_raises(self):
        with self.assertRaises(ParseError) as ctx:
            parse((self.fixtures / "malformed_quote_in_unquoted.csv").read_text(encoding="utf-8"))
        self.assertIn("quote", ctx.exception.reason.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
