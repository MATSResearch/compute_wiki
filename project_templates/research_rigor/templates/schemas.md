# Run-dir artifact schemas

The machine-readable contract for a run. Every skill reads and writes
these five artifacts inside a run directory (see `README.md` in this directory
for the directory layout and the wiki's `docs/engineering/research-rigor.md` for why they exist).

Two of the five have formal schemas/templates you can point tooling at:
- `metadata.json` → JSON Schema at `metadata.schema.json` here
- `prereg.yaml` → annotated template at `prereg.template.yaml` here

The three append-only logs are specified here (JSON Lines — one JSON object per
line, never rewritten).

---

## 1. `metadata.json` — reproducibility (auto, never hand-written)

See `metadata.schema.json`. Key point: the fields the field chronically
under-reports (model ID, release date, reasoning mode, harness version, compute,
**cost**) are all **required or first-class here and captured automatically**.
That alone makes a run more rigorously documented than most published agent work.
`compute` carries a `provider` + `ephemeral` flag because MATS compute is usually
a rented box that no longer exists by analysis time.

---

## 2. `prereg.yaml` — the commitment device (human-written, then frozen)

See `prereg.template.yaml`. Lifecycle:

1. **Draft** — the Fellow writes `hypotheses` (statement, prediction, analysis
   metric + decision_rule + method, prespecified_confounds).
2. **Freeze** — the tool sets `frozen_at`, computes `content_hash` (sha256 over
   the `hypotheses` block), asserts `registered_before_data`, and commits the file
   to git. The git commit timestamp + content hash together make the commitment
   tamper-evident and provably pre-data.
3. **Check** (analysis time) — the tool diffs the *actual* analysis against the
   frozen `analysis` block and flags any changed metric, decision rule, or method.
   Deviations aren't forbidden — they must be *visible* (surfaced at the analysis
   gate, and recordable only as a logged `amendments` entry).

The `method` field exists specifically to catch an agent silently swapping an
expensive-but-correct procedure for a cheap-but-wrong proxy (the archetype:
attribution patching substituted for causal patching, which correlate ρ≈0).

---

## 3. `provenance.jsonl` — agent decisions (auto, append-only)

One line per agent action: tool call, model invocation, decision, branch taken.
W3C-PROV-flavored (after PROV-AGENT). This is the audit substrate for every human
gate, **and** the pool the attention-check injector samples real mistakes from.

```json
{"event_id":"ev_0c1a","parent_event_id":"ev_0b77","ts":"2026-07-07T12:31:04Z","run_id":"run_20260707_120000_reward_hacking_probe","actor":"agent","stage":"run","event":"model_invocation","model_id":"claude-opus-4-8","prompt_hash":"sha256:9f2c…","summary":"chose SAE layer 8 over layer 12 for ablation","inputs":{"layers_considered":[8,12]},"outputs":{"layer_selected":8},"cost":{"tokens_in":4210,"tokens_out":880,"usd":null}}
```

| Field | Type | Notes |
|---|---|---|
| `event_id` | string | Unique within the run. |
| `parent_event_id` | string \| null | The event this one followed from (lineage). |
| `ts` | ISO-8601 UTC | |
| `run_id` | string | |
| `actor` | `"agent"` \| `"human"` | Who took the action. |
| `stage` | enum | One of the eleven stage ids in `metadata.schema.json` (`stage_status`). |
| `event` | enum | `tool_call` \| `model_invocation` \| `decision` \| `branch_selected` \| `artifact_written` \| `error`. |
| `model_id` | string \| null | Present for `model_invocation`. |
| `prompt_hash` | string \| null | sha256 of the prompt; lets you prove what was asked without storing PII/secrets inline. |
| `summary` | string | One-line human-readable description of the action. |
| `inputs` / `outputs` | object | Structured, event-specific. |
| `cost` | object \| null | Per-event tokens/usd, summed into `metadata.json`. |

**Append-only.** A correction is a new line with `event:"error"` (or a revised
decision) referencing the old `event_id` via `parent_event_id` — never an edit.

---

## 4. `gates.jsonl` — human approval gates (auto, append-only)

