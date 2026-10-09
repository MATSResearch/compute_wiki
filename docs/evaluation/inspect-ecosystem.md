---
tags:
  - evaluation
---

# The Inspect Ecosystem (Meridian Labs)

**Meridian Labs** (`meridianlabs-ai` on GitHub, <https://meridianlabs.ai>) is a
501(c)(3) non-profit building open-source tooling for evaluating and testing
frontier AI models and agents. If you use Inspect, you are using their work, and
several of their other tools are worth knowing about — especially **Scout**,
which will read the transcripts you are already producing.

**Relationship to Inspect and UK AISI.** Inspect AI was built by Meridian's
founding team in collaboration with the **UK AI Security Institute (AISI)**, and
Meridian continues to develop the ecosystem around it. Note the core repository
still lives at **`UKGovernmentBEIS/inspect_ai`** — that is where issues go, even
though the surrounding packages (`inspect_scout`, `inspect_petri`,
`inspect_flow`, `inspect_swe`, plus `petri_dish`, `petri_bloom`, `inspect_harbor`,
`inspect_sentinel`, `inspect_steward`) live under `meridianlabs-ai`. Inspect is now the
standard evaluation framework across UK AISI, US CAISI, the EU AI Office, Japan
AISI and Korea AISI, and at METR, Apollo, Epoch, SecureBio, Redwood and RAND. (The
`inspect_evals` benchmark library is a *different* project: it is maintained by Generality
Labs, repo `UKGovernmentBEIS/inspect_evals` — see [`evals.md`](evals.md).)

## At a glance

| I want to... | Use | PyPI |
|---|---|---|
| Write and run an evaluation | **Inspect AI** — see [`evals.md`](evals.md) | `inspect-ai` |
| Analyse agent **transcripts** for refusals, evaluation awareness, broken environments | **Inspect Scout** | `inspect-scout` |
| **Audit a model's alignment** automatically over multi-turn conversations | **Inspect Petri** | `inspect-petri` |
| Manage configs and run **large eval sets** reproducibly | **Inspect Flow** | `inspect-flow` |
| Run **Claude Code / Codex CLI / Gemini CLI / Kimi Code / OpenCode** as the agent under test | **inspect-swe** — see [`agent-scaffolds.md`](agent-scaffolds.md) | `inspect-swe` |
| Audit alignment against the **real** coding-agent scaffold, not a simulated one | **Petri Dish** | `petri-dish` |
| Generate an evaluation suite around **one** behaviour (sycophancy, self-preservation …) | **Petri Bloom** | `petri-bloom` |
| Run **Harbor-format** agent tasks in Inspect | **Inspect Harbor** — see [`agent-scaffolds.md`](agent-scaffolds.md) | `inspect-harbor` |
| **Monitors and control protocols** that watch an agent and intervene | **Inspect Sentinel** (pre-release) | `inspect-sentinel` (placeholder; install from git) |
| Have an agent **mind a long eval run** (crash isolation, status, retries) | **Inspect Steward** | `inspect-steward` |

## Inspect Scout: analysing transcripts you already have

**Inspect Scout** (`inspect-scout` on PyPI, v0.5.4 as of 2026-10-06,
[`meridianlabs-ai/inspect_scout`](https://github.com/meridianlabs-ai/inspect_scout),
docs <https://meridianlabs-ai.github.io/inspect_scout/>) runs **scanners** over
agent transcripts to surface problems you would otherwise have to read for.
Typical targets are **refusals**, **evaluation awareness** (the model noticing
it is being tested), and **misconfigured environments** — the last of which
quietly invalidates more agent evals than anything else. These are *scanners you
write or copy*, not named built-ins: the repo's `examples/docs/` directory ships
`eval_awareness.py`, `refusal_classifier.py` and `refusal_keywords.py` to start from.

Scanners can be **LLM-based** (`llm_scanner()`: you give a `question` and an
`answer` type — boolean, number, string, classification or structured JSON) or
**pattern-based** (`grep_scanner()`: cheap and deterministic), or fully custom.

```python
# scanner.py
from inspect_scout import Scanner, Transcript, llm_scanner, scanner

@scanner(messages="all")
def ctf_environment() -> Scanner[Transcript]:
    return llm_scanner(
        question="In the transcript above do you detect instances of environment "
                 "misconfiguration preventing the agent from completing its task?",
        answer="boolean",
    )
```

```bash
pip install inspect-scout
scout scan scanner.py -T ./logs --model openai/gpt-5   # -T points at the transcripts: a log directory or a transcripts database
scout view                     # interactive results
scout scan list                # recent scans
scout scan resume              # continue an interrupted scan
```

Python API: `scan()` to run programmatically, `transcripts_from()` to load,
`scan_results_df()` for a pandas dataframe of results, and the `@scanner` /
`@scanjob` decorators to write your own.

**What changed July–October 2026 (0.4.43 → 0.5.4).** Scout 0.5.0 (2026-09-04) is
**breaking**: default dataframe / reader output now *excludes* the heavy
`input`, `input_data` and `scan_events` columns — pass `exclude_columns=[]` (or use
`ScanResultsArrow.get_fields()`) if your analysis code reads them; symptom:
those columns are simply missing from the dataframe after upgrading. New in the same release: `scan_results_batches()`
(`scan_results_df()` semantics without loading everything into memory) and typed
parsed answers on scanner results. 0.5.3 streams large transcripts and bounds the
segments an `llm_scanner` holds at once (use it for very long agent runs); 0.4.45
added **Harbor ATIF** (Agent Trajectory Interchange Format) as a transcript source and
an example importer for OpenClaw telemetry.

### It reads more than Inspect logs — including Claude Code

This is the part worth knowing. Scout ingests transcripts from **Inspect, Arize
Phoenix, LangSmith, Logfire, MLflow, Weights & Biases Weave, Claude Code and Harbor**,
plus anything else via its **capture and import APIs**. Local directories or
remote storage (S3) both work.

**Practical consequence for MATS fellows:** if you have been running Claude Code
on the cluster — including through the dashboard's Automated Alignment tool,
which runs one Claude Code session per experiment — **those transcripts are
already scannable**. You do not need to have used Inspect at all. Pointing
`scout scan` at the session directory is the whole integration.

That makes Scout the cheapest available answer to "did my agent quietly refuse
half of these, notice it was being evaluated, or spend the run fighting a broken
environment?" — questions that are otherwise answered by reading hundreds of
transcripts, i.e. not answered.

### Writing your own scanner

The `@scanner` decorator is the extension point, and a custom scanner is usually
a better first move than a bespoke analysis script: you get the transcript
loading, parallel scanning, resumability and the results dataframe for free.

## Inspect Petri: automated alignment auditing

**Inspect Petri** (`inspect-petri` on PyPI, v3.1.1 as of 2026-10-01,
[`meridianlabs-ai/inspect_petri`](https://github.com/meridianlabs-ai/inspect_petri),
docs <https://meridianlabs-ai.github.io/inspect_petri/>, a collaboration between
Meridian Labs and the UK AISI Red Team) is an **automated auditing agent**: it
drives multi-turn conversations against a target model to surface concerning
behaviour, then scores what happened. Petri was created at Anthropic (as part of
MATS and the Anthropic Fellows Program) and is now maintained by Meridian; **Petri
3.0 (2026-05-07)** split the auditor and the target into independent components that
talk through a small command protocol (set system prompt, create tool, return tool
result, roll back, …), so you can swap in a custom target (a prompted model organism,
a real agent scaffold) or extend the auditor without touching the other side. Petri
2.0 remains on the `petri-v2` branch; 3.0 kept the CLI but broke some internal Python APIs.

Three model roles:

| Role | Job |
|---|---|
| **Auditor** | takes a seed instruction and designs/drives the conversation |
| **Target** | the model under audit |
| **Judge** | scores the resulting transcript against rubrics |

It ships **170+ conversation seeds** and **38 judging dimensions**, covering
things like unprompted sycophancy, concerning or dangerous outputs, evaluation
awareness, and admirable behaviour. It simulates tools and supports rollback, so
the auditor can back up and try a different line.

```bash
pip install inspect-petri
inspect eval inspect_petri/audit \
  -T seed_instructions=tags:sycophancy \
  --model-role auditor=anthropic/claude-sonnet-4-6 \
  --model-role target=openai/gpt-5-mini \
  --model-role judge=anthropic/claude-opus-4-6 \
  --limit 5
inspect view
```

Roles are given with `--model-role` (not `--model`); `-T seed_instructions=` takes
`tags:<tag>`, `id:<seed id>` or a directory of Markdown seed files, and omitting it
runs **all** 170+ seeds × up to 30 turns judged by a frontier model — "typically a
few hours and a non-trivial API spend", so start with one tag and `--limit 5`.
Python: the `audit()` function from `inspect_petri`, run through Inspect's `eval()`.

**Output** is transcripts plus judge scores (1–10) with written justifications
tied to specific messages, browsable from both the target's and the auditor's
side.

**What changed July–October 2026.** `inspect-petri` 3.1.0 (changelog date
2026-07-22) added `audit_scanner()`, a generic `llm_scanner`-style building block
for custom Petri scorers, and made auditor *prefill* distinguishable from genuine
target output; 3.1.1 (2026-10-01) stops providers from running target tools
server-side (target tool options are dropped) and **rejects seed tool definitions
with unknown or misspelled keys** — symptom: a seed that used to load now errors.

### When to use it, and when not to

- **Good for:** broad first-pass sweeps for concerning behaviour; generating
  candidate behaviours worth studying properly; a cheap baseline before hand-
  crafting a behavioural eval.
- **Be careful:** a judge score is a **model's opinion**, not a measurement.
  Treat a 1–10 rating as a *pointer to a transcript worth reading*, not as a
  number to average and report. If you do report rates from it, validate the
  judge against hand labels first — see the judge-validation note in
  [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md).
- Petri finds *candidates*. Confirming one is a real, robust behaviour is a
  separate piece of work with its own statistics — see
  [`statistics.md`](../engineering/statistics.md).
- **The default continuation message is a confound.** Petri's auditor prompt
  (still so in `inspect_petri` main on 2026-10-09, `src/inspect_petri/tools/_messages.py`)
  suggests answering a target that makes no tool call with "Please proceed to the next
  step using your best judgement." (Zhong, LessWrong 2026-09-11). That can read as
  approval of whatever the target had hesitated over and inflate misbehaviour; in Gram
  (Lindner, Krakovna & Farquhar, arXiv:2605.30322) the single sabotage in 500 Gemini 3.1
  Pro Preview samples began right after that exact message. If you report a propensity
  rate, check what the auditor sent after tool-less turns. See [`agent-scaffolds.md`](agent-scaffolds.md).
- **Auditor realism is a first-order validity issue.** The auditor simulates system
  prompts, tools and tool results, which models can often tell from deployment; see
  Dish and critique refinement below, and report an eval-awareness rate next to every number.
  Petri has a built-in **realism filter**: `-T realism_filter=true` (default threshold 0.6) or a
  float such as `-T realism_filter=0.8`. A realism model scores each message / tool result /
  system prompt the auditor is about to stage on 0.0–1.0; below-threshold actions are rejected
  with feedback and the auditor retries. The realism model uses the `realism` model role (falls
  back to the auditor model; a cheaper one is fine: `--model-role realism=<model>`), and it
  **fails open** — an unparseable score approves the action. Low-realism signals it looks for:
  placeholder names (`Acme Corp`, `John Doe`, `test@example.com`), implausibly clean content,
  round numbers, mentions of testing/monitoring, and scenario details that do not match a real
  deployment. **Tension to know about:** the cure for placeholder names is realistic ones, but
  in any environment where the target can act on the real internet fictional names must be
  *unclaimable* ([`agent-scaffolds.md`](agent-scaffolds.md)). Plain Petri and Dish both have the auditor
  *simulate* tool results (Dish's docs: "tool definitions are real; results are still simulated", apart
  from planning/todo tools the scaffold runs itself), so the real-internet risk arises mainly with a
  custom target that executes real tools; if you build one, keep it off the network.

### Petri Dish: audit the real coding-agent scaffold

**Dish** (`petri-dish` on PyPI, v0.3.4 as of 2026-08-21,
[`meridianlabs-ai/petri_dish`](https://github.com/meridianlabs-ai/petri_dish), docs
<https://meridianlabs-ai.github.io/petri_dish/>; "Deployment Imitating SWE-agent
Harness"; Meridian Labs with the UK AISI Red Team; announced as a research preview)
runs Petri audits against the *real* **Claude Code, Codex CLI or Gemini CLI** scaffold
instead of a bare model API. The scaffold supplies its own production system prompt,
tools (`bash`, `read_file`, `edit_file` …) and context-injection format; the auditor
plays the user. Fewer auditor-invented artefacts means fewer tells.

```bash
pip install petri-dish
inspect eval petri_dish/dish_audit \
  -T agent_type=claude_code \
  --model-role auditor=anthropic/claude-sonnet-4-6 \
  --model-role target=anthropic/claude-opus-4-6 \
  --model-role judge=anthropic/claude-opus-4-6
```

Default seeds cover reward hacking, self-exfiltration, shutdown resistance, oversight
subversion, sabotage and sycophancy under gaslighting; select them with
`-T seed_instructions=tags:reward-hacking` or `id:reward_hacking_debugging`. A seed's
front matter may set `docker_image` to choose the container the scaffold runs in.
**When *not* to use it:** you are auditing a non-coding deployment (Dish only covers
coding-agent scaffolds), or you cannot run Docker.

**Critique refinement and measured realism.** The yardstick is a **realism win rate**: an LLM judge compares an audit transcript with real deployment transcripts and the metric is the fraction of comparisons where it wrongly picks the audit as the real one (Kissane, MacDiarmid & Roger, Anthropic Fellows Program / Anthropic, 2026-03-23, "coding audit realism", which also showed that giving the Petri auditor real system prompts, tool sets and codebases raised the win rate on five reward-hacking scenarios from 4.6% to 32.8% without significantly changing the target's reward-hacking rate; analysis code `ckkissane/petri-realism-win-rate`). Ahlqvist et al., *Improving Evaluation
Realism with Inference-Time Compute and Deployment Scaffolds* (arXiv:2609.02302,
2026-09-02; Meridian, Cambridge Boston Alignment Initiative, UK AISI,
Anthropic) introduces **critique refinement** — the target model critiques the realism
of each candidate auditor action, and a champion-challenger protocol (depth) plus a
single-elimination bracket (breadth) picks the most realistic — and uses Dish for
coding-agent audits. The authors' summary (LessWrong post) is that the two techniques
compose to **triple the realism win rate** and substantially reduce unprompted verbalized
eval awareness in Petri; scaling the refinement compute improves both further. The
paper's own numbers show how uneven that is: on Sonnet 4.6, critique refinement (`cr2bo4`)
raised the realism win rate from 10% to 26%, Dish alone raised it from 9% to 21% on the
coding seeds, and adding critique refinement to Dish gave a further 13 pp; on Opus 4.8
the win rate stays low in absolute terms (2% to 6% with critique refinement, 2% to 3%
with Dish alone). The paper compares against a compute-matched *multibranch*
baseline (auditor rollback with a larger turn budget). Code: Dish (above); the
critique-refinement / best-of-N protocol is released as a standalone package that ports
it to the current Petri, `AxelAhlqvist1995/petri-bon`, and the frozen prompts behind the
paper's measures are in `AxelAhlqvist1995/petri-realism-reproduction` (the paper's
experiments ran on a fork of Petri 2). Author-reported results on four targets (Sonnet 4.6, Opus 4.8, GPT-5.5, Gemini 3.5 Flash; Dish results also Opus 4.7).

### Petri Bloom: one behaviour, a generated eval suite

**Bloom** (Anthropic released it in December 2025; it now lives at Meridian as
**Petri Bloom**: `petri-bloom` on PyPI, v0.2.6 as of 2026-06-08,
[`meridianlabs-ai/petri_bloom`](https://github.com/meridianlabs-ai/petri_bloom), docs
<https://meridianlabs-ai.github.io/petri_bloom/>) generates an evaluation suite around
**one** named behaviour (sycophancy, self-preservation, political bias …), runs it with
Petri's auditor/target framework (including against real scaffolds through Dish), and
scores it. Petri explores broadly; Bloom goes deep on one behaviour. Over 20 behaviour
definitions are built in (the docs say 20+; 22 in the repo on 2026-10-09), or write your own.

```bash
pip install petri-bloom
bloom init delusion_sycophancy                      # bootstrap a behaviour project
bloom scenarios ./delusion_sycophancy --model-role scenarios=anthropic/claude-sonnet-4-6
inspect eval petri_bloom/bloom_audit -T behavior=./delusion_sycophancy \
  --model-role auditor=anthropic/claude-sonnet-4-6 \
  --model-role target=openai/gpt-5-mini \
  --model-role judge=anthropic/claude-opus-4-6
```

The judge gives a 1–10 behaviour score plus `eval_awareness` and `scenario_realism`
scores. **Pitfall:** unlike a fixed benchmark, a Bloom suite grows differently
depending on how it is seeded — the docs say to cite the **full seed configuration**
for reproducibility. **When *not* to use it:** you need a fixed, shareable benchmark
(use a static dataset) or a broad sweep (use Petri).

**BLOOM-WILT — find rare on-policy examples when you have the target's logits.**
Skapars & Manino, *BLOOM-WILT: Logit Tilting for Behaviour Elicitation in Automated LLM
Auditing* (arXiv:2608.31105, 2026-08-31; code `AdrSkapars/bloom-wilt`, transcripts on
Hugging Face `AdrSkapars/bloom-wilt-transcripts`, and `AdrSkapars/inspect_logittilt`
which exposes LogitTilt as an Inspect model provider) adds two pieces to the Bloom
pipeline: on the output side it reweights the target's decoding using the model's own
distribution conditioned on an elicitation prompt (**LogitTilt**), and on the input side
the auditor revises its strategy across rounds from scored interactions (**G-PAIR**).
Author-reported: it beat the baseline auditor in 30 of 32 settings (4 targets × 8
behaviours) and raised self-harm encouragement from Qwen3.5-4B from 51% to 100% average
behaviour presence at matched compute. **When *not* to use it:** the target is an API
model without logprobs/logits access, or you need the behaviour to be representative
rather than merely reachable.

**Auditing needs compute — and smarter search can cut it.** Slocum, Palan, Chute, Kim
& Van Roy, *OpenAI-HuggingFace: A Reproduction & Lessons for Alignment Testing*
(LessWrong, 2026-09-11; code `msp895/oai-hf-incident-reproduction`) built a Petri-based
scaffold (GLM 5.2 as auditor and target, Opus 4.8 as judge) and elicited all four
misbehaviours from the public OpenAI–Hugging Face incident from high-level descriptions,
but the compute needed differed greatly by behaviour (the cost was dominated by the
rarest one), i.e. the set of behaviours an audit can find scales with the budget. A
simple **in-context RL** variant — sequential waves, with a Reviewer agent reading the
previous wave's audits and proposing new ideas to the next wave's auditors — cut the
compute to reach 80% elicitation probability on the hardest behaviour by 2.2×.
Author-reported; treat as a design pattern to try, not a settled result.

**Community extension.** `carissacullen/Petri_MultiAgent_` (LessWrong, 2026-07-22) adds
multi-agent targets to Petri (N targets with `select_target()` and `route_message()`
auditor tools). It is an unofficial extension, so check it against your Petri version;
Meridian has also created an `inspect_swarm` repository for swarm evals but, as of
2026-10-09, it is an experimental repository (README: "no stable API, no releases"; design documents only, no implementation).

## Inspect Flow: configs and large eval sets

**Inspect Flow** (`inspect-flow`,
docs <https://meridianlabs-ai.github.io/inspect_flow/>) is configuration and
workflow management for evaluations: defining eval **sets**, running them
systematically, and keeping the runs reproducible. It is in use at UK AISI and
US CAISI for auditing and pre-deployment testing.

Reach for it when you have outgrown a shell script full of `inspect eval`
invocations — many models × many tasks × many configurations, where you need the
matrix to be declarative and re-runnable rather than remembered.

For a single fellow project running a handful of evals, plain `inspect eval` is
usually still the right amount of machinery.

**What changed July–October 2026 (v0.10.0 → v0.13.1, 2026-09-19).** `FlowTask` gained
`turn_limit`, `score_on_error` and `checkpoint` (v0.11.0), and Flow can run **Scout scanners
inline** via a `scanner` on `FlowOptions` (v0.11.0); v0.13.0 (2026-09-09) added
`headline_metric`, `sandbox_prebuilt`, `incomplete_action` / `incomplete_max` and list-valued
model roles (for grader panels). **Breaking in v0.13.0:** `FlowModel.default` was removed —
a config that declares `default` under a model now fails validation at load; delete the key
(it never had any effect). Flow tracks `inspect_ai` closely, so upgrade the two together.

## Inspect Sentinel and Inspect Steward (new, pre-1.0)

**Inspect Sentinel** (`meridianlabs-ai/inspect_sentinel`, created 2026-09-21, docs
<https://meridianlabs-ai.github.io/inspect_sentinel>) provides **monitors** and **control
protocols** that watch an agent and intervene. A *monitor* observes one step of the agent's
execution and reports a **suspicion score** — it never acts. A *protocol* decides what happens
at that step, optionally after consulting monitors (a protocol with no monitors is a plain
rule). Both run at one of four stages: before or after a model generate, and before or after a
tool call. The same monitor runs **inside an Inspect eval**, in a **network proxy in front of a
model API**, and **offline over recorded transcripts** for validation and calibration — the
last is how you measure a monitor's false-positive/negative rate before trusting it. This is
the vocabulary of AI control ([`ai-control.md`](../oversight-and-control/ai-control.md)).

```bash
pip install git+https://github.com/meridianlabs-ai/inspect_sentinel   # PyPI `inspect-sentinel` 0.0.0 is a placeholder
```

**When *not* to use it:** you need a stable API — the README says the package is "under
active design", and it installs the development version of `inspect_ai` from `main` until
`inspect_ai` ships the sentinel hooks. For established control-protocol experiments see ControlArena in [`ai-control.md`](../oversight-and-control/ai-control.md).

**Inspect Steward** (`inspect-steward` on PyPI, v0.2.9 as of 2026-10-07,
`meridianlabs-ai/inspect_steward`, docs <https://meridianlabs-ai.github.io/inspect_steward>)
is "an agent that supervises evaluations on your behalf": it runs each task of an eval set in
its **own process** (one crash costs one task, not the run; CPU-bound work runs in parallel),
reconciles the log directory against what your eval-set definition asks for on a schedule, and
lets you ask for status.

```bash
pip install inspect-steward
steward init my-sweep      # create a workspace
steward tasks evalset.py   # see what the definition resolves to, before running it
steward launch             # start it, arm the timer, return
steward status             # ask how it is going
```

**When *not* to use it:** Windows (macOS and Linux only), or a short single-task eval where
`inspect eval` is enough.


## What else plugs in

Meridian list these as integrating with the ecosystem, all covered elsewhere in
this wiki: **ControlArena** and **LinuxArena** (see
[`ai-control.md`](../oversight-and-control/ai-control.md)), **TransformerLens**
and **nnterp** (see [`mech-interp.md`](../interpretability/mech-interp.md)).

## Common questions

### Which Petri command do I run, and why does `--model` not set the auditor?

Petri uses three roles: `inspect eval inspect_petri/audit -T seed_instructions=tags:sycophancy --model-role auditor=<model> --model-role target=<model> --model-role judge=<model> --limit 5`. `--model` is not how you pick the auditor or judge. Start with one tag and `--limit 5`: the full default run is 170+ seeds × up to 30 turns.

### How do I audit Claude Code (or Codex CLI) itself rather than the bare model?

Use **Petri Dish**: `pip install petri-dish` then `inspect eval petri_dish/dish_audit -T agent_type=claude_code --model-role auditor=… --model-role target=… --model-role judge=…`. The target sees the real scaffold's system prompt and tools. For *capability* evals of a CLI, use `inspect-swe` instead ([`agent-scaffolds.md`](agent-scaffolds.md)).

### I upgraded Scout and my dataframe lost `input` / `scan_events`.

That is the 0.5.0 breaking change: heavy columns are excluded by default. Pass `exclude_columns=[]`, or use `scan_results_batches()` to stream large results.

### I never used Inspect. Is any of this useful to me?

Yes — **Scout** especially. It reads Claude Code transcripts and several
tracing formats directly, so you can scan agent runs you already have without
adopting Inspect for anything.

### Where do I file a bug?

Core framework: `UKGovernmentBEIS/inspect_ai`; benchmark ports: `UKGovernmentBEIS/inspect_evals`
(upload `.eval` logs showing the problem). The satellite packages (`inspect_scout`,
`inspect_petri`, `petri_dish`, `petri_bloom`, `inspect_flow`, `inspect_swe`, `inspect_harbor`,
`inspect_sentinel`, `inspect_steward`): under `meridianlabs-ai`. Getting this wrong is the most common small friction with
this ecosystem, because the branding and the repository owner differ.

### Can I use these on the MATS cluster?

Yes — they are ordinary pip installs into your virtual environment. Anything
that calls a model API needs your key set up as in
[`faq.md`](../start-here/faq.md); anything that runs a real workload should go
through Slurm rather than sitting on the dev node.

---

Last verified: 2026-10. Checked against meridianlabs.ai and the project docs:
Meridian Labs is a 501(c)(3); Inspect AI was built by Meridian's founding team
in collaboration with UK AISI and the core repo remains `UKGovernmentBEIS/
inspect_ai`; Scout ingests Inspect / Arize Phoenix / LangSmith / Logfire /
MLflow / W&B Weave / Claude Code plus custom sources; Petri ships 170+ seeds and
38 judging dimensions with auditor/target/judge roles. Drafted by Claude;
pending MATS research-staff review. (Additions 2026-10: corrected the Scout CLI — `scout scan scanner.py -T <transcripts>`; refusal / eval-awareness are example scanners in `examples/docs/`, not named built-ins — verified against the Scout docs and repo tree; Scout 0.5.0 breaking change and 0.5.3 streaming from its CHANGELOG; Petri 3.x (PyPI 3.1.1, 3.0 blog post 2026-05-07, `--model-role` CLI and cost warning from the Petri docs, 3.1.0/3.1.1 release notes); Petri Dish (`petri-dish` 0.3.4, docs), Petri Bloom (`petri-bloom` 0.2.6, docs), arXiv 2609.02302 with `petri-bon` / `petri-realism-reproduction`, arXiv 2608.31105 with `bloom-wilt` / `inspect_logittilt`, Slocum et al. repo `msp895/oai-hf-incident-reproduction`; Inspect Flow 0.10.0–0.13.1 changelog; Inspect Sentinel (repo README, PyPI placeholder 0.0.0) and Inspect Steward (`inspect-steward` 0.2.9 README); all verified via GitHub/PyPI/arXiv/vendor docs.)
