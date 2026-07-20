"""Objective tests for the loop-01 baseline character-state-machine parser.

Run with: python test_parser.py
"""

import unittest

from parser import ParseError, parse


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


class TestQuotedFields(unittest.TestCase):
    def test_quoted_comma(self):
        self.assertEqual(parse('a,"b,c",d\n'), [["a", "b,c", "d"]])

    def test_embedded_lf(self):
        self.assertEqual(parse('a,"line1\nline2",b\n'), [["a", "line1\nline2", "b"]])

    def test_embedded_crlf_normalized(self):
        self.assertEqual(
            parse('a,"line1\r\nline2",b\n'), [["a", "line1\nline2", "b"]]
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


class TestRaggedRowsAndEmptyFields(unittest.TestCase):
    def test_ragged_rows_preserved(self):
        text = "a,b,c\n1,2\nx,y,z,w\n"
        self.assertEqual(
            parse(text), [["a", "b", "c"], ["1", "2"], ["x", "y", "z", "w"]]
        )

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


class TestCrOnlyLines(unittest.TestCase):
    def test_cr_only_physical_lines(self):
        text = "a,b\r1,2\r"
        self.assertEqual(parse(text), [["a", "b"], ["1", "2"]])


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

    def test_bom_away_from_start_raises_with_position(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,b\n\ufeffc,d\n')
        err = ctx.exception
        self.assertEqual(err.line, 2)
        self.assertEqual(err.col, 1)

    def test_error_message_mentions_line_and_column_words(self):
        with self.assertRaises(ParseError) as ctx:
            parse('a,"b,c\n')
        msg = str(ctx.exception)
        self.assertIn("line", msg)
        self.assertIn("column", msg)


class TestNoStdlibCsvImport(unittest.TestCase):
    def test_source_does_not_import_csv(self):
        with open("parser.py", "r", encoding="utf-8") as f:
            source = f.read()
        self.assertNotIn("import csv", source)
        self.assertNotIn("from csv", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
