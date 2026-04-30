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

Aliases: `sparsify` (EleutherAI's, **not** the Neural Magic one), `EleutherAI/sparsify` on GitHub, `pip install sparsify` (note: the PyPI `sparsify` name is taken by Neural Magic — install from source).

**What it is.** EleutherAI's SAE training library. Defaults to **TopK SAEs** (which directly enforce sparsity rather than penalizing L1) and supports transcoders via a `--transcode` flag. Distributed training via `torchrun`.

**When to use it:**
- Training your own SAE from scratch, especially TopK or Skip-TopK.
- Training a transcoder.
- You want fast, multi-GPU SAE training with sensible defaults (DDP, fp16).

**When *not* to use it:**
- You just want to load pretrained SAEs — use SAELens.
- You need crosscoder training — see **clt-training** instead.

**Pitfalls:**
- **PyPI name collision.** `pip install sparsify` installs Neural Magic's unrelated tool. Install from `git+https://github.com/EleutherAI/sparsify`.
- **Default dataset is `EleutherAI/SmolLM2-135M-10B`.** Training on a different model? You probably want a different activation dataset; pass `--dataset`.
- **Distributed checkpoint format.** Saved SAEs use a directory layout, not a single file. Don't rename or copy without preserving the structure.

## dictionary_learning

Aliases: `dictionary_learning`, `saprmarks/dictionary_learning` on GitHub, "Sam Marks's library".

**What it is.** A research-y SAE library from Sam Marks's lab. Lower-level than SAELens; closer to "here are the math primitives, build what you need." Used for many papers on transcoders and feature circuits.

**When to use it:** You're doing methodological research on SAE architectures (new loss functions, new sparsity mechanisms) and want minimal abstraction.

**When *not* to use it:** You want plug-and-play; SAELens is friendlier.

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

Aliases: `delphi`, `EleutherAI/delphi` on GitHub.

**What it is.** A library for **automated interpretability** of SAE features and transcoder latents — generates and scores natural-language explanations using an explainer LLM. Pairs with sparsify; works with SAELens.

**When to use it:** You trained your own SAE and want to auto-generate explanations for the features. Also: scoring methods (detection, fuzz testing) for evaluating explanation quality.

**Pitfall:** Auto-interp quality scales with the explainer model. Cheap explainer models (GPT-3.5, small open models) produce vague explanations. Budget for a strong model.

## clt-training (EleutherAI)

Aliases: `clt-training`, "cross-layer transcoders".

**What it is.** Library for training **cross-layer transcoders** (CLTs) — a 2025 architecture that learns sparse features explaining MLP behavior across layers jointly.

**When to use it:** Specifically researching CLTs / cross-layer transcoders. Otherwise stick with SAELens / sparsify.

## SAEDashboard / SAEVis

Aliases: `sae_vis`, `SAEDashboard`, "Callum McDougall's dashboards".

**What it is.** Library for generating per-feature dashboards (activation histograms, top examples, logit lens projections) like the ones on Neuronpedia, but local. Used to publish your own dashboards.

**When to use it:** You trained an SAE and want to inspect features without uploading to Neuronpedia.

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

Last verified: 2026-04. SAELens 6.x current. EleutherAI sparsify 1.1.3 (April 2026). Delphi and clt-training maintained alongside.
