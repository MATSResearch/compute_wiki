# Open-Weights Models for Safety Research

Which open-weights (downloadable, self-hostable) model to reach for, and *why each one is worth knowing*. This page is about research fit — capability ceiling, alignment character, interpretability-tooling support, fine-tuning ergonomics, and baseline value — not a leaderboard. For *where* to run these, see [`10_compute.md`](10_compute.md); for fine-tuning them as model organisms, see [`16_model_organisms.md`](16_model_organisms.md) and [`14_rl_training.md`](14_rl_training.md).

Acronyms used throughout: **MoE** = Mixture-of-Experts (only a subset of "expert" sub-networks activate per token, so *active* params ≪ *total* params). **SAE** = Sparse Autoencoder. **CoT** = Chain-of-Thought. **HF** = Hugging Face. **KV cache** = key/value cache (the memory that grows with context length during generation).

## Research-fit decision table

| I want to… | Reach for | Why |
|---|---|---|
| The most capable open-weights model, period | **DeepSeek-V4-Pro** | Currently the strongest open-weights model overall. |
| Genuinely usable **very long context** (100k–1M tokens) | **DeepSeek-V4** (Pro or Flash) | New compressed-attention architecture keeps long-context FLOPs and KV cache tractable. |
| An **open-weights stand-in for a Claude-like, "virtue-aligned" model** | **Kimi K2.6** | Notably more character/virtue-aligned than most open-weights models; vision-enabled. |
| **Pretrained SAEs / transcoders off the shelf** for interpretability | **Gemma** (2 or 3) via **Gemma Scope** | The only model family with a comprehensive open SAE suite. See [`02_saes.md`](02_saes.md). |
| To **run locally / fine-tune cheaply** on a laptop or single GPU | **Gemma** (1B/4B) or **Qwen** (0.6B–9B) | Small sizes, well-supported by Unsloth/Llama-Factory. |
| **Capable small models for fine-tuning experiments** | **Qwen3** family | Best capability-per-param at small sizes; open base models; huge tuning ecosystem. |
| A **matched baseline** comparable to prior published fine-tuning work | **Llama** (3.1/3.3) | Behind the frontier, but the de-facto baseline in the existing literature. |

---

## How fellows actually access these: OpenRouter

Most of these models — especially the large ones (**DeepSeek-V4**, **Kimi K2.6**, big Qwen) — are **too large to run locally**. Unless your project specifically needs the raw weights (fine-tuning, activation extraction, SAEs, custom hooks), the path of least resistance is to call them through **OpenRouter** (`openrouter.ai`), a single API gateway that fronts dozens of providers behind one OpenAI-compatible endpoint and one API key. The project's OpenRouter key lives at `~/projects/.env` (`OPENROUTER_API_KEY`).

**Why OpenRouter for this work:** one key for every model below (no per-lab signups), pay-per-token (no GPU rental or cold-start), automatic provider fallback, and it plugs straight into `safety-tooling`, Inspect AI, LiteLLM, and the OpenAI SDK (`base_url="https://openrouter.ai/api/v1"`). For black-box behavioral evals, cross-model replication, and judge/labeler pipelines this is almost always the right call. Use the **raw weights** (self-host or NDIF/vLLM-Lens, see [`07_serving_and_activations.md`](07_serving_and_activations.md)) only when you need activations, fine-tuning, or token-level control.

**Verified on OpenRouter (2026-05-26)** — model slugs, input modalities, context, and approx. price ($/Mtok = US dollars per million tokens, in / out):

| Model | OpenRouter slug | Inputs | Context | ~Price in/out ($/Mtok) |
|---|---|---|---|---|
| DeepSeek-V4-Pro | `deepseek/deepseek-v4-pro` | text | 1,048,576 (1M) | 0.44 / 0.87 |
| DeepSeek-V4-Flash | `deepseek/deepseek-v4-flash` (also `:free`) | text | 1,048,576 (1M) | 0.10 / 0.20 |
| Kimi K2.6 | `moonshotai/kimi-k2.6` | text, **image** | 262,144 (256k) | 0.73 / 3.49 |
| Qwen3.6-35B-A3B | `qwen/qwen3.6-35b-a3b` | text, image, video | 262,144 | 0.15 / 1.00 |
| Gemma 3 27B IT | `google/gemma-3-27b-it` | text, image | 131,072 | 0.08 / 0.16 |
| Llama 4 Maverick | `meta-llama/llama-4-maverick` | text, image | 1,048,576 (1M) | 0.15 / 0.60 |

