"""messy-csv-parser variant: loop-03-merged (Synthesis: hardened core + concise finalisation).

Merge the hardened state machine with the regex track's concise field-finalisation helper.

Emitted from run_example.py so this snapshot is exactly the code that produced
the recorded test-results.json. parse(text) -> list[list[str]]."""
from __future__ import annotations


class ParseError(Exception):
    """Raised when the vendor CSV cannot be parsed."""

def parse(text):
    def finalize(chars, quoted):
        value = "".join(chars)
        return value if quoted else value.strip()

    if text and text[0] == "\ufeff":
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    n = len(text)
    i = 0
    line = 1
    rows = []
    while i < n:
        if text[i] == "#":
            while i < n and text[i] != "\n":
                i += 1
            if i < n:
                i += 1
                line += 1
            continue
        if text[i] == "\n":
            i += 1
            line += 1
            continue
        row = []
        field = []
        quoted = False
        mode = "start"
        col = 1
        while True:
            ch = text[i] if i < n else None
            if mode == "start":
                if ch is None:
                    row.append(finalize(field, quoted))
                    rows.append(row)
                    i = n
                    break
                if ch == '"':
                    quoted = True
                    mode = "quoted"
                    i += 1
                    col += 1
                    continue
                if ch == ",":
                    row.append(finalize(field, quoted))
                    field = []
                    quoted = False
                    i += 1
                    col += 1
                    continue
                if ch == "\n":
                    row.append(finalize(field, quoted))
                    rows.append(row)
                    i += 1
                    line += 1
                    break
                field.append(ch)
                mode = "unquoted"
                i += 1
                col += 1
                continue
            if mode == "unquoted":
                if ch is None or ch == "," or ch == "\n":
                    row.append(finalize(field, quoted))
                    field = []
                    quoted = False
                    if ch == ",":
                        i += 1
                        col += 1
                        mode = "start"
                        continue
                    rows.append(row)
                    if ch == "\n":
                        i += 1
                        line += 1
                    else:
                        i = n
                    break
                if ch == '"':
                    raise ParseError(f"unexpected quote in unquoted field at line {line}, column {col}")
                field.append(ch)
                i += 1
                col += 1
                continue
            if mode == "quoted":
                if ch is None:
                    raise ParseError(f"unterminated quoted field at line {line}, column {col}")
                if ch == '"':
                    if i + 1 < n and text[i + 1] == '"':
                        field.append('"')
                        i += 2
                        col += 2
                        continue
                    mode = "after_quote"
                    i += 1
                    col += 1
                    continue
                if ch == "\n":
                    line += 1
                field.append(ch)
                i += 1
                col += 1
                continue
            if mode == "after_quote":
                if ch is None or ch == "," or ch == "\n":
                    row.append(finalize(field, True))
                    field = []
                    quoted = False
                    if ch == ",":
                        i += 1
                        col += 1
                        mode = "start"
                        continue
                    rows.append(row)
                    if ch == "\n":
                        i += 1
                        line += 1
                    else:
                        i = n
                    break
                if ch == " ":
                    i += 1
                    col += 1
                    continue
                raise ParseError(f"unexpected data after closing quote at line {line}, column {col}")
    return rows
