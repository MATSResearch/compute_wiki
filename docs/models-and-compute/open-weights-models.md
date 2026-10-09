---
tags:
  - models
  - infrastructure
---

# Open-Weights Models for Safety Research

Which open-weights (downloadable, self-hostable) model to reach for, and *why each one is worth knowing*. This page is about research fit — capability ceiling, alignment character, interpretability-tooling support, fine-tuning ergonomics, and baseline value — not a leaderboard. For *where* to run these, see [`compute.md`](compute.md); for fine-tuning them as model organisms, see [`model-organisms.md`](../alignment-science/model-organisms.md) and [`rl-training.md`](../oversight-and-control/rl-training.md).

Acronyms used throughout: **MoE** = Mixture-of-Experts (only a subset of "expert" sub-networks activate per token, so *active* params ≪ *total* params). **SAE** = Sparse Autoencoder. **CoT** = Chain-of-Thought. **HF** = Hugging Face. **KV cache** = key/value cache (the memory that grows with context length during generation). **mHC** = Manifold-Constrained Hyper-Connections (a replacement for the plain residual connection; see the DeepSeek section). **RLVR** = Reinforcement Learning with Verifiable Rewards. **SFT / DPO** = Supervised Fine-Tuning / Direct Preference Optimization.

**What changed since the last full pass (2026-05-26 → 2026-10-09).** The open-weights frontier moved from DeepSeek-V4 / Kimi K2.6 to **Kimi K3** (2.8T-parameter MoE), **GLM-5.3**, **Qwen3.8**, **DeepSeek-V4.1-Flash** and Xiaomi's **MiMo-V2.6**; **Gemma 4** and **Olmo 3** are now common research substrates (lens papers, community SAE releases, replications); and **Qwen-Scope** (official Qwen SAEs) means Gemma is no longer the only family with an official off-the-shelf SAE suite. The decision table below is the current answer; the per-model sections carry the details and the pitfalls.

## Research-fit decision table

| I want to… | Reach for | Why |
|---|---|---|
| The most capable open-weights model | **Kimi K3**, **GLM-5.3**, **MiMo-V2.6-Pro** (statistical tie; ranking changes monthly) — or **DeepSeek-V4.1-Flash** / **Qwen3.8-27B** if you need something far cheaper to serve | On the Artificial Analysis open-weights page (fetched 2026-10-09; Intelligence Index v4.3.2, each model at its maximum reasoning setting) MiMo-V2.6-Pro scored 46, GLM-5.3 45, Kimi K3 44, GLM-5.3-Flash 42, DeepSeek-V4.1-Flash 39, Qwen3.8-27B 34. A 1–2 point gap is noise, and the index version and the reasoning setting both change the absolute numbers, so use the ordering and gaps, never the raw numbers across dates. |
| Genuinely usable **very long context** (100k–1M tokens) | **DeepSeek-V4 / V4.1**, **Qwen3.8**, **Kimi K3**, **GLM-5.3** (all list 1M-token windows) | Compressed / linear / sparse attention designs keep long-context FLOPs and KV cache tractable. |
| An **open-weights stand-in for a Claude-like, "virtue-aligned" model** | **Kimi K2.6 / K3**, with a caveat | K2.6 was reported to be character-trained like a Claude-style assistant (not verified here), but commentators report Kimi K3 sometimes claims to be Claude and appears partly distilled from Claude outputs — so it is *not* an independent data point for "other labs' models". See the Kimi section. |
| **Pretrained SAEs / transcoders / lenses off the shelf** for interpretability | **Gemma 2 / Gemma 3** (Gemma Scope 1 / 2, every layer, transcoders) first; **Qwen3 / Qwen3.5** (Qwen-Scope, official) second; **Gemma 4**, **Olmo 3**, **Qwen3.5-0.8B/4B** (community SAEs, few layers) third | Full coverage table in "Interpretability artifacts by model" below. See also [`saes.md`](../interpretability/saes.md). |
| A model with **every post-training checkpoint and the pretraining data public** (attribute a behavior to SFT vs DPO vs RLVR, or to a pretraining step) | **Olmo 3 / 3.1** (7B, 32B) | Fully open: SFT → DPO → RLVR checkpoints, 718 intermediate pretraining branches on `allenai/Olmo-3-1125-32B`, Dolma 3 / Dolci data. See the Olmo section. |
| To **run locally / fine-tune cheaply** on a laptop or single GPU | **Gemma 4** (E2B, E4B, 12B), **Qwen3.5** (0.8B–9B) | Small sizes, Apache 2.0, supported by Unsloth / Llama-Factory. 9B bf16 weights ≈ 19 GB. |
| **Capable mid-size model (27–32B) for fine-tuning or interpretability** | **Qwen3.6-27B**, **Gemma 4 31B**, **Olmo 3 32B** (bf16 weights ≈ 56 / 63 / 64 GB) | All three have pre-fitted Jacobian / J++ lenses (Gemma 4 and Olmo 3 lenses are for the *base* checkpoints); Gemma 4 and Olmo 3 have community SAEs; Olmo 3 has open training stages. |
| **Open chain-of-thought** for CoT-faithfulness / monitoring work | **gpt-oss-20b / 120b**, **Olmo 3 Think**, **Qwen3.x thinking** | gpt-oss exposes its full reasoning trace (not intended to be shown to end users). |
| A **matched baseline** comparable to prior published fine-tuning work | **Llama** (3.1/3.3), or whatever checkpoint the prior paper used | Behind the frontier, but the de-facto baseline in the older literature. |

---

## How fellows actually access these: OpenRouter

Most of these models — especially the large ones (**DeepSeek-V4.x**, **Kimi K3**, **GLM-5.3**, big Qwen) — are **too large to run locally**. Unless your project specifically needs the raw weights (fine-tuning, activation extraction, SAEs, custom hooks), the path of least resistance is to call them through **OpenRouter** (`openrouter.ai`), a single API gateway that fronts dozens of providers behind one OpenAI-compatible endpoint and one API key. The project's OpenRouter key lives at `~/projects/.env` (`OPENROUTER_API_KEY`).

**Why OpenRouter for this work:** one key for every model below (no per-lab signups), pay-per-token (no GPU rental or cold-start), automatic provider fallback, and it plugs straight into `safety-tooling`, Inspect AI, LiteLLM, and the OpenAI SDK (`base_url="https://openrouter.ai/api/v1"`). For black-box behavioral evals, cross-model replication, and judge/labeler pipelines this is almost always the right call. Use the **raw weights** (self-host or NDIF/vLLM-Lens, see [`serving-and-activations.md`](../interpretability/serving-and-activations.md)) only when you need activations, fine-tuning, or token-level control.

