"""messy-csv-parser variant: loop-01-naive-split (Naive comma split).

Splitting each line on commas is the simplest thing that could possibly work.

Emitted from run_example.py so this snapshot is exactly the code that produced
the recorded test-results.json. parse(text) -> list[list[str]]."""
from __future__ import annotations

def parse(text):
    rows = []
    for line in text.split("\n"):
        line = line.rstrip("\r")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        rows.append([field.strip() for field in line.split(",")])
    return rows
