import re
import unittest

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
        self.assert_parse_error('a,b\n"x"x,y', 2, 4)

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