**Pin the provider for any result you will report.** Unpinned OpenRouter requests go to whichever third-party provider is available, and providers differ in quantization, inference backend and parameter handling (Khoriaty, LessWrong 2026-07-23). The recipe is in [`evals.md`](../evaluation/evals.md#pin-your-inference-provider-openrouter-and-other-routers).

**Verified on OpenRouter (2026-10-09)** — slugs, input modalities, context, and price as returned by `https://openrouter.ai/api/v1/models` ($/Mtok = US dollars per million tokens, prompt / completion):

| Model | OpenRouter slug | Inputs | Context | $/Mtok in / out |
|---|---|---|---|---|
| Kimi K3 | `moonshotai/kimi-k3` | text, image, video | 1,048,576 | 0.80 / 13.50 |
| Kimi K2.6 | `moonshotai/kimi-k2.6` | text, image | 262,144 | 0.43 / 2.45 |
| GLM-5.3 | `z-ai/glm-5.3` | text | 1,048,576 | 0.05 / 6.00 |
| GLM-5.3-Flash | `z-ai/glm-5.3-flash` | text, image, video | 1,048,576 | 0.15 / 0.50 |
| DeepSeek-V4.1-Flash | `deepseek/deepseek-v4.1-flash` | text, image | 1,048,576 | 0.30 / 1.20 |
| DeepSeek-V4-Pro-0813 (official release) | `deepseek/deepseek-v4-pro-0813` | text | 1,048,576 | 0.66 / 1.98 |
| DeepSeek-V4-Flash-0731 (official release) | `deepseek/deepseek-v4-flash-0731` | text | 1,048,576 | 0.005 / 1.28 |
| DeepSeek-V4-Pro (April **preview**, "0423") | `deepseek/deepseek-v4-pro` | text | 1,048,576 | 0.21 / 0.42 |
| DeepSeek-V4-Flash (April **preview**, "0423") | `deepseek/deepseek-v4-flash` | text | 1,048,576 | 0.006 / 1.28 |
| Qwen3.8-27B | `qwen/qwen3.8-27b` | text, image, video | 1,000,000 | 0.43 / 2.55 |
| Qwen3.8-2.4T-A95B | `qwen/qwen3.8-2.4t-a95b` | text | 1,048,576 | 2.00 / 6.00 |
| Qwen3.6-27B | `qwen/qwen3.6-27b` | text, image, video | 262,144 | 0.32 / 3.20 |
| Qwen3.6-35B-A3B | `qwen/qwen3.6-35b-a3b` | text, image, video | 262,144 | 0.15 / 1.00 |
| Qwen3.5-122B-A10B | `qwen/qwen3.5-122b-a10b` | text, image, video | 262,144 | 0.26 / 2.08 |
| Qwen3.5-9B | `qwen/qwen3.5-9b` | text, image, video | 262,144 | 0.10 / 0.15 |
| Gemma 4 31B IT | `google/gemma-4-31b-it` (also `:free`) | text, image, video | 262,144 | 0.09 / 0.34 |
| Gemma 4 26B-A4B IT | `google/gemma-4-26b-a4b-it` (also `:free`) | text, image, video | 262,144 | 0.07 / 0.23 |
| Gemma 3 27B IT | `google/gemma-3-27b-it` | text, image | 131,072 | 0.08 / 0.45 |
| Llama 4 Maverick | `meta-llama/llama-4-maverick` | text, image | 1,048,576 | 0.19 / 0.65 |

Notes:
- **`deepseek/deepseek-v4-pro` and `deepseek/deepseek-v4-flash` are the April *preview* checkpoints, not the latest.** The OpenRouter display names read "DeepSeek V4 Pro 0423" / "DeepSeek V4 Flash 0423"; DeepSeek's later official releases (V4-Flash-0731, V4-Pro-0813, V4.1-Flash) have their own dated slugs. A paper that says "DeepSeek-V4-Flash" may mean either — record the dated slug (and provider) in `metadata.json`.
- Some input prices look like cached-token or promotional tiers (e.g. `deepseek-v4-flash` input ≈ $0.006/Mtok against $1.28 output; `glm-5.3` input $0.05 against $6.00 output). Budget with a measured token mix, not the headline input price.
- **Kimi K3, Kimi K2.6, Qwen3.x and Gemma 4 accept image input** on OpenRouter; the DeepSeek V4 preview and V4-0731/0813 slugs are text-only, while `deepseek-v4.1-flash` and `deepseek-v4-flash-vision-exp` take images.
- Prices, slugs and which snapshot an alias points to drift — re-query `https://openrouter.ai/api/v1/models` before scripting.

---

## Interpretability artifacts by model (SAEs, transcoders, lenses) — what exists as of 2026-10-09

Which open-weights model has **pretrained Sparse Autoencoders (SAEs)**, **transcoders**, or **lenses** you can download instead of training your own? Terms: **SAE** = Sparse Autoencoder; **JumpReLU / TopK / BatchTopK / Matryoshka** = SAE architectures (activation function or nested-width training variants); **transcoder** = a sparse replacement for a multilayer-perceptron (MLP) block, used for circuit tracing; **J-Lens (Jacobian lens)** = a per-layer linear map that reads an intermediate activation out as the tokens the model is disposed to say; **J++ Lens** = an improved J-Lens fitted with filtered Jacobians. Checked on Hugging Face and Neuronpedia on 2026-10-09 — "none found" means a search of the vendor namespace and the model's Neuronpedia page, not proof of absence.

| Model family | What exists | Where | Caveats |
|---|---|---|---|
| **Gemma 2** (2B, 9B, 27B) | **Gemma Scope**: JumpReLU SAEs on every layer/sublayer of 2B and 9B, select layers of 27B; transcoders for 2B | `google/gemma-scope-*` (arXiv 2408.05147) | Oldest, best-studied; Gemma 2 is no longer the capability frontier. |
| **Gemma 3** (270M, 1B, 4B, 12B, 27B; base `-pt` and instruction-tuned `-it`) | **Gemma Scope 2**: SAEs on residual / attention-out / MLP-out sites, transcoders, cross-layer transcoders and crosscoders (file listing of `gemma-scope-2-1b-pt`), 10 repos | `google/gemma-scope-2-{270m,1b,4b,12b,27b}-{pt,it}` (CC-BY-4.0); demo on Neuronpedia | Most complete suite for a model with vision and 128k context. |
| **Gemma 4** (E2B, E4B, 12B, 26B-A4B, 31B) | **No official Google SAE suite found.** Community: Matryoshka BatchTopK SAEs for E2B (layers 6/17/28), E4B (layers 7/21/35), 31B (**layer 30 only**, 131k wide) | `decoderesearch/gemma-4-saes` (Chanin & Lin, Decode Research; SAELens format; trained on the Pile Uncopyrighted); also on Neuronpedia | Three layers per small model, one for 31B — fine for a single-layer probe or steering study, not for circuit tracing across depth. |
| **Qwen3 / Qwen3.5** (Qwen3-1.7B/8B/30B-A3B Base; Qwen3.5-2B/9B Base, 27B, 35B-A3B Base) | **Qwen-Scope** (official): TopK SAEs on the residual stream, one per layer (e.g. 9B-Base: 65,536 features, k=50 or 100, layers 0–31) | `Qwen/SAE-Res-*` on HF (arXiv 2605.11887, Qwen team, May 2026); Neuronpedia hosts Qwen-Scope sources for Qwen3.5 models (e.g. 2B, 9B, 27B); custom Qwen license (`license: other`) | The Qwen README says SAEs trained on base models are reasonable for post-trained checkpoints — a claim to test (reconstruction loss on *your* checkpoint), not assume. |
| **Qwen3.5-0.8B / 4B** | Community Matryoshka BatchTopK SAEs (base and post-trained, 3 layers each) | `decoderesearch/qwen-3.5-saes` | Sparse layer coverage. |
| **Qwen3.6, Qwen3.8** | No SAE suite found (Qwen3.6-27B has pre-fitted lenses, below) | — | Qwen-Scope stops at Qwen3.5; don't load a Qwen3.5 SAE onto Qwen3.6 activations. |
| **Olmo 3** (7B, 32B) | Community SAEs: 7B base (layers 4/16/28, 65k wide) and 32B base (residual layer 32, BatchTopK; Neuronpedia "Olmo 3 32B SAE", 131k) | `decoderesearch/olmo-3-saes`, `bcywinski/Olmo-3-32B-Base-SAE` | Trained on the **base** models; the SFT / DPO / RLVR checkpoints are separate weights. |
| **DeepSeek-V4/V4.1, Kimi K2.6/K3, GLM-5.x, MiMo, Muse Glimmer** | No SAE suite found (DeepSeek-V4-Flash has a pre-fitted lens, below) | — | Plan on the black-box API route, or on training your own SAEs on a *small* sibling. |
| **gpt-oss-20b**, **Llama 3.1-8B / 3.3-70B**, **Qwen3 dense** | Pre-fitted Jacobian lenses; third-party SAEs for Llama exist (see [`saes.md`](../interpretability/saes.md)) | `neuronpedia/jacobian-lens` | — |

**Lenses.** Anthropic's *Verbalizable Representations Form a Global Workspace in Language Models* (Gurnee, Sofroniew et al., transformer-circuits.pub, 2026-07-06) introduced the Jacobian lens; the reference code is `anthropics/jacobian-lens` (Apache-2.0; its README says "not maintained and not accepting contributions"). Pre-fitted J-Lens and J++ Lens files for roughly 40 open models — Gemma 2/3/4, Qwen3/3.5/3.6, Olmo 3, DeepSeek-V4-Flash, gpt-oss-20b, Llama 3.1/3.3 — are in `neuronpedia/jacobian-lens` on Hugging Face and browsable at `neuronpedia.org/jlens`. The J++ Lens paper (Ayonrinde & Lindsey, *J++ Lens: Jacobian Filtering Enables More Faithful Workspace Lenses*, 2026-10; code `safety-research/jpp_lens`, lenses `koayon/jpp-lenses`) released lenses for six models — **Qwen3.6-27B, Qwen3.5-9B, Gemma 4 31B (base), Olmo-3-1125-32B (base), Qwen3.5-122B-A10B, DeepSeek-V4-Flash (April preview checkpoint)** — with recall@10 on the paper's readout tasks of 55.2 / 55.0 / ~58 (one readout task dropped for Gemma 4) / 50.0 / 48.4 / 61.4 %. Qwen3.6-27B in bf16 needs about 54 GB of GPU memory (README). Interpretation of the method belongs in [`mech-interp.md`](../interpretability/mech-interp.md) and [`probes.md`](../interpretability/probes.md).

**Pitfalls (searchable symptoms).** (MoE = Mixture-of-Experts; KV cache = key/value cache.)
- **Checkpoint mismatch.** A lens or SAE is fitted to one set of weights. `deepseek-ai/DeepSeek-V4-Flash` (April preview), `DeepSeek-V4-Flash-0731` and `DeepSeek-V4.1-Flash` are three different checkpoints, and the Gemma 4 31B lens is documented for the base `google/gemma-4-31B`, not `-it` (read each SAE's `cfg.json` for the model it was trained on). Wrong match gives plausible-looking garbage or `RuntimeError: size mismatch for ...` — assert the model id and layer count when you load.
- **Hybrid attention breaks attention-pattern tooling.** Qwen3.5 / 3.6 / 3.8 interleave **Gated DeltaNet** (a linear-attention recurrence, no softmax attention matrix) with ordinary gated attention in a 3 : 1 pattern; the `Qwen/Qwen3.5-9B` config has 32 layers = 24 `linear_attention` + 8 `full_attention`. Head-level attention-pattern analysis, induction-head searches and attention-based steering therefore apply to only a quarter of the layers; hook code written for Llama-style blocks may raise `AttributeError` on the linear-attention layers. Kimi K3 (Kimi Delta Attention), GLM-5.3-Flash (sparse + linear attention) and DeepSeek-V4 (Compressed Sparse / Heavily Compressed Attention) also depart from plain softmax attention.
- **mHC changes what "the residual stream" is.** DeepSeek-V4 and GLM-5.3-Flash use Manifold-Constrained Hyper-Connections (mHC, arXiv 2512.24880, DeepSeek-AI), a constrained version of Hyper-Connections, which *expand the residual stream width* (per the abstract). Hook libraries that assume one `d_model`-wide residual vector per layer need checking; the J++ repo ships a DeepSeek-V4-Flash lens, so its code shows one team's definition of the layer output.
- **Thinking-mode tokens change what you hook.** Gemma 4 generates an empty thought block (`<|channel>thought\n<channel|>`) before the answer even with thinking off (every size except E2B/E4B), and Qwen3.8 has thinking on by default; so the same prompt yields different generated token sequences, and therefore different positions for probes and steering, depending on mode. Always render with `tokenizer.apply_chat_template`, print the string, and record the thinking setting.

---

## DeepSeek-V4 family (V4-Pro, V4-Flash, V4.1-Flash)

Aliases: **DeepSeek V4**, **DeepSeek-V4.1**, `deepseek-ai/DeepSeek-V4-Pro`, `deepseek-ai/DeepSeek-V4-Flash`, `deepseek-ai/DeepSeek-V4-Pro-0813`, `deepseek-ai/DeepSeek-V4-Flash-0731`, `deepseek-ai/DeepSeek-V4.1-Flash` on Hugging Face, "DeepSeek's V4", DeepSeek-AI (High-Flyer / 深度求索). **MIT license** on every repo checked (permissive — fine-tune and redistribute freely). Technical report: *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*, arXiv:2606.19348.

**Which checkpoint is which (the naming trap).**

| Checkpoint (HF repo) | Date (HF) | What it is |
|---|---|---|
| `DeepSeek-V4-Pro`, `DeepSeek-V4-Flash` (+ `-Base` variants) | 2026-04-22 | The original **preview** release. Pro: 1.6T total / 49B active MoE; Flash: 284B total / 13B active; both 1M context. |
| `DeepSeek-V4-Flash-0731` | 2026-07-31 | The **official** Flash release, "superseding the preview version"; stronger agentic performance; a speculative-decoding module (DSpark) is attached. |
| `DeepSeek-V4-Pro-0813` | 2026-08-13 | The **official** Pro release, same relationship to the Pro preview. |
| `DeepSeek-V4-Flash-Vision-Exp` | 2026-08-31 | Experimental multimodal Flash (image in, text out). |
| `DeepSeek-V4.1-Flash` | 2026-09-10 | New multimodal MoE: 552B backbone plus a 196B-parameter "Engram" conditional-memory table, a **Causal Encoder-Decoder** layout (8B active per token at prefill, 16B at decode), FP4 KV cache, 1M context, 45T training tokens. |

The OpenRouter aliases `deepseek/deepseek-v4-pro` and `deepseek/deepseek-v4-flash` still point at the **April preview** — see the OpenRouter table. A paper that says "DeepSeek-V4-Flash" is ambiguous; record the dated repo or slug.

**Why it's notable.** (MoE = Mixture-of-Experts; KV cache = key/value cache; FP4 / FP8 = 4-bit / 8-bit floating point.) The V4 line's headline feature is **long-context efficiency**: a hybrid attention scheme (Compressed Sparse Attention plus Heavily Compressed Attention) that, per the tech report, needs about 27% of the single-token inference FLOPs and 10% of the KV cache of DeepSeek-V3.2 at 1M tokens (Pro). The architecture also uses **Manifold-Constrained Hyper-Connections (mHC)** — Xie et al., *mHC: Manifold-Constrained Hyper-Connections*, arXiv:2512.24880 — a replacement for the plain residual connection that widens the residual stream while restoring the identity-mapping property for stability, plus the Muon optimizer. V4.1 adds a "Single-Pass mHC" revision and the Engram memory. mHC matters to interpretability because it changes what "the residual stream" is (see the artifacts section above).

**Memory reality check (corrects an earlier version of this page).** The released V4-Flash checkpoint stores MoE expert weights in FP4 and most other weights in FP8, and the HF repo is about **160 GB** — it does **not** fit on a single 80 GB GPU; plan on at least two 80 GB cards (or one ≥192 GB card) for weights alone, plus KV cache. V4-Pro is about 865 GB and V4.1-Flash about 510 GB on disk.

**Best for:**
- Tasks needing **near-frontier open-weights capability at modest serving cost** (V4.1-Flash and V4-Flash-0731 are far cheaper than the 1–3T-parameter frontier models; see agent scaffolds in [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md)).
- **Long-context experiments** — many-document retrieval, long-transcript analysis, long-horizon agent traces, whole-codebase reasoning, long-context faithfulness studies ([`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)).
- A **non-US-lab open model** for cross-lab generalization checks in behavioral safety work ([`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md)).
- **Lens-based readout** work on a very large MoE: a pre-fitted J++ lens exists for the April `DeepSeek-V4-Flash` checkpoint.

**When *not* to use it:**
- You want to fine-tune on modest hardware — even Flash needs a multi-GPU node and expert-parallel tooling. Use Qwen / Gemma / Olmo instead.
- You need SAEs or transcoders — none found for any V4 checkpoint.
- You need a long published track record of fine-tuning recipes — the line is six months old and the checkpoints keep changing.

**Pitfalls:**
- **Preview vs official vs V4.1.** Three generations of weights share the name. Results, lenses and quantized builds are not interchangeable; the J++ Lens for `DeepSeek-V4-Flash` was fitted on the April preview, so do not assume it transfers to `-0731` or V4.1.
- **MoE serving complexity.** Expert-parallel serving is non-trivial; expect vLLM / SGLang with tensor + expert parallelism. `CUDA out of memory` on a single 80 GB GPU is expected for every V4 checkpoint. Most fellows should use **OpenRouter** (pin the provider) unless they need raw weights.
- **Long-context ≠ free.** The architecture makes 1M context *tractable*, not *instant*. Latency and cost still scale with context; measure before assuming you can stuff 1M tokens every call. DeepSeek recommends a context window of at least 384K tokens for the Think-Max reasoning mode.
- **Verify the exact HF repo and quant build** before scripting a download — there are Pro/Flash, base/instruct, preview/official, NVFP4 (`nvidia/DeepSeek-V4.1-Flash-NVFP4`) and community GGUF repos with different names.

---

## Kimi K3 and Kimi K2.6

Aliases: **Kimi K3**, `moonshotai/Kimi-K3`; **Kimi K2.6**, **Kimi v2.6**, `moonshotai/Kimi-K2.6`; "Kimi" (Moonshot AI / 月之暗面 Moonshot), Moonshot's open-weights agentic models. Also `moonshotai/Kimi-K2.7-Code` (coding variant, HF repo 2026-06-11, 1T-class, modified MIT).

| | Kimi K2.6 | Kimi K3 |
|---|---|---|
| Weights on HF | 2026-04-14 | first commit 2026-07-27 (announced mid-July) |
| Size | ~1T total / 32B active MoE | **2.8T total / 104B active** MoE, 16 of 896 experts, 93 layers; weights released in MXFP4 (quantization-aware training) |
| Attention | MLA (multi-head latent attention), 61 layers | 69 Kimi Delta Attention (linear) + 24 gated MLA layers, plus "Attention Residuals" |
| Context | 256K | 1M |
| Inputs | text, image (MoonViT, ~400M-parameter vision encoder) | text, image, video (MoonViT-V2, ~401M) |
| License | Modified MIT | **Kimi K3 License**: a broad grant (internal use is exempt from the extra terms) with added conditions for operators of a "Model as a Service" business above US$20M revenue (separate agreement needed) and for products above 100M monthly active users or US$20M monthly revenue (must display "Kimi K3") — read it before redistributing derivatives |

**Why it's notable.** (MoE = Mixture-of-Experts; MLA = multi-head latent attention; MXFP4 = 4-bit microscaling floating point.) (1) **Capability**: K3 is, with GLM-5.3 and MiMo-V2.6-Pro, at the top of the open-weights tables (Artificial Analysis open-weights page, 2026-10-09, Intelligence Index v4.3.2: MiMo-V2.6-Pro 46, GLM-5.3 45, Kimi K3 44). Zvi Mowshowitz's review (LessWrong, 2026-07-20, *On Kimi K3*) judges it the strongest open model on raw capability but "several months behind the closed model frontier" (his median guess: six), "somewhat distilled", scored at maximum reasoning effort (many more tokens than rival tests), slow and token-hungry. (2) **Alignment character**: earlier reporting described K2.6 as more "virtue-aligned" than most open-weights models — a trained disposition closer to a Claude-style assistant than a raw open model. That makes the Kimi line useful when your research *needs* a frontier-assistant-like open model.

**Independence warning (new).** Commentators collected in the same review report that K3 **sometimes claims to be Claude** (one commenter says it "thinks it's Claude 1 in 10 times"; another, "not usually, but sometimes"), that its reasoning-trace style resembles Claude's, and that Moonshot distilled from Claude outputs (the review's author judges Claude distillation to be part of the story). All of this is second-hand social-media reporting; Moonshot has not confirmed it and we have not verified it. If it is true, **Kimi agreeing with Claude is weak evidence of cross-lab generalization** — do not use K3 as the "independent lab" arm of a cross-model check without testing for it.

**Safety posture.** The same review relays user reports (not systematic evaluations) that K3 has no explicit biology or cyber safeguards, and that its cyber capability is weaker than its general coding. For misuse-adjacent evaluations treat it as an *un-safeguarded* open model and handle outputs accordingly.

**Best for:**
- An **open-weights baseline that behaves like Claude/GPT-class assistants** — comparison points for alignment, character, refusal, sycophancy, and welfare/introspection studies ([`welfare-introspection.md`](../alignment-science/welfare-introspection.md)) — subject to the independence warning.
- **Agentic / tool-use** research on a capable open model ([`agent-scaffolds.md`](../evaluation/agent-scaffolds.md), [`ai-control.md`](../oversight-and-control/ai-control.md)); K3 is relatively strongest on typical agentic coding (per the Zvi review).
- Studies that want a **non-US, character-trained open model** for cross-model generalization.

**When *not* to use it:**
- You need pretrained SAEs/transcoders — none found for Kimi; use Gemma Scope or Qwen-Scope models.
- You need a small, cheaply-fine-tunable model — K3's checkpoint is well over a terabyte; use Qwen / Gemma / Olmo.
- You need a cheap model for judge/labeler pipelines — K3's OpenRouter output price (US$13.50 per million tokens, 2026-10-09) is an order of magnitude above Flash-class models.
- You need an independent-lab data point (see the independence warning).

**Pitfalls:**
- **Large to serve yourself** — same MoE/VRAM caveats as other frontier open models. Most fellows will hit it via **OpenRouter** (`moonshotai/kimi-k3`, `moonshotai/kimi-k2.6`; pin the provider), see "How fellows actually access these".
- **Linear-attention layers** (K3): attention-pattern analysis applies only to the 24 gated-MLA layers (see the artifacts section).
- **"Virtue-aligned" is a disposition, not a guarantee.** Red-team it for your specific use ([`red-teaming.md`](../evaluation/red-teaming.md)) rather than assuming Claude-equivalent guardrails.

---

## Gemma (Gemma 2 / Gemma 3 / Gemma 4) — the interpretability workhorse

Aliases: **Gemma**, `google/gemma-2-*`, `google/gemma-3-*`, `google/gemma-4-*` on Hugging Face (e.g. `google/gemma-2-9b`, `google/gemma-3-27b-it`, `google/gemma-4-31B-it`), Google DeepMind's open model family. Sizes: Gemma 2 — 2B, 9B, 27B; Gemma 3 — 270M, 1B, 4B, 12B, 27B (base + instruction-tuned `-it`); **Gemma 4 (released early April 2026 — HF first commit 2026-04-02; 12B added 2026-06-03)** — **E2B, E4B, 12B, 26B-A4B (Mixture-of-Experts, MoE), 31B (dense)**, 256K context on 12B and up, text + image on all (audio on E2B / E4B / 12B), a thinking mode, and a native `system` role. **Licenses: Gemma 4 is Apache 2.0 (HF `license: apache-2.0`); Gemma 2 and 3 use the custom Gemma terms — read them.** Gemma 4 technical report: arXiv:2607.02770. Also `google/diffusiongemma-26B-A4B-it` (2026-06-09, Apache 2.0): a discrete-diffusion variant of the 26B-A4B MoE that denoises blocks of tokens in parallel — a non-autoregressive substrate that LessWrong posts in July–August 2026 used for latent-reasoning and jailbreak studies, with correspondingly little tooling.

**Why it's notable.** Not because it's the most capable — it isn't. Gemma earns its place for three research-specific reasons:

1. **Gemma Scope** — the most complete open interpretability suite. Google DeepMind released **SAEs (Sparse Autoencoders)** on every layer/sublayer of **Gemma 2** (2B/9B, plus select layers of 27B): 400+ SAEs, 30M+ learned features (paper: "Gemma Scope," arXiv 2408.05147, JumpReLU SAEs). **Gemma Scope 2** (`google/gemma-scope-2-*`, Dec 2025) covers **Gemma 3** 270M–27B, base and instruction-tuned, with SAEs, transcoders, cross-layer transcoders and crosscoders. **There is no official Gemma Scope for Gemma 4 as of 2026-10-09**; the community fills part of the gap (`decoderesearch/gemma-4-saes`: E2B and E4B at three layers each, 31B at one layer). If your project needs full-depth SAE/transcoder coverage for circuit work, **Gemma 3 is still the default substrate**; Gemma 4 is the better *model* but the thinner *toolkit*. See the artifacts table above and [`saes.md`](../interpretability/saes.md).
2. **Small enough to run locally and fine-tune easily.** The Gemma 3 1B/4B and Gemma 4 E2B/E4B/12B sizes train on a single consumer or workstation GPU; Gemma 4 31B in bf16 is about 63 GB of weights (31.3B parameters in the HF safetensors total; the model card lists 30.7B). Google also ships quantization-aware-trained builds (`*-it-qat-*`) — fine for serving, but use bf16 weights for activations and fine-tuning.
3. **Distilled + a deliberately large vocabulary.** Gemma is **trained via distillation from larger Gemini-family teacher models**, which is part of why small Gemmas punch above their weight. Separately, Gemma uses a **very large (~256k–262k token) multilingual vocabulary** (262K in Gemma 4), so the **embedding/unembedding matrices are a disproportionately large fraction of the parameter count** in the small models (Gemma 4 E2B: 2.3B "effective" parameters, 5.1B with embeddings, because of per-layer embeddings). For interpretability this matters: a lot of the model's "size" is the token embedding, not the residual stream you're studying.

**Best for:**
- **Any SAE / feature-steering / circuit project** on Gemma 2 or 3 — Gemma Scope makes it the path of least resistance ([`saes.md`](../interpretability/saes.md), [`steering.md`](../interpretability/steering.md)).
- **Local development and cheap fine-tuning** on small GPUs; Gemma 4 12B / 26B-A4B / 31B are strong mid-size fine-tuning and lens targets (pre-fitted Jacobian lenses exist for Gemma 4 E2B, E4B and 31B).
- Multimodal-on-a-budget and multilingual work.

**When *not* to use it:**
- You need frontier capability — Gemma trails Kimi K3 / GLM-5.3 / Qwen3.8 at the top end. Use those for hard tasks.
- You need *full-depth* SAEs on a Gemma 4 model — only a few layers exist; use Gemma 3 or Qwen3.5 (Qwen-Scope).
- You need a *matched baseline to prior Llama-based papers* — use Llama.

**Pitfalls:**
- **Anomalous first-token / BOS activation.** Like Llama, Gemma's position-0 activation is often an outlier; skip it or handle explicitly when probing/steering (see cross-cutting pitfalls in [`index.md`](../index.md)).
- **SAE/model version match.** A Gemma Scope SAE is trained for a *specific* Gemma checkpoint and layer. Loading a Gemma-2 SAE against Gemma-3 activations, a Gemma 3 SAE on Gemma 4, or a base SAE against instruct activations gives garbage — `shape mismatch` if you're lucky, silently wrong features if not. Match version, size, layer, and base-vs-instruct exactly.
- **Gemma 4 thinking tokens.** Thinking is switched on by putting `<|think|>` at the start of the system prompt. With thinking off, every size except E2B/E4B still emits an empty thought block (`<|channel>thought\n<channel|>`) before the answer, and historical turns must contain only the final response (no earlier thoughts) — so generated token positions — and any probe or steering offsets tied to them — can differ between modes. Use `tokenizer.apply_chat_template` and print the rendered string.
- **Large-embedding memory.** The big vocab means the embedding table eats VRAM; don't be surprised the 1B "small" model isn't as tiny as the active-compute suggests.

---

## Qwen (Qwen3 / Qwen3.5 / Qwen3.6 / Qwen3.8)

Aliases: **Qwen**, **Qwen3** / **Qwen3.5** / **Qwen3.6** / **Qwen3.8**, `Qwen/Qwen3-*`, `Qwen/Qwen3.5-*`, `Qwen/Qwen3.6-*`, `Qwen/Qwen3.8-*` on Hugging Face (and ModelScope), Alibaba's Tongyi Qianwen (通义千问) team.

| Generation | Open-weight sizes (HF) | Date (HF) | License |
|---|---|---|---|
| Qwen3.5 | 0.8B, 2B, 4B, **9B**, 27B (dense); 35B-A3B, **122B-A10B**, 397B-A17B (Mixture-of-Experts, MoE). Base (`-Base`) models exist for 0.8B / 2B / 4B / 9B / 35B-A3B only | Feb 2026 | Apache 2.0 |
| Qwen3.6 | **27B** (dense), 35B-A3B (MoE); **no base models**; names such as `qwen3.6-plus` and `qwen3.6-flash` appear on OpenRouter but not as HF repos | Apr 2026 | Apache 2.0 |
| Qwen3.8 | **27B** (dense, 2026-08-05); Flash-Next (125B total / 6B active plus n-gram embeddings, 2026-08-24, `qwen-community-1.0` license); **2.4T-A95B** (2.4T total / 95B active, 2026-08-08, `qwen3.8-max` license) | Aug 2026 | Apache 2.0 for the 27B; custom Qwen licenses for the other two |

**Qwen3.5, 3.6 and 3.8 are hybrid-attention models** (checked in the configs / model cards of Qwen3.5-9B, Qwen3.6-27B, Qwen3.8-27B and Qwen3.8-2.4T-A95B): three Gated DeltaNet (linear-attention) layers for every one gated-attention layer, a 248,320-token padded vocabulary, and a 262,144-token native context extensible to about 1M. The dense and small models take image and video input; Qwen3.8-2.4T-A95B is text-only.

**Why it's notable.** Qwen offers the **best capability-per-parameter at small and mid sizes**, across a **wide ladder of sizes** under a clean Apache 2.0 license (for the open dense models), with **open base models for the small sizes** and the **largest fine-tuning ecosystem** of any open family (Unsloth, Llama-Factory, ms-swift, axolotl all support it first-class; thousands of community fine-tunes on HF). For a researcher, that combination — capable small models + open base weights + permissive license + mature tuning tooling — makes Qwen the **default for fine-tuning experiments**, especially model-organism work where you want to train many variants quickly ([`model-organisms.md`](../alignment-science/model-organisms.md), [`rl-training.md`](../oversight-and-control/rl-training.md)). **New since the last pass:** Alibaba released **Qwen-Scope** — official SAEs for Qwen3 and Qwen3.5 (arXiv:2605.11887) — so Qwen is now the second family with an official SAE suite; and **Qwen3.5-9B, Qwen3.6-27B and Qwen3.5-122B-A10B** all have pre-fitted J++ lenses (see the artifacts section).

**Best for:**
- **Fine-tuning experiments** (SFT = supervised fine-tuning, DPO = direct preference optimization, GRPO = group relative policy optimization) where you want a capable but small/cheap base and a size ladder to test scaling ([`rl-training.md`](../oversight-and-control/rl-training.md)). For a clean *base* model use Qwen3.5 (0.8B–9B, 35B-A3B); Qwen3.6 and the 27B / 122B-A10B Qwen3.5 models are post-trained only.
- **SAE / feature work on a modern small model** — Qwen3.5-9B with Qwen-Scope (all 32 layers) plus a pre-fitted J++ lens is a well-supported combination outside Gemma.
- **Cross-model replication** as the "capable small open model" arm alongside Llama/Gemma ([`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md)).
- Quick local iteration (0.8B–4B) before scaling a recipe up; Qwen3.8-27B is the current strong dense mid-size option (bf16 weights ≈ 56 GB).

**When *not* to use it:**
- You need SAEs for **Qwen3.6 or Qwen3.8** — Qwen-Scope stops at Qwen3.5.
- You need attention-head-level interpretability — three of every four layers have no softmax attention (see the pitfall below). Use Gemma 3 or Olmo 3.
- You need *the* matched baseline to existing Llama-based literature — use Llama for apples-to-apples.
- You want absolute top capability — Kimi K3 / GLM-5.3 / MiMo-V2.6-Pro lead; Qwen3.8-2.4T-A95B is open but needs a multi-node serve.

**Pitfalls:**
- **Many near-named variants.** Qwen3 vs Qwen3.5 vs Qwen3.6 vs Qwen3.8, dense vs `-A*B` MoE, Base vs post-trained, `-FP8`, plus API-only names like `qwen3.6-plus` / `qwen3.8-max`. **Pin the exact repo string** in your config — `Qwen/Qwen3.5-9B` vs `Qwen/Qwen3.5-9B-Base` is a different model and silently changes results; the J++ lens and Qwen-Scope SAEs are documented for specific ones of these (Qwen-Scope SAEs are mostly trained on the Base checkpoints).
- **Hybrid attention.** `Qwen/Qwen3.5-9B` has 32 layers: 24 `linear_attention` (Gated DeltaNet) and 8 `full_attention`; the architecture class is `Qwen3_5ForConditionalGeneration` (a vision-language wrapper even for text-only use). Attention-pattern code, key/value (KV) cache hooks and induction-head searches written for Llama-style models break or silently cover only the full-attention quarter; update `transformers` / vLLM before blaming your hook.
- **Chat-template specifics.** Qwen has its own chat template / special tokens; a `tokenizer mismatch` or wrong template shifts which positions you steer/probe. Thinking is on by default for Qwen3.8 and can be disabled per request, and `preserve_thinking` (prior-turn reasoning is kept in the context) is also on by default and can be switched off — so the same conversation tokenizes differently across settings. Always use `tokenizer.apply_chat_template` and inspect the rendered string.

---

## Olmo 3 / Olmo 3.1 (Ai2) — the fully open model for training-stage questions

Aliases: **Olmo 3**, **OLMo 3**, `allenai/Olmo-3-*`, `allenai/Olmo-3.1-*`, Ai2 (Allen Institute for AI), "the fully open model". Sizes: **7B and 32B**, each as a base model, a **Think** (long chain-of-thought reasoning) variant and an **Instruct** variant. **Apache 2.0.** Announced 2025-11-20 (Olmo 3; the HF repos are dated 2025-11-19); Olmo 3.1 (`Olmo-3.1-32B-Think`, `Olmo-3.1-32B-Instruct`, 2025-12-10) is the later release; for Think it is the same base, SFT and DPO data plus roughly three more weeks of RLVR.

**Why it's notable.** Ai2 releases *everything* — pretraining data (Dolma 3), post-training data (Dolci), code, and **every training-stage checkpoint**: base → SFT (supervised fine-tuning) → DPO (direct preference optimization) → RLVR (reinforcement learning with verifiable rewards, the final model) for both 7B and 32B (`Olmo-3-32B-Think-SFT`, `Olmo-3-32B-Think-DPO`, `Olmo-3-32B-Think`), plus `Olmo-3-7B-RL-Zero-*` runs and **718 intermediate pretraining branches** (719 refs counting `main`) on `allenai/Olmo-3-1125-32B` (e.g. `stage1-step597000`). That makes it the natural model for questions of the form "*which training stage caused this behavior?*":
- Bharadwaj et al. (LessWrong, 2026-06-10, *Tracing Eval-Awareness Emergence Through Training of OLMo 3*): verbalized eval awareness is about 1% during pretraining, rises with SFT, collapses with DPO and rises again with RLVR; Olmo-3-32B-Think and Olmo-3.1-32B-Think differ only in roughly three extra weeks of RLVR, and the rate roughly doubles.
- Cairns et al. (LessWrong, 2026-09-11, *SFT Also Drives Safety Eval Results in Olmo 3*; code `cheeetoo/sft-safety`): the released SFT, DPO and RLVR checkpoints of Olmo 3 32B Think are within noise of each other on every Petri dimension, ODCV-Bench, StrongREJECT, ImpossibleBench and MASK while LiveCodeBench roughly doubles — replicating, on an open model, Engels et al.'s finding that SFT already sets most safety eval results in Gemini. Caveat from the authors: Olmo's RLVR stage is small relative to frontier post-training, and flat evals do not prove unchanged safety properties.

**Interpretability tooling.** Community SAEs for the 7B base (`decoderesearch/olmo-3-saes`, layers 4/16/28) and the 32B base (`bcywinski/Olmo-3-32B-Base-SAE`, residual layer 32) and pre-fitted Jacobian / J++ lenses for `Olmo-3-1025-7B` and `Olmo-3-1125-32B` — all on the **base** checkpoints (see the artifacts table).

**Best for:**
- **Training-dynamics and model-diffing studies** across SFT → DPO → RLVR or across pretraining steps ([`model-diffing.md`](../interpretability/model-diffing.md), [`data-attribution.md`](../interpretability/data-attribution.md)).
- **Eval-awareness, reward-hacking and safety-eval-sensitivity studies** that need to know exactly what the model was trained on.
- A transparent **32B-class reasoning model** with open chain-of-thought for CoT-monitoring work ([`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)).

**When *not* to use it:**
- You need frontier or agentic capability — Olmo 3 trails the current open frontier by a wide margin.
- You need SAEs for the Think or Instruct checkpoints (only base-model SAEs exist).
- You want out-of-the-box tool calling (see the first pitfall).

**Pitfalls:**
- **Olmo 3 Think's chat template ignores the standard `tools` argument**, so serving it with vLLM exposes no functions to the model (Cairns et al.). They edited the template to render tools as the Instruct checkpoints do and made vLLM's Olmo 3 tool-call parser more tolerant of malformed calls. Symptom: the model never sees your tool definitions, so it answers without calling any tool.
- **Think vs Instruct vs 3.1.** `Olmo-3-32B-Think` and `Olmo-3.1-32B-Think` differ in RL training length and measurably in behavior; pin the exact repo and revision (a Hugging Face branch name for intermediate checkpoints).
- **Do not load a base-model SAE or lens onto a post-trained checkpoint without checking.** Reconstruction quality on SFT/DPO/RLVR activations is not guaranteed.

---

## gpt-oss (20B / 120B) — open chain-of-thought from OpenAI

Aliases: **gpt-oss**, `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `openai/gpt-oss-safeguard-20b` / `-120b` (safety reasoning models that classify text against a policy you supply), OpenAI's open-weight models (2025-08-04). **Apache 2.0.** gpt-oss-120b: 117B parameters / 5.1B active Mixture-of-Experts (MoE), fits one 80 GB GPU; gpt-oss-20b: 21B / 3.6B active, fits in 16 GB (the MoE weights are post-trained in MXFP4, 4-bit microscaling floating point). Model card: arXiv:2508.10925.

**Why it's notable.** The model card advertises **full chain-of-thought access** (not intended to be shown to end users) with configurable reasoning effort (low / medium / high) — the cleanest openly downloadable reasoning trace from a frontier lab, which is why it is a natural substrate for chain-of-thought (CoT) faithfulness and monitorability work ([`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)). A pre-fitted Jacobian lens exists for gpt-oss-20b.

