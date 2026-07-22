# Generated Examples

Each example contains one maintained `prompt.md` and one disposable committed
`generated/` snapshot. The snapshot is produced from the current project-local
experiment-loop skill, contains Manifest v1.1, Artifacts, Navigation Evidence,
the Evidence Gate report, and a standalone Viewer, and may be replaced wholesale.

| Example Prompt | Demonstrates | Viewer |
| --- | --- | --- |
| `examples/route-optimizer/prompt.md` | Quantitative objective scoring | `examples/route-optimizer/generated/viewer.html` |
| `examples/visual-design-system/prompt.md` | Visual judging and synthesis | `examples/visual-design-system/generated/viewer.html` |
| `examples/multilingual-dad-joke/prompt.md` | Multi-model generation and judging | `examples/multilingual-dad-joke/generated/viewer.html` |
| `examples/messy-csv-parser/prompt.md` | Objective architecture bake-off | `examples/messy-csv-parser/generated/viewer.html` |
| `examples/accessible-mobile-checkout/prompt.md` | Accessibility-first mobile browser/task gates and independent human-use judging | `examples/accessible-mobile-checkout/generated/viewer.html` |

At a deliberate release checkpoint, after batching related skill changes,
regenerate all five transactionally:

```text
python scripts/regenerate_examples.py
```

Use `--jobs N` to opt into bounded parallel generation. The sequential default
avoids unexpected model-credit spikes and provider throttling.

Regeneration is never run by pull-request or push CI because it invokes models
and can be expensive. After regeneration, manually run the freshness and
Evidence Gate checks or dispatch the manual Example workflow.
