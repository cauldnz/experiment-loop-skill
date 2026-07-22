# Loop 01 blind panel aggregate

## Decision

The fixed blinding map was revealed only after both independent runs completed. All seven objective gates pass for every Loop. Pairwise consensus is unanimous: resumable wizard > single page > task cards. The wizard is the **interim Track baseline champion only**; the Experiment Champion remains pending minimum Loops and synthesis.

## Exact aggregates

| Loop | Label | Human-use-quality | Exact | Visual-information-clarity | Decision |
|---|---|---:|---:|---:|---|
| resumable-wizard-loop-01 | candidate-c | 4.2727272727272725 | 47/11 | 4 | new_best |
| single-page-loop-01 | candidate-b | 3.909090909090909 | 43/11 | 4.5 | keep_for_synthesis |
| task-cards-loop-01 | candidate-a | 3.1363636363636362 | 69/22 | 3 | keep_for_synthesis |

Human-use-quality is the mean of the 11 per-lens medians, not the mean of rounded overall judge scores. Visual-information-clarity is the median of the two raw scores.

## Normalization

The accessibility schema stores `candidate`, `score`, and structured `lens_findings`; the human-use schema stores `candidate_id`, `human_use_quality_mean_11`, `lens_scores`, and textual `lens_findings`. `panel-scores.json` documents every field mapping and preserves raw values, findings, evidence references, order, models, and exact source paths. Pairwise `comparisons/preference` and `pairs/preferred` were normalized without altering raw records.

## Feedback

Manifest-ready Loop 02 instructions are in `loop-02-feedback.json`. They preserve frozen invariants and each Track paradigm. No Loop 02 work has started.
