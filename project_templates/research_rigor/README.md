# Research rigor

Not a research area like its siblings here — a **cross-cutting** template used
alongside whichever of them you are working in. It carries the checks that keep
research honest when an agent is doing some of the work.

The rules and the evidence for each are in the wiki:
[`docs/engineering/research-rigor.md`](https://matsresearch.github.io/compute_wiki/engineering/research-rigor/).
Read that first; this directory is only the enforcement layer.

| | |
|---|---|
| [`components/`](components/) | `research_rigor` — pre-registration, diversity-forced planning, result validation, the concern ledger, verdicts, claim grounding, release disclosure. Stdlib + PyYAML, 113 tests, no LLM call anywhere. |
| [`templates/`](templates/) | `prereg.template.yaml` to fill in and freeze, plus the run-directory metadata schema. |

No `example_projects/` — there is nothing here to replicate. Install the
components package next to whatever you are actually running:

```bash
uv pip install -e project_templates/research_rigor/components
```

## The one-minute version

Start with the pre-registration template and the concern ledger. Those two carry
most of the value:

1. **Freeze the hypothesis, metric and decision rule before you run anything**,
   and commit the file so its timestamp provably predates the results.
2. **Write down every worry the moment it appears, somewhere that blocks
   something.** Across 800 audited agent research runs, the most common single
   failure — **82.5%** — was an agent that identified a critical flaw during its
   own self-review and shipped the unrevised conclusion anyway. The information
   was there. Nothing made it matter.

Everything else in the package is a refinement of those two ideas.

## Also available as

- **A skill**, for agents working from a terminal:
  [`skills/mats-research-rigor/`](../../skills/mats-research-rigor/).
- **A tool**, for people working in a browser: the MATS dashboard's **Automated
  Alignment** page (Tools → 🧪, opt-in beta), which implements the same rules as
  gates on a research-stage rail.

Same rules, three surfaces. The wiki doc is the source of truth for the rules;
if you change one, change it there first.