**When *not* to use it:** you need frontier-level agentic capability (it is more than a year old and well behind the 2026 open frontier), vision, or a standard chat template — see the pitfall.

**Pitfalls:** the models were trained on the **harmony response format** and "should only be used with the harmony format"; the Transformers chat template applies it, but raw `model.generate` on a hand-built prompt does not (symptom: degenerate or off-format output). Check the reasoning-effort setting you ran, because it changes CoT length.

---

## Other open-weights families to know (as of 2026-10-09)

| Family | Verified facts | Research notes |
|---|---|---|
| **GLM-5.3 / GLM-5.3-Flash** (Z.ai, `zai-org/GLM-5.3`, `zai-org/GLM-5.3-Flash`, 2026-08-25) | GLM-5.3: ~753B parameters, custom `glm-5.3` license; GLM-5.3-Flash: 320B total / 18B active (Mixture-of-Experts), **MIT**, first natively multimodal GLM, hybrid sparse + linear attention, mHC (Manifold-Constrained Hyper-Connections), 1M context | Top-three on the Artificial Analysis open-weights page; Flash is the cheaper route to near-frontier capability. No SAEs found. |
| **MiMo-V2.6** (Xiaomi, HF org `XiaomiMiMo`; Pro / Flash `-RL` and `-MOPD` checkpoints, Sep 2026) | Listed first (46) on the Artificial Analysis open-weights page, 2026-10-09; the four `-RL` / `-MOPD` repos checked are MIT on HF | Newest entrant at the top; least studied by safety researchers. |
| **Muse Glimmer 30B** (Meta Superintelligence Lab, `meta-models/Muse-Glimmer-30B`, 2026-08-09) | **Apache 2.0**, dense ~29.6B parameters including a ~1.8B-parameter vision encoder, distilled from Muse Spark, 128K+ context, ~4-bit quantization targets 24 GB of VRAM; knowledge cutoff 2026-01-04 | Meta's newest open-weights release (after Llama 4). No SAEs found. |

