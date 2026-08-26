# `research_rigor`

Deterministic checks for keeping research honest when an agent is doing some of
the work. Each module is a **self-contained unit**: use the ones you need, vendor
(copy) the ones you want to modify, ignore the rest.

**The rules these implement, and the evidence for each, are in the wiki:**
[`docs/engineering/research-rigor.md`](https://matsresearch.github.io/compute_wiki/engineering/research-rigor/).
Read that first — this package is only the enforcement layer.

**No LLM call anywhere in here, on purpose.** These are the checks that have to
fail loudly and identically every time. The judgement lives in the agent reading
them or in the researcher; the moment a check needs a model to decide, it stops
being a check. Stdlib only, plus PyYAML for the pre-registration file.

## Install

From this directory:
```bash
uv pip install -e .
```

Or in another project's `pyproject.toml`:
```toml
[tool.uv.sources]
research-rigor = { path = "../path/to/research_rigor/components", editable = true }
```

## Modules

| Module | What it gives you | The failure it targets |
|---|---|---|
| `preregister` | Validate → hash → stamp → git-commit a `prereg.yaml`; at analysis time, tamper-check and diff what you actually did against it | Choosing the analysis after seeing results |
| `planning` | Normalised-entropy diversity score over candidate designs, correlated-failure-mode clustering, PI-approved rubric scoring that ranks but never selects | Agents self-selecting proposals (LLM "innovativeness" correlates −0.06 with effectiveness) |
| `verify` | `Verifier` rules-as-code (`expect_range`, `expect_shape`, `not_constant`, `reproduces`, `invariant`) plus a driver that refuses an attempt with no reasoning trace and never auto-accepts | Silent failure — code runs, exits 0, number is wrong |
| `analysis` | Findings that must name their source artifact, evidence typed `causal`/`observational`/`qualitative`, and an anomaly ledger whose entries the agent cannot close | The 82.5% case: agent spots its own critical flaw, ships anyway |
| `resolve` | A verdict for every frozen hypothesis (`supported`/`refuted`/`inconclusive`), a scope guard against claiming past what was run, follow-ups that must trace to evidence | Overclaiming with concealed negative results (78.1% of audited runs) |
| `writing_gate` | Claim-grounding: every numeric or hypothesis claim traces to a real result artifact; scans prose for unsourced numbers | Fabrication that LLM reviewers accept 67–82% of the time |
| `publish` | Disclosure scorecard (cost, harness, model IDs, dates, reasoning mode, uncertainty) plus release checks — secrets, machine-local paths, unhashed artifacts | Agent-benchmark disclosure scoring 0.38/1.0 |
| `run_dir` | A run directory with `metadata.json` and append-only `provenance.jsonl` / `gates.jsonl` / `attention_checks.jsonl` | Nothing to audit after the fact |
| `attention_check` | ⚠️ Not for deployment — see below | Whether the *human* reviewer is actually reviewing |

## ⚠️ Two things to know before using this

### `attention_check` is designed, not approved

It implements seeding a review stream with ground-truthed fake errors and
escalating a low catch-rate to a coach. That is a real answer to a real gap — no
system in a 317-paper survey measured whether its human overseer was actually
overseeing — but running it *on another person* is a program-level policy
decision that has not been made. The module is inert until something calls it.
Do not wire it up to a colleague's review stream on your own initiative.

### `run_dir.RunDir` is not `mi_components.runs.RunDir`

Same class name, different jobs, and they will confuse you if you import both
without aliasing:

| | `mi_components.runs.RunDir` | `research_rigor.run_dir.RunDir` |
|---|---|---|
| For | Where the artifacts go | What was decided, and by whom |
| Gives you | `checkpoints/`, `plots/`, `logs/`, `save_checkpoint()` | `metadata.json` to a strict schema, append-only `provenance.jsonl`, `gates.jsonl`, `attention_checks.jsonl` |
| Use when | Running mech-interp experiments | You need the decision trail to be auditable afterwards |

They are complementary but **not** currently interoperable — both want to own
`metadata.json` in the run directory. If you use both, keep them in separate
directories until someone merges them properly. That merge is a known piece of
outstanding work, not a subtlety you are missing.

## Templates

`../templates/` carries the paired file formats:

- `prereg.template.yaml` — the pre-registration to fill in and freeze. Every
  field is commented with why it exists.
- `metadata.schema.json` — the run-directory metadata schema `run_dir` writes and
  validates against.
- `README.md` — the run-directory layout.

## Tests

```bash
uv run --with pytest pytest tests/
```

113 tests, all of them checking that a rule actually refuses rather than that a
function returns. The interesting ones to read first are
`test_analysis.py::test_agent_cannot_close_its_own_critical_anomaly` and
`test_resolve.py::test_dropping_a_hypothesis_is_blocked` — those two are the
whole point of the package.

## Relationship to the MATS dashboard tool

The dashboard's **Automated Alignment** page (Tools → 🧪, opt-in beta)
implements the same rules for people working in a browser, as gates on its
research-stage rail. Same rules, two surfaces: use the tool if you want the rail
without wiring anything, use this package if you work from a terminal.

The **rules** live in the wiki doc, which is the single source of truth. If you
change a rule here, change it there first.
