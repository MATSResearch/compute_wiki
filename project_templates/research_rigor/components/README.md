# `research_rigor`

Deterministic checks for keeping research honest when an agent is doing some of
the work. Each module is a **self-contained unit**: use the ones you need, vendor
(copy) the ones you want to modify, ignore the rest.

**The rules these implement, and the evidence for each, are in the wiki:**
[`docs/engineering/research-rigor.md`](https://matsresearch.github.io/compute_wiki/engineering/research-rigor/).
Read that first — this package is only the enforcement layer.

**Who decides.** The checks follow the wiki's stance: the researcher decides,
under whatever delegation the project already has. A check **blocks** only to
enforce a rule the wiki states (an open concern, a prediction with no signed
verdict, a number with no source, observational evidence carrying a causal
claim, a release with no disclosed cost or harness, a release nobody read; the
full list is the table below). Where the wiki says to flag, and for everything
it gives as advice, the check returns a **flag**: a note or a warning returned
once, in the verdict object, for the person deciding. Hypothesis verdicts and concern resolutions stay with the
researcher in every delegation mode; method selection can be delegated
(`plan_gate(agent_selection_authorized=True)`).

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

## The pre-registration CLI

Installing the package also installs `research-rigor-prereg`, the only module
here with a command line. Pre-registration has **two commitment points**, on
either side of the pilot, so `freeze` runs twice:

- **`freeze --point hypothesis`** — before the pilot. Validates the question,
  hypothesis (`statement`), `prediction` and `falsifier`, hashes them, stamps
  `commitments.hypothesis`, and optionally git-commits so the commitment
  provably predates the results it governs. A question with only one
  hypothesis and no declined rival is printed as a note; the freeze goes ahead.
  ```bash
  research-rigor-prereg freeze outputs/run_20260707_120000_probe/prereg.yaml --point hypothesis --git-commit
  ```
- **`freeze --point design`** — after the pilot, before the main run. Validates
  the metric, decision rule and method, the prespecified confounds, and a guard
  for each measure (at least one for the metric); stamps `commitments.design`.
  Refuses if a hypothesis, prediction or falsifier was edited, added or removed
  since the first freeze: the pilot does not license rewriting them, and a new
  prediction goes in a new run directory's `prereg.yaml`. A hypothesis no
  planned run tests, and a planned run that tests nothing on the record, are
  printed as notes.
  ```bash
  research-rigor-prereg freeze outputs/run_20260707_120000_probe/prereg.yaml --point design --git-commit
  ```
- **`check`** — at analysis time, confirm neither commitment was tampered with
  and diff the analysis you actually ran against the one you registered:
  ```bash
  research-rigor-prereg check outputs/run_20260707_120000_probe/prereg.yaml \
      --actual outputs/run_20260707_120000_probe/analysis/actual_analysis.yaml
  ```
  Exits 1 if any registered metric, decision rule or method changed, 2 if a
  frozen commitment was edited.

Without installing, `uv run --project <this dir> research-rigor-prereg ...`
does the same from your own project's root. (Not `--directory`: that changes
the working directory, so a relative `outputs/...` path resolves inside this
package and `--git-commit` commits to the wrong repository.)

## Modules

