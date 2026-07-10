"""Objective correctness + robustness gate for the champion parser.

Run from this directory:

    python -m unittest -v

Reads the committed vendor samples in samples/ and asserts the champion parser
reproduces every expected row set and raises ParseError on every malformed
input. This is the primary objective_command for the worked example.
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parser import parse, ParseError  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLES = os.path.join(HERE, "samples")


def _read(*parts):
    with open(os.path.join(SAMPLES, *parts), "r", encoding="utf-8", newline="") as handle:
        return handle.read()


class Correctness(unittest.TestCase):
    pass


class Robustness(unittest.TestCase):
    pass


def _install():
    with open(os.path.join(SAMPLES, "expected.json"), encoding="utf-8") as handle:
        expected = json.load(handle)
    for sid, rows in expected.items():
        def check(self, sid=sid, rows=rows):
            self.assertEqual(parse(_read(sid + ".csv")), [list(r) for r in rows])
        setattr(Correctness, "test_" + sid, check)

    with open(os.path.join(SAMPLES, "malformed.json"), encoding="utf-8") as handle:
        malformed = json.load(handle)
    for mid in malformed:
        def check(self, mid=mid):
            with self.assertRaises(ParseError):
                parse(_read("malformed", mid + ".csv"))
        setattr(Robustness, "test_" + mid, check)


_install()

if __name__ == "__main__":
    unittest.main(verbosity=2)
