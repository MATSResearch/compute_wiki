---
tags:
  - interpretability
---

# Sparse Autoencoders (SAEs)

Tooling for training and using SAEs (Sparse Autoencoders) on language model activations. SAEs decompose activations into a large dictionary of sparse, ostensibly more-monosemantic features. Related architectures: **transcoders** (decompose MLP I/O), **crosscoders** (decompose across layers or models), **JumpReLU SAEs**, **TopK SAEs**, **Gated SAEs**.

## At a glance: which SAE library?

| If you want… | Use |
|---|---|
| Use pretrained SAEs on Gemma-2 / Llama-3 / GPT-2 in PyTorch | **SAELens** |
| Pretrained SAEs / transcoders / crosscoders for **Gemma 3** (270M–27B, base and instruction-tuned) | **Gemma Scope 2** (`google/gemma-scope-2-*`, loads via SAELens) |
| Browse / search SAE features in a UI | **Neuronpedia** |
| Train your own SAE from scratch, modern TopK architecture, fast | **EleutherAI sparsify** |
| Train transcoders, crosscoders, custom dictionary architectures | **dictionary_learning** (Sam Marks lab) or **sparsify** |
| Auto-interpret SAE features (LLM-generated explanations) | **Delphi** (EleutherAI) or **Neuronpedia auto-interp** |
| Cross-layer transcoders | **EleutherAI clt-training** or **CLT-Forge** (`LLM-Interp/CLT-Forge`) |
| Decompose a model's *weights* (not activations) into sparse components | **Parameter decomposition** (SPD / VPD, `goodfire-ai/param-decomp`) — research-grade, small models only |
| Take SAE/transcoder features and do circuit analysis | **circuit-tracer** (`decoderesearch/circuit-tracer`; the old `safety-research/circuit-tracer` URL redirects) |
| Pretrained Llama-3.1-8B / Llama-3.3-70B SAEs | Goodfire SAEs on HuggingFace (load via SAELens) |
| Benchmark an SAE on downstream tasks, not just L0/reconstruction | **SAEBench** (`sae-bench`) |

## Should I use SAEs at all? (the skeptic's reading list)

Before committing a MATS project to Sparse Autoencoders (SAEs), read the 2025–2026 negative-results literature. SAEs are popular but contested, and several careful studies find they often fail to beat simple baselines. This matters for project scoping: if your goal is to *act on a concept you can already name* (e.g. "find and ablate the deception direction"), a plain linear probe may match or beat an SAE at a fraction of the cost (see [`probes.md`](probes.md)).

