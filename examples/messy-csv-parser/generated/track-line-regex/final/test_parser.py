import re
import unittest
from pathlib import Path

from parser import ParseError, parse


class ValidInputTests(unittest.TestCase):
    def test_bom_comments_and_blank_lines(self):
        text = "\ufeff # heading\r\n\r\n\t \n a , b \n\t# ignored\nc,d"
        self.assertEqual(parse(text), [["a", "b"], ["c", "d"]])

    def test_quoted_comma_core_gate(self):
        self.assertEqual(parse('a,"b,c",d'), [["a", "b,c", "d"]])

    def test_embedded_lf_core_gate(self):
        self.assertEqual(parse('a,"b\nc",d'), [["a", "b\nc", "d"]])

    def test_embedded_crlf_is_normalized(self):
        self.assertEqual(parse('a,"b\r\nc",d'), [["a", "b\nc", "d"]])

    def test_doubled_quote_core_gate(self):
        self.assertEqual(parse('a,"say ""hello""",z'), [["a", 'say "hello"', "z"]])

    def test_ragged_rows(self):
        self.assertEqual(parse("a,b\nc,d,e\nf"), [["a", "b"], ["c", "d", "e"], ["f"]])

    def test_trimming_and_quoted_preservation(self):
        self.assertEqual(parse(' \ta \t, \t"  b \t" \t'), [["a", "  b \t"]])

    def test_comment_and_blank_looking_lines_inside_quotes(self):
        text = 'a,"first\n  # data\n   \nlast",z'
        self.assertEqual(parse(text), [["a", "first\n  # data\n   \nlast", "z"]])

    def test_empty_fields_and_trailing_comma(self):
        self.assertEqual(parse(",a,,\n,"), [["", "a", "", ""], ["", ""]])

    def test_cr_only_physical_lines(self):
        self.assertEqual(parse("a,b\rc,d\r# note\re,f"), [["a", "b"], ["c", "d"], ["e", "f"]])

    def test_spaces_around_quoted_token(self):
        self.assertEqual(parse('  "x" \t, y'), [["x", "y"]])

    def test_empty_quoted_field_with_padding(self):
        self.assertEqual(parse('\t"" \t, ""'), [["", ""]])

    def test_hash_is_data_after_field_starts(self):
        self.assertEqual(parse("a,# not a comment\n# ignored\nb,c"), [["a", "# not a comment"], ["b", "c"]])

    def test_unicode_data_is_preserved(self):
        self.assertEqual(parse('café,"東京, 日本",🙂'), [["café", "東京, 日本", "🙂"]])

    def test_comments_only_produce_no_rows(self):
        self.assertEqual(parse("# one\r\n \t# two\r\n\t"), [])

    def test_non_ascii_whitespace_blank_and_comment_lines(self):
        self.assertEqual(parse("\u00a0\n\u2003# ignored\na,b"), [["a", "b"]])

    def test_mixed_record_newline_spellings(self):
        self.assertEqual(parse("a,b\r\nc,d\ne,f\rg,h"), [["a", "b"], ["c", "d"], ["e", "f"], ["g", "h"]])

    def test_embedded_cr_is_normalized(self):
        self.assertEqual(parse('a,"b\rc",d'), [["a", "b\nc", "d"]])

    def test_fixture_with_comments_and_multiline_field(self):
        fixture = Path(__file__).parent / "tests" / "fixtures" / "valid-messy.csv"
        self.assertEqual(
            parse(fixture.read_text(encoding="utf-8")),
            [["vendor", "description", "amount"], ["ACME", "line one\n# retained\n\nline four", " 42 "], ["tail", "yes"]],
        )


class MalformedInputTests(unittest.TestCase):
    def assert_parse_error(self, text, line, column):
        with self.assertRaises(ParseError) as caught:
            parse(text)
        message = str(caught.exception)
        self.assertRegex(message, rf"\bline {line}, column {column}\b")
        return message

    def test_quote_in_unquoted_field(self):
        self.assert_parse_error("ok\nab\"c", 2, 3)

    def test_junk_after_closing_quote_has_precise_location(self):
        message = self.assert_parse_error('a,b\n"x"x,y', 2, 4)
        self.assertIn("non-whitespace after closing quote", message)

    def test_unterminated_quote_reports_opening(self):
        self.assert_parse_error('a,b\nc,"unfinished\nstill', 2, 3)

    def test_bom_away_from_offset_zero(self):
        self.assert_parse_error("a,b\nc,\ufeffd", 2, 3)

    def test_second_bom_is_rejected(self):
        self.assert_parse_error("\ufeffa,\ufeffb", 1, 3)

    def test_parse_error_is_public_exception(self):
        self.assertTrue(issubclass(ParseError, ValueError))

    def test_no_csv_import_in_source(self):
        with open(__file__.replace("test_parser.py", "parser.py"), encoding="utf-8") as source:
            code = source.read()
        self.assertIsNone(re.search(r"^\s*(?:from\s+csv\s+import|import\s+csv\b)", code, re.MULTILINE))

    def test_balanced_quote_in_unquoted_field_is_classified(self):
        message = self.assert_parse_error('ok\nab"c",z', 2, 3)
        self.assertIn("quote in unquoted field", message)

    def test_quote_after_unquoted_padding_is_rejected_at_quote(self):
        message = self.assert_parse_error('ab \t"x",z', 1, 5)
        self.assertIn("quote in unquoted field", message)

    def test_tab_after_closing_quote_is_allowed(self):
        self.assertEqual(parse('"x"\t,y'), [["x", "y"]])

    def test_junk_after_closing_quote_with_padding(self):
        message = self.assert_parse_error('"x" \t !,y', 1, 7)
        self.assertIn("non-whitespace after closing quote", message)

    def test_hash_after_closing_quote_is_not_a_comment(self):
        message = self.assert_parse_error('"x" # nope', 1, 5)
        self.assertIn("non-whitespace after closing quote", message)

    def test_multiline_junk_location_uses_physical_source(self):
        message = self.assert_parse_error('a,"x\r\nz"   !,b', 2, 6)
        self.assertIn("non-whitespace after closing quote", message)

    def test_unterminated_quote_after_crlf_reports_opening(self):
        message = self.assert_parse_error("a,b\r\nc,\"open\r\nstill", 2, 3)
        self.assertIn("unterminated quoted field", message)

    def test_bom_inside_quoted_field(self):
        message = self.assert_parse_error('a,"b\ufeffc"', 1, 5)
        self.assertIn("BOM", message)

    def test_bom_on_later_comment_line(self):
        message = self.assert_parse_error("a,b\n\ufeff# comment", 2, 1)
        self.assertIn("BOM", message)

    def test_leading_spaces_before_bom_are_not_offset_zero(self):
        self.assert_parse_error(" \ufeffa,b", 1, 2)

    def test_multiple_junk_reports_first_offender(self):
        self.assert_parse_error('"x"bad"more', 1, 4)

    def test_type_error_for_non_string(self):
        with self.assertRaisesRegex(TypeError, "text must be str"):
            parse(None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
