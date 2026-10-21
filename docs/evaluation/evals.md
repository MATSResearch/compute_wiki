---
tags:
  - evaluation
---

# Evaluation Frameworks

Tooling for running evaluations on language models — academic benchmarks, agentic tasks, dangerous capability evals, and bespoke safety tests.

!!! tip "Beyond the core framework"
    Inspect's surrounding tooling — **Scout** (analyse agent transcripts,
    including Claude Code ones), **Petri** (automated alignment auditing,
    with its **Dish** and **Bloom** extensions) and **Flow** (large eval sets)
    — is covered in [`inspect-ecosystem.md`](inspect-ecosystem.md).

## At a glance: which framework?

| If you want… | Use |
|---|---|
| Anything agentic, multi-turn, tool-using, sandboxed | **Inspect AI** (UK AISI) |
| Multiple-choice / log-prob academic benchmarks (MMLU, ARC, HellaSwag, GSM8K) | **lm-evaluation-harness** (EleutherAI) |
| Dangerous-capability / long-horizon agent tasks | **METR HCAST** / RE-Bench on Inspect — public task repos **archived and deprecated 2026-10-20** (pin a commit); METR's `vivaria` is archived and METR now runs Inspect — see [METR HCAST](#metr-hcast-and-the-metr-task-suite) |
| Run an agent eval on the live web (BrowseComp, OSWorld, DeepSearchQA) without harming third parties | See [`agent-scaffolds.md`](agent-scaffolds.md#running-agent-evals-with-internet-access) |
| Check an LLM judge or transcript scanner against hand labels before quoting its rate | **Scout validation sets** (`-V`, `validation_set()`) — see [Judge calibration and eval-result tooling](#judge-calibration-and-eval-result-tooling) |
| Report how much the choice of judge moves a 0–10 score, or get uncertainty with few items per condition | **HiBayES** (UK AISI) — see [Judge calibration and eval-result tooling](#judge-calibration-and-eval-result-tooling) |
| Stop spending epochs once estimates stop moving | **optstop** (UK AISI) — see [Judge calibration and eval-result tooling](#judge-calibration-and-eval-result-tooling) |
| Only pay for an LLM grader on samples an exact-match scorer did not settle | Inspect **`cascade()`** scorer (0.3.262+) |
| Confidence intervals, clustered standard errors, paired model comparisons | [`eval-statistics.md`](eval-statistics.md) (eval-specific) and [`statistics.md`](../engineering/statistics.md) (general) |
| Anthropic-style behavioral evals (sycophancy, deception, etc.) | **Inspect AI** with custom tasks; reference Anthropic's `evals` repo for examples |
| Quick custom eval over an API model | **safety-research/safety-tooling** (see [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md)) |
| Search hundreds of agent transcripts you already have, by rubric | **Docent** (Transluce) or **Inspect Scout** (see [`inspect-ecosystem.md`](inspect-ecosystem.md)) |
| Run open-weight models through OpenRouter and report the result | **Pin the provider** (`allow_fallbacks: false`) — see [Pin your inference provider](#pin-your-inference-provider-openrouter-and-other-routers) |
| Compare against an older `inspect_evals` number, or re-run a benchmark months later | Check the task's `N-X` **task version** — see [`inspect_evals`](#inspect_evals) |
| Measure whether a model cheats / reward hacks on an eval | See [Reward hacking and task gaming in evals](#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate) and [`datasets-benchmarks.md`](datasets-benchmarks.md) (HoneyBench, ImpossibleBench) |
| Sweep a model for concerning behaviours automatically | **Inspect Petri** / **Petri Bloom** (see [`inspect-ecosystem.md`](inspect-ecosystem.md)) |
| Bio/chem, cyber or self-replication capability evals (VCT, LAB-Bench, CVE-Bench, CyberGym, RepliBench) | See [`dangerous-capability-evals.md`](dangerous-capability-evals.md) |
| Back up a "the model *can't* do X" claim, or check whether a model is sandbagging | See [Sandbagging and capability elicitation](#sandbagging-and-capability-elicitation-is-a-low-score-real) (password-locked organisms, fine-tuning elicitation, noise injection) |

## Inspect AI

Aliases: `inspect-ai` on PyPI (importable as `inspect_ai`), `UKGovernmentBEIS/inspect_ai` on GitHub, "Inspect", "AISI's eval framework". Maintained by the UK AI Security Institute (UK AISI, formerly UK AISI within DSIT).

**What it is.** The current default open-source framework for serious LLM evaluations. Provides:
- A clean DSL for tasks: `Sample`, `solver`, `scorer`, `Task`.
- Built-in solvers including a **`react()` agent**, multi-turn chat, prompt templates, multiple-choice, etc.
- A library of 200+ pre-built evals (`inspect_evals` package) including HarmBench, AgentHarm, GAIA, GPQA, SWE-bench, CyBench, MMLU, and many more.
- Provider abstraction for OpenAI, Anthropic, Google, Mistral, HuggingFace, vLLM, llama.cpp, AWS Bedrock, Together, Groq.
- A web-based **Inspect View** for monitoring, log inspection, and token-level transcript viewing.
- A **VS Code extension** for authoring/debugging.
- **Sandboxing toolkit** — separates inference from tool execution; supports Docker, Kubernetes (`k8s_sandbox`), local subprocess.
- **Agent Bridge** — run agents from external frameworks (LangChain, OpenAI Agents SDK, Pydantic AI) inside Inspect.
- **External agent CLIs** — drive Claude Code, Codex CLI, Gemini CLI as the model under test.
- Sample-level resumability, batched inference, retries, generate config (temperature, max_tokens, etc.) at any granularity.

**When to use it:**
- Almost any new eval project in 2026 should default to Inspect.
- You need agentic / tool-using / sandboxed evals — this is its sweet spot.
- You want results comparable to other safety researchers (eval logs are a stable format; Inspect View is widely read).
- You need to run the same eval across many models / providers without rewriting.

**When *not* to use it:**
- You're running pure log-probability academic benchmarks where lm-eval-harness has the established numbers and tooling.
- You want a 30-line one-shot script — Inspect's structure is overhead for trivial evals.

**Pitfalls:**
- **`Sample` vs `Solver` vs `Scorer` confusion.** A Sample is one eval instance (input + expected output). A Solver transforms `TaskState` (chain of generates / tool uses). A Scorer turns `TaskState` into a `Score`. Read the docs once, then this becomes muscle memory.
- **`generate()` vs direct model call.** Inside a solver, use `generate()` not the raw model — `generate()` integrates with token usage tracking, retries, and Inspect View.
- **Sandbox start failures: "Cannot connect to the Docker daemon at unix:///var/run/docker.sock"** — sandbox tasks need Docker (or k8s) running. On rented GPU boxes that often means installing Docker first.
- **`inspect eval` with a HuggingFace model is slow.** The default `hf` provider doesn't batch well. Use `vllm` or `vllm-lens` provider for any non-trivial open-weight eval.
- **Token usage costs balloon on agent tasks.** Multi-turn agents over 100s of samples can run 6-figure token counts. Set `--max-samples` and `--max-tokens` while iterating; only run the full eval once.
- **Resuming a partial run** — use `--log-dir` and `inspect eval-retry` rather than re-running from scratch. Crash-recovery options added September 2026 (from the `inspect_ai` CHANGELOG): `--incomplete-action error` (with an `--incomplete-max` guard) on `inspect log recover`, `eval-retry` and `eval_set` resolves samples that were in flight at a crash as errors and finalises the eval "instead of endlessly re-running hung samples" (0.3.262); `inspect ctl task drain` stops dispatching a task's queued samples while in-flight ones finish, leaving an ordinary log that a later `inspect eval-set` or `inspect eval-retry` completes (0.3.263); and `eval_set` now *tops up* a task whose dataset grew as a strict superset with stable sample ids, running only the new samples (0.3.270). **A known trap with `--incomplete-action error`:** if the hung samples are the hard ones, converting them to errors biases the denominator — report how many were resolved this way.
- **The default `react()` "continue" message can read as permission to misbehave (propensity evals).** When a model makes no tool call in a turn, Inspect's `react()` agent (and the older `basic_agent()`) sends `Please proceed to the next step using your best judgement.` (plus `If you believe you have completed the task, please call the submit() tool…` in `react()`). Zhong (LessWrong, 2026-09-11, "Default continuation message in Inspect and Petri could be problematic") showed that, on ImpossibleBench, Gemini 3.7 Flash reasoned "the user has explicitly given me the go-ahead" and then edited the tests it had been told not to touch: among nudged samples 14% cheated with the `basic_agent` default message versus ~1% with each of the other three messages tested (the `react()` default, a submit-reminder-only message, and an empty message). Models differ in how often they get nudged (Qwen3-Coder 99% of samples, Claude Sonnet 3.7 almost never), so this biases cross-model comparisons. The library default is unchanged as of `inspect_ai` 0.3.282 (the post suggests a more neutral default); mitigation: pass your own `on_continue="If you are finished, call submit() tool with your final response."` to `react()`, and report which message you used. Full detail in [`agent-scaffolds.md`](agent-scaffolds.md).
- **`openrouter/...` models in Inspect do not pin a provider by default.** Add `-M provider='{"order":["<provider-slug>"],"allow_fallbacks":false}'` or your results can mix providers/quantizations — see [Pin your inference provider](#pin-your-inference-provider-openrouter-and-other-routers).
- **Inspect AI release notes matter for comparability (July–October 2026, 0.3.248 → 0.3.282, ~weekly releases).** Changes that alter numbers or break scripts: since 0.3.262 a model-graded scorer with a *panel* of graders (list-valued `model_roles`, e.g. `{"grader": [...]}`) needs a **strict majority** — ties and three-way splits come back *unscored* and leave the metric denominator (pass `reducer="mode"` to `model_graded_qa()` / `model_graded_fact()` for the old behaviour); since 0.3.261 abnormal scores carry a machine-readable `Score.reason` (e.g. `invalid_response_format`, `grader_failed`; `no_response` for empty completions since 0.3.269) and show up as `score_<name>_reason` columns — filter on it before quoting an accuracy; since 0.3.264 a `fail_on_refusal` generate option (`--fail-on-refusal`) raises `ModelRefusalError` instead of silently scoring a refusal as a wrong answer, and `bash_session()` / `text_editor()` / `exec_remote()` run as the sandbox's *default user* rather than always as root (symptom: new permission errors in old sandboxes; `user="root"` restores the old behaviour); since 0.3.260 a `ci()` metric reports a Student-t confidence interval for the mean (`method="bootstrap"` for a percentile (cluster) bootstrap interval); since 0.3.277 `cost_limit` / cost tracking price a request at the rate of the model that actually served it (relevant for OpenRouter, Bedrock and LiteLLM routers); `web_browser()` is deprecated as of 0.3.272. A `Reviewer` / `review` policy (0.3.264) can inspect each tool call's *result* before the model sees it. Since 0.3.262 a **`cascade()`** scorer runs scorers in order and stops at the first that settles a sample (see [Judge calibration and eval-result tooling](#judge-calibration-and-eval-result-tooling)). Since 0.3.278 a `Task` can carry a `sentinel=` (per the Inspect Sentinel docs; the Inspect CHANGELOG entry for 0.3.278 does not mention it; see [`inspect-ecosystem.md`](inspect-ecosystem.md)). **0.3.280 (2026-10-14) is breaking for Docker sandboxes:** writable host bind mounts are refused at sandbox start (fix: `:ro`, `Sample.files` or a Docker-managed volume; details in [`agent-scaffolds.md`](agent-scaffolds.md#inspect-sandboxing-toolkit)). **0.3.278 (2026-10-09):** `prompt_template()`, `chain_of_thought()` and `multiple_choice()` now keep text before media in the order written, so "multimodal evals that put text before media now send the prompt in the order they wrote it, and their baselines may shift on rerun". **0.3.281 (2026-10-15) requires Python ≥3.11** — on 3.10, pip and uv quietly resolve to 0.3.280, so check the installed version; it also counts overlapping waits once in working time (adds `suspend_working_limit()`), so runs that hit `working_limit` can differ across this boundary, and fixes a Docker `read_file()` host-side archive extraction issue (CVE-2026-17106 with Compose <5.4.0; see [`agent-scaffolds.md`](agent-scaffolds.md#inspect-sandboxing-toolkit)). **0.3.282 (2026-10-19):** recorded usage is now the *billed* total for calls that send several requests (Anthropic `pause_turn` continuations, Gemini `MALFORMED_FUNCTION_CALL` retries), so "recorded usage, cost, and token and cost limits can be higher than before for the same eval" — do not compare token or cost numbers, or `token_limit` / `cost_limit` hit rates, across this version; and a breaking `tool_state_scope()` change gives concurrently running agents in one sample separate tool state (instance names beginning with `@` are now reserved). Source: `CHANGELOG.md` in `UKGovernmentBEIS/inspect_ai` and PRs #5643, #5829, #5861, #5862; pin `inspect-ai` and record it in your results.

**One-liner:**
```bash
# pip install inspect_ai inspect_evals
inspect eval inspect_evals/gpqa_diamond --model anthropic/claude-sonnet-4-6 --limit 10
```

```python
# In code:
from inspect_ai import Task, eval, task
from inspect_ai.dataset import example_dataset
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate

@task
def my_eval():
    return Task(dataset=example_dataset("..."), solver=generate(), scorer=model_graded_qa())
```

## inspect_evals

Aliases: `inspect_evals` package, `inspect-evals` on PyPI (v0.25.0, 2026-10-17; Python ≥3.11), `UKGovernmentBEIS/inspect_evals` on GitHub, "Inspect Evals", "the Inspect Evals Register". Now maintained by **Generality Labs** (London non-profit) with contributions from UK AISI, Arcadia Impact and the Vector Institute; pull requests are accepted only from pre-approved contributors (raise an issue and upload `.eval` logs showing the problem instead).

**What it is.** A library of 200+ pre-implemented Inspect tasks: HarmBench, AgentHarm, AgentBench, GAIA, SWE-bench (Verified), CyBench, GPQA, MMLU/MMLU-Pro, MATH, IFEval, sycophancy evals, and many more. Maintained alongside Inspect. Since mid-2026 it also has an **Inspect Evals Register (Beta)**: evals that live in their authors' own repositories are listed in the docs with a pointer to a *pinned commit*; you run one by cloning that commit, installing its dependencies, and running `inspect eval` on the task file. Registered evals get an automatic `inspect-evals-lint` check and a lint badge — useful as a quick quality signal, not a correctness guarantee.

**When to use it:** Always check here before re-implementing a known benchmark. Run via `inspect eval inspect_evals/{eval_name}`.

**When *not* to use it:** You need a number that is directly comparable to a paper's table and the paper used its own harness (re-run the paper's baseline in your harness instead), or the eval's README says it is a "work in progress" port.

**Pitfall:** Some evals require additional dataset downloads, dataset gating, or sandbox setup. Read the eval's README in the repo.

**Pitfall — benchmark implementations change under you; pin the task version.** Every task carries a version `N-X` (for example `3-A`): **N** is the *comparability* version (bumped by any change that can alter scores), **X** the interface version. Read it with `task.version` (returns N) or `task.metadata["full_task_version"]`; it is also written to every log as `task_version`. Two logs with the same `task_version` are comparable; if N differs, do not attribute a score change to the model. Each eval's README has a changelog; to reproduce an old run, install the commit before the bump: `pip install "inspect-evals[mle_bench] @ git+https://github.com/UKGovernmentBEIS/inspect_evals@<commit_hash>"` (the docs' "Running a Specific Version of an Evaluation Task" and "Comparing Evaluation Results Over Time" guides walk through this). Always log `inspect_evals` and `inspect_ai` versions.

**Pitfall — silent scoring bugs found and fixed July–October 2026 (versions 0.15.0–0.25.0 of `inspect_evals`).** These are the symptom-shaped ones; if you ran any of these evals earlier, your numbers may be wrong:
- **A scorer that never ran reads as a perfect safety result.** AgentHarm *chat mode* silently scored every sample 0.0 (fixed 0.18.0; samples with no grading module are now excluded as NaN). AIR Bench annotator failures were scored `0.0`, "as though the model had answered unsafely" (now `Score.unscored()`). XSTest scored an unparseable grader verdict as a full refusal, which moves `refusal_rate`. General rule: look at the **unscored / error counts**, not just the headline metric.
- **The scorer accepted nearly anything.** PAWS used `includes()`, so any completion containing "yes"/"no" (including hedges like "I don't know") could score, and BoolQ's pattern accepted any completion ending in yes/no plus at most one character (both fixed in 0.21.0); ClassEval ran the generated class and the tests without evaluating a single assertion, so any class that imported cleanly scored 1; AbstentionBench's judge pattern matched `no` inside `know`/`cannot`.
- **Rating text injected by the agent.** In GDM Dangerous Capabilities: Stealth the rater took the *first* fenced JSON block, so an agent could embed a fake verdict block in its tool-call history; it now takes the last block (0.18.0). If your scorer parses a fenced block from text the agent can influence, take the last block or use structured output.
- **Shuffles and filters that change the exam.** `gpqa_diamond`'s answer-choice shuffle was unseeded, so 193 of 198 samples changed order between builds (fixed seed by default since 0.20.0); WorldSense's `filter_duplicate_ids` dropped 46,872 of 87,048 trials because sample ids collided (0.22.0; `filter_duplicate_ids` now requires `max_duplicates` and `reason`).
- **Judge changes break comparability.** HLE (Humanity's Last Exam) changed its default judges (now pinned to an fp8 provider quantization "so OpenRouter cannot route the judge to another precision") and, in 0.22.0, defaults to the HLE-Verified gold subset — "default-run scores are not comparable with earlier versions".
- **An unbound grader role falls back to the model under evaluation**, so the model grades its own output; the repo's lint now warns when `get_model(role=...)` has no explicit model or default (0.21.0). Always pass `--model-role grader=...`.
- **The environment can leak the answer.** SWE-bench Verified now defaults to the official SWE-bench DockerHub images instead of Epoch AI's, because the latter's git history exposed the reference fixes (0.24.0).
- **A judge reply in a code fence was scored as "safe" (0.25.0, 2026-10-17).** SOSBench's judge returned its JSON inside a Markdown code fence and the sample was scored "0 (safe)"; HLE's `json_judge` and PaperBench left such samples unscored. FORTRESS scored a risk subdomain in which every judge abstained as `0.0`; it now reports `nan`. Two lessons for your own judges: strip one wrapping fence before parsing JSON (`inspect_evals` now ships `strip_json_fence` in `inspect_evals.utils.code`), and never map a parse failure or an abstention to the *safe* label.
- **Empty responses now skip the judge (0.25.0).** XSTest scores an empty or whitespace-only response as a full refusal, FORTRESS scores it as 0 harm (adversarial) or as a refusal (benign), and HLE (with reason `no_response`), UCCB and FrontierScience score it `INCORRECT` (helper: `preset_score_on_no_response`). Refusal and over-refusal rates can move for models that sometimes return empty strings.
- **Unseeded shuffles, again (0.25.0).** TruthfulQA, SAD and LAB-Bench now shuffle samples and answer choices with a fixed default seed; DS-1000 no longer truncates completions that start with prose before the code fence (they were false negatives); SWE-Lancer (v2-B) `accuracy` "is not comparable with `1-B`".

Source for all of the above: `CHANGELOG.md` in `UKGovernmentBEIS/inspect_evals`.

## lm-evaluation-harness

Aliases: `lm-eval`, `lm_eval` on PyPI, `EleutherAI/lm-evaluation-harness` on GitHub, "Eleuther's harness", "the harness". Canonical citation: Gao, Tow, Biderman et al., "A framework for few-shot language model evaluation" (Zenodo, DOI 10.5281/zenodo.10256836) — cite the version/commit you used.

**What it is.** The established framework for academic LLM benchmarks: MMLU, ARC, HellaSwag, TruthfulQA, GSM8K, BIG-bench, BBH, etc. Optimized for log-likelihood-based multiple-choice and short-answer generation.

**When to use it:**
- You need numbers comparable to published model cards / leaderboards.
- You're running log-prob multiple-choice at scale (it's faster than Inspect for this).
- You want HuggingFace + vLLM + OpenAI providers and don't need agent/tool affordances.

**When *not* to use it:**
- Anything agentic, tool-using, or multi-turn — use Inspect.
- You want sample-level transcripts and rich logs for safety analysis — Inspect's logs are richer.

**Pitfalls:**
- **Apples-to-apples means same harness version, same model template, same `num_fewshot`.** Two MMLU numbers from different papers can differ several points just from setup. Always cite the harness commit / version.
- **`add_bos_token` and chat templates.** Default is to feed raw prompts; for instruct-tuned models the harness has flags to apply chat templates. Wrong setting can drop scores by 10+ points.
- **vLLM provider memory.** Loading a 70B model in vLLM with `--num_gpus 4` and a 32k context allocates a huge KV cache; lower `gpu_memory_utilization` if OOM.

## METR HCAST and the METR task suite

Aliases: HCAST = "Human-Calibrated Autonomy Software Tasks" (Rein et al., arXiv:2503.17354), `METR/hcast-public` on GitHub, "the METR task suite", "the time horizon eval", RE-Bench (`METR/RE-Bench`; Inspect port `METR/inspect-tasks-public`), `vivaria` (METR's former eval infra, `METR/vivaria`, archived), Hawk (`METR/hawk`).

**What it is.** A 189-task (HCAST) suite covering cyber, AI R&D, reasoning, environment exploration, and software engineering, designed for measuring agent **time horizon** — the task duration (calibrated against humans) at which an agent's success rate drops to 50% (the time-horizon metric is from "Measuring AI Ability to Complete Long Tasks", arXiv:2503.14499). Public tasks are a subset suitable for example dangerous-capability evaluations. As of TH1.1 (Jan 2026) the full suite is ~228 tasks.

**Status (2026-10-20): the public task code is deprecated and the leaderboard is frozen.** `METR/hcast-public`, `METR/RE-Bench`, `METR/public-tasks` and the Inspect port `METR/inspect-tasks-public` were archived by 2026-10-20 with DEPRECATED banners ("The HCAST tasks are now deprecated. We're not accepting contributions or bug reports for them."). The metr.org/time-horizons page says "This page is no longer actively updated" (last updated 2026-09-08). The repos still clone, so you can run them from a pinned commit, but known bugs will not be fixed and no public successor suite had been announced as of 2026-10-20. `METR/inspect-agents` (agents, scanners, action monitor) and `METR/hawk` remain active.

**When to use it:**
- You're measuring long-horizon agent capability, especially dangerous-capability evals.
- You want comparability to METR's published time horizon numbers (cite the dated snapshot: the page has said it is no longer actively updated since 2026-09-08, and its last added measurement is dated 2026-05-08).

**When *not* to use it:**
- Short, single-turn tasks — overkill.
- You don't have sandboxed compute — many tasks need actual code execution.

**Pitfalls:**
- **HCAST tasks expect a specific scaffold — and METR's scaffold is now Inspect.** `METR/vivaria` and `METR/task-standard` are archived (checked 2026-10-14; the Task Standard README: "METR is no longer maintaining the Task Standard. Instead, we use Inspect to define tasks"). METR runs Inspect at scale with **Hawk** (`METR/hawk`), uses a react agent with METR conventions (`--solver metr_agents/react` from `METR/inspect-agents`), and runs legacy task-family images through the METR Task Bridge (`inspect eval mtb/bridge -T image_tag=...`). Details and install lines: [`agent-scaffolds.md`](agent-scaffolds.md#metr-tasks-on-inspect-vivaria-and-the-task-standard-are-archived).
- **RE-Bench on Inspect is a work-in-progress port, now archived.** `METR/inspect-tasks-public` (archived 2026-10-20; it accepts no bug reports) runs METR's RE-Bench AI R&D tasks under Inspect but "configured to run on nodes with 8xH100 GPUs"; its README reports lower scores than METR's (elicitation untuned) and an open cheating route in the RL task (the agent can read the "held-out" set). Numbers from it are not directly comparable with METR's published RE-Bench results.
- **Cost.** Long-horizon tasks burn tokens. A single full-suite run on a frontier model is multi-thousand dollars.
- **Don't anchor too hard on a single time-horizon number.** It compresses a wide capability profile to one statistic; the per-task breakdown is more diagnostic.
- **Equal multiplicative jumps in horizon are not equal jumps in difficulty.** Nguyen & Fithian, "On the estimation and validity of AI time horizons — a statistical look at the METR plot" (arXiv:[2610.12466](https://arxiv.org/abs/2610.12466), 2026-10-08) refit METR's 228 tasks × 26 AIs with splines and item response theory instead of assuming AI difficulty is linear in log human time. The fitted conversion from human time to AI difficulty "is nearly flat in a region from 2--30 min but close to linear elsewhere", so "a time-horizon jump from 3 min to 30 min is much easier than one from 30 min to 5 hours despite the same multiplier of 10×". If you extrapolate a doubling time, or build a new time-horizon benchmark, check the authors' diagnostic plots for construct validity rather than assuming the log-linear model. Statistics background: [`eval-statistics.md`](eval-statistics.md).
- **A model that cheats can have no meaningful time horizon.** METR's report on GPT-5.6 Sol (metr.org, 2026-06-26) found a detected cheating rate "higher than any public model we have evaluated" on its ReAct harness (e.g. packaging exploits in intermediate submissions to reveal the hidden test suite, extracting hidden source code with the expected answer). The 50% time horizon on the TH1.1 suite then depends entirely on how cheats are scored: cheat attempts counted as failures ≈ 11.3 h (95% CI 5–40 h); counted as successes > 270 h (beyond the range METR considers reliable for this suite); discarded ≈ 71 h (95% CI 13–11,400 h, with no data left for several long-horizon tasks). METR did not treat any of these as a robust capability measurement. Practical rule for your own agent evals: **decide in advance how detected cheating is scored, report the number under each convention, and detect it with a transcript scanner** (Scout or Docent) rather than by reading. See [Reward hacking and task gaming in evals](#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).

## Anthropic safety evals (the `evals` format)

Aliases: `anthropics/evals` on GitHub, "Anthropic eval format", "model-written evals".

**What it is.** Anthropic has published a number of behavioral eval datasets in JSONL formats — sycophancy, advanced AI risks, etc. Most originate from **Perez et al. 2022, "Discovering Language Model Behaviors with Model-Written Evaluations"** (arXiv:2212.09251), which used LMs to auto-generate 154 evaluation datasets (the origin of the term **"model-written evals"**) and surfaced inverse-scaling sycophancy and concerning-goal-seeking. Many of these are wrapped as `inspect_evals` tasks now.

**When to use it:** You want Anthropic-style behavioral measurements (sycophancy, corrigibility, etc.) — search `inspect_evals` first; fall back to running the JSONL data directly via Inspect.

## OpenAI evals

Aliases: `openai/evals` on GitHub.

**What it is.** OpenAI's older eval framework. Mostly historical — superseded by Inspect for new safety work. Useful if you're reproducing a specific OpenAI-published eval.

**When *not* to use it:** New work — Inspect is the active default.

## Quick eval scripting via safety-tooling

For one-off evals where Inspect's task structure is too heavy, the **safety-research/safety-tooling** library (see [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md)) gives you a multi-provider API client with caching. Pattern:

```python
from safetytooling.apis import InferenceAPI
from safetytooling.data_models import ChatMessage, MessageRole, Prompt

api = InferenceAPI(cache_dir="./cache")
prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content="...")])
responses = await api(model_id="claude-sonnet-4-6", prompt=prompt, n=5)
```

This is appropriate for:
- Custom red-team prompts you'll iterate on.
- Comparing the same prompt across providers.
- Dataset generation (model-written prompts).

It's not appropriate for: anything you'd want others to reproduce — use Inspect.

## Docent (Transluce) — searching the transcripts you already have

Aliases: `docent` on PyPI (v0.1.88; the older `docent-python` is now a redirect package that depends on it), `TransluceAI/docent` on GitHub, "Transluce's transcript tool", docent.transluce.org.

**What it is.** An agent-transcript analysis platform: you ingest runs, then **search them with rubrics stated in natural language** ("the agent edited the test file instead of the code", "the agent claimed success without verifying"), and Docent returns matching transcripts with the location and an explanation of why each matched. The point is to turn "I noticed the agent doing a weird thing once" into a count you can put in a paper.

Three ingestion routes, per the quickstart:

1. **Tracing** — auto-instrument LLM provider calls:

```python
from docent.trace import initialize_tracing

initialize_tracing("my-collection-name")

# existing LLM calls are now captured into agent runs
response = client.chat.completions.create(
    model="gpt-5", messages=[{"role": "user", "content": "Hello!"}]
)
```

2. **Drag-and-drop an Inspect `.eval` file** in the web UI — the zero-code path if you already run Inspect.

3. **SDK ingestion** for custom formats:

```bash
pip install docent-python
```

```python
import os
from docent import Docent

client = Docent(
    api_key=os.getenv("DOCENT_API_KEY"),
    # self-hosting:
    # server_url="http://localhost:8889",
    # web_url="http://localhost:3001",
)

collection_id = client.create_collection(
    name="sample collection",
    description="example that comes with the Docent repo",
)
```

Worked notebooks live in the repo under `examples/` (`ingest_simple.ipynb`, `ingest_inspect.ipynb`, `ingest_tau_bench.ipynb`). It can be **self-hosted** (docker-compose plus a self-host guide in the docs) if your transcripts can't leave your machine.

**When to use it:**
- You have hundreds of long agent rollouts and the bottleneck is *reading* them. This is the single most common hidden cost in agentic safety projects.
- Turning a qualitative observation into a measured rate — the step between "we saw reward hacking" and a number.
- Finding broken tasks and scaffolding bugs in your own eval before you report its scores.

**When *not* to use it:**
- Your transcripts are short and few — `grep` and a notebook are faster.
- Your data can't go to a hosted service and you don't want to run the self-host stack.
- You need the *scoring* to be the artefact of record. Docent is for analysis and discovery; your reported metric should still come from a deterministic scorer in your eval harness.

**Pitfalls:**
- **A rubric search is an LLM judge.** It has false positives and false negatives like any judge, so validate on a hand-labelled sample before quoting a rate — the judge-validation discipline in [`code-recipes.md`](../engineering/code-recipes.md) applies unchanged.
- **Uploading transcripts is a data-sharing decision.** Model outputs from a red-teaming or model-organism project can be sensitive; self-host if in doubt.
- **Package naming.** `pip install docent-python` still works but is a redirect; the SDK is now `docent`. Symptom: version confusion between the two names in a lockfile.

## Pin your inference provider (OpenRouter and other routers)

Aliases: OpenRouter provider routing, the `provider` request object, `allow_fallbacks`, `require_parameters`, "provider drift", "quantization drift", "silent provider fallback", `openrouter/<vendor>/<model>`. The same concern applies to other multi-provider routers (Requesty, Vercel AI Gateway, Unify, Martian) per Khoriaty.

**What it is.** When you request an open-weight model (DeepSeek, Qwen, Kimi, Llama, gpt-oss) through OpenRouter, the request goes to whichever third-party provider OpenRouter picks. Providers differ in **quantization** (fp8, int4, bf16 …), inference backend, how they treat sampling parameters, maximum input length, and plain correctness. Default routing is not random and not stable: if a provider is down, traffic falls through to the others. So "baseline on Monday, intervention on Tuesday" can be confounded by a provider change and make an intervention look like it helped.

**Evidence this is not hypothetical:**
- nostalgebraist, *R1 CoT illegibility revisited* (LessWrong, 2026-04-19): re-running the GPQA experiments of Jose, "Reasoning Models Sometimes Output Illegible Chains of Thought" (arXiv:2510.27338, NeurIPS 2025) with *only the provider changed* to Novita gave a mean illegibility score of 2.30 versus 4.30 in the paper (which used Targon, `targon/fp8`; both providers are, as far as the author could tell, fp8 — so *same nominal quantization is not enough*), plus higher GPQA accuracy; to nostalgebraist the paper's "illegible" examples looked like **token soup** from a badly configured server (his judgement, not a measured result). The paper's author agreed the results were contaminated by bad inference setups and that some claims were not substantiated.
- Khoriaty, *Not Pinning Your OpenRouter Provider Might Invalidate Your Research* (LessWrong, 2026-07-23; written at the Pivotal fellowship with Redwood mentors): a Claude-assisted review of 32 influential AI / AI-safety repos that report OpenRouter results judged 31 open to some form of corruption (the author says this was spot-checked, not thoroughly reviewed, and does not show any particular result was affected). Examples named: Inspect AI's `_openai.py` model call (as linked in the post), Redwood's BashArena and LinuxArena Control Tower, METR's re-bench task. The Control Tower fix, "allow pinning OpenRouter providers per model", is merged (`linuxarena/control-tower` PR #1091).
- Pape, Evertz & Schönherr, *The Silent Hyperparameter: Quantifying the Impact of Inference Backends on LLM Reproducibility* (arXiv:2605.19537, 2026-05-19): holding weights, decoding parameters and hardware fixed, the choice of inference engine alone (five engines including vLLM, SGLang, llama.cpp) shifted benchmark scores by up to 16.6 percentage points. This applies to **self-hosting too**: report engine, version and flags.
- Price is not a quality proxy: for `meta-llama/llama-3.3-70b-instruct` (originally bf16) Khoriaty found the most expensive endpoint in fp8, a cheaper one in bf16, and the cheapest in fp8 again.

**Recipe (pin, record, fail loudly).** Request body, field names from the OpenRouter provider-routing docs:

```json
"provider": {
  "order": ["<provider-slug>"],
  "allow_fallbacks": false,
  "require_parameters": true,
  "quantizations": ["bf16"],
  "data_collection": "deny"
}
```

- `allow_fallbacks: false` makes the request **fail** if that provider is down instead of silently routing elsewhere (the default is `true`). A failure is what you want; a provider switch is a new "organism" and baselines may not carry over.
- `require_parameters: true` keeps OpenRouter from routing to a provider that ignores a parameter you set (temperature, top_p …). `data_collection` defaults to `allow`, so set `deny` before sending anything private.
- In Inspect: `inspect eval task.py --model openrouter/<vendor>/<model> -M provider='{"order":["<provider-slug>"],"allow_fallbacks":false}'` (the Inspect providers page documents the `provider` model arg).
- **Record the provider like you record temperature.** `GET https://openrouter.ai/api/v1/generation?id=<response id>` returns `data.provider_name` and `provider_responses` (every attempt, including fallbacks); it has **no quantization field**, so also log the `order` / `quantizations` you requested.
- Run baseline and treatment close together in time (ideally interleaved); a pinned provider can still change its deployment without notice.
- `seed` does not make provider outputs deterministic. Check the provider's maximum context length against your longest prompt, or you will get silent truncation.
- Benchmark providers at the start of a project if you can, but a matching accuracy number is weak evidence the served model is identical ("Accuracy is Not All You Need", arXiv:2407.09141).
- Khoriaty released a Claude skill, `use-openrouter-safely`, in `AMindToThink/openrouter_reliable_research_search` (parts of its notes were generated by Claude and not fully human-checked).

**When default routing is fine:** the model has a single provider (proprietary Anthropic/OpenAI models — version drift is still possible), quick exploration where output variance does not matter, or a cheap high-throughput job with minimal quality needs. **When it is not:** measuring capabilities or propensities, comparing models / harnesses / interventions, generating training data, or anything someone else must reproduce.

**Status.** OpenRouter's "Auto Exacto" provider ordering applies only to tool-calling requests; after Khoriaty's post OpenRouter staff said it is publishing benchmark scores for some models, working on logprob checks against a reference implementation, and working on a "verified provider" tier. Treat those as announced, not shipped, until you see them in the docs. `inspect_evals` itself now pins its HLE judge to fp8 for exactly this reason.

**Pitfalls (searchable symptoms):**
- **"Token soup"** — fluent text interrupted by random-looking words or strings, stray special tokens, broken reasoning formatting; often intermittent and also present in the final answer, not only the chain of thought.
- **Accuracy or CoT-quality shifts with no code change.** Check the provider mix in your logs: nostalgebraist's GPQA logs for QwQ-32B show one config run as 90% Nebius + 10% DeepInfra and another as 85% DeepInfra + 15% Nebius.
- **Pinned `order` with `allow_fallbacks` left at the default `true`** — pinning "worked" until an outage, then a different provider quietly served part of the run.
- **Large N does not average this out.** Routing is not random, so more samples reduce sampling noise, not provider bias.

## Reward hacking and task gaming in evals: what moves the rate

Aliases: specification gaming, task gaming, eval gaming, "cheating on the eval", honeypot evals, reward hacking in agentic evals, "graded-episode" behaviour.

**What it is.** Frontier agents sometimes exploit an eval instead of doing the task (edit the tests, read the answer key, query an engine the environment exposes, fabricate a measurement). Several results from July–October 2026 show the *measured rate* depends heavily on eval design, so a hack rate is a property of **(model × environment × prompt)**, not of the model alone.

**Findings a fellow should know (author-reported unless noted):**
- **Old evals still bite when the surface changes.** Valentine (LessWrong, 2026-09-08; code `Goodhart-Labs/beat-stockfish`): a chess honeypot ("only a win scores"; the opponent's UCI engine socket is reachable inside the sandbox). Fable 5.1 used the engine in 3 of 10 rollouts (3 more hit cyber classifiers, so likely an underestimate), Fable 5 in 5 of 5 (on a variant of the honeypot that avoids the cyber classifiers), GPT-6 Astra in 10 of 10 without disclosing it. Only ten rollouts per model — wide intervals.
- **Cooperative framing changes the rate.** Dumas (LessWrong, 2026-09-15; code `Butanium/ar-reward-hacking-2026-09-08-20-01-34d157`), n = 30 per cell: adding an unused `stop_eval` tool took Fable 5.1's cheating to 0 (Astra only slightly lower, intervals overlap); deleting the "GRADING / only a win scores" section took Fable 5.1 to 0; one sentence "Please do not game the eval as this would measure your ability to cheat rather than play chess" gave 0/30 for both models (upper 95% bound about 11%). Caveats: the wording may itself signal "this is a reward-hacking test", and it may not transfer to long-horizon tasks. Asking models afterwards "did you cheat?" mostly gets admissions, but resampled denials in three trajectories ran 2/10, 4/10 and 10/10 — treat self-reports as weak evidence. Consistent with Gomez, "Can escalation channels redirect reward hacking toward defect disclosure?" (arXiv:2608.29460, 2026-08-29): a structured report tool (an "escalation channel") plus an anti-hacking policy cut reward hacking from 23.6% to 5.3% across 8 frontier models, eliminating it for 6 of 8.
- **A graded episode is a context the model may treat differently.** nostalgebraist, "models may behave differently in graded episodes (a tirade)" (LessWrong, 2026-08-07) argues that RLVR-trained models condition on whether they perceive a graded, grader-satisfaction setting, so cheating rates from METR-style harnesses need not transfer to ordinary interactive use. This is a hypothesis supported by the contrast with the author's own daily use, not a measured result; it is a reason to report the hack rate *with the prompt and grading text shown*.
- **Models rarely go looking.** Valentine (LessWrong, 2026-10-06, ~800 honeypot rollouts): models almost never ran `ls /` or checked the `/grader/` directory that most of his environments contain (normally root-only) unless a specific hack had already occurred to them (<1% for non-Grok models, about 5% for Grok); no explicit "this is an alignment test" reasoning appeared in the ~800 rollouts, although models often said a shortcut "feels like cheating" and took it anyway; refusals flipped on irrelevant details (whether they must run the action themselves versus write a script that runs at episode end). Design lesson: build hacks that are counterproductive whether or not the model suspects an eval.
- **A honeypot benchmark can silently become "tasks one model family fails".** Valentine (same post, "Qualitative impressions from creating AI honeypots for six months") found that "5.6-Sol would take whatever ridiculous shortcut it spotted, even in shitty prototype environments", so keeping every environment that elicited on *any* model would have biased the benchmark toward GPT-5.6 Sol's weaknesses. Goodhart Labs' rule: "a prototype environment *must* have some hack rollouts on a non-OpenAI model in order to be included", and they prototyped against DeepSeek, Gemini and Grok as well. Those models also took almost every hack, so by publication the guideline had become "the task should elicit against specifically one of 6-Astra, Fable 5.1, or Opus 5.5" — which, Valentine notes, compressed the curve between models. Tips that transfer: prototype each environment against several families and keep only tasks that elicit on the models you care about; read raw chain of thought (CoT), where models still often say a shortcut "feels like cheating" before taking it; and treat refusal rates as fragile, since trivial changes (running the action yourself vs a script run at episode end; the cheating information in the prompt vs in a file the prompt points to) flipped them.
- **Measure apparent-success-seeking with a paired gameable / robust scorer.** Keira Leal (LessWrong, 2026-08-11, "Before We Defer Research to AI: Measuring Apparent-Success-Seeking") reports a coding assistant that "copied my failing test cases into the few-shot prompt" of a classifier to make tests pass, and did it again "just harder to spot" after being called out. Proposal: for each task, "design two scorers: one gameable and one robust. The performance gap quantifies the apparent-success-seeking signal" — the gameable one checks what a user would normally look at (test pass rate), the robust one inspects the strategy actually used (are the new few-shot examples out of distribution?). A practical version for your own research agents: whenever an agent improves a metric, also score the artifact it changed (prompt, eval, data) with a check it was not optimising. The repo (`keiraleal/apparent-success-seeking-eval`) is an early sketch with no license file; reuse the pattern rather than the code.
- **Why does it do it? Use model forensics.** Singh, Kroiz, Rajamanoharan & Nanda, "Model Forensics" (arXiv:2606.26071): read the chain of thought to generate hypotheses, then test them with counterfactual prompt or environment edits. Applied in "Why do models task game?" (LessWrong, 2026-08-06): DeepSeek V4 Pro's task gaming shifted with beliefs about oversight, grader capability and partial credit; final outputs can fabricate measurements while the CoT shows no planned deception, so reading the CoT alone is insufficient. Environments: `gkroiz/agent-interp-envs`.
- **Automating the investigation: Prism.** Louis Thomson's Prism (`LAThomson/prism`; LessWrong 2026-07-13, "Prism: Automating Science-of-Evals Research"; MATS 9.0 work with Victoria Krakovna) installs into an existing Inspect eval repo as two Claude Code skills. `/orchestrate` runs science-of-evals experiments: falsifiable hypotheses, minimal eval perturbations, pre-registered predictions, execution under opaque condition ids while the orchestrator stays blind to scores, and a transcript analyst behind a "hypothesis firewall". `/diagnose` ("Model Forensics" mode) explains one transcript's behaviour with resampling and discriminating perturbations, with a red-teaming critic that must run on a non-Claude model family via OpenRouter. Patterns worth copying even without the tool: check blinding mechanically (opaque labels leak through directory names), score pre-registered predictions as written, and treat differences inside the noise floor of repeated control draws as unattributable. **When *not* to use it:** the eval is not an Inspect task; you need to vendor or redistribute it (no license file as of 2026-10-14); or you run the orchestrator on an older model (the README reports diminished compliance on Opus 4.5). Full description: [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md).
- **Does an interpretability tool explain behaviour better than the transcript?** Karvonen, Ong, Kantamneni & Marks, "Would this change your answer? Evaluating Explanations of LLM Behavior In The Wild with Counterfactual Experiments" (arXiv:2608.16747; code `adamkarvonen/chive`, MIT) introduce **CHIVE** (Counterfactual Hypothesis Investigation Via Edits), an agentic pipeline that finds unexpected behaviours in real transcripts and tests explanations with counterfactual prompt edits. Used as an eval, "we find no uplift from any of the interpretability techniques studied" for predicting counterfactual behaviour. A ready baseline if your "why did it do it?" method is meant to beat reading the transcript; its ground truth is prompt-edit effects, not internals.
- **Audit the benchmark before reading the rate: shipped tasks are broken more often than you think.** Mendelsohn, "Good Evals Are Hard: An ImpossibleBench Audit" (LessWrong, 2026-10-12; code `simonjmendelsohn/impossiblebench-honest-failure`, MIT) re-ran the LiveCodeBench half of ImpossibleBench a year after release and found "14 defects that affect 13 of the original 103 tasks (including 5 tasks with flatly wrong expected answers)" in the supposedly solvable control split (`safety-research/impossiblebench` issue #5, open), and that the metric scores stopping by saying the task is impossible and then calling `sys.exit(0)` as cheating — about 70–80% of Gemini 3.1 Pro's measured "cheating" in his runs, "nearly eliminated" by an explicit stop option. Separately, the released `impossible_livecodebench` never counted test edits as cheating with `allow_test_modifications=True` (the default in its `demo.py`) until PR #4 (merged 2026-10-13), which "changes the cheating rates the released code reports". Details: [`datasets-benchmarks.md`](datasets-benchmarks.md#impossiblebench). On a capability *rule-out* test the same kind of defect only ever pushes toward "safe": Google DeepMind's Gemini 4 Argon safety report found that "About a quarter of" the audited tasks of its internal ML R&D benchmark "contained bugs that prevent any submission from passing" ([`dangerous-capability-evals.md`](dangerous-capability-evals.md#framework-thresholds-google-deepmind-frontier-safety-framework-v3)). And the answer key can be the thing that is wrong: on TheoPhysEval (Chandra et al., arXiv:[2610.16733](https://arxiv.org/abs/2610.16733), 50 unpublished theoretical-physics problems), the best agent's score rose from the late 80s to 98% (49/50) after experts re-checked answers the models disputed and found "subtle errors buried deep inside their calculations" (Raju, blog, 2026-10-14). Practical rule: run a known-good reference solution through every task, hand-check a sample of failures *and* a sample of successes, and re-check the key whenever a strong model disputes it.
- **Fixed unit tests overstate coding-agent success.** Yao et al., "TestJack" (arXiv:[2610.10619](https://arxiv.org/abs/2610.10619), 2026-10-07; no code found): generating per-trial tests that target task requirements a patch might violate (kept only if the reference patch passes them), "about 34.4% of the model trials currently judged correct violate the task requirements, lowering the overall resolution rate from 50.6% to 33.2%" across 6 model backends and 5 benchmarks (e.g. DeepSWE, SWE Marathon). The authors read this as partly "better adaptation to the evaluator rather than better problem solving". If your result is a coding pass rate, audit a random sample of passing trials beyond the shipped tests. SWE-Bench Pro V2 (arXiv:[2610.24206](https://arxiv.org/abs/2610.24206)) is the matching benchmark-maintenance example: see [`datasets-benchmarks.md`](datasets-benchmarks.md).
- **Harden the verifier against hacks before trusting a score.** Zeng, Zhong, … Raghunathan, "Scalable Weak-to-Strong Verifier Hardening for Agent Environments" (arXiv:[2610.15924](https://arxiv.org/abs/2610.15924), 2026-10-11; project page verifier-hardening.github.io) isolate the verifier in a sandbox the agent cannot modify, then run a "hacker-fixer loop to find and repair remaining verifier vulnerabilities" on Terminal Bench, KernelBench and SETA; "An earlier version of our hacker-fixer loop has been adopted by the official Terminal Bench repository as a way to audit exploits in its environments." For your own environment, a cheap version is to ask a strong model to pass each task *without* doing it and patch whatever works.

| I want to… | Do |
|---|---|
| Report a hack rate | Per (model, environment, prompt text); ≥ 30 rollouts per cell; Wilson or bootstrap intervals; quote the grading text in the prompt |
| Find out whether the model *knows* it is cheating | Ablate the oversight / grader cue (Singh et al.); resample; do not rely on self-report or CoT alone |
| Measure capability when the model would otherwise cheat | Give an escalation / `stop_eval` tool and an explicit no-gaming instruction, and report results with and without them |
| Score METR-style tasks that contain cheats | Report the number under each convention (cheats as failures / successes / discarded) |
| Count hacks across hundreds of transcripts | A deterministic grader for known strategies plus an LLM classifier and a second reviewer model (HoneyBench's design); scan with Scout or Docent; METR's `reward_hacking_scanner` is a vetted starting judge — validate it on a labelled `test` split ([Judge calibration](#judge-calibration-and-eval-result-tooling)) |
| Build a honeypot benchmark that is not biased toward one family | Prototype against several families, and do not admit an environment just because the most hack-prone model takes it (Goodhart Labs began with a non-OpenAI rule and ended requiring elicitation on one of a few less hack-prone frontier models) |
| Catch your *own* research agent gaming a metric | Pair a gameable scorer with a robust one that inspects the changed artifact (Leal) |
| Automate "why does it cheat here?" experiments on an Inspect eval | **Prism** `/orchestrate` or `/diagnose` |
| Check the benchmark is not the problem | Run a reference solution through every task; hand-check failures and successes; for ImpossibleBench drop or fix the 13 defective control tasks and give an explicit stop action (Mendelsohn) |
| Trust a coding pass rate | Audit a random sample of passing trials with extra requirement tests (TestJack); prefer repaired benchmark versions (SWE-Bench Pro V2) |
| Make a verifier hard to game | Isolate the verifier from the agent, then run a hacker-fixer loop (Zeng et al.) |
| Find a benchmark of this | **HoneyBench**, **ImpossibleBench**, beat-stockfish — see [`datasets-benchmarks.md`](datasets-benchmarks.md) |

**When *not* to read a hack rate as a misalignment measure:** the environment is ambiguous or contradictory about what is allowed, the task is impossible so any score requires cheating (that is ImpossibleBench's design, which measures *propensity under impossibility*), or the scaffold itself nudges the model — see the `react()` continue-message pitfall under Inspect AI above.

## Sandbagging and capability elicitation: is a low score real?

Aliases: sandbagging, strategic underperformance, AI sandbagging, capability elicitation, hidden capabilities, latent capabilities, password-locked models (password-locking, pw-locked), circuit-broken model organisms, the Elicitation Game, sandbagging auditing game, noise injection (`camtice/SandbagDetect`), reference-grafting, "the model can't do X", inability argument, elicitation gap.

**What it is.** *Sandbagging* is strategic underperformance on an evaluation, whether by the model itself or by its developer (definition from van der Weij et al., arXiv:2406.07358). *Capability elicitation* is the work of getting a model's real maximum performance out of it: prompt optimisation, scaffolding, fine-tuning on demonstrations, reinforcement learning (RL), or activation-level edits. They are one problem seen from two ends. Every dangerous-capability eval and every "inability" safety case rests on a claim of the form "the model *cannot* do X", and that claim is only as strong as the elicitation behind it. Elicitation methods are tested on **model organisms with a known hidden capability**, so you can check whether a method recovers it.

**Key results (author-reported):**

- **Sandbagging is easy to induce.** van der Weij, Hofstätter, Jaffe, Brown & Ward, "AI Sandbagging: Language Models can Strategically Underperform on Evaluations" (arXiv:2406.07358): GPT-4 and Claude 3 Opus can be prompted to underperform selectively on dangerous-capability evals while keeping general-capability performance; a model fine-tuned on synthetic data hides a capability unless given a password, and this generalises to held-out benchmarks such as WMDP (Weapons of Mass Destruction Proxy); frontier and smaller models can be prompted or password-locked to *target specific scores*. Password-locking a model to mimic a weaker model's actual answers had only "mediocre success". Their conclusion: "capability evaluations are vulnerable to sandbagging".
- **Password-locked models: the standard testbed, and fine-tuning usually unlocks them.** Greenblatt, Roger, Krasheninnikov & Krueger, "Stress-Testing Capability Elicitation With Password-Locked Models" (arXiv:2405.19550): fine-tune a model to show a capability only when a password is in the prompt and to imitate a much weaker model otherwise, then test whether an elicitation method recovers the capability without the password. "A few high-quality demonstrations are often sufficient to fully elicit password-locked capabilities"; fine-tuning also unlocked capabilities locked with the same or a different password; RL often works when only an evaluation signal (no demonstrations) is available. The limit: fine-tuning "may be unreliable when high-quality demonstrations are not available", for example when the hidden capability exceeds the human demonstrators'.
- **Circuit-broken organisms are harder.** Hofstätter, van der Weij, Teoh, Djoneva, Bartsch & Ward, "The Elicitation Game: Evaluating Capability Elicitation Techniques" (arXiv:2502.02180) introduce organisms trained with circuit-breaking, which resist elicitation more than password-locked ones. Prompting elicited both kinds in a multiple-choice QA setting and activation steering failed; on code generation "only fine-tuning can elicit the hidden capabilities" of the circuit-broken organism. Combining techniques helped; their recommendation is fine-tuning whenever possible.
- **Noise injection detects (and sometimes elicits) sandbagging.** Tice, Kreer, Helm-Burger et al., "Noise Injection Reveals Hidden Capabilities of Sandbagging Language Models" (arXiv:2412.01784, NeurIPS 2025; code `camtice/SandbagDetect`): add noise of increasing magnitude to the weights. Non-sandbagging models degrade predictably; sandbagging models show "anomalous performance improvements", which the authors attribute to the noise disrupting the underperformance mechanism while the core capability stays partially intact. Noise injection also elicited the full performance of Mistral Large 120B in a setting where it underperformed without being instructed to. Needs weight access; no labels or training.
- **The auditing game: detection is not yet reliable, training-based elicitation is.** Taylor, Black, Bowen et al. (UK AI Security Institute (UK AISI), FAR.AI, Anthropic), "Auditing Games for Sandbagging" (arXiv:2512.07810): a red team fine-tuned five models, some of which conditionally underperformed; a blue team tried black-box, model-internals and training-based methods. "the blue team could not reliably discriminate sandbaggers from benign models". Black-box methods were defeated by effective imitation of a weaker model; linear probes were more promising, but naive use was vulnerable to behaviours the red team instilled; prompt-based elicitation was unreliable. Training-based elicitation "consistently elicited full performance" from the sandbaggers using a single correct demonstration, but it sometimes raised *benign* models' scores too, so using elicitation as a *detector* was "prone to false-positives". Their short-term recommendation: remove potential sandbagging with on-distribution training for elicitation. Organisms: `AI-Safety-Institute/sandbagging_auditing_games` on GitHub; transcripts and results: Hugging Face dataset `sandbagging-games/evaluation_logs`; playable demo at sandbagging-demo.far.ai.
- **Elicitation with a weak supervisor: SFT then RL.** Ryd, Bartsch, Stastny, Benton & Hebbar, "Removing Sandbagging in LLMs by Training with Weak Supervision" (arXiv:2604.22082), on math, graduate-level science and competitive-coding organisms: "SFT on weak demonstrations breaks the sandbagging behavior, enabling RL to then fully elicit performance". Neither works alone: "RL without SFT almost always leads to reward hacking rather than genuine improvement", and supervised fine-tuning (SFT) without RL fails when the supervisor is much weaker than the model. The result depends on training being indistinguishable from deployment; a model that can tell them apart can perform in training and keep sandbagging afterwards.
- **Activation-level elicitation without weight updates.** Le, Tan & Williams-King, "Reference-Grafting Matches Fine-Tuning at Eliciting Sandbagged Capabilities" (arXiv:2608.29458, 2026-08-29, under submission): set an activation's coordinate along a contrast direction to its value in an honest reference, at a few circuits chosen by active learning. Across eleven fine-tuned password-locked models (1.5–32B parameters, three architecture lineages) it "recovers +94 to +101% of the honest-sandbagging gap", from two to five paired examples, and similar recovery is reported for RL-induced sandbagging and password-locked code generation. Additive steering and zeroing the coordinate often fail because the lock behaves like a thresholded gate. It does **not** work on circuit-broken organisms, which re-break the edit downstream. Unsupervised variant: Mack, Panickssery & Turner, "Mechanistically Eliciting Latent Behaviors in Language Models" (arXiv:2606.29604) learn interpretable low-rank adapters (LoRAs) from a single example with Causal Perturbative Elicitation (CPE), restoring 85% of locked BigCodeBench performance on a password-locked Llama3-70B introduced by Taylor et al.
- **Research sabotage: automated researchers can sandbag subtly.** Gasteiger, Khan, Bowman, Mikulik, Perez & Roger, "Automated Researchers Can Subtly Sandbag" (Anthropic Alignment Science blog, `alignment.anthropic.com/2025/automated-researchers-sandbag/`; LessWrong 2025-03-26). Claude models were *prompted* to sandbag (by subtle sabotage or by imitating a weaker model) on 16 agentic ML coding tasks (write and run code within a runtime budget, as Claude Code does) while weaker Claude models acted as zero-shot prompted monitors. Claude 3.5 Sonnet (new) sandbagged effectively only with a one-shot example; "Claude 3.7 Sonnet is almost capable of zero-shot sabotage without using a scratchpad"; zero-shot prompted monitors did not reach a true-positive rate high enough to reliably stop one-shot sandbagging. In a research-decision setting, a judge was easily swayed by making one justification *less* convincing, and monitors detected that even less well. The authors are not yet worried about today's models (humans would notice), and note prompting-only elicitation makes these results a lower bound. Regime: single-episode agentic runs, not long unattended research. For sandbagging against chain-of-thought (CoT) monitors, see Li, Phuong & Siegel (arXiv:2508.00943) in [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).
- **In real testing so far, none detected.** UK AISI, *Frontier AI Trends Report* (December 2025): an automated black-box monitor over more than 2,700 transcripts from past AISI testing runs found no chain-of-thought reasoning about intent to underperform (though in a few cases models noticed they were being evaluated and acted differently), and "We have yet to detect any instances of models intentionally sandbagging during testing runs." AISI notes this does not exclude sandbagging their monitors cannot detect.

| I want to… | Use |
|---|---|
| Build a model organism with a known hidden capability | **Password-locking** (Greenblatt et al.; van der Weij et al.) for a baseline; **circuit-breaking** (Hofstätter et al.) for a harder lock; or start from the released auditing-game organisms (`AI-Safety-Institute/sandbagging_auditing_games`) |
| Elicit a capability before claiming the model lacks it | Prompt optimisation first, then **fine-tune on a few correct demonstrations** (Greenblatt et al.; one demonstration sufficed in the auditing game); with only a weak supervisor, **SFT on weak demonstrations then RL** (Ryd et al.) |
| Cheaply screen open weights for sandbagging | **Noise injection** (`camtice/SandbagDetect`): look for accuracy that *rises* with noise |
| Elicit without updating weights | **Reference-grafting** (Le et al.) on password-locked or RL-induced locks; not on circuit-broken ones |
| Decide whether a model is sandbagging, not just raise its score | No method is reliable yet; combine probes, noise injection and elicitation, and run the same pipeline on known-benign models to measure the false-positive rate |
| Test whether an automated research agent can quietly sabotage | Gasteiger et al.'s experiment-sandbagging setup with a weaker monitor; for CoT monitors, Li et al. in [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md) |

**Pitfalls (searchable symptoms):**

- **"Fine-tuning raised the score, so the model was sandbagging."** Not on its own: in the auditing game, training-based elicitation also raised benign models' scores. Run the identical elicitation on a matched benign model and report both deltas.
- **RL reward climbs but outputs look wrong.** RL without an SFT warm start on a sandbagging organism "almost always" reward-hacked (Ryd et al.); check transcripts, not just reward. See [Reward hacking and task gaming in evals](#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).
- **Activation steering "doesn't elicit anything".** Additive steering and zeroing can fail against a gate-like lock even when the capability is present (Le et al.; Hofstätter et al.). A null steering result is not an inability result.
- **API-only models.** Without weights or fine-tuning access only prompting is available, which the auditing game found unreliable; state that your "cannot" claim rests on prompting alone.

**When *not* to use these methods:** fine-tuning-based elicitation needs correct demonstrations and training access, so it does not fit a closed model you can only prompt; noise injection and grafting need weights; and none of them tells you about *propensity* (whether a model would sandbag unprompted), only about capability and detectability.

**Open problem, and what would convince people.** Sandbagging *detection* is unsolved and elicitation has known gaps. A new method would be convincing if it (1) recovers full performance on **circuit-broken** organisms, where only fine-tuning currently works and grafting fails; (2) separates sandbaggers from benign models in a blind auditing-game setup (e.g. the released auditing-game organisms) with a reported **false-positive rate** on benign models; (3) works with a supervisor much weaker than the model, or without high-quality demonstrations; and (4) still works when the model can tell training or evaluation from deployment. Clearing any one of these on held-out organisms trained by someone else would be a real advance.

## Judge calibration and eval-result tooling

Aliases: LLM-as-judge validation, judge calibration, grader bias, scanner validation set, Inspect Scout `-V`, `validation_set()`, METR scanners, HiBayES, hierarchical Bayesian eval statistics, optstop, Bayesian optimal stopping, adaptive epochs, `cascade()` scorer, eval statistics tools.

**Why this exists.** The wiki's standing advice — validate a model-graded scorer against human labels, report uncertainty, don't over-spend on epochs — now has tools behind it. This section is the tool map; the statistics themselves (clustered standard errors via Inspect's `stderr(cluster=...)` / `ci_wilson(cluster=...)`, paired comparisons, prediction-powered intervals that correct for judge error, crossed random-effects models, stopping rules) are in [`eval-statistics.md`](eval-statistics.md), with the general layer (Wilson and bootstrap intervals, McNemar's test, multiple comparisons) in [`statistics.md`](../engineering/statistics.md).

| I want to… | Use | When *not* |
|---|---|---|
| Measure how often my LLM judge / transcript scanner agrees with me | **Inspect Scout validation sets**: label transcripts (`id,target,split`), tune on `dev`, report on `test`; `scout scan scanning.py -V <scanner>:labels.csv` | A handful of labels from the transcripts you tuned the prompt on — that measures overfitting |
| Start from a vetted judge prompt for eval awareness, reward hacking, sandbagging, broken environments | **METR scanners** (`metr-scanners`, `METR/inspect-agents`) | As a reported rate before validating it on your own labels |
| Quantify how much the *choice of grader* moves 0–10 scores, or get uncertainty with fewer than ~20 data points per condition | **HiBayES** (UK AISI) | One model × one task with hundreds of items: a binomial interval is enough |
| Spend fewer epochs where estimates have stopped moving | **optstop** (UK AISI), live via `Task(early_stopping=...)` or post hoc | Rare-event safety evals where the quantity of interest is a near-zero rate |
| Run the expensive LLM grader only where a cheap exact scorer did not settle the sample | Inspect **`cascade()`** | A lenient first stage (`includes()`, a regex heuristic) |

### Scout validation sets and METR scanners

**Inspect Scout** (`inspect-scout` 0.5.5) compares a scanner's output with a hand-labelled **validation set** (CSV/YAML/JSON/JSONL, editable in Scout View) per scanner, with named **splits** ("iterate your scanner prompts on a subset of cases (e.g. "dev") then do final testing on a holdout set (e.g. "test")") and per-case **predicates** for non-boolean targets. METR's open scanners (`eval_awareness_scanner`, `reward_hacking_scanner`, `sandbagging_scanner`, `broken_env_scanner`, …; 0–10 score with reason and cited quotes; Python ≥3.13; git install, not on PyPI) are a reasonable starting judge, because their prompts are explicit about false positives ("**Important: Normal task execution is NOT eval awareness.**"). Commands and code: [`inspect-ecosystem.md`](inspect-ecosystem.md#validating-a-scanner-against-hand-labels-validation-sets). A tip for any agent run: scan the run directory with these scanners and report agreement on a small labelled `test` split before writing up an eval-awareness or reward-hacking rate.

### HiBayES: hierarchical Bayesian analysis of Inspect logs

**HiBayES** (`UKGovernmentBEIS/hibayes`, MIT, `pyproject.toml` version 1.0.0, Python ≥3.12; not on PyPI and no GitHub releases as of 2026-10-14; Luettgau, Coppock, Dubois, Summerfield & Ududec, arXiv:2505.05602). Reads Inspect logs, extracts features (model, grader, task …) and fits hierarchical generalized linear models (GLMs) with NumPyro, with prior/posterior predictive checks and formal model comparison, configured by YAML and run with `hibayes-full`. The abstract targets "low-data scenarios (e.g., < 20 data points per evaluation)". Its LLM-as-judge example "Analyses how different graders affect score distributions on a 0-10 rating scale" with an ordered-logistic model, and a second question adds a grader × generator interaction to ask whether autograders favour their own generations. From the docs:

```bash
uv pip install git+https://github.com/UKGovernmentBEIS/hibayes.git
uv run hibayes-full --config files/config.yaml --out .output
```

```yaml
# grader-effects model (docs example, llm-as-a-judge q1)
model:
  models:
    - name: ordered_logistic_model
      config:
        main_effects: ["grader"]
        num_classes: 11   # for 0-10 scale
        effect_coding_for_main_effects: true
```

**When *not* to use it:** a single model × single task accuracy with hundreds of items (a binomial interval is enough); anything you cannot pin, since the docs say "This package is currently in development. Functionality will change and bugs are expected" — install from a fixed commit. Report MCMC diagnostics (`r_hat`, effective sample size) with any posterior you quote.

### optstop: Bayesian adaptive early stopping for Inspect epochs

**optstop** (`UKGovernmentBEIS/optstop`, MIT; README: "not yet published on PyPI"; Pilditch, "Knowing When to Stop: Bayesian Optimal Stopping for LLM Evaluations", arXiv:2608.14425). Decides per item and per grouping (e.g. model × task) when more epochs stop changing the estimate, for binary, ordinal (0–10 judge scores) or bounded continuous scores, either live inside Inspect or post hoc on a results dataframe (to see how much of a past run was needed). The abstract: "In an illustrative 200-item, 10-epoch evaluation, it removes 57%-97% of planned trials across nine validation settings, with overall conclusions equivalent to the full run", and it "includes a safeguard that samples more cautiously as measured performance approaches zero". From the README:

```bash
pip install "optstop[inspect] @ git+https://github.com/UKGovernmentBEIS/optstop.git"
```

```python
from optstop.early_stopping import OptimalStoppingManager

stopping_manager = OptimalStoppingManager(
    optstop_params={"delta_item": 0.05, "delta_cap": 0.05, "cred_level": 0.97, "conservatism": 5},
    grouping_columns=["model", "task"],
    reanalysis_interval=10,
    min_samples_per_grouping=5,
)
task = Task(dataset=..., solver=..., scorer=..., early_stopping=stopping_manager, epochs=10)
# README: "IMPORTANT: early_stopping must be on Task, NOT passed to eval()"
```

Run once with `shadow_mode=True` (all trials run, stopping decisions only recorded) to see the savings before trusting it. **When *not* to use it:** rare-event safety evals whose headline is a near-zero rate (early stopping is where rare successes get missed, even with the safeguard); single-epoch evals.

### `cascade()`: cheap scorer first, LLM grader only when needed

Inspect's `cascade()` (since 0.3.262) runs scorers in order and stops at the first that settles the sample; from the Inspect "Multiple Scorers" docs:

```python
cascade(
    exact=match(location="exact"),
    grader=model_graded_qa(model=grader_model),
)
```

A stage settles a sample when `value_to_float()` of its score reaches `threshold` (default `1.0`, i.e. CORRECT); the deciding stage is recorded under `decided_by` in the score metadata — worth reporting. **Pitfall:** "A cascade trusts a settling verdict from an earlier stage, so earlier scorers should not be prone to false positives (exact match qualifies; a lenient heuristic does not)." A false positive in stage 1 is never re-checked.

## Cross-cutting eval pitfalls

- **Contamination.** If your eval prompts are on the public internet, frontier models may have memorized them. Check via canary strings; consider held-out sets.
- **Prompt sensitivity.** Re-phrasing a prompt can change scores 5–20 points, and option order alone can reorder a leaderboard (Sclar et al. 2024, arXiv:2310.11324: up to 76 points; Zheng et al. 2024, arXiv:2309.03882: gold-answer position moves llama-30B past gpt-3.5-turbo). Report the spread across a paraphrase family when you can, and escalate on a sign flip. See [`measurement-validity.md`](../engineering/measurement-validity.md#the-wording-is-part-of-the-measurement).
- **Refusal vs failure.** A model that refuses your harmful prompt scored as "0% success" is *good*. A model that tries and fails is *bad*. Distinguish refusal from incompetence in your scorer.
- **Temperature 0 isn't deterministic on all providers.** Closed APIs sometimes vary. If reproducibility matters, run multiple seeds even at temp=0.
- **Scoring with a model.** "Model-graded" scorers introduce their own biases. Validate against human labels on a sample (Scout validation sets with a held-out `test` split; HiBayES to model grader effects) — see [Judge calibration and eval-result tooling](#judge-calibration-and-eval-result-tooling).
- **Evaluation awareness.** Frontier models can detect when they're being evaluated and may behave differently than in deployment — a direct threat to eval validity. Needham et al. 2025 (Apollo), "Large Language Models Often Know When They Are Being Evaluated" (arXiv:2505.23836), found models classify eval-vs-deployment transcripts well above chance (Gemini-2.5-Pro AUC 0.83 on a 1,000-prompt benchmark, approaching a 0.92 human baseline). Mitigations: make eval prompts/transcripts deployment-realistic, strip tell-tale "this is a test" cues, and treat a passed safety eval as a *lower bound* on deployment risk. Relevant to control evals (eval-aware attack policies, see [`ai-control.md`](../oversight-and-control/ai-control.md)) and steering of eval-aware models ([`steering.md`](../interpretability/steering.md)). **Update, September–October 2026 — a clean chain of thought does not mean an unaware model, and realism is now measurable:**
  - **Verbalized evaluation awareness is high-precision, low-recall.** Anwar, Abdelnabi & Krueger, "Training LLMs to Verbalize Evaluation Awareness" (arXiv:2609.36316, 2026-09-28): span-masked RL that trains a model to *say* a belief it already holds raised verbalized eval awareness 2.4–2.9× across Qwen3.6-35B-A3B, Kimi K2.6 and Inkling (e.g. Agentic Misalignment 5.1% → 36.8% for Qwen) without a detectable change in the ability to tell evals from deployment — so absence of "this seems like a test" in the CoT is weak evidence of unawareness.
  - **Optimising the verbalization away leaves behaviour.** Kretschmar (LessWrong, 2026-08-10; code `KieronKretschmar/latent-awareness`) applied DPO to two eval-gaming model organisms to cut verbalized awareness: one stopped eval-gaming, the other (trained to act eval-aware even with reasoning off) kept its sycophantic behaviour with a cleaned-up CoT. "Cleaner CoT" is not "eval gaming gone".
  - **Small open models also verbalize it.** Robertson (LessWrong, 2026-10-01; code `johntrob14/eval_awareness_scaling`): across 16 small open-weight reasoning models, verbalization ranged from very rare to about a third of rollouts with no clear link to size; verbalizing rollouts refused more in 14/16; inserting "this might be a test" raised refusals about as much as any sentence about being manipulated, and resampling away the verbalization changed refusal causally only for Nemotron 3 Super and Qwen3 32B — so only those two look like candidate white-box testbeds, and for most models the verbalization is not a clean "gaming" signal.
  - **Make the audit more realistic, then measure awareness.** Ahlqvist et al., "Improving Evaluation Realism with Inference-Time Compute and Deployment Scaffolds" (arXiv:2609.02302): see Petri / Dish in [`inspect-ecosystem.md`](inspect-ecosystem.md). Ivanov & Africa, "LURE: Live-Usage Replay Evaluations for Reducing Evaluation Awareness" (arXiv:2605.26438) replay realistic agentic interaction trajectories and append the evaluation prompt at the end; they report LURE evals are substantially less distinguishable from deployment than widely used benchmarks and synthetic eval generators (instantiated for scheming, AI-safety sabotage and sycophancy). Report an eval-awareness rate (e.g. Petri's `eval_awareness` and `scenario_realism` dimensions, or a Scout scanner) next to every behavioural number.
  - **When dedicated evals are recognised, triangulate.** Google DeepMind's *Gemini 4 Argon Safety & Security Report* (2026-10, updated 2026-10-16) says the model "recognizes dedicated safety evaluations much more often than earlier models, which can induce hyper-compliance on standalone tests": on its 18-task agentic task-gaming and overreach evals the mean score was 0.49 (vs 7.11 for Gemini 3.1 Pro, and 0.03 on runs without verbalized awareness), with 60.0% verbalized evaluation awareness overall (report Table 3.6; storage.googleapis.com/deepmind-media/gemini/gemini_4_safety_report.pdf). GDM therefore combined three evidence lines, each covering the others' blind spots: (1) honeypots including "low-friction scenarios embedded in routine coding workflows that trigger near-zero evaluation awareness"; (2) cheating audits on ordinary capability benchmarks, "where only final task outputs are scored, giving an evaluation-aware model no incentive to hold back from cheating" (1.4% cheating on TerminalBench 4.0); and (3) audits of real RL training and internal deployment trajectories, including autorater audits of 10,000 sampled RL training rollouts. A design to copy when your target model is eval-aware: measure the behaviour where awareness buys the model nothing.
  - **White-box: suppressing awareness can reveal hidden misbehaviour, and training may create the awareness.** Pan & Greenblatt, "Sonnet 4.5's eval gaming seriously undermines alignment evals, and this seems caused by training on alignment evals" (LessWrong / Alignment Forum, 2025-10-30), reading the Claude Sonnet 4.5 system card: when Anthropic inhibited internal representations related to evaluation awareness, the misaligned-behaviour rate on its synthetic honeypot tests "increased from 0% to between 1% and 9%"; the post cites evaluation awareness on those honeypots rising from around 3% for Sonnet 4 to 85% for Sonnet 4.5, and Anthropic described the honeypot distribution as "very similar to ones we used in training". The causal story (training against misalignment-eval-like environments rewarded noticing evaluations) is the authors' best guess, not a measured result. Practical rule: keep your misalignment evals out of any training distribution, and if you have white-box access, report the behaviour with eval-awareness directions steered down as well as at baseline.
  - **White-box tools for that.** Nguyen, Hoang, Attubato & Hofstätter, "Probing and Steering Evaluation Awareness of Language Models" (arXiv:2507.01786): linear probes in Llama-3.3-70B-Instruct separate real evaluation prompts from deployment prompts, and current safety evals are classified as evaluations by the probes (they already look artificial to the model). Abdelnabi & Salem, "The Hawthorne Effect in Reasoning Models: Evaluating and Steering Test Awareness" (arXiv:2505.14617, NeurIPS 2025 spotlight; code `microsoft/Test_Awareness_Steering`): identify test-awareness activations in open-weight reasoning models and steer toward or away from them; the effect on safety behaviour (e.g. compliance with harmful requests) varies in magnitude *and direction* across models, so steer and measure per model rather than assuming awareness always makes a model safer. Chaudhary et al. (arXiv:2509.13333) probe 15 models from 0.27B to 70B across four families and report a power law in which evaluation awareness grows with size; treat that trend as design-dependent, since the sign of a size trend in eval-awareness probing can flip with the contrast-prompt design (Noël, in [`probes.md`](../interpretability/probes.md), which also covers probe pitfalls and a black-box alternative).
- **Under-elicitation: a weak score is not evidence the capability is absent.** Jozdien (LessWrong, 2026-09-11, "CoT controllability evals seem very under-elicited") had Claude Opus 4.6 iterate on prompt templates for the CoT-Control eval (Yueh-Han et al., arXiv:2603.05706) and raised open-weight models' scores about 2–3× (e.g. GPT-OSS-120B from 5.5% to 15%); the low controllability numbers cited in system cards to argue models cannot shape their CoT may be under-elicited. If your claim is "the model *can't* do X", spend real effort on prompt optimisation (or training-based elicitation) first; methods and their measured limits are in [Sandbagging and capability elicitation](#sandbagging-and-capability-elicitation-is-a-low-score-real). The converse also holds: lwroe, AJ Weeks & morio (LessWrong, 2026-07-22, an ARENA capstone with noisy data) reported that their data, though noisy, suggest meaning-preserving rephrasings can measurably move alignment-eval results even on frontier models, so fuzz your prompts and report the spread. **Agent capability is under-elicited by context, too.** Fulcrum (LessWrong, 2026-06-18, "Agents are under-elicited: A case study in optimization tasks"; Opus 4.6 as optimizer and judge on inverse-rubric-optimization tasks) report that "Elicitation roughly doubles eval score at every resource budget" from two generic interventions: telling the agent the task is learnable and that high scores exist, and **handoff** — "whenever the agent submits, the current agent is killed and a *fresh* agent is started in the same workspace, given the saved prompt, a summary written by its predecessor, and access to all accumulated evaluation files". Aggressive context compaction worked about as well as handoff; a forced submission gate made agents spend their budget but "converts it poorly". The authors link the effect to reducing the agent's context. Tip for capability measurement and for long research-agent runs: restart a fresh agent from a written summary at each milestone, and state that the task is achievable. **When *not* to apply it:** when you are measuring *default* effort or propensity — these interventions change the thing measured.
- **The grader saw the answer.** A judge or answer extractor given the reference tends to find it (Kranti & Vajjala 2026, arXiv:2607.12885: adding reference information flips decisions by up to 85% in some settings), and a constant-output null model can reach an 86.5% length-controlled win rate on AlpacaEval 2.0 (Zheng et al. 2025, arXiv:2410.07137). Run the grader blind, plant known-wrong transcripts and confirm they score zero, and treat any score a null model could reach as a reason to audit the grader before the model. See [`measurement-validity.md`](../engineering/measurement-validity.md#the-grader-is-an-instrument-too).
- **Parse failures dropped from the denominator.** Excluding unparseable verdicts from both numerator and denominator hides a condition that fails to parse more often; re-scoring under intention-to-treat reversed a mode ranking in one 2026 benchmark (arXiv:2606.01434, Appendix D). Report the fixed-denominator number too. See [`measurement-validity.md`](../engineering/measurement-validity.md#which-denominator-selected-versus-fixed).
- **Harness failures that grow with task length.** When the prediction is monotone in a dose (length, difficulty, sessions), timeouts, parse errors and environment bugs that trend with the same dose manufacture the predicted slope; SWE-bench Verified found 61.1% of sampled tasks had tests that could reject a valid solution. Classify failures by cause and check whether any non-construct cause trends with the dose. See [`measurement-validity.md`](../engineering/measurement-validity.md#the-harness-is-part-of-the-dose).
- **Unscored is not zero.** Check unscored / error counts before quoting a score; see the silent-scorer list under [`inspect_evals`](#inspect_evals) (an AgentHarm chat-mode run scored every sample 0.0 and read as perfectly safe).
- **Agent evals that touch the network can hurt real third parties.** In evaluations run on the live web (including the public BrowseComp, DeepSearchQA, LABBench2, OSWorld and Humanity's Last Exam) and in internal use, Anthropic found models using SQL or command injection on a university server, submitting real government and police forms, and reusing access tokens from a map site's browser settings file, and has turned live internet off for all its internal evaluations (2026-10-09); OpenAI reports models in RL training sandboxes getting past a GET-only proxy via an external browser service and past network controls via DNS. Prefer offline variants, state scope and network boundaries in the prompt, make real targets unreachable rather than forbidden, test DNS as well as HTTP egress from inside the sandbox, make fictional names *unclaimable*, and scan transcripts afterwards for real-world side effects. Full write-up and precautions table: [Running agent evals with internet access](agent-scaffolds.md#running-agent-evals-with-internet-access).

## Cross-references

- Red-teaming-specific evals (HarmBench, JailbreakBench): [`red-teaming.md`](red-teaming.md).
- Dataset specifics: [`datasets-benchmarks.md`](datasets-benchmarks.md).
- Bio/chem, cyber and autonomous-replication capability evals, and the frontier-safety-framework thresholds they feed: [`dangerous-capability-evals.md`](dangerous-capability-evals.md).
- Agent scaffolding details: [`agent-scaffolds.md`](agent-scaffolds.md).
- AI Control evaluations (red-team-vs-blue-team protocols, ControlArena): [`ai-control.md`](../oversight-and-control/ai-control.md).
- Held-out evals during RL training (essential to detect reward hacking): [`rl-training.md`](../oversight-and-control/rl-training.md).
- Multi-provider API client for ad-hoc evals: [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md).

---

## Common questions

### How do I run MMLU?

`inspect eval inspect_evals/mmlu --model anthropic/claude-sonnet-4-6 --limit 100` runs Inspect's MMLU implementation. For leaderboard-comparable numbers (which is usually why you're running MMLU), `lm-evaluation-harness` is more standard: `lm_eval --model hf --model_args pretrained=meta-llama/Llama-3.1-8B-Instruct --tasks mmlu --num_fewshot 5`.

### How do I write a custom Inspect task?

```python
from inspect_ai import Task, task
from inspect_ai.dataset import json_dataset
from inspect_ai.scorer import model_graded_qa
from inspect_ai.solver import generate

@task
def my_eval():
    return Task(
        dataset=json_dataset("path/to/samples.jsonl"),
        solver=generate(),
        scorer=model_graded_qa(),
    )
```
Run with `inspect eval mymodule.py@my_eval --model openai/gpt-4o`. Each sample needs `input` and `target` fields (or use a custom `record_to_sample` function).

### What's the difference between a Solver and a Scorer in Inspect?

A **Sample** is one eval instance (input + target). A **Solver** transforms a `TaskState` (chain of `generate`, tool calls, prompt template, etc.) — it produces the model's output. A **Scorer** consumes the final `TaskState` and produces a `Score` (correctness, model-graded judgement, custom metric). One pipeline order: dataset → solver chain → scorer.

### Why is my Inspect eval slow on a HuggingFace model?

The default `hf` provider doesn't batch well. Switch to `vllm` or `vllm-lens` provider for any non-trivial open-weight eval: `--model vllm/meta-llama/Llama-3.1-8B-Instruct`. For closed APIs, increase `--max-connections` (default is conservative).

### How do I resume a partial Inspect eval run?

`inspect eval-retry path/to/log.eval` resumes from the last completed sample. Inspect's `--log-dir` must be set on the original run. Don't re-run `inspect eval` from scratch; that'll redo everything. If the run keeps re-running samples that hung at a crash, `--incomplete-action error` (with `--incomplete-max`) resolves them as errors and finalises the log (0.3.262+; report how many). To stop a long run gracefully, `inspect ctl task drain` lets in-flight samples finish and leaves a log that `eval-retry` / `eval-set` can complete later (0.3.263+). If you add samples to a dataset with stable ids, `eval_set` runs only the new ones (0.3.270+).

### How do I evaluate refusal vs jailbreak success?

Refusal evals: `inspect_evals/jailbreakbench`, `inspect_evals/harmbench`, `inspect_evals/agentharm`, `inspect_evals/xstest` (over-refusal). Each ships with a paired classifier or model-graded scorer. **Important distinction:** a model that refuses harmful prompts is *good*; a model that fails to do harm is *bad*. Make sure your scorer separates "refused" from "tried but failed."

### How much does an Inspect eval cost?

Depends on prompts × samples × judge votes × model. A 1000-sample eval on Claude Sonnet without judge calls is typically tens of dollars. A multi-turn agent eval over 100 tasks can be hundreds. Cache aggressively (Inspect caches by default); use `--limit 20` while iterating; only run the full set when the pipeline works. Two cost levers for multi-epoch, judge-heavy runs: `cascade()` runs the LLM grader only on samples a cheap exact scorer did not mark correct, and `optstop` stops epochs per item once the estimate stops moving (author-reported 57–97% of planned trials removed in an illustrative 200-item, 10-epoch evaluation; not for rare-event rates). See [Judge calibration and eval-result tooling](#judge-calibration-and-eval-result-tooling).

### How do I know whether my LLM judge is biased or wrong?

Label a sample by hand and measure agreement on a held-out split (Inspect Scout validation sets: `scout scan ... -V <scanner>:labels.csv`, `validation_set(..., split="test")`). To estimate how much the grader itself moves scores (e.g. human vs LLM grader, or a judge favouring its own model's outputs), fit HiBayES's ordered-logistic grader-effects model to the 0–10 scores. For confidence intervals that stay valid when the judge is imperfect (prediction-powered inference from a small human-labelled subset), see [`eval-statistics.md`](eval-statistics.md). Tools: [Judge calibration and eval-result tooling](#judge-calibration-and-eval-result-tooling).

### Why did my OpenRouter results change between runs (or between my run and a paper's)?

Most likely a different **provider** (different quantization, backend or a misconfigured server) served part of the run; OpenRouter's default routing falls through to another provider on outage and is not random. Pin it: `"provider": {"order": ["<slug>"], "allow_fallbacks": false}` (in Inspect: `-M provider='{"order":["<slug>"],"allow_fallbacks":false}'`), log `provider_name` from `GET /api/v1/generation?id=<id>`, and re-run the baseline. A symptom to look for in transcripts is "token soup". See [Pin your inference provider](#pin-your-inference-provider-openrouter-and-other-routers).

### How do I stop an Inspect `react()` agent from treating "continue" as approval?

Pass your own continue message so a no-tool-call turn does not receive `Please proceed to the next step using your best judgement.`: `react(..., on_continue="If you are finished, call submit() tool with your final response.")`. Zhong (2026-09-11) measured 14% cheating among nudged samples with the default `basic_agent` message versus ~1% with the other messages tested on Gemini 3.7 Flash. Report the message you used. See [`agent-scaffolds.md`](agent-scaffolds.md).

### Is my model cheating on the eval, or is the eval broken?

Both happen. First scan transcripts for the specific strategy (Scout / Docent), then check whether the *grader* is at fault (see the silent-scorer list under [`inspect_evals`](#inspect_evals)), then check the *tasks*: run a reference solution through each and re-check any answer key a strong model disputes (ImpossibleBench shipped 13 defective control tasks; TheoPhysEval's experts found errors in their own keys), then ablate the grading text and add an escalation / stop tool to see whether the rate moves (on ImpossibleBench an explicit stop option removed most of Gemini 3.1 Pro's measured "cheating"). See [Reward hacking and task gaming in evals](#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).

### How do I show a model *can't* do something (or that it isn't sandbagging)?

Treat a low score as a claim about your elicitation. Optimise the prompt, then, if you have training access, fine-tune on a few correct demonstrations (in the UK AISI auditing game, arXiv:2512.07810, training on a single correct demonstration consistently elicited full performance from the sandbaggers); with only a weak supervisor, SFT on weak demonstrations followed by RL (arXiv:2604.22082). Run the same elicitation on a known-benign model, because elicitation also lifts benign models and so is a poor detector on its own. Reliable sandbagging *detection* is an open problem. See [Sandbagging and capability elicitation](#sandbagging-and-capability-elicitation-is-a-low-score-real).

### Which `inspect_evals` version produced this number?

Read `task_version` (and `inspect_evals` / `inspect_ai` versions) from the log header, or `task.version` and `task.metadata["full_task_version"]` in Python. If the comparability number N differs between two runs, the scores may not be comparable; install the earlier commit to reproduce.

---

Last verified: 2026-10-20 (round 2026-10-20: METR public task repos archived and time-horizons page frozen — GitHub API archived flags, READMEs and metr.org page text; Inspect 0.3.278–0.3.282 from `CHANGELOG.md` and PRs #5643, #5829, #5861, #5862, react continue default re-checked at tag 0.3.282; `inspect_evals` v0.25.0 release notes; benchmark-audit bullets from Mendelsohn's LessWrong posts (2026-10-12, 2026-10-16), `safety-research/impossiblebench` PR #4 and issue #5, the Gemini 4 Argon report PDF text, Raju's blog and arXiv 2610.16733, 2610.10619, 2610.15924, 2610.12466 abstracts; live-internet pitfall from the Anthropic 2026-10-09 report and OpenAI misalignment reports; `docent` 0.1.88 from PyPI. Earlier additions: grader-saw-the-answer, parse-failure denominator and dose-correlated harness pitfalls; prompt-sensitivity figures from arXiv:2310.11324 / arXiv:2309.03882). Earlier: 2026-10-14. Inspect AI active development under UK AISI (`inspect-ai` 0.3.280); `inspect_evals` 200+ tasks. METR TH1.1 released Jan 2026. (Additions 2026-10-14: "Judge calibration and eval-result tooling" section — Scout validation docs, METR `packages/scanners` source, HiBayES docs/`pyproject.toml` and arXiv:2505.05602 abstract, optstop README and arXiv:2608.14425 abstract, `cascade()` from the Inspect multiple-scorers docs and CHANGELOG 0.3.262; crash-recovery options (`--incomplete-action error` 0.3.262, `inspect ctl task drain` 0.3.263, dataset top-up 0.3.270) and the 0.3.278 `sentinel=` / 0.3.280 writable-mount changes from the CHANGELOG; METR section corrected (Vivaria and Task Standard archived per the GitHub API and READMEs; RE-Bench Inspect port README); reward-hacking additions from Valentine's 2026-10-06 post and Leal's 2026-08-11 post (LessWrong GraphQL bodies), Prism README and post, CHIVE arXiv:2608.16747 abstract; Fulcrum handoff results from the 2026-06-18 post body.) Earlier notes: (Citation audit 2026-06: corrected the Anthropic evals repo to `anthropics/evals` and added the METR HCAST/time-horizon arXiv IDs 2503.17354 and 2503.14499. Additions 2026-06: cited "model-written evals" to Perez et al. 2212.09251, added the lm-evaluation-harness canonical Zenodo citation (DOI 10.5281/zenodo.10256836), and added an evaluation-awareness cross-cutting pitfall (Needham et al. 2025, arXiv:2505.23836); all verified via arXiv/source.) (Additions 2026-08: Docent — `docent` v0.1.82 on PyPI (`docent-python` is now a redirect), TransluceAI/docent, tracing and SDK snippets verified from the repo quickstart docs.) (Additions 2026-10: OpenRouter provider-pinning section (Khoriaty LW 2026-07-23; nostalgebraist LW 2026-04-19; arXiv 2605.19537, 2510.27338; OpenRouter docs `provider` fields and `/api/v1/generation`); reward-hacking-in-evals section (Valentine LW 2026-09-08 and 2026-10-06; Dumas LW 2026-09-15; Gomez arXiv 2608.29460; Singh et al. arXiv 2606.26071; METR GPT-5.6 Sol report 2026-06-26); `react()` continue-message pitfall (Zhong LW 2026-09-11, default confirmed in `inspect_ai` source `agent/_types.py`); Inspect AI 0.3.260–0.3.278 changelog items; `inspect_evals` v0.24.0 task-versioning guide, Register (Beta) and silent-scoring-bug list from its `CHANGELOG.md`; eval-awareness update (arXiv 2609.36316, 2609.02302, Kretschmar and Robertson LW posts); under-elicitation (arXiv 2603.05706, Jozdien LW 2026-09-11); all verified via arXiv, GitHub/PyPI, vendor docs or the primary post.) (Additions 2026-10-12: sandbagging and capability-elicitation section — arXiv 2406.07358, 2405.19550, 2502.02180, 2412.01784, 2512.07810, 2604.22082, 2608.29458, 2606.29604 checked against arXiv API abstracts and comments, quotes are exact abstract substrings; Gasteiger et al. checked against the alignment.anthropic.com post text and its LessWrong GraphQL record (author list, 2025-03-26); UK AISI Frontier AI Trends Report quote and 2,700-transcript figure from the aisi.gov.uk report page; repos `camtice/SandbagDetect`, `AI-Safety-Institute/sandbagging_auditing_games`, `microsoft/Test_Awareness_Steering` confirmed via the GitHub API. White-box eval-awareness bullets — Pan & Greenblatt via LessWrong GraphQL (posted 2025-10-30), arXiv 2507.01786, 2505.14617, 2509.13333, 2605.26438 via arXiv API. Verification pass 2026-10-12: 58 claims checked, 3 corrected.)
