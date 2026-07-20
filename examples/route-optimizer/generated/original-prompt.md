Use the experiment-loop skill.

Improve a small delivery-route optimizer. The route must start and end at a
depot, visit every stop exactly once, and minimize total Euclidean distance.
Create a fixed input set of at least twelve named stops so every candidate is
judged against identical data.

Frame the Problem for a technically curious reader: state the optimization
target, constraints, success criteria, and exact original Experiment Prompt.
Score route length, validity, reproducibility, and explainability. Declare each
criterion's direction, unit, cross-Track comparability, baseline value and
source where applicable, and hard gate operator/threshold where applicable.
Route length is the primary metric. Validity and reproducibility are objective
gates: a candidate that misses or duplicates a stop, fails to return to the
depot, or changes across repeated runs cannot become Champion.

Run one quantitative Track with at least four Loops: measured baseline,
construction heuristic, local-search improvement, and a final synthesis or
multi-start improvement. Use `gpt-5.6-sol` to generate the candidates and
`claude-sonnet-5` as an independent explanation judge; the judge explains the
metrics but cannot override objective validity or route length.

Use an independent exact solver or objective oracle to determine whether the
Champion is globally optimal for the fixed input. Produce runnable optimizer
code, fixed input data, objective metric-set Artifacts, inline-viewable route-map
SVG Artifacts, judge notes, and the complete prompt/input-feedback/judge-
feedback/next-prompt chain for every Loop.

Produce a Manifest v1.1. Use `parent_ids` for lineage. Give every Artifact a
stable ID, role, presentation mode, primary/featured state, comparison key,
caption, and alternative text where visual. Declare authored milestone Loops
and captions. Record structured Champion reasons and caveats linked to metric
or Artifact evidence. Record the actual model ID for every Loop and role.

Generate the shared standalone Viewer, run Navigation Evidence, and pass the
unified Evidence Gate. The Viewer must embed route maps and render objective
metrics rather than presenting either as raw links or JSON dumps.
