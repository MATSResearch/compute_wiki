# Sparse Autoencoders (SAEs)

Tooling for training and using SAEs (Sparse Autoencoders) on language model activations. SAEs decompose activations into a large dictionary of sparse, ostensibly more-monosemantic features. Related architectures: **transcoders** (decompose MLP I/O), **crosscoders** (decompose across layers or models), **JumpReLU SAEs**, **TopK SAEs**, **Gated SAEs**.

## At a glance: which SAE library?

| If you want… | Use |
|---|---|
| Use pretrained SAEs on Gemma-2 / Llama-3 / GPT-2 in PyTorch | **SAELens** |
| Browse / search SAE features in a UI | **Neuronpedia** |
| Train your own SAE from scratch, modern TopK architecture, fast | **EleutherAI sparsify** |
| Train transcoders, crosscoders, custom dictionary architectures | **dictionary_learning** (Sam Marks lab) or **sparsify** |
| Auto-interpret SAE features (LLM-generated explanations) | **Delphi** (EleutherAI) or **Neuronpedia auto-interp** |
| Cross-layer transcoders | **EleutherAI clt-training** |
| Take SAE/transcoder features and do circuit analysis | **circuit-tracer** (`safety-research/circuit-tracer`) |
| Pretrained Llama-3.1-8B / Llama-3.3-70B SAEs | Goodfire SAEs on HuggingFace (load via SAELens) |

## SAELens

Aliases: `sae-lens` on PyPI, `decoderesearch/SAELens` on GitHub (formerly under `jbloomAus`), "Joseph Bloom's SAE library", "the SAE Lens library". Maintained by Joseph Bloom, Curt Tigges, Anthony Duong, David Chanin.