---

## Llama (Llama 3.x / Llama 4) — the baseline of record

Aliases: **Llama**, **LLaMA**, `meta-llama/Llama-3.1-*`, `meta-llama/Llama-3.3-70B-Instruct`, `meta-llama/Llama-4-*` on Hugging Face, Meta AI's open model family. Llama 3.1 (8B/70B/405B), **Llama 3.3 70B** (still the most-deployed open 70B), **Llama 4** (Scout / Maverick — MoE, multimodal, very long context; Behemoth announced but not released open). Llama Community License (permissive with conditions — read it; not OSI-approved).

**Why it's notable.** Llama is **well behind the current frontier** (DeepSeek/Kimi/Qwen/GLM have passed it on capability; the `meta-llama` Hugging Face org has published no new model since April 2025, and Meta's newer open release is Muse Glimmer 30B), **but it has been around long enough that an enormous body of fine-tuning and interpretability experiments was built on it.** That history is the value: when you need a **matched baseline** to reproduce or extend a published result — Emergent Misalignment, persona vectors, steering, probing, control evals — there's a good chance the original used a Llama (often Llama-3.1-8B or 70B). Using the *same* base model removes "different model" as a confound. Llama is the **lingua franca baseline** of the safety-research literature.

**Best for:**
- **Reproducing / extending prior work** that used Llama — apples-to-apples ([`model-organisms.md`](../alignment-science/model-organisms.md), [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md)).
- A **well-trodden fine-tuning target** (Llama-3.1-8B is the most-documented small fine-tune in existence; Unsloth/Llama-Factory/TRL all assume it works).
- A stable **default cross-model arm** in behavioral evals (GPT, Claude, Llama, Qwen, Gemma is the canonical line-up).

