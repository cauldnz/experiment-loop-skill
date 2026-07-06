# Worked examples

This repository includes two completed experiment runs. They are intentionally small enough to read, rerun, and adapt.

Both examples are self-contained for review: generated artifacts, judge notes, `manifest.json`, and `viewer.html` are committed. Rerunning is optional.

## Quantitative: route optimizer

Path: `examples\route-optimizer`

This example optimizes a small delivery route. The primary scorer is objective: route length must go down while every stop is visited exactly once. The run compares input order, nearest-neighbor construction, 2-opt local search, and deterministic multi-start 2-opt.

Open:

- `examples\route-optimizer\README.md` for the story;
- `examples\route-optimizer\prompt.md` for the kickoff prompt;
- `examples\route-optimizer\manifest.json` for the source of truth;
- `examples\route-optimizer\viewer.html` for the inspection UI.

Rerun:

```powershell
Set-Location examples\route-optimizer
python run_example.py
```

## Qualitative: CadQuery phone stand

Path: `examples\cadquery-design`

This example explores a small parametric phone stand and cable dock. It produces real CadQuery STEP files, CadQuery SVG projections, and lightweight concept SVG previews. Objective gates check coarse physical constraints, but champion selection depends on qualitative design judgement. It also demonstrates two independent experiment runs followed by a cross-run synthesis experiment with multi-parent graph lineage.

Open:

- `examples\cadquery-design\README.md` for the story;
- `examples\cadquery-design\prompt.md` for the kickoff prompt;
- `examples\cadquery-design\manifest.json` for the source of truth;
- `examples\cadquery-design\viewer.html` for the inspection UI.

Rerun:

```powershell
Set-Location examples\cadquery-design
python run_example.py
```

CadQuery is required for STEP and projection export.

Install rerun dependencies from inside the example folder:

```powershell
pip install -r requirements.txt
```