Notes: DeepSeek-V4 is **text-only on OpenRouter** even though it's the long-context champion (its 1M window *is* exposed). **Kimi K2.6 accepts image input** on OpenRouter — vision is real and usable through the API, not just self-hosted weights. Many Qwen3.5/3.6 sizes are listed (`qwen/qwen3.6-flash`, `qwen3.6-plus`, `qwen3.5-397b-a17b`, etc.) with text+image+video and up to 1M context. Prices and slugs drift — re-query `https://openrouter.ai/api/v1/models` before scripting.

---

## DeepSeek-V4 (Pro and Flash)

Aliases: **DeepSeek V4**, `deepseek-ai/DeepSeek-V4-Pro` and `deepseek-ai/DeepSeek-V4-Flash` on Hugging Face, "DeepSeek's V4", DeepSeek-AI (High-Flyer / 深度求索). API model names `deepseek-chat`-style via the DeepSeek API. Released **April 2026**, **MIT license** (permissive — fine-tune and redistribute freely).

**Why it's notable.** **DeepSeek-V4-Pro is currently the most capable open-weights model available** — the open-weights frontier. Both variants share a new architecture whose headline feature is **long-context efficiency**: a hybrid attention scheme (reported as Compressed Sparse Attention + Heavily Compressed Attention) that lets it **competently handle very long contexts** — up to a **1M-token context window** — while using a small fraction of the inference FLOPs and KV-cache memory that the previous DeepSeek-V3.x generation needed at the same length. This is the practical differentiator: many models *claim* long context but degrade or become uneconomical past ~128k tokens; V4 is built so the long context is actually usable.

**The two sizes:**
- **V4-Pro** — ~1.6T total parameters MoE, ~49B active per token, 1M context. The capability flagship. Needs a multi-GPU node to serve.
- **V4-Flash** — ~284B total / ~13B active MoE, same architecture and context. Much cheaper to serve — fits on a single 80GB GPU when quantized. The pragmatic choice when you want V4-family behavior without a cluster.

