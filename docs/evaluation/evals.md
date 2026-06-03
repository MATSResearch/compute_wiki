---
tags:
  - evaluation
---

# Evaluation Frameworks

Tooling for running evaluations on language models — academic benchmarks, agentic tasks, dangerous capability evals, and bespoke safety tests.

## At a glance: which framework?

| If you want… | Use |
|---|---|
| Anything agentic, multi-turn, tool-using, sandboxed | **Inspect AI** (UK AISI) |
| Multiple-choice / log-prob academic benchmarks (MMLU, ARC, HellaSwag, GSM8K) | **lm-evaluation-harness** (EleutherAI) |
| Dangerous-capability / long-horizon agent tasks | **METR HCAST** (run via Inspect or METR's `vivaria`) |
| Anthropic-style behavioral evals (sycophancy, deception, etc.) | **Inspect AI** with custom tasks; reference Anthropic's `evals` repo for examples |
| Quick custom eval over an API model | **safety-research/safety-tooling** (see [`safety-toolkits.md`](../models-and-compute/safety-toolkits.md)) |

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

Aliases: `inspect_evals` package, `UKGovernmentBEIS/inspect_evals` on GitHub.

**What it is.** A library of 200+ pre-implemented Inspect tasks: HarmBench, AgentHarm, AgentBench, GAIA, SWE-bench (Verified), CyBench, GPQA, MMLU/MMLU-Pro, MATH, IFEval, sycophancy evals, and many more. Maintained alongside Inspect.

**When to use it:** Always check here before re-implementing a known benchmark. Run via `inspect eval inspect_evals/{eval_name}`.

**Pitfall:** Some evals require additional dataset downloads, dataset gating, or sandbox setup. Read the eval's README in the repo.

## lm-evaluation-harness

Aliases: `lm-eval`, `lm_eval` on PyPI, `EleutherAI/lm-evaluation-harness` on GitHub, "Eleuther's harness", "the harness".

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

## Anthropic safety evals (the `evals` format)

Aliases: `anthropics/evals` on GitHub, "Anthropic eval format", "model-written evals".

**What it is.** Anthropic has published a number of behavioral eval datasets in JSONL formats — sycophancy, advanced AI risks, model-written evals, etc. Many of these are wrapped as `inspect_evals` tasks now.

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

## Cross-cutting eval pitfalls

- **Contamination.** If your eval prompts are on the public internet, frontier models may have memorized them. Check via canary strings; consider held-out sets.
- **Prompt sensitivity.** Re-phrasing a prompt can change scores 5–20 points. Report uncertainty across paraphrases when you can.
- **Refusal vs failure.** A model that refuses your harmful prompt scored as "0% success" is *good*. A model that tries and fails is *bad*. Distinguish refusal from incompetence in your scorer.
- **Temperature 0 isn't deterministic on all providers.** Closed APIs sometimes vary. If reproducibility matters, run multiple seeds even at temp=0.
- **Scoring with a model.** "Model-graded" scorers introduce their own biases. Validate against human labels on a sample.

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

---

Last verified: 2026-06. Inspect AI active development under UK AISI; `inspect_evals` 200+ tasks. METR TH1.1 released Jan 2026. (Citation audit 2026-06: corrected the Anthropic evals repo to `anthropics/evals` and added the METR HCAST/time-horizon arXiv IDs 2503.17354 and 2503.14499.)