| Module | What it gives you | The failure it targets |
|---|---|---|
| `preregister` | Two freezes — `hypothesis` (hypothesis, prediction, falsifier) before the pilot, `design` (metric, decision rule, method, confounds, a guard per measure) after it — each validated, hashed, stamped and git-committed; at analysis time, tamper-check and diff what you actually did. Notes (never refusals) for a question with one hypothesis and a hypothesis no planned run tests | Choosing the analysis after seeing results; a question with one answer waiting to be confirmed |
| `planning` | Normalised-entropy diversity score over candidate designs, each of which records its mechanism and the failure mode it is most vulnerable to; correlated-failure-mode clustering; rubric scoring that ranks but never selects; selection by the researcher or under recorded delegation | Candidates that differ only in hyperparameters; correlated evidence that does not average out |
| `verify` | `Verifier` rules-as-code (`expect_range`, `expect_shape`, `not_constant`, `reproduces`, `invariant`, `expect_counts`) plus a driver that refuses an attempt with no reasoning trace and never auto-accepts. `expect_counts`: where a run declares units (`result["conditions"]`), each condition records `launched`, `scored`, `errored` (did not run, for any reason) | Silent failure — code runs, exits 0, number is wrong; an unscored unit read as a result |
| `analysis` | Findings that must name their source artifact, evidence typed `causal`/`observational`/`qualitative`, and an anomaly ledger: the agent submits a repair proposal (what changed + evidence references), the researcher accepts or declines it, and nothing an agent does closes its own critical concern. Flags a shape claim seen only in a projection | The 82.5% case: agent spots its own critical flaw, ships anyway |
| `evidence` | The citation ledger (`evidence.jsonl`): each run that bears on a prediction, signed and weighted, kept apart from the verdict. `tally` is context for the signer; `disagreement` flags a verdict that disagrees with its own evidence | Overclaiming by omission — refutation evidence left out of the write-up |
| `resolve` | A signed verdict for every frozen hypothesis (`supported`/`refuted`/`inconclusive`), read against the evidence ledger (disagreement is flagged, not blocked), a "rivals still stand" flag, a scope guard against claiming past what was run, a flag on a `refuted`/`inconclusive` verdict that records no swept axis (`Resolution.swept`, optional `sensitivity`), follow-ups that trace to evidence and say what done means | Overclaiming with concealed negative results (78.1% of audited runs); an absence claim from one configuration |
| `comparability` | Factor-by-factor comparison of your configuration with a paper's and a check of the shared axis you declared; for several agents' arms, a flag on any arm whose judge, judge prompt, n or shared-file hash differs from the coordinator's, and the "not examined" rows of the per-arm checklist; a flag on a judge, reviewer or grader model whose id differs between runs compared in one analysis (`instrument_flags`); a method-versus-baseline comparison's `matched_on` and baseline tuning budget (`BaselineComparison`, `baseline_flags`) | Reading a paper's absolute number as your baseline; spread between agents larger than the effect; a method compared per update with an untuned baseline |
| `writing_gate` | Claim-grounding: every numeric or hypothesis claim traces to a real result artifact; scans prose for unsourced numbers; blocks on a prediction with no signed verdict; flags a paper cited without authors, year and a checked link, and a key paper read abstract-only or with no read date (`Paper.read`, `read_date`, `version`) | Fabrication that LLM reviewers accept 67–82% of the time |
| `publish` | Disclosure scorecard over the wiki's table (cost, harness, model IDs, run dates, reasoning mode, uncertainty; cost per step noted where missing) plus release checks — secrets, machine-local paths, unhashed artifacts, served model ids; blocks on a prediction with no signed verdict; reports each headline's sensitivity range (`PublishVerdict.sensitivity`) | Agent-benchmark disclosure scoring 0.38/1.0 |
| `run_dir` | A run directory filed with its acceptance condition (what done means), `metadata.json` (each model's `served_id` beside its requested `id`; `unachievable` closes the agent proposes and the researcher accepts or reopens), and append-only `provenance.jsonl` / `gates.jsonl` / `evidence.jsonl` / `attention_checks.jsonl` | Nothing to audit after the fact; "complete" and "silently stuck" looking identical; a requested model id that is not what ran |
| `attention_check` | ⚠️ Not for deployment — see below | Whether the *human* reviewer is actually reviewing |

### What blocks and what flags

| Gate | Blocks on | Flags (warnings, never a block) |
|---|---|---|
| `preregister.freeze` | a missing or placeholder field of that commitment point; a hypothesis, prediction or falsifier edited, added or removed after its freeze | a question with one hypothesis and no declined rival; a hypothesis no planned run tests; a planned run that names no registered hypothesis and does not say `exploration` |
| `planning.plan_gate` | a candidate set with one mechanism or low diversity; selection by an agent with no recorded delegation | every selected candidate sharing a failure mode |
| `verify.expect_counts` | where a run declares units: a condition missing `launched`, `scored` or `errored`, or `scored + errored != launched` (adding the check declares countable units, so a result without the counts fails; a project with no units does not add it — not checked) | a non-zero `errored`, reported beside the metric (a soft `did_not_run` result) |
| `analysis.analysis_gate` | an open concern (including one whose repair proposal is unreviewed); a finding with no artifact; observational evidence carrying a causal claim; no sign-off | single runs with no uncertainty; exploratory findings; a shape claim with no variance share or non-projecting check |
| `resolve.resolve_gate` | a frozen hypothesis with no signed verdict; a concluding verdict over an open concern; a claim past what was run | a verdict that disagrees with its evidence; evidence against it not addressed by name; rivals still standing; inconclusive results; a `refuted` or `inconclusive` verdict with no swept axis |
| `comparability` | nothing | a judge, reviewer or grader whose id differs between runs compared in one analysis; a method-versus-baseline comparison whose `matched_on` is undeclared or updates-only (`not_applicable` with a reason is not flagged) |
| `writing_gate.publication_verdict` | a prediction with no signed verdict; a contradicted, ungrounded or unsourced number; no human read | papers missing authors, year or link, unchecked links, papers filed from memory; a key paper read abstract-only or with no read date |
| `publish.publish_gate` | a prediction with no signed verdict; a failed or agent-disabled hard check; cost, harness, model IDs or run dates missing; no researcher approval | reasoning mode, uncertainty or cost per step not disclosed; failed soft checks, including a model with no `served_id` and one whose `served_id` differs from its `id` |

Closing as `unachievable` is a decision, not a gate: `RunDir.propose_unachievable`
(and `FollowUp.unachievable`) records the agent's proposal with its required
reason, and only the researcher's `accepted` (`decided_by: "pi"`) closes the
work; `reopened` leaves it open. An accepted close is an honest end state, not a
pass, and not a silent stop.

Wiki sections with no code here, because they are advice to a person and not a
checkable property: the research interview (see `skills/mats-research-interview/`),
"a dead end is not a stopping point", quiet reminders (the MATS dashboard
owns their persistence), checking an agent's own report against the record,
never asking an agent for a "compelling" result on data it can search, human
reading being necessary but not sufficient, and re-reading claim status from the
records after a context compaction. The skill carries them.

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
| Gives you | `checkpoints/`, `plots/`, `logs/`, `save_checkpoint()` | `metadata.json` to a strict schema, append-only `provenance.jsonl`, `gates.jsonl`, `evidence.jsonl`, `attention_checks.jsonl` |
| Use when | Running mech-interp experiments | You need the decision trail to be auditable afterwards |

They are complementary but **not** currently interoperable — both want to own
`metadata.json` in the run directory. If you use both, keep them in separate
directories until someone merges them properly. That merge is a known piece of
outstanding work, not a subtlety you are missing.

## Templates

`../templates/` carries the paired file formats:

- `prereg.template.yaml` — the pre-registration to fill in and freeze, in two
  sittings. Every field is commented with why it exists and which freeze it
  belongs to.
- `metadata.schema.json` — the run-directory metadata schema `run_dir` writes and
  validates against.
- `schemas.md` — the field reference for all six run-directory artifacts,
  including the four append-only logs (`provenance.jsonl`, `gates.jsonl`,
  `evidence.jsonl`, `attention_checks.jsonl`) that have no formal schema file.
- `README.md` — the run-directory layout.

## Tests

```bash
uv run --with pytest pytest tests/
```

273 tests, all of them checking that a rule actually refuses (or flags
without refusing) rather than that a function returns. The interesting ones to
read first are
`test_analysis.py::test_agent_cannot_close_its_own_critical_anomaly` and
`test_resolve.py::test_dropping_a_hypothesis_is_blocked` — those two are the
whole point of the package.

## Changes in 0.3.0

The six checks the wiki doc's 2026-11-23 additions plan. Additive: existing
callers keep working, except where noted.

- `verify.expect_counts(key="conditions")`: where a run declares units, a hard
  `counts:<key>` verifier (each condition's `launched`, `scored`, `errored`
  present and adding up) and a soft `did_not_run:<key>` one (a non-zero
  `errored` reported beside the metric). Adding the check declares units: a result with no `key` fails the hard check (a project with no countable units does not add it).
- `resolve.Resolution.swept` (axis → values tried, two or more) and
  `.sensitivity` (axis → `(low, high)`); `resolve_gate` warns on a `refuted` or
  `inconclusive` verdict with no swept axis; `PublishVerdict.sensitivity`
  reports each signed verdict's ranges.
- Served model ids: `metadata.json` model records gain `served_id`
  (`RunDir.record_served_id`; a second, different served id becomes another
  record). `publish.default_release_checks()` adds two soft checks,
  `served_ids_recorded` and `served_ids_match`; `model_ids` in a release may be
  model records (`metadata.json`'s `models`) or bare ids, which count as having
  no served id. A malformed model record fails `publish_gate` loudly.
  `comparability.instrument_flags` flags a `judge`, `reviewer` or `grader`
  whose id differs between runs compared in one analysis.
- `writing_gate.Paper.read` (`abstract` | `full`), `.read_date`, `.version`;
  `paper_flags` flags a key paper read abstract-only or with no read date.
  Changed behaviour: a key `Paper` with no `read_date` now carries a flag.
- `comparability.BaselineComparison` (`matched_on` from `generated_tokens`,
  `wall_clock`, `in_domain_learning`, `updates`, or `not_applicable` with
  `not_applicable_reason`; `baseline_tuning_budget`) and `baseline_flags`
  (undeclared or updates-only).
- `run_dir.UnachievableProposal`; `RunDir.propose_unachievable`,
  `review_unachievable` (`accepted` | `reopened`, by `pi`),
  `closed_unachievable`; `metadata.json` gains `unachievable` (a list);
  `resolve.FollowUp.unachievable`, carried through `handoff_followups`.
- Also changed behaviour: a release whose `model_ids` are bare ids now carries
  a `served_ids_recorded` warning.

## Changes in 0.2.0

Brought back in line with the wiki doc. Breaking, with no aliases:

- `preregister`: one freeze became two (`freeze --point hypothesis|design`);
  `hypotheses_hash` → `commitment_hash(prereg, point)`; `validate_draft` takes a
  point; new required fields `question`, `falsifier`, `guards`, and
  `prespecified_confounds` is now required; `frozen_at` / `content_hash` /
  `registered_before_data` at the top of `prereg.yaml` → `commitments.<point>`;
  optional top-level `planned_runs` (`{id, tests}`) and per-hypothesis
  `rivals_declined`. A prediction added after the `hypothesis` freeze goes in a
  new run directory's `prereg.yaml`: the design freeze refuses an added one.
- `run_dir`: `RunDir.create(..., acceptance=...)` is required;
  `link_prereg(point=...)`; new `evidence.jsonl`.
- `analysis`: `Finding.disconfirming` and `AnalysisReport.disconfirming` are
  gone (cite it in the evidence ledger); `Anomaly.propose_repair` /
  `review_repair`; the single-run warning says to vary the sample, not the seed.
- `resolve`: `resolve_gate` takes `evidence` and `question_of` in place of
  `disconfirming_findings`; `blocked_unaddressed_disconfirming` is now a
  warning; an open concern blocks `refuted` as well as `supported`;
  `FollowUp.acceptance` is required.
- `writing_gate.publication_verdict` and `publish.publish_gate` take
  `frozen_hypothesis_ids` and `resolutions` and block on an unsigned prediction;
  `publication_verdict` also takes `papers`.
- `publish`: `task_identity`, `inference_settings` and `failure_breakdown` are
  no longer scored (the wiki's disclosure table does not list them).
- `planning.diversity_report`: every proposal needs `mechanism` and
  `failure_mode`; `correlated_key` is gone; one shared mechanism is insufficient.
- New modules `evidence` and `comparability`.

## Relationship to the MATS dashboard tool

The dashboard's **Automated Alignment** page (Tools → 🧪, opt-in beta)
implements the same rules for people working in a browser, as gates on its
research-stage rail. The wiki counts two optional surfaces beyond a text file
and a git commit: that tool, and the terminal pair of the
[`mats-research-rigor`](../../../skills/mats-research-rigor/) skill (the method,
for the agent) with this package (the deterministic checks). Use the tool if you
want the rail without wiring anything, the skill and this package if you work
from a terminal.

The **rules** live in the wiki doc, which is the single source of truth. If you
change a rule here, change it there first.