**Best for:**
- Tasks needing the **highest open-weights capability** (hard reasoning/coding evals, strong agent scaffolds — see [`12_agent_scaffolds.md`](12_agent_scaffolds.md)).
- **Long-context experiments** — many-document retrieval, long-transcript analysis, long-horizon agent traces, whole-codebase reasoning, long-context faithfulness studies ([`17_cot_faithfulness.md`](17_cot_faithfulness.md)).
- A **non-US-lab open frontier model** for cross-lab generalization checks in behavioral safety work ([`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md)).

**When *not* to use it:**
- You want to fine-tune on modest hardware — even Flash is large; a 1.6T MoE (Pro) is out of reach for most academic setups. Use Qwen/Gemma instead.
- You need a long published track record of fine-tuning recipes — it's new; tooling/quirks are still settling. Llama/Qwen have more community recipes.
- You need vision — DeepSeek-V4 is text-focused; for multimodal use Kimi K2.6, Qwen-VL variants, or Gemma 3.

**Pitfalls:**
- **MoE serving complexity.** Expert-parallel serving of a 1.6T model is non-trivial; expect to use vLLM/SGLang with tensor+expert parallelism and lots of VRAM. `CUDA out of memory` on a single GPU for Pro is expected — quantize and/or shard. Most fellows won't self-host Pro at all — use **OpenRouter** (`deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4-flash`) unless you need raw weights.
- **Long-context ≠ free.** The architecture makes 1M context *tractable*, not *instant*. Latency and cost still scale with context; measure before assuming you can stuff 1M tokens every call.
- **Verify the exact HF repo and quant build** before scripting a download — there are Pro/Flash, base/instruct, and community GGUF/quantized repos with different names.

---

## Kimi K2.6

Aliases: **Kimi K2.6**, **Kimi v2.6**, "Kimi" (Moonshot AI / 月之暗面 Moonshot), Moonshot's open-weights agentic model. Predecessor **Kimi K2.5** (Feb 2026) introduced vision + agent-swarm features. Released **April 2026**. Check the Moonshot HF org for exact repo slug and license before relying on redistribution terms.

**Why it's notable.** Two things. (1) **Capability**: it's among the leading open-weights models — competitive with DeepSeek-V4 and Qwen's top tier, especially strong on **agentic and coding** tasks. (2) **Alignment character**: Kimi K2.6 is **notably more "virtue-aligned" than most open-weights models** — its trained disposition (helpfulness with a coherent values/character layer, less brittle sycophancy or jailbreak-on-request behavior) is the **closest open-weights analogue to a Claude-style model**. That makes it uniquely useful when your research *needs* a model that behaves like a frontier assistant with character, rather than a raw or thinly-aligned open model.

**Vision.** K2.6 is **natively multimodal and vision-enabled** — a ~400M-parameter MoonViT vision encoder is integrated into the model (text + image) rather than bolted on. **Image input is available**, including via OpenRouter (`moonshotai/kimi-k2.6` accepts `text` + `image`). Vision is a relative weakness vs. its text strength, so don't pick it *primarily* for hard grounded-vision benchmarks — but you can pass images.

**Best for:**
- An **open-weights baseline that behaves like Claude/GPT-class assistants** — comparison points for alignment, character, refusal, sycophancy, and welfare/introspection studies ([`15_welfare_introspection.md`](15_welfare_introspection.md)) where a virtue-aligned open model is the natural counterpart.
- **Agentic / tool-use** research on a capable open model ([`12_agent_scaffolds.md`](12_agent_scaffolds.md), [`13_ai_control.md`](13_ai_control.md)).
- Studies that want a **non-US, character-trained open model** for cross-model generalization.

**When *not* to use it:**
- You need pretrained SAEs/transcoders — none for Kimi; use Gemma + Gemma Scope.
- You need a small, cheaply-fine-tunable model — Kimi is large; use Qwen/Gemma.
- Your study hinges on strong grounded vision — its multimodal ranking lags its text capability.

**Pitfalls:**
- **Large to serve yourself** — same MoE/VRAM caveats as other frontier open models. Most fellows will hit it via **OpenRouter** (`moonshotai/kimi-k2.6`) rather than self-host (see "How fellows actually access these" below).
- **"Virtue-aligned" is a disposition, not a guarantee.** It's *relatively* well-aligned; still red-team it for your specific use ([`04_red_teaming.md`](04_red_teaming.md)) rather than assuming Claude-equivalent guardrails.

---

## Gemma (Gemma 2 / Gemma 3) — the interpretability workhorse

Aliases: **Gemma**, `google/gemma-2-*` and `google/gemma-3-*` on Hugging Face (e.g. `google/gemma-2-9b`, `google/gemma-3-27b-it`), Google DeepMind's open model family. Gemma 3 sizes: **1B, 4B, 12B, 27B** (base + instruction-tuned `-it`); Gemma 2: 2B, 9B, 27B. Gemma license (custom, permissive for research — read the terms).

**Why it's notable.** Not because it's the most capable — it isn't. Gemma earns its place for three research-specific reasons:

1. **Gemma Scope** — the killer feature. Google DeepMind released a comprehensive open suite of **SAEs (Sparse Autoencoders)** trained on *every* layer/sublayer of **Gemma 2** (2B/9B, plus select layers of 27B): 400+ SAEs, 30M+ learned features (paper: "Gemma Scope," arXiv 2408.05147, JumpReLU SAEs). **Gemma Scope 2** extends this to **Gemma 3** with SAEs *and* transcoders on every layer (Matryoshka SAEs, skip-transcoders, cross-layer transcoders) for multi-step-circuit analysis. **No other open model has interpretability artifacts this complete.** If your project does SAE/feature or circuit work, Gemma is the default substrate. Full coverage in [`02_saes.md`](02_saes.md).
2. **Small enough to run locally and fine-tune easily.** The 1B/4B sizes train on a single consumer GPU; great for fast iteration and laptops-to-Lambda workflows.
3. **Distilled + a deliberately large vocabulary.** Gemma is **trained via distillation from larger Gemini-family teacher models**, which is part of why small Gemmas punch above their weight. Separately, Gemma uses a **very large (~256k–262k token) multilingual vocabulary**, so the **embedding/unembedding matrices are a disproportionately large fraction of the parameter count** in the small models — this is the "weirdly large embedding table" you notice when you inspect a Gemma checkpoint. (These are two distinct facts: distillation explains the *capability-per-param*; the big vocab explains the *param distribution*.) For interpretability this matters: a lot of the model's "size" is the token embedding, not the residual stream you're studying.

**Best for:**
- **Any SAE / feature-steering / circuit project** — Gemma Scope makes it the path of least resistance ([`02_saes.md`](02_saes.md), [`05_steering.md`](05_steering.md)).
- **Local development and cheap fine-tuning** on small GPUs.
- Multimodal-on-a-budget (Gemma 3 4B+ are vision-capable) and multilingual work.

**When *not* to use it:**
- You need frontier capability — Gemma trails DeepSeek/Kimi/Qwen-top-tier. Use those for hard tasks.
- You need a *matched baseline to prior Llama-based papers* — use Llama.

**Pitfalls:**
- **Anomalous first-token / BOS activation.** Like Llama, Gemma's position-0 activation is often an outlier; skip it or handle explicitly when probing/steering (see cross-cutting pitfalls in [`index.md`](index.md)).
- **SAE/model version match.** A Gemma Scope SAE is trained for a *specific* Gemma checkpoint and layer. Loading a Gemma-2 SAE against Gemma-3 activations (or base-SAE against instruct activations) gives garbage — `shape mismatch` if you're lucky, silently wrong features if not. Match version, size, layer, and base-vs-instruct exactly.
- **Large-embedding memory.** The big vocab means the embedding table eats VRAM; don't be surprised the 1B "small" model isn't as tiny as the active-compute suggests.

---

## Qwen (Qwen3 family)

Aliases: **Qwen**, **Qwen3** / **Qwen3.5** / **Qwen3.6**, `Qwen/Qwen3-*` on Hugging Face (and ModelScope), Alibaba's Tongyi Qianwen (通义千问) team. Sizes span **~0.6B to 235B+**, dense and MoE (e.g. Qwen3.5-35B-A3B is 35B total / ~3B active), **Apache 2.0 license** (very permissive). Base models (`*-Base`) are released alongside instruct versions.

**Why it's notable.** Qwen offers the **best capability-per-parameter at small and mid sizes**, across a **wide ladder of sizes** under a clean Apache 2.0 license, with **open base models** and the **largest fine-tuning ecosystem** of any open family (Unsloth, Llama-Factory, ms-swift, axolotl all support it first-class; thousands of community fine-tunes on HF). For a researcher, that combination — capable small models + open base weights + permissive license + mature tuning tooling — makes Qwen the **default for fine-tuning experiments**, especially model-organism work where you want to train many variants quickly ([`16_model_organisms.md`](16_model_organisms.md), [`14_rl_training.md`](14_rl_training.md)).

**Best for:**
- **Fine-tuning experiments** (SFT/DPO/GRPO) where you want a capable but small/cheap base and a size ladder to test scaling ([`14_rl_training.md`](14_rl_training.md)).
- **Cross-model replication** as the "capable small open model" arm alongside Llama/Gemma ([`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md)).
- Quick local iteration (0.6B–4B) before scaling a recipe up.