**What it is.** The default community library for working with pretrained SAEs and for training new ones. Provides:
- `SAE.from_pretrained(...)` to load hundreds of community-trained SAEs (Gemma Scope, Llama Scope, GPT-2 small, Pythia, etc.)
- `HookedSAETransformer` (the spiritual successor to TransformerLens's removed `HookedSAETransformer`) that splices SAEs into a model's residual stream
- A training loop with the standard architectures: vanilla L1, TopK, JumpReLU, Gated

**When to use it:**
- You want to use existing pretrained SAEs (this is the dominant use case for MATS fellows).
- You want to train an SAE on a model that's already supported by TransformerLens.
- You're integrating SAEs into a TransformerLens or HuggingFace pipeline.

**When *not* to use it:**
- You want the absolute fastest TopK training on big activations — **EleutherAI sparsify** is built for that.
- You want non-standard architectures (transcoders, crosscoders) — sparsify and dictionary_learning are more flexible.

**Pitfalls:**
- **Tokenizer / dataset mismatch.** Pretrained SAEs were trained on a specific tokenizer and a specific activation distribution (e.g. Pile for GPT-2, OpenWebText for Gemma Scope). Applying them to chat-template-formatted prompts gives degraded reconstruction. Sanity-check reconstruction loss on your prompts.
- **Hook point off-by-one.** Different SAEs are trained at different hook points: `blocks.{L}.hook_resid_pre` vs `hook_resid_post` vs `hook_mlp_out`. Read the SAE's metadata; loading at the wrong hook point gives you garbage features.
- **L0 vs L1 confusion.** L0 = average number of active features per token. L1 = the loss penalty that produced low L0. Modern SAEs (TopK, JumpReLU) target L0 directly; vanilla SAEs use an L1 penalty whose right value is dataset-dependent.
- **`SAE.from_pretrained("...")` not in registry** — older SAEs may need explicit `release` and `sae_id`. Check `sae_lens.toolkit.pretrained_saes_directory.get_pretrained_saes_directory()`.
- **Memory blowup with `HookedSAETransformer`.** Splices all SAEs at once by default; pass `use_error_term=False` and only the layers you need.
- **Inference speed.** Adding an SAE to the forward pass roughly halves throughput. For eval-time SAE feature extraction at scale, consider extracting raw activations once (vLLM-Lens) and applying SAEs offline.

**One-liner:**
```python
# pip install sae-lens
from sae_lens import SAE
sae, cfg, sparsity = SAE.from_pretrained(
    release="gemma-scope-2b-pt-res",
    sae_id="layer_20/width_16k/average_l0_71",
    device="cuda",
)
```

## EleutherAI sparsify

Aliases: `eai-sparsify` on PyPI (**new name** — the unprefixed `sparsify` on PyPI belongs to Neural Magic), `EleutherAI/sparsify` on GitHub, "EleutherAI's SAE library". Latest v1.3.0 (Nov 2025).

**What it is.** EleutherAI's SAE training library. Defaults to **TopK SAEs** (which directly enforce sparsity rather than penalizing L1) and supports transcoders via a `--transcode` flag. Experimental **GroupMax** and end-to-end training. Distributed training via `torchrun` / DDP.

**When to use it:**
- Training your own TopK SAE from scratch.
- Training a transcoder (the `--transcode` flag).
- You want fast, multi-GPU SAE training with sensible defaults (DDP, fp16/bf16).

**When *not* to use it:**
- You just want to load pretrained SAEs — use SAELens.
- You need JumpReLU / Gated / matryoshka architectures — those live in SAELens or `dictionary_learning`.
- You need crosscoders / cross-layer transcoders — see **clt-training** (a fork of sparsify).

**Pitfalls:**
- **PyPI rename.** Older docs say "install from source because PyPI sparsify is taken." That's no longer needed: `pip install eai-sparsify`. The unprefixed `sparsify` on PyPI is still Neural Magic's unrelated tool.
- **Default dataset is `EleutherAI/SmolLM2-135M-10B`.** Training on a different model? You probably want a different activation dataset; pass `--dataset`.
- **Distributed checkpoint format.** Saved SAEs use a directory layout, not a single file. Don't rename or copy without preserving the structure.

## dictionary_learning

Aliases: `dictionary_learning`, `saprmarks/dictionary_learning` on GitHub, "Sam Marks's library". Architectures: Standard, Gated, TopK, JumpReLU, **Matryoshka BatchTopK** (a real differentiator vs SAELens). Integrates with nnsight — this is how Marks-lab papers (e.g. "Sparse Feature Circuits" follow-ons) actually consume it.

**What it is.** A research-y SAE library from Sam Marks's lab. Lower-level than SAELens; closer to "here are the math primitives, build what you need." Used for many papers on transcoders and feature circuits.

**Status (2026-04):** Last commit August 2025 — research-grade and slow-cadence; expect to read source. Not abandoned, but not on the SAELens release pace.

**When to use it:** You're doing methodological research on SAE architectures (new loss functions, new sparsity mechanisms, Matryoshka-style hierarchical SAEs) and want minimal abstraction. You're working in the Marks-lab feature-circuits idiom (nnsight + sparse-feature attribution).

**When *not* to use it:** You want plug-and-play; SAELens is friendlier. You expect frequent updates.

## Neuronpedia

Aliases: `neuronpedia.org`, "the SAE feature browser".

**What it is.** A web UI and API for browsing, searching, and steering with SAE features. Hosts auto-interp explanations, activation visualizations, and per-feature dashboards for many open SAE releases (Gemma Scope, Llama Scope, GPT-2 small, etc.).

**When to use it:**
- Looking up "what does feature 3217 in Gemma-2-2B layer 20 do?"
- Searching for features by natural-language description.
- Sharing SAE results with collaborators (deep links to features).
- Pulling auto-interp explanations programmatically (Neuronpedia API).

**When *not* to use it:** Your SAE isn't on Neuronpedia (you trained it yourself). You can host private dashboards via SAEDashboard / SAEVis.

## Delphi (EleutherAI)

Aliases: `delphi`, `EleutherAI/delphi` on GitHub. Latest v0.1.3 (March 2026). **Install from source — not on PyPI.** The codebase behind Paulo et al. 2024, "Automatically Interpreting Millions of Features" (arXiv:2410.13928).

**What it is.** A library for **automated interpretability** of SAE features and transcoder latents — generates and scores natural-language explanations using an explainer LLM. Scoring methods include **detection**, **recall**, and **fuzzing** for evaluating explanation quality. Pairs with sparsify; works with SAELens.

**When to use it:** You trained your own SAE and want to auto-generate explanations for the features. You want detection / recall / fuzz scoring of explanation quality.

**vs alternatives:** Use **Delphi** if your SAE is local (you trained it). Use **Neuronpedia auto-interp** if your SAE is already hosted on Neuronpedia — easier path, no infra.

**Pitfall:** Auto-interp quality scales with the explainer model. Cheap explainer models (GPT-3.5, small open models) produce vague explanations. Budget for a strong model.

## clt-training (EleutherAI)

Aliases: `clt-training`, `EleutherAI/clt-training` on GitHub, "cross-layer transcoders". **Fork of `EleutherAI/sparsify`** — sparsify configs partly transfer. Adds DTensor tensor parallelism, bfloat16, KL+FVU training, pre-layernorm hookpoints.

**What it is.** Library for training **cross-layer transcoders** (CLTs) — a 2025 architecture that learns sparse features explaining MLP behavior across layers jointly.

**Status (2026-04):** Small/research-grade fork (~22 stars), last activity Nov 2025. Install via `uv venv --seed && uv sync` — no PyPI. Useful only for the specific CLT use case.

**When to use it:** Specifically researching CLTs / cross-layer transcoders. Otherwise stick with SAELens / sparsify.

## SAEDashboard (the active one) and sae_vis (deprecated)

Aliases:
- **`sae-dashboard`** on PyPI (v0.8.0, April 2026), `jbloomAus/SAEDashboard` on GitHub — the **maintained successor**, integrates with SAELens, has Docker.
- **`sae-vis`** on PyPI (v0.3.7, Feb 2026), `callummcdougall/sae_vis` on GitHub — **deprecated by the author**, who points users to SAELens / SAEDashboard. Kept here for keyword search.

**What it is.** Library for generating per-feature dashboards (activation histograms, top examples, logit-lens projections) like the ones on Neuronpedia, but local. Used to publish your own dashboards.

**Recommendation:** Use **`sae-dashboard`** (`pip install sae-dashboard`). Treat `sae-vis` as the historical original.

**When to use it:** You trained an SAE and want to inspect features without uploading to Neuronpedia.

**Alternative:** Run a self-hosted Neuronpedia instance if you want the full UI for a custom SAE (heavier setup, richer browsing).

## circuit-tracer

Aliases: `circuit-tracer`, `safety-research/circuit-tracer` on GitHub (maintained by Decode Research / `decoderesearch`), "the Anthropic Transformer Circuits team's transcoder circuit library". Latest v0.5.0 (April 2026).

**What it is.** A library for doing **circuit-level analysis on top of MLP transcoder features** — given trained transcoders, it discovers attribution graphs (which features at which layers drove a particular completion), renders them, and supports interventions. Implements methods from Anthropic's Transformer Circuits team (Hanna, Piotrowski, Lindsey, Ameisen). Supports Gemma-2, Llama-3.2, Qwen-3, GPT-OSS, Gemma-3 transcoders.

**When to use it:** You've trained or loaded transcoders (via sparsify `--transcode`, dictionary_learning, or pretrained Anthropic-published ones) and you want to do circuit discovery — "which features explain this output?" — rather than just feature inspection. The natural next step after most SAE/transcoder projects.

**When *not* to use it:** You only have residual-stream SAEs (not transcoders) and just want feature dashboards — SAEDashboard or Neuronpedia is the right tool.

**Pitfall:** Attribution graphs are computationally heavy on long prompts. Start with short prompts and small token windows; the renderer can choke on dense graphs.

## Goodfire pretrained SAEs

The Goodfire SDK was archived (Oct 2025) and the public Ember API was deprecated (Feb 2026), but their **open-source SAEs remain on HuggingFace** and are usable directly with SAELens:

- `Goodfire/Llama-3.3-70B-Instruct-SAE-l50`
- `Goodfire/Llama-3.1-8B-Instruct-SAE-l19`

These are some of the few publicly available SAEs trained on instruction-tuned (not base) Llama checkpoints, which matters for behavioral / refusal / alignment research.

## Common SAE pitfalls (cross-cutting)

- **Reconstruction loss is not the goal.** A trivially-perfect-reconstruction SAE can still be uninterpretable. Check L0, % alive features, and qualitative feature inspection.
- **Dead features.** A nontrivial fraction of features may never activate. SAELens and sparsify both have "ghost grad" / "auxiliary loss" mechanisms; use them or expect 30%+ dead features.
- **Width matters.** A 16k-feature SAE on Gemma-2-2B residual stream is "narrow" by 2026 standards; 65k–1M is now common. Width changes feature granularity.
- **"Feature splitting."** As you increase width, what was one feature splits into several finer-grained ones. Don't assume a feature with the same description in two SAE widths is "the same."
- **Don't compare absolute reconstruction loss across models / hook points.** It's only meaningful within a fixed setup.

## Cross-references

- Mechanistic interp libraries SAEs run on top of: [`01_mech_interp.md`](01_mech_interp.md).
- High-throughput activation extraction (for SAE feature collection at scale): [`07_serving_and_activations.md`](07_serving_and_activations.md).
- SAE-based steering: [`05_steering.md`](05_steering.md).

---

## Common questions

### How do I load a Gemma Scope SAE?

```python
from sae_lens import SAE
sae, cfg, sparsity = SAE.from_pretrained(
    release="gemma-scope-2b-pt-res",
    sae_id="layer_20/width_16k/average_l0_71",
    device="cuda",
)
```
Gemma Scope is the open Gemma-2 SAE release; `release` and `sae_id` come from the SAELens registry. List available SAEs via `sae_lens.toolkit.pretrained_saes_directory.get_pretrained_saes_directory()`.

### What's the difference between TopK and JumpReLU SAEs?

**TopK SAE**: enforces sparsity directly — only the top K activations per token are kept, the rest are zeroed. No L1 penalty needed; L0 = K by construction. **JumpReLU SAE**: uses a learned threshold per feature; activations below threshold go to zero. Both are 2024-era replacements for vanilla L1-penalty SAEs and produce cleaner features for the same sparsity level.

### My SAE has too many dead features — what do I do?

Dead features (never activate on any input) are common, often 30%+ in vanilla SAEs. Mitigations: use **TopK** or **JumpReLU** SAEs (much fewer dead features by construction); enable **ghost-grad / auxiliary loss** in SAELens or sparsify (resurrects dying features mid-training); use higher learning rate early in training.

### Should I use SAELens or EleutherAI sparsify for training?

**SAELens** if you want plug-and-play with the TransformerLens / HuggingFace ecosystem and many architectures (GatedSAE, JumpReLU, TopK). **EleutherAI sparsify** for fastest TopK SAE training, multi-GPU via DDP, and transcoder support (`--transcode` flag). Install with `pip install eai-sparsify` (the unprefixed `sparsify` on PyPI belongs to Neural Magic's unrelated tool). For Matryoshka BatchTopK or feature-circuits-style research, **dictionary_learning** (Sam Marks).

### Can I steer using SAE features?

Yes. Pattern: encode the residual stream into SAE features, modify the feature you want (clamp, scale, ablate), decode back, continue forward pass. SAELens has hooks for this. See [`05_steering.md`](05_steering.md) "SAE feature steering." Pitfalls: reconstruction error compounds; feature splitting at higher SAE widths may mean your "deception feature" is now five features.

### What is feature splitting?

When you train a wider SAE on the same model, what was one feature in a narrower SAE often becomes 2–10 finer-grained features. So "feature 3217 in the 16k SAE" is *not* the same thing as "feature 3217 in the 65k SAE." Don't compare feature IDs across widths; compare via cosine similarity or activation pattern.

### My SAE features look uninterpretable — what's wrong?

Most common causes: (1) **hook point mismatch** — different SAEs are trained at `hook_resid_pre` vs `hook_resid_post` vs `hook_mlp_out`; loading at the wrong hook gives garbage. (2) **Tokenizer / chat-template mismatch** — pretrained SAEs were trained on raw text or specific chat format; applying to other formats degrades reconstruction. (3) **Width too narrow** for the model — 16k features on a 2B model is small by 2026 standards.

---

Last verified: 2026-04-30. SAELens 6.x current. EleutherAI sparsify v1.3.0 on PyPI as `eai-sparsify` (Nov 2025). dictionary_learning last commit Aug 2025. Delphi v0.1.3 (March 2026, install from source). clt-training last activity Nov 2025. SAEDashboard v0.8.0 (Apr 2026); sae_vis deprecated by its author. circuit-tracer v0.5.0 (Apr 2026). Goodfire SDK archived; Goodfire SAEs remain on HuggingFace.
