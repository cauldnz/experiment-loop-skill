"""Architecture-neutral objective tests for both finalist parsers."""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PARSERS = {
    "line-regex": ROOT / "track-line-regex" / "final" / "parser.py",
    "state-machine": ROOT / "track-state-machine" / "final" / "parser.py",
}


def load_parser(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(f"bakeoff_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALID_CASES = [
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

ERROR_CASES = [
    ("quote_in_unquoted", 'a,b"c\n', 1, 4, "quote"),
    ("junk_after_quote", '"a"x\n', 1, 4, "after"),
    ("unterminated", 'a,"b\nc', 1, 3, "unterminated"),
    ("junk_second_lf", 'ok\n"x"z\n', 2, 4, "after"),
    ("junk_second_crlf", 'ok\r\n"x"z\r\n', 2, 4, "after"),
    ("interior_bom", "a,\ufeffb\n", 1, 3, "BOM|Byte-order"),
    ("second_bom", "\ufeffa,b\n\ufeffc,d\n", 2, 1, "BOM|Byte-order"),
]


class BakeoffTests(unittest.TestCase):
    maxDiff = None


def add_tests() -> None:
    for parser_name, parser_path in PARSERS.items():
        module = load_parser(parser_name, parser_path)

        for case_name, text, expected in VALID_CASES:
            def valid_test(self, module=module, text=text, expected=expected):
                self.assertEqual(module.parse(text), expected)

            setattr(BakeoffTests, f"test_{parser_name.replace('-', '_')}_{case_name}", valid_test)

        for case_name, text, line, column, message_pattern in ERROR_CASES:
            def error_test(
                self,
                module=module,
                text=text,
                line=line,
                column=column,
                message_pattern=message_pattern,
            ):
                with self.assertRaises(module.ParseError) as caught:
                    module.parse(text)
                message = str(caught.exception)
                self.assertRegex(message, rf"line\s+{line}\b")
                self.assertRegex(message, rf"column\s+{column}\b")
                self.assertRegex(message, re.compile(message_pattern, re.IGNORECASE))

            setattr(BakeoffTests, f"test_{parser_name.replace('-', '_')}_{case_name}", error_test)

        def constraint_test(self, parser_path=parser_path):
            source = parser_path.read_text(encoding="utf-8")
            self.assertNotRegex(source, r"(?m)^\s*(?:from\s+csv\s+import|import\s+csv\b)")

        setattr(BakeoffTests, f"test_{parser_name.replace('-', '_')}_constraint", constraint_test)


def write_summary(result: unittest.TestResult) -> None:
    failures = [str(test) for test, _ in result.failures + result.errors]
    summary = {
        "suite": "shared architecture-neutral bakeoff",
        "tests_run": result.testsRun,
        "passed": result.wasSuccessful(),
        "failures": failures,
        "blocking_core_samples": {
            "line-regex": "pass" if not any("line_regex_blocking_" in item for item in failures) else "fail",
            "state-machine": "pass" if not any("state_machine_blocking_" in item for item in failures) else "fail",
        },
    }
    (Path(__file__).with_name("summary.json")).write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    add_tests()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BakeoffTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    write_summary(result)
    raise SystemExit(0 if result.wasSuccessful() else 1)