One line per human review gate (the Gated-stage boundaries: `lit_review`,
`design`, `writeup` — and the `analysis` review). This is the differentiator: no surveyed
system treats the PI's approval as first-class data with review-time captured.

```json
{"gate_id":"gt_04","ts":"2026-07-07T14:02:11Z","run_id":"run_20260707_120000_reward_hacking_probe","stage":"writeup","artifact":"writeup/draft_v1.md","decision":"reject","review_seconds":812,"attention_check_ids":["ac_11"],"notes":"figure 3 caption overstates effect size vs results/table2.csv"}
```

| Field | Type | Notes |
|---|---|---|
| `gate_id` | string | Unique within the run. |
| `ts` | ISO-8601 UTC | |
| `run_id` | string | |
| `stage` | enum | Which stage's gate. One of the eleven stage ids in `metadata.schema.json` (`stage_status`). |
| `artifact` | string | Run-dir-relative path of what was reviewed. |
| `decision` | `approve` \| `reject` \| `edit` | |
| `review_seconds` | integer | **Load-bearing for attention checks** — implausibly fast approvals are themselves a signal of rubber-stamping. |
| `attention_check_ids` | string[] | Which seeded checks were embedded in this gate (cross-refs `attention_checks.jsonl`). Empty if none. |
| `notes` | string | The PI's reasoning; feeds the coaching conversation, never a performance score. |

---

## 5. `attention_checks.jsonl` — verifying the overseer (auto, append-only)

One line per seeded fake error (Gap 8; full design in the `mats_dashboards`
repo, `docs/auto_alignment_research/supervision_attention_checks.md`). Drawn from real AI mistakes sampled out
of `provenance.jsonl`, injected into a Gated review stream, ground-truthed, and
scored on whether the PI caught it.

```json
{"ac_id":"ac_11","ts":"2026-07-07T14:02:11Z","run_id":"run_20260707_120000_reward_hacking_probe","stage":"writeup","injected_into_gate":"gt_04","error_type":"fabricated_result","difficulty":"medium","source_provenance_event":"ev_0c1a","ground_truth":"figure 3 effect size (0.61) does not match results/table2.csv (0.28)","two_sided_control":false,"caught":true,"caught_at":"2026-07-07T14:02:11Z"}
```

| Field | Type | Notes |
|---|---|---|
| `ac_id` | string | Unique within the run. |
| `ts` | ISO-8601 UTC | When injected. |
| `run_id` | string | |
| `stage` | enum | Stage whose gate it was injected into. |
| `injected_into_gate` | string | The `gate_id` it rode in on. |
| `error_type` | enum | Sampled from the real mistake distribution: `fabricated_result` \| `subtle_bug` \| `unfaithful_summary` \| `misread_metric` \| `dropped_confound` \| `overstated_conclusion` \| … |
| `difficulty` | `easy` \| `medium` \| `hard` | **Difficulty-stratified** — required so a miss on a hard check reads differently than a miss on an easy one. |
| `source_provenance_event` | string \| null | The real agent mistake this was modeled on (provenance lineage → "indistinguishable from real"). |
| `ground_truth` | string | The objectively-checkable fact that makes it an error. |
| `two_sided_control` | boolean | If `true`, this is a *correct* item mislabeled as suspect — catches PIs who reject everything to game the check (two-sidedness). |
| `caught` | boolean \| null | `true`/`false` after the gate resolves; `null` while pending. |
| `caught_at` | ISO-8601 \| null | |

**Escalation** reads a cross-run aggregate of these (miss *rate*, difficulty-
weighted — never a single miss) and, past threshold, notifies the MATS Research
Manager, whose role is **explicitly non-judgemental** (a coach, not an evaluator).
That decoupling is what makes an imperfect detector safe to run.

---

## Why JSON Lines for the three logs

Append-only `.jsonl` is tamper-evident by construction (you can't quietly rewrite
history), survives a killed process mid-run (each line is independently valid),
and streams cheaply from ephemeral compute back to the persistent dev node. The
git commit of a frozen `prereg.yaml` plus the append-only logs together give the
pipeline its "provably-pre-data" and "provably-reviewed" guarantees.
