---
tags:
  - infrastructure
---

# General Safety Research Toolkits

Multi-purpose libraries that bundle the plumbing safety researchers need across many providers and providers — API clients, caching, rate limiting, prompt formatting, finetuning helpers, human-labeling.

## At a glance

| If you want… | Use |
|---|---|
| One unified API across OpenAI, Anthropic, Gemini, DeepSeek, Together, vLLM, etc., with caching | **safety-research/safety-tooling** (`safetytooling`) |
| Same but in an eval setting | **Inspect AI** (`inspect_ai`) — see [`evals.md`](../evaluation/evals.md) |
| Just an LLM API wrapper with no safety-specific extras | LiteLLM (general-purpose, not safety-flavored but commonly used) |
| Project starter / cookiecutter for safety research | hand-rolled or fork an existing `safety-research/*` repo |

## safety-research/safety-tooling

Aliases: `safetytooling` (the import name; verify exact PyPI name on install), `safety-research/safety-tooling` on GitHub, "the safety-tooling library", "the Perez-lab inference glue", "Anthropic-adjacent safety toolkit" (informal — maintained under the `safety-research` org, originated in Ethan Perez's projects with contributions from Anthropic-affiliated and external researchers).

**Important framing:** Despite the name, this is **primarily an LLM inference API wrapper** (with caching / rate-limiting / cost tracking / human-labeling extras), not a red-team or eval framework in the garak/PyRIT/Inspect sense. Position it as: **the inference glue layer that Anthropic-adjacent labs build experiments on top of**. Companion repo `safety-research/safety-examples` shows submodule usage patterns.

**What it is.** A unified Python toolkit for AI safety research projects, originally built up over 2023–2026 across many collaborative projects. Provides:

- **Inference API:** `safetytooling.apis.InferenceAPI` — one async interface to OpenAI, Anthropic, Google Gemini, HuggingFace endpoints, GraySwan, Together AI, DeepSeek, vLLM (local), and any OpenAI-compatible endpoint.
- **Automatic caching:** disk or Redis. Re-running the same prompt is free. Critical when iterating on dataset/prompt/scorer code.
- **Rate limit management** and concurrent request handling — handles per-provider rate limits and exponential backoff out of the box.
- **Custom response filtering with retries** — drop completions that fail your validator, retry up to N times.
- **Finetuning integration** with W&B logging — kick off a finetuning job (open-weight providers; note OpenAI's finetuning API is being retired) and log to wandb.
- **Image and audio support.**
- **Text-to-speech** via ElevenLabs.
- **API usage tracking** for OpenAI and Anthropic (cost reporting).
- **Human labeling framework** with persistent storage.
- **Unified prompt/message classes** (`Prompt`, `ChatMessage`, `MessageRole`) so you don't rewrite per-provider message formats.

Key modules:
- `safetytooling.apis.inference.api` — `InferenceAPI` class.
- `safetytooling.data_models.messages` — prompt/response classes.
- `safetytooling.utils.experiment_utils` — `ExperimentConfigBase` you can subclass.

**When to use it:**
- You're writing a safety research script that calls multiple providers (the typical case for cross-provider behavioral evals).
- You want caching so reruns are free.
- You're building a dataset of model outputs and want to swap providers without rewriting.
- You need API cost tracking for a budget-constrained project.
- You want a sensible `ExperimentConfigBase` rather than rolling your own argparse/Hydra.

**When *not* to use it:**
- You're running a structured eval — use **Inspect AI** instead (it has its own multi-provider support and produces standard logs).
- You only need one provider — direct SDK is simpler.
- You need an OSS-license-compatible commercial deployment — read the license first.

**Pitfalls:**
- **Cache key includes the model ID.** Renaming `claude-sonnet-4-5` → `claude-sonnet-4-6` doesn't invalidate the cache — it just misses. If you want to re-run, clear the cache or change the cache_dir.
- **Cache key does *not* always include sampling parameters.** Verify by reading the source if your experiment changes temperature / top_p — re-running with new params may unexpectedly hit cache.
- **Async-only.** `InferenceAPI` is an async API. Wrap with `asyncio.run(...)` or use inside an async function. No sync convenience wrapper.
- **Provider-specific param leakage.** Some kwargs (e.g. Anthropic's `system` parameter format, OpenAI's `seed`) need to go into the right place; the unified prompt format mostly handles this but there are edges.
- **Rate limits are heuristic.** When provider rate limits change (Anthropic does this often), you may see `429` storms; tune `max_concurrent_calls`.
- **No vLLM-Lens integration out of the box** — for activation extraction you'd still wire up vLLM-Lens separately.

```python
# pip install ... (check repo for exact install command)
import asyncio
from safetytooling.apis import InferenceAPI
from safetytooling.data_models import ChatMessage, MessageRole, Prompt

async def main():
    api = InferenceAPI(cache_dir="./cache")
    prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content="Hello")])
    responses = await api(model_id="claude-sonnet-4-6", prompt=prompt, n=3)
    for r in responses:
        print(r.completion)

asyncio.run(main())
```

## Inspect AI as a "toolkit"

Although Inspect AI is primarily an eval framework (see [`evals.md`](../evaluation/evals.md)), it doubles as a multi-provider toolkit because:

- It has model providers for OpenAI, Anthropic, Google, vLLM, vLLM-Lens, HuggingFace, Bedrock, Together, Groq, etc.
- Calling `get_model("anthropic/claude-sonnet-4-6").generate(...)` works outside of an Inspect task too.
- It has caching, retries, rate limiting.

**When to use Inspect-as-toolkit instead of safety-tooling:**
- You'll later wrap the work in an eval anyway.
- You want eval logs (Inspect View) for your work-in-progress.

**When to use safety-tooling instead:**
- Faster iteration loop without Task/Solver/Scorer structure.
- Want async-first ergonomics.
- Need the human-labeling framework, cost tracking, ElevenLabs TTS, or other extras specific to safety-tooling.

## LiteLLM (general-purpose alternative)

Aliases: `litellm` on PyPI, `BerriAI/litellm`.

**What it is.** A general-purpose multi-provider LLM API wrapper — not safety-research-specific, but battle-tested and broadly used. Handles 100+ providers with a common interface.

**When to use it:** Production / general-purpose LLM applications; you want maximum provider coverage; you're outside the safety-research workflow.

**When *not* to use it:** You want safety-research-specific features (human labeling, experiment configs, structured caching for re-running experiments) — safety-tooling is built for that.

## Other safety-research org repos worth knowing

The `safety-research` GitHub org hosts several adjacent projects beyond safety-tooling. Browse the org for current projects; common ones include:
- Specific paper code (model organisms work, control evals, etc.).
- **`safety-research/circuit-tracer`** — circuit-tracer for transcoder-based circuit discovery, implementing methods from Anthropic's Transformer Circuits team; maintained by Decode Research (`decoderesearch`). See [`saes.md`](../interpretability/saes.md) for full coverage.
- Datasets and eval suites for specific properties.

When starting a new project, search `safety-research/*` first — there's a non-trivial chance someone has already built what you need.

## Cross-cutting pitfalls

- **Cache invalidation is hard.** If your prompt/template changes by even a whitespace, you'll get a cache miss; if your *scorer* changes but the model output is the same, you don't want to re-call the API. Design your pipeline so prompt-stage and scoring-stage caches are separate.
- **Logging tokens / costs.** Token-cost accuracy depends on the provider returning correct usage info, which they sometimes don't (esp. for streaming). Always log the raw usage block; don't trust a single "cost" number.
- **Async + Jupyter.** Mixing async APIs with Jupyter is a frequent source of `RuntimeError: This event loop is already running`. Use `nest_asyncio` or `await api(...)` directly in a notebook cell.
- **Retries amplify rate limit pressure.** A burst of 429s + retries can produce a cascade. Bound retries (default 5 is usually fine).
- **Don't commit your cache.** Multi-GB caches in git is not what you want. Add `cache/` to `.gitignore`.

## Cross-references

- Eval framework: [`evals.md`](../evaluation/evals.md).
- Datasets to feed into these tools: [`datasets-benchmarks.md`](../evaluation/datasets-benchmarks.md).
- Compute for self-hosting open-weight models referenced via these toolkits: [`compute.md`](compute.md).

---

## Common questions

### How do I call Claude, GPT, and Gemini in one script?

Use **safety-research/safety-tooling** (`safetytooling` import). One async API:
```python
from safetytooling.apis import InferenceAPI
from safetytooling.data_models import ChatMessage, MessageRole, Prompt

api = InferenceAPI(cache_dir="./cache")
prompt = Prompt(messages=[ChatMessage(role=MessageRole.user, content="Hello")])
responses = await api(model_id="claude-sonnet-4-6", prompt=prompt, n=3)
```
Same `api(model_id=..., prompt=...)` works with `gpt-4o`, `gemini-2.0-flash`, `deepseek-chat`, `meta-llama/...` via Together, etc. **LiteLLM** is the general-purpose alternative.

### How do I cache API calls to avoid re-paying for the same prompt?

safety-tooling caches automatically when you pass `cache_dir="./cache"` (disk) or configure Redis. Re-running the same prompt + model + sampling-params combination returns the cached response. Inspect AI also caches by default. **Caveat:** cache key includes model ID; renaming `claude-sonnet-4-5` → `claude-sonnet-4-6` doesn't invalidate, it just misses.

### What is safety-tooling?

`safety-research/safety-tooling` (originated in Ethan Perez's projects, Anthropic-affiliated and external collaborators, under the `safety-research` GitHub org). **Primarily a unified LLM inference API wrapper** with multi-provider support (OpenAI, Anthropic, Gemini, GraySwan, Together, DeepSeek, vLLM, HF endpoints), automatic disk/Redis caching, rate-limit handling, finetune integration, ElevenLabs TTS, and human-labeling utilities. Originated in 2023; widely used in 2024–2026 safety research projects, especially in the Perez-lineage / Anthropic-alignment pipeline. **Not a red-team / eval framework** — pair it with Inspect AI for evals, garak/PyRIT for red-team, etc.

### LiteLLM vs safety-tooling — which?

**LiteLLM** for general-purpose LLM apps with maximum provider coverage (100+ providers). **safety-tooling** for safety research workflows: caching designed for re-running experiments, `ExperimentConfigBase`, human-labeling framework, finetune integration with W&B logging, batch behavioral evals. If you're doing the [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md) workflow, safety-tooling is the better fit.

### How do I avoid getting rate-limited?

(1) **Cache** — second hit is free. (2) **Lower concurrent requests** (`max_concurrent_calls` parameter). (3) **Apply for higher rate limits** in the provider's dashboard. (4) **Multi-provider fallback** — safety-tooling can route to a different provider on persistent 429. (5) **Schedule retries with backoff** — most libraries do this by default.

### `RuntimeError: This event loop is already running` in Jupyter

Mixing async APIs with Jupyter's event loop. Two fixes: `import nest_asyncio; nest_asyncio.apply()` once at notebook start; or use `await api(...)` directly in cells (Jupyter ≥7 supports top-level await).

### Where do I put my API keys?

Environment variables, loaded from a `.env` file in the project root (gitignored). Standard names: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `TOGETHER_API_KEY`. Most safety-research libraries read these from env automatically. Never paste keys into source files or notebooks.

---

Last verified: 2026-04-30. `safety-research/safety-tooling` actively maintained under the `safety-research` GitHub org (last push March 2026, 24 contributors). Repositioned framing: primarily an LLM inference API wrapper, not a red-team/eval framework. `circuit-tracer` lives under `safety-research/circuit-tracer` but is maintained by Decode Research (`decoderesearch`). Inspect AI under UK AISI.
