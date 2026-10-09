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
| Generate a behavioral-evaluation suite (sycophancy, self-preservation, …) from a seed behavior description | **Bloom**, now maintained as **Petri Bloom** (`petri-bloom` on PyPI, `meridianlabs-ai/petri_bloom`) — see below |
| Audit a model's alignment with an automated auditor agent over multi-turn conversations | **Inspect Petri** (`inspect-petri`, `meridianlabs-ai/inspect_petri`) — see [`inspect-ecosystem.md`](../evaluation/inspect-ecosystem.md) |
| Run many Claude Code agents in parallel on ephemeral cloud containers | `safetytooling.infra.cloud_run` (`ClaudeCodeClient`) inside **safety-tooling** — see below; needs a GCP project |
| Control experiments (protocols, monitors, settings) | **ControlArena** (`UKGovernmentBEIS/control-arena`) — see [`ai-control.md`](../oversight-and-control/ai-control.md); pin the version, it ships breaking majors |

## safety-research/safety-tooling

Aliases: `safetytooling` (the import name; **not published on PyPI** — `pypi.org/pypi/safetytooling` returns 404 as of 2026-10-09 — so install from a clone, a git submodule, or `pip install git+https://github.com/safety-research/safety-tooling.git`), `safety-research/safety-tooling` on GitHub, "the safety-tooling library", "the Perez-lab inference glue", "Anthropic-adjacent safety toolkit" (informal — maintained under the `safety-research` org, originated in Ethan Perez's projects with contributions from Anthropic-affiliated and external researchers).

**Important framing:** Despite the name, this is **primarily an LLM inference API wrapper** (with caching / rate-limiting / cost tracking / human-labeling extras), not a red-team or eval framework in the garak/PyRIT/Inspect sense. Position it as: **the inference glue layer that Anthropic-adjacent labs build experiments on top of**. Companion repo `safety-research/safety-examples` shows submodule usage patterns.

**What it is.** A unified Python toolkit for AI safety research projects, originally built up over 2023–2026 across many collaborative projects. Provides:

- **Inference API:** `safetytooling.apis.InferenceAPI` — one async interface to OpenAI, Anthropic, Google Gemini, HuggingFace endpoints, GraySwan, Together AI, DeepSeek, vLLM (local), and any OpenAI-compatible endpoint.
- **Automatic caching:** disk or Redis. Re-running the same prompt is free. Critical when iterating on dataset/prompt/scorer code.
- **Rate limit management** and concurrent request handling — handles per-provider rate limits and exponential backoff out of the box.
- **Custom response filtering with retries** — drop completions that fail your validator, retry up to N times.
- **Finetuning integration** with W&B logging — kick off a finetuning job (the built-in integration targets the **OpenAI finetuning API**; note OpenAI is retiring that API, so this path is increasingly legacy) and log to wandb.
- **Image and audio support.**
- **Text-to-speech** via ElevenLabs.
- **API usage tracking** for OpenAI and Anthropic (cost reporting).
- **Human labeling framework** with persistent storage.
- **Unified prompt/message classes** (`Prompt`, `ChatMessage`, `MessageRole`) so you don't rewrite per-provider message formats.
- **Cloud Run runner for Claude Code ("Claudes in the Cloud", added 2026-02):** `safetytooling.infra.cloud_run` provides `ClaudeCodeClient` and `ClaudeCodeTask`; `client.run(tasks)` uploads inputs once to a Google Cloud Storage (GCS) bucket, runs many Claude Code instances in parallel on ephemeral Google Cloud Platform (GCP) Cloud Run containers (e.g. `n=10` repeats of a task), and returns each run's stdout, full transcript and output directory (`run_stream` yields results as they finish). Needs a GCP project with Cloud Run, Cloud Storage and Secret Manager enabled, `gcloud auth application-default login`, the Anthropic API key in Secret Manager, and a restricted service account (see `safetytooling/infra/cloud_run/README.md`). Later commits added virtual-private-cloud (VPC) egress firewall support (2026-03), reuse of Cloud Run job definitions to avoid quota limits (2026-02), and inlining of subagent transcripts into the main transcript (2026-03).
- **Bounded caches:** `FileBasedCacheManager` has a memory limit (2025-12) and least-recently-used (LRU) eviction instead of smallest-first (2026-02).

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
- **Exact dependency pins.** `pyproject.toml` pins `openai==1.70.0`, `anthropic==0.49.0`, `google-generativeai==0.8.4`, `together==1.5.4`, `pandas==2.2.3`, `wandb==0.19.9` and others exactly (`transformers>=4.50,<6` is a range). Installing it into an environment that already has a newer `anthropic` or `openai` SDK downgrades them, or fails resolution with `ResolutionImpossible` / `Cannot install ... because these package versions have conflicting dependencies`. Use it as a git submodule in its own `uv` environment, or loosen the pins in your fork — and expect newer SDK features (newer Claude models' parameters, new response types) to be missing until the pin is bumped.
- **Maintenance cadence.** Last push 2026-05-29 (`deps: support transformers>=5 (Qwen3.5 multimodal arch compatibility)`); no PyPI release, and the GitHub release is still `v1.0.0` from 2025-05-08. Provider-specific features added to APIs after the last push may need a `force_provider` workaround (the repo's own `CLAUDE.md` suggests trying `force_provider="openai"` / `"anthropic"` for new model ids before editing code).

```python
# not on PyPI: clone it (or add it as a git submodule) and run `uv pip install -e .`
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

**Pitfall: PyPI supply-chain incident (2026-03-24).** `litellm` versions **1.82.7 and 1.82.8** on PyPI were malicious (credential-stealing payload; 1.82.8 also shipped a `litellm_init.pth` file that runs at interpreter start-up). The versions have been removed — PyPI's release list now ends at 1.82.6 for that series — but any machine that installed or upgraded `litellm` during that window should be treated as compromised: rotate API keys, and look for `litellm_init.pth` in `site-packages`. Primary sources: `BerriAI/litellm` issues #24518 (timeline) and #24512 / #24521. Pin with a lockfile (`uv.lock`) and hashes, and do not run `pip install -U litellm` on a machine holding provider keys. LiteLLM's proxy server has also had separate published security advisories (SSRF, privilege escalation) — keep it patched if you self-host it.

## Bloom and Petri: automated behavioral evaluation and auditing (both moved to Meridian Labs)

Aliases: **Bloom** ("Bloom: an open source tool for automated behavioral evaluations", Gupta, Fronsdal, Sheshadri, Michala, Tay, Wang, Bowman, Price; `safety-research/bloom`), **Petri Bloom** (`petri-bloom` on PyPI, `meridianlabs-ai/petri_bloom`, docs `meridianlabs-ai.github.io/petri_bloom`), **Petri** (Parallel Exploration Tool for Risky Interactions; `inspect-petri` on PyPI, `meridianlabs-ai/inspect_petri`, formerly `safety-research/petri`).

**What they are.** **Bloom** takes a *seed* — a description of a target behavior (sycophancy, self-preservation, delusion-sycophancy, political bias, …), optional example transcripts, and variation dimensions — and generates a suite of test scenarios, runs multi-turn conversations with the target model, and scores them with a judge. Unlike a fixed benchmark, its suites change with the seed, so **cite the full seed configuration** for reproducibility. **Petri** is the auditor/target framework underneath: an auditor model plays the user and simulates tools, a target model is evaluated, a judge scores transcripts. Both run on **Inspect AI**.

**Where they live now (verified 2026-10-09).**
- `safety-research/bloom` is **frozen**: its README says the project "is now developed and maintained by Meridian Labs" and "will not receive updates" (notice committed 2026-05-07; last push the same day). The maintained successor is **Petri Bloom** — an implementation of Bloom on the Petri auditor/target framework — `pip install petri-bloom` (version 0.2.6, Python ≥ 3.12; GitHub release 2026-07-15).
- `safety-research/petri` now redirects to `meridianlabs-ai/inspect_petri`. **Petri 3.x** (`inspect-petri` 3.1.1, 2026-10-01, Python ≥ 3.12) keeps most command-line interface (CLI) commands from Petri 2.0 but **has incompatible Python APIs**; Petri 2.0 remains installable from the `petri-v2` branch (`pip install git+https://github.com/meridianlabs-ai/inspect_petri@petri-v2`). Release notes: 3.1.0 (released 2026-08-12; its changelog heading is dated 2026-07-22) added `audit_scanner()` (a building block for custom Petri scorers) and made the auditor's prefill distinguishable from genuine target output; 3.1.1 (2026-10-01) **drops target tool options so providers cannot run tools server-side**, rejects seed tool definitions with unknown or misspelled keys, and tolerates CRLF in seed front matter.

**How to run Petri Bloom** (commands from its documentation; model ids are the docs' examples):

```bash
pip install petri-bloom
bloom init delusion_sycophancy                     # create a behavior project from a builtin definition
bloom scenarios ./delusion_sycophancy --model-role scenarios=anthropic/claude-sonnet-4-6
inspect eval petri_bloom/bloom_audit -T behavior=./delusion_sycophancy \
  --model-role auditor=anthropic/claude-sonnet-4-6 \
  --model-role target=openai/gpt-5-mini \
  --model-role judge=anthropic/claude-opus-4-6
inspect view
```

**When to use it:**
- You want a *propensity* evaluation for a behavior no existing benchmark covers, and a researcher-written seed is a better fit than a fixed dataset.
- You want auditor-driven multi-turn probing with tool simulation and rollback (Petri).

**When *not* to use it:**
- You need a fixed, citable benchmark with a stable test set — use an Inspect task from `inspect_evals` ([`evals.md`](../evaluation/evals.md)). Bloom and Petri findings are *candidates*: judge-model scores depend on the auditor, judge and seed, so confirm a behavior with a held-out prompt set.
- You are starting new work on `safety-research/bloom` — it is frozen; start from Petri Bloom.
- You are auditing tool-using behavior on a version older than Petri 3.1.1 — before it, target tool options were passed through and providers could run tools server-side; upgrade first.

**Pitfalls:**
- **Version drift between the Petri API and your scripts.** Scripts written for Petri 2.x fail on 3.x with `ImportError` / `AttributeError` on moved Python APIs; pin `inspect-petri` and record the version in `metadata.json`.
- **Judge and auditor choice dominate results.** Record auditor, judge and target ids (and provider; see the OpenRouter pinning pitfall in [`evals.md`](../evaluation/evals.md#pin-your-inference-provider-openrouter-and-other-routers)) alongside every score.
- Bloom's README carries a canary string — do not put benchmark outputs into training corpora.

## Fast-moving libraries: pin the version

| Library | Version checked (2026-10-09) | What changed that can alter your results or break scripts |
|---|---|---|
| **ControlArena** (`UKGovernmentBEIS/control-arena`, MIT) | v20.0.1 (2026-10-05); majors every few weeks (v17 → v20 between 2026-06-09 and 2026-10-05) | v20.0.0 (release notes list several `!` breaking changes): "run vllm and iac on k8s, and take all three sandboxes offline", "remove the docker sandbox mode" (infra), "take the SWE-bench Django sandbox offline", "regenerate the vLLM main task dataset and pin its version", and "sanitize last_tool_calls monitor prompt". It also fixed monitor-score parsing — **"parse 'X out of Y' monitor scores as X rather than Y"** — and bootstrapped confidence intervals for ROC AUC (receiver operating characteristic, area under the curve) that crashed on tied scores, so monitor results computed on older versions may have been affected; re-run before quoting them. Use [`ai-control.md`](../oversight-and-control/ai-control.md) for protocols. |
| **Inspect AI** (`UKGovernmentBEIS/inspect_ai`, MIT) | 0.3.278 (2026-10-09) | Roughly weekly releases; release-note items that change numbers are summarised in [`evals.md`](../evaluation/evals.md). |
| **circuit-tracer** (`decoderesearch/circuit-tracer`; `safety-research/circuit-tracer` redirects to it) | v0.5.2 (2026-07-18); PyPI `circuit-tracer` 0.5.0 | The PyPI release lags GitHub; for transcoder-based circuit discovery see [`saes.md`](../interpretability/saes.md). |

## Other safety-research org repos worth knowing

The `safety-research` GitHub org hosts many adjacent projects. Search `safety-research/*` first — there is a non-trivial chance someone has already built what you need. Verified 2026-10-09 (all non-archived):

| Repo | What it is | Notes |
|---|---|---|
| `safety-research/auditing-agents` | Code for **AuditBench** (arXiv:2602.22755, Sheshadri et al.): 56 language models with implanted hidden behaviors plus an investigator agent that uses configurable auditing tools | Models and datasets on the Hugging Face org `auditing-agents`; needs CUDA GPUs (H100-class for 70B models) and Anthropic + OpenAI keys; active (last push 2026-10-08). Key finding reported in the abstract: a *tool-to-agent gap* — tools that work standalone do not always help an agent. |
| `safety-research/red-teaming-auto-mode` | Code for *Red-Teaming Auto Mode: Improving Blocking Classifiers Against Malign Coding Agents* (arXiv:2609.19587): a real Claude Code agent in a Docker sandbox red-teams the Auto Mode / Codex Guardian action monitors | See [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md) for what it means for daily use. |
| `safety-research/automated-w2s-research` | Sandbox, datasets, baselines and a Claude-powered automated researcher for weak-to-strong generalization (MIT) | See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md). |
| `safety-research/trusted-monitor`, `safety-research/sleight-bench` | A CLI that scores Claude Code transcripts (JSONL) 0–100 for suspiciousness with a monitor model; a benchmark of attack/benign agent-transcript pairs for evaluating trusted monitors | Monitor-evaluation building blocks for [`ai-control.md`](../oversight-and-control/ai-control.md). |
| `safety-research/agent-transcript-editor` | Web UI for viewing, editing and AI-assisted red-teaming of agent transcripts | Useful for building monitor test cases. |
| `safety-research/thimble` | A Claude Code **plugin** (alpha, Apache-2.0) that opens a browser workbench for making sense of large volumes of agent output — cards with citations, labels, reports | Changes daily; its server has no login, so treat a corpus like code you are about to run. See [`ai-scientist-frameworks.md`](../engineering/ai-scientist-frameworks.md). |
| `safety-research/jpp_lens` | Code and evaluations for the **J++ Lens** (Ayonrinde & Lindsey, 2026) | Released lenses: `koayon/jpp-lenses`; see [`open-weights-models.md`](open-weights-models.md). |
| `safety-research/circuit-tracer` → `decoderesearch/circuit-tracer` | Transcoder-based circuit discovery, implementing methods from Anthropic's Transformer Circuits team; now maintained by Decode Research | See [`saes.md`](../interpretability/saes.md). |

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

### How do I install safety-tooling? `pip install safetytooling` fails with "No matching distribution found"

It is not on PyPI (checked 2026-10-09). Clone `safety-research/safety-tooling` and `uv pip install -e .`, add it as a git submodule (the README's recommended pattern; `safety-research/safety-examples` shows it), or `pip install git+https://github.com/safety-research/safety-tooling.git`. Put it in its own environment: it pins `openai==1.70.0` and `anthropic==0.49.0` exactly.

### Where did Bloom and Petri go? `safety-research/bloom` says it will not receive updates

Both are now maintained by Meridian Labs: Bloom as **Petri Bloom** (`pip install petri-bloom`, `meridianlabs-ai/petri_bloom`) and Petri as **Inspect Petri** (`pip install inspect-petri`, `meridianlabs-ai/inspect_petri`; `safety-research/petri` redirects there). See the Bloom and Petri section above.

### How do I run many Claude Code agents in parallel on the cloud?

`safetytooling.infra.cloud_run.ClaudeCodeClient` runs batches of Claude Code tasks on ephemeral GCP Cloud Run containers and returns transcripts and output files; it needs a GCP project, a GCS bucket, an Anthropic key in Secret Manager and a restricted service account. For local parallelism see [`agentic-swe-practices.md`](../engineering/agentic-swe-practices.md).

### Is `litellm` safe to install?

Versions 1.82.7 and 1.82.8 (2026-03-24) were malicious and have been removed from PyPI; check for them and for `litellm_init.pth` if you installed during that window, rotate keys, and pin with a lockfile. See the LiteLLM section.

---

Last verified: 2026-10. `safety-research/safety-tooling` — no push since 2026-05-29, not on PyPI, exact SDK pins in `pyproject.toml`; Cloud Run runner (`safetytooling.infra.cloud_run`) read from its README and commit log. `circuit-tracer` lives under `decoderesearch/circuit-tracer` (`safety-research/circuit-tracer` redirects). Inspect AI under UK AISI. (Citation audit 2026-06: corrected the finetuning-integration note — it targets the OpenAI finetuning API, not open-weight providers.) (Additions 2026-10: Bloom / Petri moves — `safety-research/bloom` frozen, `meridianlabs-ai/petri_bloom` 0.2.6 and `meridianlabs-ai/inspect_petri` 3.1.1 checked on GitHub and PyPI; ControlArena v20.0.0/v20.0.1 release notes; LiteLLM 1.82.7/1.82.8 incident from `BerriAI/litellm` issues #24518 / #24512 / #24521 and the PyPI release list; `safety-research/*` repos AuditBench (arXiv:2602.22755), red-teaming-auto-mode (arXiv:2609.19587), thimble, trusted-monitor, sleight-bench, agent-transcript-editor, jpp_lens; all verified via arXiv/GitHub/PyPI. Not verified: that Petri Bloom runs end to end with the docs' example model ids — the commands are copied from its documentation, not executed.)
