"""Small demo script over the fixtures/ files (not part of the objective
test suite; run manually to eyeball the champion parser's behavior).

    python demo_fixtures.py
"""

from parser import ParseError, parse


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def main() -> None:
    good = parse(_read("fixtures/sample.csv"))
    print("fixtures/sample.csv ->")
    for row in good:
        print(" ", row)

    for bad_path in (
        "fixtures/malformed_unterminated_quote.csv",
        "fixtures/malformed_quote_in_unquoted.csv",
    ):
        print(f"\n{bad_path} ->")
        try:
            parse(_read(bad_path))
            print("  (unexpectedly parsed without error)")
        except ParseError as exc:
            print(f"  ParseError: {exc}")


if __name__ == "__main__":
    main()
