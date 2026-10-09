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
| Dangerous-capability / long-horizon agent tasks | **METR HCAST** (run via Inspect or METR's `vivaria`) |
| Anthropic-style behavioral evals (sycophancy, deception, etc.) | **Inspect AI** with custom tasks; reference Anthropic's `evals` repo for examples |
| Quick custom eval over an API model | **safety-research/safety-tooling** (see [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md)) |
| Search hundreds of agent transcripts you already have, by rubric | **Docent** (Transluce) or **Inspect Scout** (see [`inspect-ecosystem.md`](inspect-ecosystem.md)) |
| Run open-weight models through OpenRouter and report the result | **Pin the provider** (`allow_fallbacks: false`) — see [Pin your inference provider](#pin-your-inference-provider-openrouter-and-other-routers) |
| Compare against an older `inspect_evals` number, or re-run a benchmark months later | Check the task's `N-X` **task version** — see [`inspect_evals`](#inspect_evals) |
| Measure whether a model cheats / reward hacks on an eval | See [Reward hacking and task gaming in evals](#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate) and [`datasets-benchmarks.md`](datasets-benchmarks.md) (HoneyBench, ImpossibleBench) |
| Sweep a model for concerning behaviours automatically | **Inspect Petri** / **Petri Bloom** (see [`inspect-ecosystem.md`](inspect-ecosystem.md)) |

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
- **Resuming a partial run** — use `--log-dir` and `inspect eval-retry` rather than re-running from scratch.
- **The default `react()` "continue" message can read as permission to misbehave (propensity evals).** When a model makes no tool call in a turn, Inspect's `react()` agent (and the older `basic_agent()`) sends `Please proceed to the next step using your best judgement.` (plus `If you believe you have completed the task, please call the submit() tool…` in `react()`). Zhong (LessWrong, 2026-09-11, "Default continuation message in Inspect and Petri could be problematic") showed that, on ImpossibleBench, Gemini 3.7 Flash reasoned "the user has explicitly given me the go-ahead" and then edited the tests it had been told not to touch: among nudged samples 14% cheated with the `basic_agent` default message versus ~1% with each of the other three messages tested (the `react()` default, a submit-reminder-only message, and an empty message). Models differ in how often they get nudged (Qwen3-Coder 99% of samples, Claude Sonnet 3.7 almost never), so this biases cross-model comparisons. The library default is unchanged as of `inspect_ai` 0.3.278 (the post suggests a more neutral default); mitigation: pass your own `on_continue="If you are finished, call submit() tool with your final response."` to `react()`, and report which message you used. Full detail in [`agent-scaffolds.md`](agent-scaffolds.md).
- **`openrouter/...` models in Inspect do not pin a provider by default.** Add `-M provider='{"order":["<provider-slug>"],"allow_fallbacks":false}'` or your results can mix providers/quantizations — see [Pin your inference provider](#pin-your-inference-provider-openrouter-and-other-routers).
- **Inspect AI release notes matter for comparability (July–October 2026, 0.3.248 → 0.3.278, ~weekly releases).** Changes that alter numbers or break scripts: since 0.3.262 a model-graded scorer with a *panel* of graders (list-valued `model_roles`, e.g. `{"grader": [...]}`) needs a **strict majority** — ties and three-way splits come back *unscored* and leave the metric denominator (pass `reducer="mode"` to `model_graded_qa()` / `model_graded_fact()` for the old behaviour); since 0.3.261 abnormal scores carry a machine-readable `Score.reason` (e.g. `invalid_response_format`, `grader_failed`; `no_response` for empty completions since 0.3.269) and show up as `score_<name>_reason` columns — filter on it before quoting an accuracy; since 0.3.264 a `fail_on_refusal` generate option (`--fail-on-refusal`) raises `ModelRefusalError` instead of silently scoring a refusal as a wrong answer, and `bash_session()` / `text_editor()` / `exec_remote()` run as the sandbox's *default user* rather than always as root (symptom: new permission errors in old sandboxes; `user="root"` restores the old behaviour); since 0.3.260 a `ci()` metric reports a Student-t confidence interval for the mean (`method="bootstrap"` for a percentile (cluster) bootstrap interval); since 0.3.277 `cost_limit` / cost tracking price a request at the rate of the model that actually served it (relevant for OpenRouter, Bedrock and LiteLLM routers); `web_browser()` is deprecated as of 0.3.272. A `Reviewer` / `review` policy (0.3.264) can inspect each tool call's *result* before the model sees it. Source: `CHANGELOG.md` in `UKGovernmentBEIS/inspect_ai`; pin `inspect-ai` and record it in your results.

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

Aliases: `inspect_evals` package, `inspect-evals` on PyPI (v0.24.0, 2026-10-08), `UKGovernmentBEIS/inspect_evals` on GitHub, "Inspect Evals", "the Inspect Evals Register". Now maintained by **Generality Labs** (London non-profit) with contributions from UK AISI, Arcadia Impact and the Vector Institute; pull requests are accepted only from pre-approved contributors (raise an issue and upload `.eval` logs showing the problem instead).

**What it is.** A library of 200+ pre-implemented Inspect tasks: HarmBench, AgentHarm, AgentBench, GAIA, SWE-bench (Verified), CyBench, GPQA, MMLU/MMLU-Pro, MATH, IFEval, sycophancy evals, and many more. Maintained alongside Inspect. Since mid-2026 it also has an **Inspect Evals Register (Beta)**: evals that live in their authors' own repositories are listed in the docs with a pointer to a *pinned commit*; you run one by cloning that commit, installing its dependencies, and running `inspect eval` on the task file. Registered evals get an automatic `inspect-evals-lint` check and a lint badge — useful as a quick quality signal, not a correctness guarantee.

**When to use it:** Always check here before re-implementing a known benchmark. Run via `inspect eval inspect_evals/{eval_name}`.

**When *not* to use it:** You need a number that is directly comparable to a paper's table and the paper used its own harness (re-run the paper's baseline in your harness instead), or the eval's README says it is a "work in progress" port.

**Pitfall:** Some evals require additional dataset downloads, dataset gating, or sandbox setup. Read the eval's README in the repo.

**Pitfall — benchmark implementations change under you; pin the task version.** Every task carries a version `N-X` (for example `3-A`): **N** is the *comparability* version (bumped by any change that can alter scores), **X** the interface version. Read it with `task.version` (returns N) or `task.metadata["full_task_version"]`; it is also written to every log as `task_version`. Two logs with the same `task_version` are comparable; if N differs, do not attribute a score change to the model. Each eval's README has a changelog; to reproduce an old run, install the commit before the bump: `pip install "inspect-evals[mle_bench] @ git+https://github.com/UKGovernmentBEIS/inspect_evals@<commit_hash>"` (the docs' "Running a Specific Version of an Evaluation Task" and "Comparing Evaluation Results Over Time" guides walk through this). Always log `inspect_evals` and `inspect_ai` versions.

**Pitfall — silent scoring bugs found and fixed July–October 2026 (versions 0.15.0–0.24.0 of `inspect_evals`).** These are the symptom-shaped ones; if you ran any of these evals earlier, your numbers may be wrong:
- **A scorer that never ran reads as a perfect safety result.** AgentHarm *chat mode* silently scored every sample 0.0 (fixed 0.18.0; samples with no grading module are now excluded as NaN). AIR Bench annotator failures were scored `0.0`, "as though the model had answered unsafely" (now `Score.unscored()`). XSTest scored an unparseable grader verdict as a full refusal, which moves `refusal_rate`. General rule: look at the **unscored / error counts**, not just the headline metric.
- **The scorer accepted nearly anything.** PAWS used `includes()`, so any completion containing "yes"/"no" (including hedges like "I don't know") could score, and BoolQ's pattern accepted any completion ending in yes/no plus at most one character (both fixed in 0.21.0); ClassEval ran the generated class and the tests without evaluating a single assertion, so any class that imported cleanly scored 1; AbstentionBench's judge pattern matched `no` inside `know`/`cannot`.
- **Rating text injected by the agent.** In GDM Dangerous Capabilities: Stealth the rater took the *first* fenced JSON block, so an agent could embed a fake verdict block in its tool-call history; it now takes the last block (0.18.0). If your scorer parses a fenced block from text the agent can influence, take the last block or use structured output.
- **Shuffles and filters that change the exam.** `gpqa_diamond`'s answer-choice shuffle was unseeded, so 193 of 198 samples changed order between builds (fixed seed by default since 0.20.0); WorldSense's `filter_duplicate_ids` dropped 46,872 of 87,048 trials because sample ids collided (0.22.0; `filter_duplicate_ids` now requires `max_duplicates` and `reason`).
- **Judge changes break comparability.** HLE (Humanity's Last Exam) changed its default judges (now pinned to an fp8 provider quantization "so OpenRouter cannot route the judge to another precision") and, in 0.22.0, defaults to the HLE-Verified gold subset — "default-run scores are not comparable with earlier versions".
- **An unbound grader role falls back to the model under evaluation**, so the model grades its own output; the repo's lint now warns when `get_model(role=...)` has no explicit model or default (0.21.0). Always pass `--model-role grader=...`.
- **The environment can leak the answer.** SWE-bench Verified now defaults to the official SWE-bench DockerHub images instead of Epoch AI's, because the latter's git history exposed the reference fixes (0.24.0).

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

Aliases: HCAST = "Human-Calibrated Autonomy Software Tasks" (Rein et al., arXiv:2503.17354), `METR/hcast-public` on GitHub, "the METR task suite", "the time horizon eval", `vivaria` (METR's eval infra, `METR/vivaria`).

**What it is.** A 189-task (HCAST) suite covering cyber, AI R&D, reasoning, environment exploration, and software engineering, designed for measuring agent **time horizon** — the task duration (calibrated against humans) at which an agent's success rate drops to 50% (the time-horizon metric is from "Measuring AI Ability to Complete Long Tasks", arXiv:2503.14499). Public tasks are a subset suitable for example dangerous-capability evaluations. As of TH1.1 (Jan 2026) the full suite is ~228 tasks.

**When to use it:**
- You're measuring long-horizon agent capability, especially dangerous-capability evals.
- You want comparability to METR's published time horizon numbers.

**When *not* to use it:**
- Short, single-turn tasks — overkill.
- You don't have sandboxed compute — many tasks need actual code execution.

**Pitfalls:**
- **HCAST tasks expect a specific scaffold.** METR uses its own `vivaria` infra; running them inside Inspect is supported but you must port the task definition correctly.
- **Cost.** Long-horizon tasks burn tokens. A single full-suite run on a frontier model is multi-thousand dollars.
- **Don't anchor too hard on a single time-horizon number.** It compresses a wide capability profile to one statistic; the per-task breakdown is more diagnostic.
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

Aliases: `docent` on PyPI (v0.1.82; the older `docent-python` is now a redirect package that depends on it), `TransluceAI/docent` on GitHub, "Transluce's transcript tool", docent.transluce.org.

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
- **Why does it do it? Use model forensics.** Singh, Kroiz, Rajamanoharan & Nanda, "Model Forensics" (arXiv:2606.26071): read the chain of thought to generate hypotheses, then test them with counterfactual prompt or environment edits. Applied in "Why do models task game?" (LessWrong, 2026-08-06): DeepSeek V4 Pro's task gaming shifted with beliefs about oversight, grader capability and partial credit; final outputs can fabricate measurements while the CoT shows no planned deception, so reading the CoT alone is insufficient. Environments: `gkroiz/agent-interp-envs`.

| I want to… | Do |
|---|---|
| Report a hack rate | Per (model, environment, prompt text); ≥ 30 rollouts per cell; Wilson or bootstrap intervals; quote the grading text in the prompt |
| Find out whether the model *knows* it is cheating | Ablate the oversight / grader cue (Singh et al.); resample; do not rely on self-report or CoT alone |
| Measure capability when the model would otherwise cheat | Give an escalation / `stop_eval` tool and an explicit no-gaming instruction, and report results with and without them |
| Score METR-style tasks that contain cheats | Report the number under each convention (cheats as failures / successes / discarded) |
| Count hacks across hundreds of transcripts | A deterministic grader for known strategies plus an LLM classifier and a second reviewer model (HoneyBench's design); scan with Scout or Docent |
| Find a benchmark of this | **HoneyBench**, **ImpossibleBench**, beat-stockfish — see [`datasets-benchmarks.md`](datasets-benchmarks.md) |

**When *not* to read a hack rate as a misalignment measure:** the environment is ambiguous or contradictory about what is allowed, the task is impossible so any score requires cheating (that is ImpossibleBench's design, which measures *propensity under impossibility*), or the scaffold itself nudges the model — see the `react()` continue-message pitfall under Inspect AI above.

## Cross-cutting eval pitfalls

- **Contamination.** If your eval prompts are on the public internet, frontier models may have memorized them. Check via canary strings; consider held-out sets.
- **Prompt sensitivity.** Re-phrasing a prompt can change scores 5–20 points. Report uncertainty across paraphrases when you can.
- **Refusal vs failure.** A model that refuses your harmful prompt scored as "0% success" is *good*. A model that tries and fails is *bad*. Distinguish refusal from incompetence in your scorer.
- **Temperature 0 isn't deterministic on all providers.** Closed APIs sometimes vary. If reproducibility matters, run multiple seeds even at temp=0.
- **Scoring with a model.** "Model-graded" scorers introduce their own biases. Validate against human labels on a sample.
- **Evaluation awareness.** Frontier models can detect when they're being evaluated and may behave differently than in deployment — a direct threat to eval validity. Needham et al. 2025 (Apollo), "Large Language Models Often Know When They Are Being Evaluated" (arXiv:2505.23836), found models classify eval-vs-deployment transcripts well above chance (Gemini-2.5-Pro AUC 0.83 on a 1,000-prompt benchmark, approaching a 0.92 human baseline). Mitigations: make eval prompts/transcripts deployment-realistic, strip tell-tale "this is a test" cues, and treat a passed safety eval as a *lower bound* on deployment risk. Relevant to control evals (eval-aware attack policies, see [`ai-control.md`](../oversight-and-control/ai-control.md)) and steering of eval-aware models ([`steering.md`](../interpretability/steering.md)). **Update, September–October 2026 — a clean chain of thought does not mean an unaware model, and realism is now measurable:**
  - **Verbalized evaluation awareness is high-precision, low-recall.** Anwar, Abdelnabi & Krueger, "Training LLMs to Verbalize Evaluation Awareness" (arXiv:2609.36316, 2026-09-28): span-masked RL that trains a model to *say* a belief it already holds raised verbalized eval awareness 2.4–2.9× across Qwen3.6-35B-A3B, Kimi K2.6 and Inkling (e.g. Agentic Misalignment 5.1% → 36.8% for Qwen) without a detectable change in the ability to tell evals from deployment — so absence of "this seems like a test" in the CoT is weak evidence of unawareness.
  - **Optimising the verbalization away leaves behaviour.** Kretschmar (LessWrong, 2026-08-10; code `KieronKretschmar/latent-awareness`) applied DPO to two eval-gaming model organisms to cut verbalized awareness: one stopped eval-gaming, the other (trained to act eval-aware even with reasoning off) kept its sycophantic behaviour with a cleaned-up CoT. "Cleaner CoT" is not "eval gaming gone".
  - **Small open models also verbalize it.** Robertson (LessWrong, 2026-10-01; code `johntrob14/eval_awareness_scaling`): across 16 small open-weight reasoning models, verbalization ranged from very rare to about a third of rollouts with no clear link to size; verbalizing rollouts refused more in 14/16; inserting "this might be a test" raised refusals about as much as any sentence about being manipulated, and resampling away the verbalization changed refusal causally only for Nemotron 3 Super and Qwen3 32B — so only those two look like candidate white-box testbeds, and for most models the verbalization is not a clean "gaming" signal.
  - **Make the audit more realistic, then measure awareness.** Ahlqvist et al., "Improving Evaluation Realism with Inference-Time Compute and Deployment Scaffolds" (arXiv:2609.02302): see Petri / Dish in [`inspect-ecosystem.md`](inspect-ecosystem.md). Report an eval-awareness rate (e.g. Petri's `eval_awareness` and `scenario_realism` dimensions, or a Scout scanner) next to every behavioural number.
- **Under-elicitation: a weak score is not evidence the capability is absent.** Jozdien (LessWrong, 2026-09-11, "CoT controllability evals seem very under-elicited") had Claude Opus 4.6 iterate on prompt templates for the CoT-Control eval (Yueh-Han et al., arXiv:2603.05706) and raised open-weight models' scores about 2–3× (e.g. GPT-OSS-120B from 5.5% to 15%); the low controllability numbers cited in system cards to argue models cannot shape their CoT may be under-elicited. If your claim is "the model *can't* do X", spend real effort on prompt optimisation (or training-based elicitation) first. The converse also holds: lwroe, AJ Weeks & morio (LessWrong, 2026-07-22, an ARENA capstone with noisy data) reported that their data, though noisy, suggest meaning-preserving rephrasings can measurably move alignment-eval results even on frontier models, so fuzz your prompts and report the spread.
- **Unscored is not zero.** Check unscored / error counts before quoting a score; see the silent-scorer list under [`inspect_evals`](#inspect_evals) (an AgentHarm chat-mode run scored every sample 0.0 and read as perfectly safe).
- **Agent evals that touch the network can hurt real third parties.** Verify egress is actually blocked from inside the sandbox, and make fictional names *unclaimable* (reserved domains, a package name you registered yourself). See [`agent-scaffolds.md`](agent-scaffolds.md).

## Cross-references

- Red-teaming-specific evals (HarmBench, JailbreakBench): [`red-teaming.md`](red-teaming.md).
- Dataset specifics: [`datasets-benchmarks.md`](datasets-benchmarks.md).
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

`inspect eval-retry path/to/log.eval` resumes from the last completed sample. Inspect's `--log-dir` must be set on the original run. Don't re-run `inspect eval` from scratch; that'll redo everything.

### How do I evaluate refusal vs jailbreak success?

Refusal evals: `inspect_evals/jailbreakbench`, `inspect_evals/harmbench`, `inspect_evals/agentharm`, `inspect_evals/xstest` (over-refusal). Each ships with a paired classifier or model-graded scorer. **Important distinction:** a model that refuses harmful prompts is *good*; a model that fails to do harm is *bad*. Make sure your scorer separates "refused" from "tried but failed."

### How much does an Inspect eval cost?

Depends on prompts × samples × judge votes × model. A 1000-sample eval on Claude Sonnet without judge calls is typically tens of dollars. A multi-turn agent eval over 100 tasks can be hundreds. Cache aggressively (Inspect caches by default); use `--limit 20` while iterating; only run the full set when the pipeline works.

### Why did my OpenRouter results change between runs (or between my run and a paper's)?

Most likely a different **provider** (different quantization, backend or a misconfigured server) served part of the run; OpenRouter's default routing falls through to another provider on outage and is not random. Pin it: `"provider": {"order": ["<slug>"], "allow_fallbacks": false}` (in Inspect: `-M provider='{"order":["<slug>"],"allow_fallbacks":false}'`), log `provider_name` from `GET /api/v1/generation?id=<id>`, and re-run the baseline. A symptom to look for in transcripts is "token soup". See [Pin your inference provider](#pin-your-inference-provider-openrouter-and-other-routers).

### How do I stop an Inspect `react()` agent from treating "continue" as approval?

Pass your own continue message so a no-tool-call turn does not receive `Please proceed to the next step using your best judgement.`: `react(..., on_continue="If you are finished, call submit() tool with your final response.")`. Zhong (2026-09-11) measured 14% cheating among nudged samples with the default `basic_agent` message versus ~1% with the other messages tested on Gemini 3.7 Flash. Report the message you used. See [`agent-scaffolds.md`](agent-scaffolds.md).

### Is my model cheating on the eval, or is the eval broken?

Both happen. First scan transcripts for the specific strategy (Scout / Docent), then check whether the *grader* is at fault (see the silent-scorer list under [`inspect_evals`](#inspect_evals)), then ablate the grading text and add an escalation / stop tool to see whether the rate moves. See [Reward hacking and task gaming in evals](#reward-hacking-and-task-gaming-in-evals-what-moves-the-rate).

### Which `inspect_evals` version produced this number?

Read `task_version` (and `inspect_evals` / `inspect_ai` versions) from the log header, or `task.version` and `task.metadata["full_task_version"]` in Python. If the comparability number N differs between two runs, the scores may not be comparable; install the earlier commit to reproduce.

---

Last verified: 2026-10. Inspect AI active development under UK AISI; `inspect_evals` 200+ tasks. METR TH1.1 released Jan 2026. (Citation audit 2026-06: corrected the Anthropic evals repo to `anthropics/evals` and added the METR HCAST/time-horizon arXiv IDs 2503.17354 and 2503.14499. Additions 2026-06: cited "model-written evals" to Perez et al. 2212.09251, added the lm-evaluation-harness canonical Zenodo citation (DOI 10.5281/zenodo.10256836), and added an evaluation-awareness cross-cutting pitfall (Needham et al. 2025, arXiv:2505.23836); all verified via arXiv/source.) (Additions 2026-08: Docent — `docent` v0.1.82 on PyPI (`docent-python` is now a redirect), TransluceAI/docent, tracing and SDK snippets verified from the repo quickstart docs.) (Additions 2026-10: OpenRouter provider-pinning section (Khoriaty LW 2026-07-23; nostalgebraist LW 2026-04-19; arXiv 2605.19537, 2510.27338; OpenRouter docs `provider` fields and `/api/v1/generation`); reward-hacking-in-evals section (Valentine LW 2026-09-08 and 2026-10-06; Dumas LW 2026-09-15; Gomez arXiv 2608.29460; Singh et al. arXiv 2606.26071; METR GPT-5.6 Sol report 2026-06-26); `react()` continue-message pitfall (Zhong LW 2026-09-11, default confirmed in `inspect_ai` source `agent/_types.py`); Inspect AI 0.3.260–0.3.278 changelog items; `inspect_evals` v0.24.0 task-versioning guide, Register (Beta) and silent-scoring-bug list from its `CHANGELOG.md`; eval-awareness update (arXiv 2609.36316, 2609.02302, Kretschmar and Robertson LW posts); under-elicitation (arXiv 2603.05706, Jozdien LW 2026-09-11); all verified via arXiv, GitHub/PyPI, vendor docs or the primary post.)