**When *not* to use it:**
- You want maximum capability — it trails the 2026 frontier; use Kimi K3 / GLM-5.3 / DeepSeek-V4.x / top Qwen.
- You want pretrained SAEs — Gemma Scope is on Gemma and Qwen-Scope on Qwen, not Llama (some third-party Llama SAEs exist via SAELens/Neuronpedia but coverage is thinner — check [`saes.md`](../interpretability/saes.md)); pre-fitted Jacobian lenses do exist for Llama 3.1-8B and 3.3-70B.

**Pitfalls:**
- **Anomalous BOS/first-token activation** is well-known on Llama — skip position 0 or handle explicitly when probing/steering.
- **Version sprawl as a baseline trap.** "Llama" in a paper could be 2, 3, 3.1, 3.2, 3.3, or 4 — and 8B vs 70B vs 405B behave very differently. To truly match a baseline, pin the *exact* checkpoint the prior work used, not just "a Llama."
- **License conditions.** The Llama Community License has acceptable-use and naming/attribution conditions and isn't a standard OSI open-source license — check before redistributing derivatives.

---

## Quick cross-cutting guidance

- **"Open weights" ≠ "open source."** You get downloadable weights to self-host and fine-tune, but licenses differ: DeepSeek-V4.x, GLM-5.3-Flash and Kimi K2.6 (modified MIT) are permissive (MIT-style); Qwen3.5 / 3.6 / 3.8-27B, Gemma 4, Olmo 3, gpt-oss and Muse Glimmer are Apache 2.0; Kimi K3, Qwen3.8-2.4T / Flash-Next, GLM-5.3 and Gemma 2/3 use custom licenses with conditions; Llama uses the Llama Community License. Read the license before redistributing a fine-tuned derivative.
- **MoE total vs active params.** A "1.6T" or "2.8T" MoE only activates a slice per token, so serving VRAM tracks *total* params but compute tracks *active* params. Budget VRAM by total size; budget latency/throughput by active size. Dense bf16 weights cost about 2 bytes per parameter (9B ≈ 19 GB, 27–32B ≈ 56–64 GB) before KV cache and activations.
- **Match the checkpoint exactly** (version, size, base-vs-instruct, preview-vs-official, quant) across data prep, fine-tuning, SAE / lens loading, and eval — most silent "my results are weird" bugs trace to a mismatch here.
- **Just call them as a black box:** **OpenRouter** (one key, all the slugs in the table above; pin the provider) — the dominant access path for the large models. **Where to self-host / rent GPUs:** [`compute.md`](compute.md). **How to fine-tune them:** [`rl-training.md`](../oversight-and-control/rl-training.md), [`model-organisms.md`](../alignment-science/model-organisms.md). **Get activations from a big one you can't host:** NDIF / vLLM-Lens in [`serving-and-activations.md`](../interpretability/serving-and-activations.md).