**When *not* to use it:**
- You need pretrained SAEs — Gemma + Gemma Scope instead.
- You need *the* matched baseline to existing Llama-based literature — use Llama for apples-to-apples.
- You want absolute top capability — V4-Pro/Kimi may edge it at the frontier depending on the month.

**Pitfalls:**
- **Many near-named variants.** Qwen3 vs Qwen3.5 vs Qwen3.6, dense vs `-A*B` MoE, Base vs Instruct, plus `-VL` (vision) and reasoning variants. **Pin the exact repo string** in your config — `Qwen/Qwen3.5-9B` vs `Qwen/Qwen3.5-9B-Base` is a different model and silently changes results.
- **Chat-template specifics.** Qwen has its own chat template / special tokens; a `tokenizer mismatch` or wrong template shifts which positions you steer/probe. Always use `tokenizer.apply_chat_template` and inspect the rendered string.

---

## Llama (Llama 3.x / Llama 4) — the baseline of record

Aliases: **Llama**, **LLaMA**, `meta-llama/Llama-3.1-*`, `meta-llama/Llama-3.3-70B-Instruct`, `meta-llama/Llama-4-*` on Hugging Face, Meta AI's open model family. Llama 3.1 (8B/70B/405B), **Llama 3.3 70B** (still the most-deployed open 70B), **Llama 4** (Scout / Maverick — MoE, multimodal, very long context; Behemoth announced but not released open). Llama Community License (permissive with conditions — read it; not OSI-approved).

