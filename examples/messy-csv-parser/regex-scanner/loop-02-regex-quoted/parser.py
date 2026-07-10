"""messy-csv-parser variant: loop-02-regex-quoted (Per-line regex tokeniser).

A per-line regex that understands quotes can handle embedded commas and doubled quotes.

Emitted from run_example.py so this snapshot is exactly the code that produced
the recorded test-results.json. parse(text) -> list[list[str]]."""
from __future__ import annotations

import re

def parse(text):
    import re

    quoted = re.compile(r'"((?:[^"]|"")*)"')
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    rows = []
    for line in text.split("\n"):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = []
        i, n = 0, len(line)
        while True:
            j = i
            while j < n and line[j] == " ":
                j += 1
            if j < n and line[j] == '"':
                match = quoted.match(line, j)
                if not match:
                    fields.append(line[j + 1:])
                    rows.append(fields)
                    break
                fields.append(match.group(1).replace('""', '"'))
                k = match.end()
                while k < n and line[k] == " ":
                    k += 1
                i = k
            else:
                k = line.find(",", i)
                if k == -1:
                    fields.append(line[i:].strip())
                    rows.append(fields)
                    break
                fields.append(line[i:k].strip())
                i = k
            if i >= n:
                rows.append(fields)
                break
            if line[i] == ",":
                i += 1
                if i >= n:
                    fields.append("")
                    rows.append(fields)
                    break
                continue
            fields.append(line[i:].strip())
            rows.append(fields)
            break
    return rows