## Common questions

### What is the most capable open-weights model right now?
There is no stable single answer. On the Artificial Analysis open-weights page fetched 2026-10-09 (Intelligence Index v4.3.2, maximum reasoning setting): **MiMo-V2.6-Pro 46, GLM-5.3 45, Kimi K3 44**, GLM-5.3-Flash 42, **DeepSeek-V4.1-Flash 39**, **Qwen3.8-27B 34** — differences of a point or two are noise, and the index version and reasoning setting move the absolute numbers, so use the ordering and the gaps, not the numbers. By raw size Kimi K3 (2.8T total / 104B active) is the largest open model. For long context, DeepSeek-V4/V4.1, Qwen3.8, Kimi K3 and GLM-5.3 all list a 1M-token window.

### Which open model is most like Claude (well-aligned / has character)?
The **Kimi** line (Moonshot AI) has been described as the closest open analogue to a Claude-style assistant — but commentators report that Kimi K3 sometimes claims to be Claude and may be partly distilled from Claude outputs (unconfirmed by Moonshot), so it is a poor *independent* data point. See the Kimi section.

### Which open model has pretrained SAEs (Sparse Autoencoders)?
**Gemma 2** (Gemma Scope: 400+ JumpReLU SAEs, 30M+ features) and **Gemma 3** (Gemma Scope 2: SAEs, transcoders, cross-layer transcoders) have the most complete official suites; **Qwen3 / Qwen3.5** have the official **Qwen-Scope** suite (TopK SAEs on every layer of e.g. Qwen3.5-9B-Base, arXiv:2605.11887); **Gemma 4**, **Olmo 3** and **Qwen3.5-0.8B/4B** have community SAEs on a few layers (`decoderesearch/*`, `bcywinski/Olmo-3-32B-Base-SAE`). None found for DeepSeek, Kimi, GLM, Qwen3.6/3.8 or Llama. See the artifacts table above and [`saes.md`](../interpretability/saes.md).

