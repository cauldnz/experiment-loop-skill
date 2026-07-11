"""messy-csv-parser variant: loop-01-scanner (Character state machine).

Scanning character by character with a quote state can cross line boundaries safely.

Emitted from run_example.py so this snapshot is exactly the code that produced
the recorded test-results.json. parse(text) -> list[list[str]]."""
from __future__ import annotations

def parse(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    rows, row, field = [], [], []
    in_quotes = False
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            field.append(ch)
            i += 1
            continue
        if ch == '"':
            in_quotes = True
            i += 1
        elif ch == ",":
            row.append("".join(field))
            field = []
            i += 1
        elif ch == "\n":
            row.append("".join(field))
            rows.append(row)
            row, field = [], []
            i += 1
        else:
            field.append(ch)
            i += 1
    if field or row:
        row.append("".join(field))
        rows.append(row)
    return rows