**Why it's notable.** Llama is **a bit behind the current frontier** (DeepSeek/Kimi/Qwen-top-tier have passed it on capability), **but it has been around long enough that an enormous body of fine-tuning and interpretability experiments was built on it.** That history is the value: when you need a **matched baseline** to reproduce or extend a published result — Emergent Misalignment, persona vectors, steering, probing, control evals — there's a good chance the original used a Llama (often Llama-3.1-8B or 70B). Using the *same* base model removes "different model" as a confound. Llama is the **lingua franca baseline** of the safety-research literature.

**Best for:**
- **Reproducing / extending prior work** that used Llama — apples-to-apples ([`16_model_organisms.md`](16_model_organisms.md), [`19_behavioral_safety_playbook.md`](19_behavioral_safety_playbook.md)).
- A **well-trodden fine-tuning target** (Llama-3.1-8B is the most-documented small fine-tune in existence; Unsloth/Llama-Factory/TRL all assume it works).
- A stable **default cross-model arm** in behavioral evals (GPT, Claude, Llama, Qwen, Gemma is the canonical line-up).

**When *not* to use it:**
- You want maximum capability — it trails the 2026 frontier; use DeepSeek-V4/Kimi/top Qwen.
- You want pretrained SAEs — Gemma Scope is on Gemma, not Llama (some third-party Llama SAEs exist via SAELens/Neuronpedia but coverage is thinner — check [`02_saes.md`](02_saes.md)).

**Pitfalls:**
- **Anomalous BOS/first-token activation** is well-known on Llama — skip position 0 or handle explicitly when probing/steering.
- **Version sprawl as a baseline trap.** "Llama" in a paper could be 2, 3, 3.1, 3.2, 3.3, or 4 — and 8B vs 70B vs 405B behave very differently. To truly match a baseline, pin the *exact* checkpoint the prior work used, not just "a Llama."
- **License conditions.** The Llama Community License has acceptable-use and naming/attribution conditions and isn't a standard OSI open-source license — check before redistributing derivatives.

---

## Quick cross-cutting guidance

- **"Open weights" ≠ "open source."** You get downloadable weights to self-host and fine-tune, but licenses differ: DeepSeek-V4 and Qwen are permissive (MIT / Apache 2.0); Gemma and Llama use custom licenses with conditions. Read the license before redistributing a fine-tuned derivative.
- **MoE total vs active params.** A "1.6T" or "235B" MoE only activates a slice per token, so serving VRAM tracks *total* params but compute tracks *active* params. Budget VRAM by total size; budget latency/throughput by active size.
- **Match the checkpoint exactly** (version, size, base-vs-instruct, quant) across data prep, fine-tuning, SAE loading, and eval — most silent "my results are weird" bugs trace to a mismatch here.
- **Just call them as a black box:** **OpenRouter** (one key, all the slugs in the table above) — the dominant access path for the large models. **Where to self-host / rent GPUs:** [`10_compute.md`](10_compute.md). **How to fine-tune them:** [`14_rl_training.md`](14_rl_training.md), [`16_model_organisms.md`](16_model_organisms.md). **Get activations from a big one you can't host:** NDIF / vLLM-Lens in [`07_serving_and_activations.md`](07_serving_and_activations.md).

## Common questions

### What is the most capable open-weights model right now?
**DeepSeek-V4-Pro** (~1.6T MoE, 1M context, MIT license, April 2026) is currently the strongest open-weights model overall, with **Kimi K2.6** and the top **Qwen3.x** models close behind. For long context specifically, DeepSeek-V4's compressed-attention architecture makes 1M tokens genuinely usable.

### Which open model is most like Claude (well-aligned / has character)?
**Kimi K2.6** (Moonshot AI) — notably more "virtue-aligned" than most open-weights models and the closest open analogue to a Claude-style assistant, while being a leading agentic/coding model. It's also natively multimodal (MoonViT vision encoder).

