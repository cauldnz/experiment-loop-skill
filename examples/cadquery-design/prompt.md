# Prompt used for this worked example

```text
Use the experiment-loop skill.

Goal: Generate a compact parametric phone stand and cable dock that could plausibly be 3D printed. Demonstrate two separate experiment runs and a third synthesis experiment that builds from both.

Scorecard:
- stability: broad enough base, sensible support height, low tip risk
- cable_access: charging cable can pass through without making the lip confusing
- printability: simple geometry, no extreme unsupported features
- visual_clarity: the purpose is obvious from a rendered preview
- desk_fit: compact footprint and not overbuilt

Judging mode:
- Use objective gates for coarse geometry constraints.
- Use an independent qualitative panel for champion selection.

Topology:
- Run A: utility-cradle path with two loops.
- Run B: printable-bracing path with two loops.
- Run C: cross-run synthesis path with two loops that uses both Run A and Run B finals as parents.
- Produce CadQuery STEP files, SVG previews, metrics, judge notes, a manifest, and a local viewer with graph lineage, metadata/provenance drawers, and raw JSON.
```