### Which open models have pre-fitted lenses (Jacobian lens / J++ Lens)?
`neuronpedia/jacobian-lens` on Hugging Face holds pre-fitted lenses for roughly 40 models, including Gemma 2/3/4, Qwen3/3.5/3.6, Olmo 3, DeepSeek-V4-Flash (April preview), gpt-oss-20b and Llama 3.1/3.3; the J++ Lens paper's own set is Qwen3.6-27B, Qwen3.5-9B, Gemma 4 31B, Olmo-3-1125-32B, Qwen3.5-122B-A10B and DeepSeek-V4-Flash.

### What's the best small open model to fine-tune?
**Qwen3.5** (0.8B–9B, Apache 2.0, open base models, strong small-model capability, largest tuning ecosystem) for capability-per-param, and it now has official Qwen-Scope SAEs; **Gemma 4 E2B/E4B/12B** (Apache 2.0) for a modern Google model, or **Gemma 3 1B/4B** if you need full-depth Gemma Scope 2 coverage; **Olmo 3 7B** if you need every training stage public; **Llama-3.1-8B** if you specifically need a matched baseline to existing literature.

### Which open model should I use to study what a training stage does (SFT vs DPO vs RLVR)?
**Olmo 3 / 3.1** (7B or 32B): SFT, DPO and RLVR checkpoints and hundreds of intermediate pretraining checkpoints are public. Two worked examples: Bharadwaj et al. on eval-awareness across Olmo 3 training and Cairns et al. on safety evals across the released stages.