- **Kantamneni et al. 2025**, "Are Sparse Autoencoders Useful? A Case Study in Sparse Probing" (arXiv:2502.16681; ICML 2025; Subhash Kantamneni, Josh Engels, Senthooran Rajamanoharan, Max Tegmark, Neel Nanda). Tests SAEs on activation probing across data scarcity, class imbalance, label noise, and covariate shift. Finding: SAE latents do **not** reliably beat standard probing baselines on raw activations. If probing is your goal, don't assume SAEs help.
- **Leask et al. 2025**, "Sparse Autoencoders Do Not Find Canonical Units of Analysis" (arXiv:2502.04878; ICLR 2025; Patrick Leask, Bart Bussmann, Joseph Bloom, Curt Tigges, Lee Sharkey, Neel Nanda). Uses **SAE stitching** to show SAE dictionaries are *incomplete* and **meta-SAEs** to show latents are *not atomic* (a latent decomposes into finer latents). This is the theoretical backbone of the "feature splitting" pitfall below — there is no single "true" feature set to recover.
- **Korznikov et al. 2026**, "Sanity Checks for Sparse Autoencoders: Do SAEs Beat Random Baselines?" (arXiv:2602.14111). Sharpest negative result: a **random baseline** matched fully-trained SAEs across interpretability (0.87 vs 0.90), sparse probing (0.69 vs 0.72), and causal editing (0.73 vs 0.72). Always include a random/untrained-dictionary baseline in your SAE evals.
- **Peng et al. 2025**, "Use Sparse Autoencoders to Discover Unknown Concepts, Not to Act on Known Concepts" (arXiv:2506.23845; Kenny Peng, Rajiv Movva, Jon Kleinberg, Emma Pierson, Nikhil Garg). The reconciling framing, and a useful project-scoping heuristic: SAEs are a good tool for **discovering unknown concepts** (open-ended exploration, auditing, surfacing structure you didn't know to look for) but a poor tool for **acting on known concepts** (where a targeted probe or steering vector is better). Pick the tool to match which of those you're doing.

**Bottom line:** SAEs remain valuable for open-ended discovery and circuit analysis, but for "I know the concept, I want to detect/steer it" tasks, baseline-check against probes first.

## SAELens

Aliases: `sae-lens` on PyPI, `decoderesearch/SAELens` on GitHub (formerly under `jbloomAus`), "Joseph Bloom's SAE library", "the SAE Lens library". Maintained by Joseph Bloom, Curt Tigges, Anthony Duong, David Chanin. Latest v6.54.0 (2026-10-04); requires Python `>=3.10,<4.0` and `transformer-lens>=2.16.1,<4.0.0`.

**What it is.** The default community library for working with pretrained SAEs and for training new ones. Provides:
- `SAE.from_pretrained(...)` to load hundreds of community-trained SAEs (Gemma Scope — Google DeepMind, Lieberum et al., arXiv:2408.05147; Llama Scope — OpenMOSS, arXiv:2410.20526; GPT-2 small, Pythia, etc.)
- `HookedSAETransformer` — the same class that used to live in TransformerLens (removed there in TransformerLens 2.0 and moved into SAELens); it splices SAEs into a model's residual stream
- A training loop with the standard architectures: vanilla L1, TopK, JumpReLU, Gated; recent additions (release notes) include an **AbsTopK** bidirectional SAE (6.53.0, 2026-10-02), a covariance-whitening normalization option (6.52.0), the quadratic sparsity loss from Gemma Scope 2 for JumpReLU SAEs (6.51.0), `fold_W_dec_norm=True` to fold decoder norms at load time (6.54.0), and final L0 / dead-feature counts recorded in SAE metadata (6.47.0)
- `SAETransformerBridge` (beta; needs TransformerLens 3.x) — the `TransformerBridge` counterpart of `HookedSAETransformer`, for models the old hand-ported TransformerLens list did not cover (its docstring cites Gemma 3)

**When to use it:**
- You want to use existing pretrained SAEs (this is the dominant use case for MATS fellows).
- You want to train an SAE on a model that's already supported by TransformerLens.
- You're integrating SAEs into a TransformerLens or HuggingFace pipeline.

**When *not* to use it:**
- You want the absolute fastest TopK training on big activations — **EleutherAI sparsify** is built for that.
- You want non-standard architectures (transcoders, crosscoders) — sparsify and dictionary_learning are more flexible.

**Pitfalls:**
- **`ImportError: cannot import name 'HookedTransformer' from 'transformer_lens'` on `import sae_lens`** (SAELens issue #738, 2026-09-22) — TransformerLens 4.0.0 (2026-09-21) removed `HookedTransformer`, and SAELens releases before 6.51.2 declared `transformer-lens>=2.16.1` with no upper bound. SAELens 6.51.2 (2026-09-24) pins `transformer-lens<4.0.0`; issue #739 tracks real TL 4 support. Fix: upgrade `sae-lens` to ≥6.51.2, or `pip install "transformer-lens<4"`. For SAE work, stay on TransformerLens 3.x until that issue closes.
- **Tokenizer / dataset mismatch.** Pretrained SAEs were trained on a specific tokenizer and a specific activation distribution (e.g. Pile for GPT-2, OpenWebText for Gemma Scope). Applying them to chat-template-formatted prompts gives degraded reconstruction. Sanity-check reconstruction loss on your prompts.
- **Hook point off-by-one.** Different SAEs are trained at different hook points: `blocks.{L}.hook_resid_pre` vs `hook_resid_post` vs `hook_mlp_out`. Read the SAE's metadata; loading at the wrong hook point gives you garbage features.
- **L0 vs L1 confusion.** L0 = average number of active features per token. L1 = the loss penalty that produced low L0. Modern SAEs (TopK, JumpReLU) target L0 directly; vanilla SAEs use an L1 penalty whose right value is dataset-dependent.
- **`SAE.from_pretrained("...")` not in registry** — older SAEs may need explicit `release` and `sae_id`. Check `sae_lens.loading.pretrained_saes_directory.get_pretrained_saes_directory()`.
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

Aliases: `eai-sparsify` on PyPI (**new name** — the unprefixed `sparsify` on PyPI belongs to Neural Magic), `EleutherAI/sparsify` on GitHub, "EleutherAI's SAE library". Latest PyPI v1.3.3 (2026-07-16).

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
- **Training bugs fixed in July 2026 — runs made with ≤1.3.1 may be affected** (the `micro_acc_steps` bug only if you set it, fixed in 1.3.2; the AuxK bug in TopK runs with an auxiliary loss, fixed in 1.3.3, so 1.3.2 still has it). v1.3.2 (2026-07-16) fixed `micro_acc_steps`, which had been a no-op since end-to-end training support was added: setting `micro_acc_steps=N` saved no memory *and* silently divided the loss by an extra factor of N, scaling gradients down (it now chunks activations for the `fvu` loss only; combining it with `ce`/`kl` losses raises). v1.3.3 (2026-07-16) fixed the TopK **AuxK loss double-counting `b_dec`**, which pulled dead latents toward `(e - b_dec)` and put an unintended gradient on `b_dec`. Symptom: unusual dead-latent counts or slow dead-latent revival in TopK runs.
- **Default optimizer changed on `main`.** A 2026-07-20 commit changed the default optimizer from `signum` to `adam` (the recipe the released SAEs used; auto learning rate for Adam is `2e-4 / sqrt(num_latents / 2**14)`). PyPI 1.3.3 predates it, so set `optimizer` explicitly when comparing runs across versions or against a `main` checkout.
- **PyPI rename.** Older docs say "install from source because PyPI sparsify is taken." That's no longer needed: `pip install eai-sparsify`. The unprefixed `sparsify` on PyPI is still Neural Magic's unrelated tool.
- **Default dataset is `EleutherAI/SmolLM2-135M-10B`.** Training on a different model? You probably want a different activation dataset; pass `--dataset`.
- **Distributed checkpoint format.** Saved SAEs use a directory layout, not a single file. Don't rename or copy without preserving the structure.

## dictionary_learning

Aliases: `dictionary_learning`, `saprmarks/dictionary_learning` on GitHub, "Sam Marks's library". Architectures: Standard, Gated, TopK, **BatchTopK** (Bussmann et al. 2024, arXiv:2412.06410 — relaxes TopK's per-token sparsity to a per-batch budget), JumpReLU, **Matryoshka BatchTopK** (Bussmann et al. 2025, arXiv:2503.17547 — trains nested dictionaries of increasing size so small dictionaries reconstruct independently, mitigating feature absorption; a real differentiator vs SAELens). Integrates with nnsight — this is how Marks-lab papers (e.g. "Sparse Feature Circuits" follow-ons) actually consume it.

**What it is.** A research-y SAE library from Sam Marks's lab. Lower-level than SAELens; closer to "here are the math primitives, build what you need." Used for many papers on transcoders and feature circuits.

**Status (2026-04):** Last commit August 2025 — research-grade and slow-cadence; expect to read source. Not abandoned, but not on the SAELens release pace.

**When to use it:** You're doing methodological research on SAE architectures (new loss functions, new sparsity mechanisms, Matryoshka-style hierarchical SAEs) and want minimal abstraction. You're working in the Marks-lab feature-circuits idiom (nnsight + sparse-feature attribution).

**When *not* to use it:** You want plug-and-play; SAELens is friendlier. You expect frequent updates.

## Neuronpedia

Aliases: `neuronpedia.org`, "the SAE feature browser", `hijohnnylin/neuronpedia` on GitHub (open source, Johnny Lin / Decode Research; latest release v2.6.33 on 2026-10-09).

**What it is.** A web UI and API for browsing, searching, and steering with SAE features. Hosts auto-interp explanations, activation visualizations, and per-feature dashboards for many open SAE releases (Gemma Scope, Gemma Scope 2, Llama Scope, GPT-2 small, etc.). It is also the hosting layer for several newer interpretability tools: **attribution graphs** from circuit-tracer (create or upload graphs; the model must exist on Neuronpedia), the **Jacobian-lens family** at `neuronpedia.org/jlens` (J-Lens, J++ Lens and Oracle Lens readouts; lens weights in the `neuronpedia/jacobian-lens` HuggingFace repo — see [`mech-interp.md`](mech-interp.md#workspace-lenses-j-lens-r-lens-j-lens)), and **natural language autoencoders** at `neuronpedia.org/nla`.

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

**Alternative: CLT-Forge** (`LLM-Interp/CLT-Forge` on GitHub, MIT; Draye, Palit, Harrasse, Wu et al., *CLT-Forge: A Scalable Library for Cross-Layer Transcoders and Attribution Graphs*, arXiv:2603.21014, 2026-03-22; repo verified, last push 2026-07-30). An end-to-end CLT toolkit: distributed training with model sharding and compressed activation caching, an automated-interpretability pipeline for feature explanations, attribution-graph computation through circuit-tracer, and a visualization interface. Choose it over `clt-training` when you want the whole train → explain → attribute → visualize pipeline in one place; both are research-grade (CLT-Forge ~110 stars), so expect to read source.

## SAEDashboard (the active one) and sae_vis (no longer maintained)

Aliases:
- **`sae-dashboard`** on PyPI (v0.8.0, April 2026), `jbloomAus/SAEDashboard` on GitHub — the **maintained successor**, integrates with SAELens, has Docker.
- **`sae-vis`** on PyPI (v0.3.7, Feb 2026), `callummcdougall/sae_vis` on GitHub — **no longer actively maintained** (the author's README points users to SAELens and still accepts PRs, but isn't developing it further). Kept here for keyword search.

**What it is.** Library for generating per-feature dashboards (activation histograms, top examples, logit-lens projections) like the ones on Neuronpedia, but local. Used to publish your own dashboards.

**Recommendation:** Use **`sae-dashboard`** (`pip install sae-dashboard`). Treat `sae-vis` as the historical original.

**When to use it:** You trained an SAE and want to inspect features without uploading to Neuronpedia.

**Alternative:** Run a self-hosted Neuronpedia instance if you want the full UI for a custom SAE (heavier setup, richer browsing).

## circuit-tracer

Aliases: `circuit-tracer`, **`decoderesearch/circuit-tracer` on GitHub** (canonical; `safety-research/circuit-tracer` is the old slug and still resolves to it), "the Anthropic Transformer Circuits team's transcoder circuit library", "attribution graphs library". Authors Michael Hanna, Mateusz Piotrowski, Jack Lindsey, Emmanuel Ameisen; maintained by Decode Research (`decoderesearch`). Latest tag v0.5.2 (2026-07-18; auto-versioning via `hatch-vcs`), PyPI 0.5.0; the README says to install from a clone (`pip install .`).

**What it is.** A library for **circuit-level analysis on top of MLP transcoder features** — given trained transcoders, it discovers attribution graphs (which features at which layers drove a particular completion), renders them, and supports interventions on features. The transcoder-circuit approach was introduced by Dunefsky, Chlenski & Nanda 2024, "Transcoders Find Interpretable LLM Feature Circuits" (arXiv:2406.11944; NeurIPS 2024); circuit-tracer implements the attribution-graph methods from Anthropic's Transformer Circuits team (Ameisen et al. 2025, Lindsey et al. 2025). It runs three steps — attribution, graph-file creation (pruning), local visualization server (`circuit-tracer attribute --prompt ... --transcoder_set gemma --slug ... --graph_file_dir ... --server`) — and graphs can also be created on Neuronpedia with no install.

**Available transcoder sets (from the README, 2026-10):** Gemma-2 2B per-layer transcoders (PLTs) and cross-layer transcoders (CLTs; 426K and 2.5M features); Llama-3.2 1B PLTs and CLTs; Qwen-3 PLTs (0.6B, 1.7B, 4B, 8B, 14B); a GPT-OSS 20B CLT (`mntss/clt-131k`); **Gemma-3 PLTs from Gemma Scope 2 for 270M, 1B, 4B, 12B and 27B (pretrained and instruction-tuned; these require the `nnsight` backend)**; and **Llama-3.1-8B-Instruct TopK PLTs** (`facebook/crv-8b-instruct-transcoders`; license `cc-by-nc-4.0`, i.e. non-commercial). Locally trained transcoders load by passing their full root path. Added in v0.5.0 (April 2026): support for TopK transcoders and local CLT features in graphs. The `lazy_encoder` / `lazy_decoder` options need transcoders in `circuit-tracer`-compatible format; the README documents `save_transcoders_to_cache` for converting them.

**When to use it:** You've trained or loaded transcoders (via sparsify `--transcode`, dictionary_learning, CLT-Forge, or pretrained sets above) and you want to do circuit discovery — "which features explain this output?" — rather than just feature inspection. The natural next step after most SAE/transcoder projects.

**When *not* to use it:** You only have residual-stream SAEs (not transcoders) and just want feature dashboards — SAEDashboard or Neuronpedia is the right tool. You need attention-mechanism explanations — QK attributions and head loadings were requested (issue #53) and proposed (#114) but are not in a release.

**Automating the manual step.** Grouping features into *supernodes* is normally done by hand. Patel, Zhang & Hu, *LLMs Can Annotate Attribution Graphs* (arXiv:2608.02632, 2026-07-28; ICML 2026 Mechanistic Interpretability Workshop; code `maxh119Z/circuit-tracer-automation`, data `circuit-tracer-automation/pipeline_automation` on HuggingFace) feed feature descriptions (from top-activating text on Neuronpedia plus logit effects) to a language model that groups them into supernodes; on Gemma-2-2B with Gemma Scope transcoders the supernodes scored as interpretable as the 15 human-annotated reference graphs, and the pipeline recovered the intermediate-hop supernode on a two-hop "Capitals" task in 97 of 100 prompts. Limits stated by the authors: one model, one transcoder suite, one annotator LLM (GPT-5 mini), a naive grouping that ignores layer/position and attribution flow, and supernode labels too coarse for arithmetic circuits. Use it to triage many graphs, not to replace reading the graph for a claim you will publish.

**Pitfalls:**
- **Attribution graphs are computationally heavy on long prompts.** Start with short prompts and small token windows; the renderer can choke on dense graphs. A long-context OOM on an 80 GB H100 at ~6,000-token prompts is an open issue (#92); a long-context memory estimator is proposed (#109).
- **`ImportError: cannot import name 'HookedTransformer' from 'transformer_lens'` on `import circuit_tracer`** (issue #115, open as of 2026-10-09). The default backend's `ReplacementModel` subclasses TransformerLens' `HookedTransformer`, which TransformerLens 4.0 (2026-09-21) removed; `pyproject.toml` declares `transformer-lens>=2.16.0` with no upper bound. Per the issue thread, `main` currently also caps `transformers<=4.57.3`, so a fresh resolve picks TransformerLens 3.2.1 — but lifting that cap would pull TL 4. Pin `transformer-lens<4`, or use `ReplacementModel.from_pretrained(model_name, backend='nnsight')` (experimental: slower and more memory-hungry, per the README).
- **nnsight version coupling.** `main` requires `nnsight>=0.8.0rc1,<0.9` (the nnsight backend was ported to 0.8 on 2026-09-11). nnsight 0.8 is a PyPI *pre-release* with breaking changes (see [`mech-interp.md`](mech-interp.md)); installing from a clone with an older pinned nnsight, or mixing with `nnterp`, can raise dependency conflicts.
- **Error-node ids changed in v0.5.1** (2026-07-12): error nodes are now `"{layer}_-1_{pos}"` instead of `"0_{layer}_{pos}"`, which previously collided with layer-0 transcoder feature ids. Graph files or analysis code written against the old id format misparse error nodes.
- **Replacement-model faithfulness.** Splicing SAEs or transcoders into several layers at once yields a model whose outputs can be badly degraded, which is why graphs carry *error nodes* for the unexplained residual. A 2026 blog post (Evan Lloyd, LessWrong 2026-07-27, unreviewed; code in `evan-lloyd/mechinterp-experiments`) argues for *replacement-aware training* — a loss term penalising distortion of the next layer's features — on Gemma-2-2B residual SAEs instead of relying on error nodes. Treat error-node mass as the first number to report with any graph.

## Goodfire pretrained SAEs

The Goodfire SDK was archived (Oct 2025) and the public Ember API was deprecated (Feb 2026), but their **open-source SAEs remain on HuggingFace** and are usable directly with SAELens:

- `Goodfire/Llama-3.3-70B-Instruct-SAE-l50`
- `Goodfire/Llama-3.1-8B-Instruct-SAE-l19`

These are some of the few publicly available SAEs trained on instruction-tuned (not base) Llama checkpoints, which matters for behavioral / refusal / alignment research.

## Gemma Scope 2

Aliases: `google/gemma-scope-2` (landing page), `google/gemma-scope-2-{270m,1b,4b,12b,27b}-{pt,it}` on HuggingFace, "GemmaScope-2", Google DeepMind. Released December 2025 (HF landing page created 2025-12-15), CC-BY-4.0, loads through SAELens (`library_name: saelens`). Interactive browser: `neuronpedia.org/gemma-scope-2`. Technical report: PDF linked from the HuggingFace landing page and the Google DeepMind blog post.

**What it is.** The successor to Gemma Scope (which covers Gemma 2): an open suite of **Sparse Autoencoders (SAEs) and transcoders for the Gemma 3 family** at 270M, 1B, 4B, 12B and 27B parameters, both pretrained and instruction-tuned. Per the model card: SAEs at three sites (`resid_post`, `attn_out`, `mlp_out`) and transcoders (including skip-transcoders) at four depths (25%, 50%, 65%, 85%) in the "subset" folders, and at *every* layer in the `*_all` folders (a smaller width/L0 range); plus multi-layer models — weakly causal `crosscoder` (4 concatenated residual-stream layers; the landing page says these cover every base Gemma 3 model) and `clt` (cross-layer transcoders reconstructing the whole model's MLP outputs; **only the 270M and 1B repos have a `clt` folder** — the 4B repo does not). Widths 16k / 64k / 256k / 1M; target L0 "small" (10–20), "medium" (30–60), "large" (60–150); the card recommends 64k or 256k width and "medium" L0 for most tasks.

```python
# pip install sae-lens   (example from the HF model card for gemma-scope-2-4b-it)
from sae_lens import SAE
sae, cfg_dict, sparsity = SAE.from_pretrained(
    release="gemma-scope-2-4b-it-resid_post",
    sae_id="layer_12_width_16k_l0_small",
)
```

**When to use it:** You work on Gemma 3 (especially instruction-tuned checkpoints — scarce for SAEs elsewhere), want transcoders for circuit analysis with circuit-tracer (its Gemma-3 PLT sets come from here), or want SAEs at every layer of a 27B model.

**When *not* to use it:** Your model is Gemma 4, Qwen or Llama — as of 2026-10 the HuggingFace API shows no `google/gemma-scope-*` repo for Gemma 4 (community SAEs for Gemma 4 E4B exist, unvetted); you need Gemma-2 SAEs (that is the original Gemma Scope, `gemma-scope-2b-pt-res`). The card's own advice: unless you are doing full circuit-style analysis, use the layer-subset folders (`resid_post`, `transcoder`) rather than the `*_all` folders.

**Pitfall:** `google/gemma-scope-2` is a landing page with **no weights** — "There are no model weights in this repo"; load from a size-specific repo. SAELens release names embed the repo and folder (`gemma-scope-2-4b-it-resid_post`).

## Parameter decomposition (SPD, VPD) — weight-space alternative to SAEs

Aliases: "parameter decomposition", "APD" / "SPD" (Stochastic Parameter Decomposition, Bushnaq, Braun & Sharkey, arXiv:2506.20790, June 2025), "VPD" (adVersarial Parameter Decomposition; Goodfire, *Interpreting Language Model Parameters*, 2026-05-05, https://www.goodfire.com/research/interpreting-lm-parameters), `goodfire-ai/param-decomp` on GitHub (MIT; verified, last push 2026-10-05).

**What it is.** Instead of decomposing *activations* into a dictionary (SAEs, transcoders, crosscoders), parameter decomposition decomposes a model's **weight matrices** into many rank-one "subcomponents" that sum back to the original parameters, are sparse (any one input token needs few of them) and are trained to be *mechanistically faithful* (ablating the unneeded ones leaves the output unchanged). VPD's change from SPD is training against adversarially chosen ablations instead of stochastic ones. Goodfire reports less feature splitting than transcoders and that it applies to attention layers too. The repository includes a handbook (`docs/handbook.md`), a compact `nano_param_decomp/` implementation, and JAX training configs.

**When to use it:** You are doing methods research on faithful, weight-space decompositions, or want a decomposition that explains a computation in the *network's own parameters* rather than in a learned activation basis.

**When *not* to use it:** You want to interpret a production-scale model — the paper's decomposition is of a **4-layer, ~67M-parameter language model** (38,912 subcomponents, ~10,000 alive); the reference config in the repo needs a 32-GPU mesh (`fsdp: 32`), Blackwell GPUs need the `cuda13` extra and driver r580+, and no pretrained decompositions of 1B+ models were found (2026-10). For "find the feature for a concept I can name" use a probe or SAE.

**Known limits (reported):**
- Goodfire's own numbers: validation cross-entropy 2.72 with unmasked subcomponents vs 2.71 for the target; Pareto-dominates transcoders on tested sparsity measures *but the advantage disappears under matched training objectives*; adversarial robustness is limited (KL divergence 0.83 after 20 adversarial steps, 25.26 after 160).
- An independent audit (Tom Angsten, LessWrong 2026-09-30; code `angsten/vpd-audit`, verified) of the *released* decomposition found that aggregating the components needed by many inputs makes the model's output drift away from the original — at 64 tokens' worth of components (~4,500) with no search, KL ≈ 0.80 nats, comparable to the paper's own 20-step adversary (0.83 nats); deleting all components never labelled "needed" moved the model 1.28 nats. It audits the paper's decomposition, not the newer unpublished recipe in the repo. Do not assume "removing these components only affects this behaviour".

## SAEBench

Aliases: `sae-bench` on PyPI (v0.6.0), `adamkarvonen/SAEBench` on GitHub, "SAE Bench", "the SAE benchmark". Paper: arXiv **2503.09532**, "SAEBench: A Comprehensive Benchmark for Sparse Autoencoders in Language Model Interpretability".

**What it is.** A suite of **eight evaluations** for SAEs, so you can compare architectures and sparsity levels on something other than the reconstruction/sparsity Pareto curve. The evals: **Feature Absorption**, **AutoInterp**, **L0 / Loss Recovered**, **RAVEL**, **Spurious Correlation Removal (SCR)**, **Targeted Probe Perturbation (TPP)**, **Sparse Probing** (plus an SAE-Probes variant), and **Unlearning**.

```bash
pip install sae-bench
```

Run a single eval over a family of SAEs (verbatim from the repo README):

```bash
python -m sae_bench.evals.sparse_probing.main \
    --sae_regex_pattern "sae_bench_pythia70m_sweep_standard_ctx128_0712" \
    --sae_block_pattern "blocks.4.hook_resid_post__trainer_10" \
    --model_name pythia-70m-deduped
```

Results are written under `eval_results/<eval_name>`.

**When to use it:**
- You trained a new SAE variant and need to show it is better at *something a person cares about*, not just at reconstruction-per-L0. This is the standard the field now expects.
- You are choosing between pretrained SAEs for a downstream project and want a principled pick.
- You want a ready-made downstream task (SCR, TPP, unlearning) rather than inventing one.

**When *not* to use it:**
- You just want L0 and loss-recovered — SAELens computes those directly, and the harness is overhead.
- Your SAE is for a model/hook not covered by the regex-selected families; you'll be writing config plumbing before you get a number.

**Pitfalls:**
- **Regex selection is silent when it matches nothing.** A typo in `--sae_regex_pattern` gives you an empty run rather than an error. Check how many SAEs were selected before interpreting an eval that finished suspiciously fast.
- **Feature absorption and SCR need probing data** and will download datasets on first run; a sandboxed/offline box fails here first.
- **Don't compare across sparsity levels without saying so.** Most of these metrics move with L0; a comparison table where SAEs sit at different L0 is not a comparison of architectures.
- **Unlearning eval ≠ unlearning research.** It measures whether SAE feature clamping suppresses a capability, which is one narrow probe — see [`unlearning.md`](../alignment-science/unlearning.md) for what the unlearning literature demands.

## Common SAE pitfalls (cross-cutting)

- **Reconstruction loss is not the goal.** A trivially-perfect-reconstruction SAE can still be uninterpretable. Check L0, % alive features, and qualitative feature inspection.
- **Dead features.** A nontrivial fraction of features may never activate. SAELens and sparsify both have "ghost grad" / "auxiliary loss" mechanisms; use them or expect 30%+ dead features.
- **Width matters.** A 16k-feature SAE on Gemma-2-2B residual stream is "narrow" by 2026 standards; 65k–1M is now common. Width changes feature granularity.
- **"Feature splitting."** As you increase width, what was one feature splits into several finer-grained ones. Don't assume a feature with the same description in two SAE widths is "the same."
- **Don't compare absolute reconstruction loss across models / hook points.** It's only meaningful within a fixed setup.

## Cross-references

- Mechanistic interp libraries SAEs run on top of: [`mech-interp.md`](mech-interp.md).
- High-throughput activation extraction (for SAE feature collection at scale): [`serving-and-activations.md`](serving-and-activations.md).
- SAE-based steering: [`steering.md`](steering.md).
- Reading a model's unspoken intermediate variables without training an SAE (J-Lens / R-Lens / J++ Lens, natural language autoencoders): [`mech-interp.md`](mech-interp.md#workspace-lenses-j-lens-r-lens-j-lens).

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
Gemma Scope is the open Gemma-2 SAE release; `release` and `sae_id` come from the SAELens registry. List available SAEs via `sae_lens.loading.pretrained_saes_directory.get_pretrained_saes_directory()`.

### What's the difference between TopK and JumpReLU SAEs?

**TopK SAE**: enforces sparsity directly — only the top K activations per token are kept, the rest are zeroed. No L1 penalty needed; L0 = K by construction. **JumpReLU SAE**: uses a learned threshold per feature; activations below threshold go to zero. Both are 2024-era replacements for vanilla L1-penalty SAEs and produce cleaner features for the same sparsity level.

### My SAE has too many dead features — what do I do?

Dead features (never activate on any input) are common, often 30%+ in vanilla SAEs. Mitigations: use **TopK** or **JumpReLU** SAEs (much fewer dead features by construction); enable **ghost-grad / auxiliary loss** in SAELens or sparsify (resurrects dying features mid-training); use higher learning rate early in training.

### Should I use SAELens or EleutherAI sparsify for training?

**SAELens** if you want plug-and-play with the TransformerLens / HuggingFace ecosystem and many architectures (GatedSAE, JumpReLU, TopK). **EleutherAI sparsify** for fastest TopK SAE training, multi-GPU via DDP, and transcoder support (`--transcode` flag). Install with `pip install eai-sparsify` (the unprefixed `sparsify` on PyPI belongs to Neural Magic's unrelated tool). For Matryoshka BatchTopK or feature-circuits-style research, **dictionary_learning** (Sam Marks).

### Can I steer using SAE features?

Yes. Pattern: encode the residual stream into SAE features, modify the feature you want (clamp, scale, ablate), decode back, continue forward pass. SAELens has hooks for this. See [`steering.md`](steering.md) "SAE feature steering." Pitfalls: reconstruction error compounds; feature splitting at higher SAE widths may mean your "deception feature" is now five features.

### What is feature splitting?

When you train a wider SAE on the same model, what was one feature in a narrower SAE often becomes 2–10 finer-grained features. So "feature 3217 in the 16k SAE" is *not* the same thing as "feature 3217 in the 65k SAE." Don't compare feature IDs across widths; compare via cosine similarity or activation pattern.

### My SAE features look uninterpretable — what's wrong?

Most common causes: (1) **hook point mismatch** — different SAEs are trained at `hook_resid_pre` vs `hook_resid_post` vs `hook_mlp_out`; loading at the wrong hook gives garbage. (2) **Tokenizer / chat-template mismatch** — pretrained SAEs were trained on raw text or specific chat format; applying to other formats degrades reconstruction. (3) **Width too narrow** for the model — 16k features on a 2B model is small by 2026 standards.

### Are there pretrained SAEs for Gemma 3?

Yes — **Gemma Scope 2** (`google/gemma-scope-2-{270m,1b,4b,12b,27b}-{pt,it}`, December 2025): SAEs, transcoders, crosscoders and cross-layer transcoders, loadable through SAELens (e.g. `release="gemma-scope-2-4b-it-resid_post"`). For Gemma 2 use the original Gemma Scope (`gemma-scope-2b-pt-res` etc.). Neuronpedia hosts a browser at `neuronpedia.org/gemma-scope-2`.

### `import sae_lens` fails with `cannot import name 'HookedTransformer' from 'transformer_lens'` — why?

TransformerLens 4.0.0 (2026-09-21) removed `HookedTransformer`. Upgrade to `sae-lens>=6.51.2` (pins `transformer-lens<4.0.0`) or `pip install "transformer-lens<4"`. Real TL 4 support is tracked in SAELens issue #739.

### How is parameter decomposition different from an SAE or transcoder?

SAEs and transcoders learn a dictionary over *activations*; parameter decomposition (SPD, VPD; `goodfire-ai/param-decomp`) splits the *weight matrices* into sparse rank-one subcomponents that sum to the original parameters. It has so far been demonstrated on a 4-layer, ~67M-parameter language model and an independent audit found aggregated explanations drift from the original model's outputs — treat it as a research direction, not a drop-in replacement for SAELens.

---

Last verified: 2026-10. SAELens 6.x current (v6.54.0, 2026-10-04). EleutherAI sparsify v1.3.3 on PyPI as `eai-sparsify` (2026-07-16). dictionary_learning last commit Aug 2025. Delphi v0.1.3 (March 2026, install from source). clt-training last activity Nov 2025. SAEDashboard v0.8.0 (Apr 2026); sae_vis deprecated by its author. circuit-tracer v0.5.2 tag (2026-07-18; PyPI 0.5.0, canonical repo now `decoderesearch/circuit-tracer`). Goodfire SDK archived; Goodfire SAEs remain on HuggingFace. (Citation audit 2026-06: fixed the self-referential `HookedSAETransformer` wording, softened the sae_vis "deprecated" claim, and added Gemma Scope / Llama Scope arXiv IDs. Additions 2026-06: a "Should I use SAEs at all?" skeptic's reading list — Kantamneni 2502.16681, Leask 2502.04878, Korznikov 2602.14111, Peng 2506.23845 — and architecture citations for BatchTopK 2412.06410, Matryoshka 2503.17547, and transcoder circuits 2406.11944; all verified via arXiv.) (Additions 2026-08: SAEBench — `sae-bench` v0.6.0 on PyPI, arXiv 2503.09532, eval list and CLI verified from the repo README.) (Additions 2026-10: SAELens release notes v6.47–6.54 and the TransformerLens-4 `<4` pin (v6.51.2, issues #738/#739); sparsify v1.3.2/v1.3.3 bug-fix release notes and the 2026-07-20 default-optimizer commit; Gemma Scope 2 (HF model card `google/gemma-scope-2-4b-it`, landing page `google/gemma-scope-2`); circuit-tracer README, v0.5.1 release notes, `pyproject.toml` and issue #115 (TL-4 breakage); `LLMs Can Annotate Attribution Graphs` arXiv:2608.02632 (code `maxh119Z/circuit-tracer-automation`); CLT-Forge arXiv:2603.21014 (`LLM-Interp/CLT-Forge`); Stochastic Parameter Decomposition arXiv:2506.20790, VPD (Goodfire 2026-05-05, `goodfire-ai/param-decomp`) and the VPD audit (LessWrong KeBccWBGXnNXzZFBp, `angsten/vpd-audit`); Neuronpedia `v2.6.33`; corrected the stale `sae_lens.toolkit` import path to `sae_lens.loading.pretrained_saes_directory`; all verified via arXiv abs pages, `gh api` and the HuggingFace API.)
