#!/usr/bin/env python3
"""Build a static GitHub Pages site for committed Generated Example Viewers."""

from __future__ import annotations

import argparse
import html
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def build(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    cards = []
    for prompt in sorted((ROOT / "examples").glob("*/prompt.md")):
        name = prompt.parent.name
        generated = prompt.parent / "generated"
        if not (generated / "viewer.html").exists():
            raise FileNotFoundError(f"{name}: generated/viewer.html is missing")
        target = output / "examples" / name
        shutil.copytree(generated, target)
        title = name.replace("-", " ").title()
        cards.append(
            f'<article class="card"><h2>{html.escape(title)}</h2>'
            f'<p><a href="examples/{html.escape(name)}/viewer.html">Open Viewer</a></p>'
            f'<p><a href="examples/{html.escape(name)}/evidence-gate.json">Evidence Gate</a> · '
            f'<a href="examples/{html.escape(name)}/navigation-report.md">Navigation Evidence</a></p>'
            "</article>"
        )
    (output / "index.html").write_text(
        _INDEX.replace("__CARDS__", "\n".join(cards)),
        encoding="utf-8",
        newline="\n",
    )
    (output / ".nojekyll").write_text("", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="_site")
    args = parser.parse_args(argv)
    build(Path(args.out).resolve())
    return 0


_INDEX = """<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Experiment Loop Generated Examples</title>
<script>
  (() => {
    const param = new URLSearchParams(window.location.search).get("scoutTheme");
    const theme =
      param || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    document.documentElement.setAttribute("data-theme", theme);
  })();
</script>
<style>
:root {
  color-scheme: light;
  --cp-bg: #f7f4ef;
  --cp-bg-elevated: #fcfbf8;
  --cp-surface: #ffffff;
  --cp-surface-soft: #f5f5f5;
  --cp-border: #dedede;
  --cp-border-strong: #919191;
  --cp-text: #242424;
  --cp-text-muted: #5c5c5c;
  --cp-text-soft: #6f6f6f;
  --cp-accent: #b11f4b;
  --cp-accent-hover: #9a1a41;
  --cp-accent-soft: rgba(177, 31, 75, 0.08);
  --cp-accent-fg: #ffffff;
  --cp-success: #16a34a;
  --cp-danger: #dc2626;
  --cp-warning: #f59e0b;
  --cp-link: #0078d4;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.12);
  --cp-overlay: rgba(255, 255, 255, 0.8);
  --cp-panel: rgba(255, 255, 255, 0.86);
  --cp-panel-strong: rgba(255, 255, 255, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.55);
  --cp-highlight: rgba(177, 31, 75, 0.12);
}
html[data-theme="dark"] {
  color-scheme: dark;
  --cp-bg: #3d3b3a;
  --cp-bg-elevated: #343231;
  --cp-surface: #292929;
  --cp-surface-soft: #2e2e2e;
  --cp-border: #474747;
  --cp-border-strong: #5f5f5f;
  --cp-text: #dedede;
  --cp-text-muted: #919191;
  --cp-text-soft: #b0b0b0;
  --cp-accent: #fd8ea1;
  --cp-accent-hover: #fb7b91;
  --cp-accent-soft: rgba(253, 142, 161, 0.14);
  --cp-accent-fg: #1a1a1a;
  --cp-success: #4ade80;
  --cp-danger: #f87171;
  --cp-warning: #fbbf24;
  --cp-link: #4da6ff;
  --cp-shadow: 0 18px 48px rgba(0, 0, 0, 0.32);
  --cp-overlay: rgba(41, 41, 41, 0.88);
  --cp-panel: rgba(41, 41, 41, 0.72);
  --cp-panel-strong: rgba(41, 41, 41, 0.96);
  --cp-sheen: rgba(255, 255, 255, 0.04);
  --cp-highlight: rgba(253, 142, 161, 0.12);
}
* { box-sizing: border-box; }
body { margin:0; background:var(--cp-bg); color:var(--cp-text); font-family:"Segoe UI",Aptos,Calibri,-apple-system,BlinkMacSystemFont,sans-serif; }
main { max-width:960px; margin:0 auto; padding:48px 24px; }
h1 { font-size:40px; margin:0; }
.intro { color:var(--cp-text-muted); margin:12px 0 32px; }
.grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; }
.card { background:var(--cp-surface); border:1px solid var(--cp-border); border-radius:16px; padding:20px; box-shadow:0 1px 2px var(--cp-border); }
.card h2 { margin-top:0; }
a { color:var(--cp-link); }
</style>
</head>
<body>
<main>
  <h1>Generated Examples</h1>
  <p class="intro">Disposable snapshots regenerated from the current experiment-loop skill.</p>
  <section class="grid">__CARDS__</section>
</main>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