### Which open model has pretrained SAEs (Sparse Autoencoders)?
**Gemma**, via **Gemma Scope** (Gemma 2: 400+ JumpReLU SAEs, 30M+ features) and **Gemma Scope 2** (Gemma 3: SAEs + transcoders on every layer). See [`02_saes.md`](02_saes.md). No comparably complete SAE suite exists for DeepSeek, Kimi, Qwen, or Llama.

### What's the best small open model to fine-tune?
**Qwen3** (0.6B–9B, Apache 2.0, open base models, best-in-class small-model capability, largest tuning ecosystem) for capability-per-param; **Gemma 1B/4B** if you also want Gemma Scope SAEs or laptop-scale runs. **Llama-3.1-8B** if you specifically need a matched baseline to existing literature.

### Why does a small Gemma model have so many parameters in its embedding layer?
Gemma uses a **very large (~256k–262k token) multilingual vocabulary**, so the token embedding / unembedding matrices are a large fraction of total parameters in the 1B/4B models. (Separately, Gemma is **distilled from larger Gemini teacher models**, which explains its strong capability-per-param — a different fact from the big embedding table.)

### How do I actually call DeepSeek / Kimi / a big open model without renting a GPU?
Use **OpenRouter** (`openrouter.ai`) — one OpenAI-compatible endpoint and one API key (`OPENROUTER_API_KEY`, in `~/projects/.env`) fronts them all: `deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4-flash` (with a `:free` tier), `moonshotai/kimi-k2.6` (accepts images), `qwen/qwen3.6-35b-a3b`, `google/gemma-3-27b-it`, `meta-llama/llama-4-maverick`, etc. Pay-per-token, no GPU rental, works with `safety-tooling`, Inspect AI, LiteLLM, and the OpenAI SDK (`base_url="https://openrouter.ai/api/v1"`). Self-host only when you need raw weights (fine-tuning, activations, SAEs). See [`08_safety_toolkits.md`](08_safety_toolkits.md) and [`10_compute.md`](10_compute.md).

### Can Kimi K2.6 take images?
Yes — Kimi K2.6 is vision-enabled (native MoonViT encoder) and **image input is exposed on OpenRouter** (`moonshotai/kimi-k2.6`, inputs `text` + `image`). Vision is a relative weakness vs. its strong text/agentic capability, but you can pass images.

### Which model should I use as a baseline to match a published result?
**Llama** — usually Llama-3.1-8B or Llama-3.3-70B — because most existing safety fine-tuning/interp papers built on it. Pin the *exact* checkpoint the prior work used; "a Llama" spans many incompatible versions/sizes.

---

Last verified: 2026-05-26. DeepSeek-V4-Pro/Flash and Kimi K2.6 released April 2026; specs (V4 1.6T/284B MoE, 1M context, MIT; Kimi MoonViT vision; Gemma Scope 2 on Gemma 3) from vendor/HF/Artificial Analysis reporting at that time. OpenRouter slugs, modalities, context, and pricing queried live from `https://openrouter.ai/api/v1/models` on 2026-05-26 (Kimi K2.6 confirmed `text`+`image`; DeepSeek-V4 text-only with 1M context exposed). The open-weights frontier and OpenRouter pricing move monthly — re-verify "most capable" claims, exact HF repo slugs / licenses, and prices before relying on them.

Sources consulted: [DeepSeek V4 (Artificial Analysis)](https://artificialanalysis.ai/articles/deepseek-is-back-among-the-leading-open-weights-models-with-v4-pro-and-v4-flash), [DeepSeek-V4-Flash (HF)](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash), [Kimi K2.6 (Artificial Analysis)](https://artificialanalysis.ai/articles/kimi-k2-6-the-new-leading-open-weights-model), [Gemma Scope (arXiv 2408.05147)](https://arxiv.org/abs/2408.05147), [Gemma Scope 2 (DeepMind)](https://deepmind.google/models/gemma/gemma-scope/), [Gemma 3 (HF blog)](https://huggingface.co/blog/gemma3), [Qwen (Wikipedia)](https://en.wikipedia.org/wiki/Qwen), [Llama 4 (Meta AI)](https://ai.meta.com/blog/llama-4-multimodal-intelligence/).
