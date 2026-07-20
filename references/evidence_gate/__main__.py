from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import validate_experiment


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an experiment-loop run.")
    parser.add_argument("run_dir", help="directory containing manifest.json and viewer.html")
    parser.add_argument("--json", action="store_true", help="print the full JSON report")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    report = validate_experiment(run_dir)
    report_data = report.to_dict()
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "evidence-gate.json").write_text(
        json.dumps(report_data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if args.json:
        print(json.dumps(report_data, indent=2, sort_keys=True))
    else:
        print(f"EVIDENCE GATE: {'PASS' if report.passed else 'FAIL'} ({run_dir})")
        for check in report.checks:
            print(f"  [{check.status.upper():7}] {check.name}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