### Why does a small Gemma model have so many parameters in its embedding layer?
Gemma uses a **very large (~256k–262k token) multilingual vocabulary**, so the token embedding / unembedding matrices are a large fraction of total parameters in the small models (Gemma 4 E2B: 2.3B effective vs 5.1B with embeddings). (Separately, Gemma is **distilled from larger Gemini teacher models**, which explains its strong capability-per-param — a different fact from the big embedding table.)

### Does my attention-head / attention-pattern analysis code work on Qwen3.5 or Qwen3.6?
Only for the quarter of layers that use ordinary attention. `Qwen/Qwen3.5-9B` has 32 layers: 24 `linear_attention` (Gated DeltaNet, no attention matrix) and 8 `full_attention`. Expect `AttributeError` or empty patterns on the linear layers, and update `transformers` / vLLM first. Kimi K3 (69 of 93 layers linear) and GLM-5.3-Flash are similar.

### Why does `DeepSeek-V4-Flash` give `CUDA out of memory` on my 80 GB GPU?
The released checkpoint is about 160 GB (FP4 experts plus FP8 weights) — an earlier version of this page wrongly said a quantized V4-Flash fits one 80 GB card. Use at least two 80 GB GPUs, or call it through OpenRouter. Also check which checkpoint you mean: preview (`deepseek-ai/DeepSeek-V4-Flash`), official (`-0731`) or `DeepSeek-V4.1-Flash`.

### How do I actually call DeepSeek / Kimi / a big open model without renting a GPU?
Use **OpenRouter** (`openrouter.ai`) — one OpenAI-compatible endpoint and one API key (`OPENROUTER_API_KEY`, in `~/projects/.env`) fronts them all: `moonshotai/kimi-k3`, `z-ai/glm-5.3`, `deepseek/deepseek-v4.1-flash`, `deepseek/deepseek-v4-pro-0813`, `qwen/qwen3.8-27b`, `google/gemma-4-31b-it` (with a `:free` tier), `meta-llama/llama-4-maverick`, etc. Pay-per-token, no GPU rental, works with `safety-tooling`, Inspect AI, LiteLLM, and the OpenAI SDK (`base_url="https://openrouter.ai/api/v1"`). **Pin the provider** for anything you will report. Self-host only when you need raw weights (fine-tuning, activations, SAEs). See [`safety-toolkits.md`](safety-toolkits.md) and [`compute.md`](compute.md).

### Can Kimi take images?
Yes — Kimi K2.6 (text + image) and Kimi K3 (text, image, video) are vision-enabled, and **image input is exposed on OpenRouter** (`moonshotai/kimi-k2.6`, `moonshotai/kimi-k3`). Vision is a relative weakness vs. their strong text/agentic capability, but you can pass images.

### Which model should I use as a baseline to match a published result?
Whatever **exact checkpoint the prior paper used** — usually Llama-3.1-8B or Llama-3.3-70B for work before 2026, and increasingly Qwen3.5-9B, Qwen3.6-27B, Gemma 4 31B, Olmo 3 32B or DeepSeek-V4-Flash (preview) for 2026 lens and interpretability papers. Pin the *exact* checkpoint; "a Llama" or "a Qwen3" spans many incompatible versions and sizes.

---

Last verified: 2026-10. (Additions 2026-10: Qwen-Scope arXiv:2605.11887; mHC arXiv:2512.24880; DeepSeek-V4 tech report arXiv:2606.19348; Gemma 4 report arXiv:2607.02770; gpt-oss model card arXiv:2508.10925; DeepSeek-V4-Flash-0731 / V4-Pro-0813 / V4.1-Flash, Kimi K3, GLM-5.3, Qwen3.8, Gemma 4, Olmo 3 and Muse Glimmer repo ids, sizes, licenses and dates checked on the Hugging Face API and model cards on 2026-10-09; SAE / lens repos `decoderesearch/{gemma-4,olmo-3,qwen-3.5}-saes`, `bcywinski/Olmo-3-32B-Base-SAE`, `Qwen/SAE-Res-*`, `neuronpedia/jacobian-lens`, `koayon/jpp-lenses` listed from their file trees; OpenRouter slugs, modalities, contexts and prices queried live from `https://openrouter.ai/api/v1/models` on 2026-10-09; all verified via arXiv / GitHub / Hugging Face.) Artificial Analysis scores were re-read from the page's embedded raw data on 2026-10-09 (Intelligence Index v4.3.2). Not verified: the Kimi K3 "claims to be Claude" / distillation reports (second-hand, from the Zvi review), whether any SAEs exist for the model families listed as "none found" beyond a search of Hugging Face and the Neuronpedia model pages. Correction to the previous version: DeepSeek-V4-Flash does not fit a single 80 GB GPU. The open-weights frontier and OpenRouter pricing move monthly — re-verify "most capable" claims, exact HF repo slugs / licenses, and prices before relying on them.

Previous pass (2026-05-26): DeepSeek-V4-Pro/Flash and Kimi K2.6 released April 2026; OpenRouter slugs queried 2026-05-26.

Sources consulted: [DeepSeek-V4-Flash (HF)](https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash), [DeepSeek-V4.1-Flash (HF)](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash), [Kimi K3 (HF)](https://huggingface.co/moonshotai/Kimi-K3), [Zvi, On Kimi K3 (LessWrong)](https://www.lesswrong.com/posts/t7oZyAFej8FZrfbtY/on-kimi-k3-its-capabilities-and-related-discontents), [Artificial Analysis open-weights models](https://artificialanalysis.ai/models/open-source), [Gemma 4 (HF)](https://huggingface.co/google/gemma-4-31B-it), [Gemma Scope (arXiv 2408.05147)](https://arxiv.org/abs/2408.05147), [Gemma Scope 2 (HF)](https://huggingface.co/google/gemma-scope-2), [Qwen-Scope (arXiv 2605.11887)](https://arxiv.org/abs/2605.11887), [Qwen3.8-27B (HF)](https://huggingface.co/Qwen/Qwen3.8-27B), [Olmo 3 32B Think (HF)](https://huggingface.co/allenai/Olmo-3-32B-Think), [Bharadwaj et al., Tracing eval-awareness through training of OLMo 3 (LessWrong)](https://www.lesswrong.com/posts/c2tqL9xPbttisAHtt/tracing-eval-awareness-emergence-through-training-of-olmo-3), [Cairns et al., SFT also drives safety eval results in Olmo 3 (LessWrong)](https://www.lesswrong.com/posts/d9rEnYcfCk4pn2PK8/sft-also-drives-safety-eval-results-in-olmo-3-1), [J++ Lens lenses (HF)](https://huggingface.co/koayon/jpp-lenses), [neuronpedia/jacobian-lens (HF)](https://huggingface.co/neuronpedia/jacobian-lens), [Gurnee et al., Global Workspace (transformer-circuits.pub)](https://transformer-circuits.pub/2026/workspace/index.html), [mHC (arXiv 2512.24880)](https://arxiv.org/abs/2512.24880), [GLM-5.3-Flash (HF)](https://huggingface.co/zai-org/GLM-5.3-Flash), [Muse Glimmer (HF)](https://huggingface.co/meta-models/Muse-Glimmer-30B), [gpt-oss-20b (HF)](https://huggingface.co/openai/gpt-oss-20b), [Khoriaty, OpenRouter provider pinning (LessWrong)](https://www.lesswrong.com/posts/KsyoSAyBRXtwzSugg/not-pinning-your-openrouter-provider-might-invalidate-your), [Llama 4 (Meta AI)](https://ai.meta.com/blog/llama-4-multimodal-intelligence/).
