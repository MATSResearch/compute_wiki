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
| Test an SAE architecture against known ground-truth features (fast, synthetic) | **SynthSAEBench** (`sae_lens.synthetic`, model `decoderesearch/synth-sae-bench-16k-v2`) |
| Decompose *attention* layers into sparse, interpretable heads | **Lorsa** (Low-Rank Sparse Attention; `OpenMOSS/Llamascopium`, PyPI `llamascopium`) |
| Train a model that is interpretable by construction (sparse weights), then prune out task circuits | **Weight-sparse transformers** (`openai/circuit_sparsity`) — tens of millions of nonzero parameters at most |
| A cheap first lens, before committing to training an SAE (no dictionary training) | **ICA Lens** (`icalens` on PyPI; independent component analysis) |
| SAEs and transcoders for **vision** models (CLIP, DINO) | **ViT-Prisma** (`Prisma-Multimodal/ViT-Prisma`) |
| Test whether an SAE captures a known concept *manifold* (colors, years) or shatters it into atoms | **sae-manifold** (`goodfire-ai/sae-manifold`); block-sparse alternative: **block-sparse-featurizer** |
| Score feature explanations with a released simulator model instead of an LLM judge | **Transluce simulator** (`Transluce/features_explain_llama3.1_8b_simulator`; see [`mech-interp.md`](mech-interp.md#automated-interpretability-and-interpretability-agents)) |
| Benchmark whether an *agent* can find the right SAE feature | **SAEScientist-Bench** (see [`mech-interp.md`](mech-interp.md#automated-interpretability-and-interpretability-agents)) |

> **Known silent bugs, as of 2026-10-14.** (1) SAELens before **6.54.2** loaded every Gemma Scope 2 `*_affine` transcoder with its skip connection transposed — see [Gemma Scope 2](#gemma-scope-2). (2) On Gemma 2/3/4 and OLMo 2/3, the raw MLP output is not what MLP SAEs read — see [Common SAE pitfalls](#common-sae-pitfalls-cross-cutting). (3) Delphi v0.1.3 loses token highlighting on transformers ≥5 — see [Delphi](#delphi-eleutherai). (4) circuit-tracer ≤0.5.2 dropped CLT skip weights on save — see [circuit-tracer](#circuit-tracer).

## Why SAEs? Superposition and feature geometry

Aliases: "superposition", "polysemanticity", "Toy Models of Superposition", "TMS", "linear representation hypothesis", "feature geometry", "strong superposition".

The case for Sparse Autoencoders (SAEs) rests on a theory of how models store features. **Elhage et al., *Toy Models of Superposition*** (Anthropic, arXiv:2209.10652, 2022; also transformer-circuits.pub/2022/toy_model) gives a toy model in which polysemantic neurons arise because the network stores more sparse features than it has dimensions, as nearly-orthogonal directions ("superposition"); it reports a phase change in whether features are stored this way, a connection to the geometry of uniform polytopes, and evidence of a link to adversarial examples. If real features are sparse linear directions that outnumber dimensions, an overcomplete dictionary trained with a sparsity penalty — an SAE — is the natural tool for recovering them. Every SAE result is therefore partly a test of that assumption; the skeptic's list below is the evidence that recovery is incomplete.

- **Superposition and scaling laws.** Liu, Liu & Gore, *Superposition Yields Robust Neural Scaling* (arXiv:2505.10465; NeurIPS 2025 Best Paper Runner-up) vary superposition in the toy model with weight decay: with weak superposition, loss follows a power law in model size only if feature frequencies are power-law distributed; under strong superposition "the loss generically scales inversely with model dimension". They report that open-source LLMs are in the strong-superposition regime and that Chinchilla scaling is consistent with this.
- **Not every structure is a bag of independent directions.** Computational-mechanics work finds activations organized as *belief-state geometry* (sometimes fractal) and as factored orthogonal subspaces — see [`slt-devinterp.md`](slt-devinterp.md). Attention has its own superposition problem, which Lorsa (below) targets.
- **Ground truth for testing.** SynthSAEBench (below) builds superposition, hierarchy and correlation into a synthetic model with known features, so you can check whether an architecture recovers them before spending on LLM runs.
- **Concept manifolds, and a tool to test for them.** Bhalla, Fel, Rager, Feucht, Haklay, Wurgaft, Boppana, Kowal et al., "Do Sparse Autoencoders Capture Concept Manifolds?" (arXiv:2604.28119, 2026-04-30; code `goodfire-ai/sae-manifold`, MIT) give a framework in which an SAE can capture a low-dimensional manifold *globally* (a compact group of atoms whose span contains it) or *locally* (features that each tile one region), and find that SAEs mix the two in a fragmented regime they call *dilution* — one reason manifold structure is rarely visible in single features. The repo ships two evaluations: **subspace capture** (does the SAE's feature set span the subspace of a known manifold — colors, temperature, age, geography, days, years, formality, sentence length — or shatter it?) and **unsupervised clustering** of features by decoder cosine, co-activation, correlation, mutual information or Ising couplings. It defaults to Llama-3.1-8B and a minimal `BatchTopKSAE`; another SAE needs only `encode`, `decode` and decoder access (README). Quickstart: `uv run data.py --manifold colors`, then `uv run subspace_capture.py plot --sae /path/to/sae.pt --k 64`. A sibling repo, `goodfire-ai/block-sparse-featurizer` (MIT, no releases), lifts the unit of sparsity from directions to **blocks** (small subspaces) with Vanilla, Grassmannian and Group-Lasso variants, e.g. `bsf.GrassmannianBSF(d=768, n_groups=256, group_size=3, l0=16)` then `bsf.train(model, x, epochs=60)`; its demo is on DINOv3 *vision* features. **When not to use them:** production SAE training (both are research code); language-model BSF claims (the shipped demo is vision-only).

**Open problem.** Whether LLM features really are the sparse linear directions the toy model assumes — or a mixture of linear directions, multi-dimensional manifolds and hierarchies that a flat dictionary splits arbitrarily (see "feature splitting" below) — is unsettled. A convincing result predicts, before looking, a measurable property of a pretrained LLM's activations or of its SAEs (e.g. how dictionary quality scales with width) from a superposition model, and confirms it.

## Should I use SAEs at all? (the skeptic's reading list)

Before committing a MATS project to Sparse Autoencoders (SAEs), read the 2025–2026 negative-results literature. SAEs are popular but contested, and several careful studies find they often fail to beat simple baselines. This matters for project scoping: if your goal is to *act on a concept you can already name* (e.g. "find and ablate the deception direction"), a plain linear probe may match or beat an SAE at a fraction of the cost (see [`probes.md`](probes.md)).

- **Kantamneni et al. 2025**, "Are Sparse Autoencoders Useful? A Case Study in Sparse Probing" (arXiv:2502.16681; ICML 2025; Subhash Kantamneni, Josh Engels, Senthooran Rajamanoharan, Max Tegmark, Neel Nanda). Tests SAEs on activation probing across data scarcity, class imbalance, label noise, and covariate shift. Finding: SAE latents do **not** reliably beat standard probing baselines on raw activations. If probing is your goal, don't assume SAEs help.
- **Leask et al. 2025**, "Sparse Autoencoders Do Not Find Canonical Units of Analysis" (arXiv:2502.04878; ICLR 2025; Patrick Leask, Bart Bussmann, Joseph Bloom, Curt Tigges, Lee Sharkey, Neel Nanda). Uses **SAE stitching** to show SAE dictionaries are *incomplete* and **meta-SAEs** to show latents are *not atomic* (a latent decomposes into finer latents). This is the theoretical backbone of the "feature splitting" pitfall below — there is no single "true" feature set to recover.
- **Korznikov et al. 2026**, "Sanity Checks for Sparse Autoencoders: Do SAEs Beat Random Baselines?" (arXiv:2602.14111). Sharpest negative result: a **random baseline** matched fully-trained SAEs across interpretability (0.87 vs 0.90), sparse probing (0.69 vs 0.72), and causal editing (0.73 vs 0.72). Always include a random/untrained-dictionary baseline in your SAE evals.
- **Peng et al. 2025**, "Use Sparse Autoencoders to Discover Unknown Concepts, Not to Act on Known Concepts" (arXiv:2506.23845; Kenny Peng, Rajiv Movva, Jon Kleinberg, Emma Pierson, Nikhil Garg). The reconciling framing, and a useful project-scoping heuristic: SAEs are a good tool for **discovering unknown concepts** (open-ended exploration, auditing, surfacing structure you didn't know to look for) but a poor tool for **acting on known concepts** (where a targeted probe or steering vector is better). Pick the tool to match which of those you're doing.

- **Wu, Arora, Geiger, Wang, Huang, Jurafsky, Manning & Potts 2025**, "AxBench: Steering LLMs? Even Simple Baselines Outperform Sparse Autoencoders" (arXiv:2501.17148; ICML 2025 spotlight; `stanfordnlp/axbench`). On Gemma-2-2B/9B, "for steering, we find that prompting outperforms all existing methods, followed by finetuning. For concept detection, representation-based methods such as difference-in-means, perform the best. On both evaluations, SAEs are not competitive." Details and the current leaderboard are in [`steering.md`](steering.md#axbench-benchmark-steering-against-prompting).
- **Chanin 2026**, "Are Sparse Autoencoder Benchmarks Reliable?" (arXiv:2605.18229). The benchmarks themselves are noisy: two SAEBench metrics fail an audit (see [SAEBench](#saebench) below).
- **A cheap non-SAE baseline: ICA Lens** (below). Independent component analysis recovers interpretable, token-selective directions without training a dictionary; worth running first and reporting next to any SAE result.

**Bottom line:** SAEs remain valuable for open-ended discovery and circuit analysis, but for "I know the concept, I want to detect/steer it" tasks, baseline-check against probes (detection) and prompting (steering) first.

## ICA Lens (independent component analysis as a first lens)

Aliases: ICA Lens, ICALens, `icalens` on PyPI, `liusida/ica-lens-paper` on GitHub, FastICA for LLMs, independent component analysis, "interpreting language models without training another dictionary". Paper: Sida Liu & Feijiang Han, "ICA Lens: Interpreting Language Models Without Training Another Dictionary", arXiv:2606.11722 (2026-06-10).

**What it is.** A GPU-parallel PyTorch FastICA pipeline with stability recipes for LLM activations (no SciPy/scikit-learn dependency), fitting diagnostics, an interactive token-level explorer (Jupyter/Colab, or `result.to_html(...)`), component profiles (top examples, logit-lens tokens, optional R-lens readouts), and steering or clamping of ICA components. The intuition from the abstract: many interpretable directions are selective on tokens, so they look less Gaussian than random directions, which is what ICA finds. Published lenses on Hugging Face (collection `sida/ica-lens`) include GPT-2 small (`sida/icalens-gpt2-small-pile10k`) and Qwen3.5-2B chat (`sida/icalens-qwen3.5-2b-ultrachat-1m`); the paper reports GPT-2 Small, Gemma 2 2B and Qwen 3.5 2B Base. Release v0.4.0 and PyPI `icalens` 0.4.0 (both 2026-09-29); MIT.

```python
# From the README (pip install icalens); the two README blocks joined
from icalens import ICALens

lens = ICALens.from_pretrained("sida/icalens-gpt2-small-pile10k")
result = lens.analyze("She deposited the check at the bank.", layer=6)
result.to_html("analysis.html")
```

Fitting your own: `icalens fit text --model openai-community/gpt2 --dataset NeelNanda/pile-10k --layers 6 --token-budget 1000 --max-iter 20 --output icalens-output/gpt2-demo` (or `icalens fit chat ...` for instruction-tuned models), then `icalens profile`. Steering: `lens.generate(messages, layer=5, steer=(188, -12.0), max_new_tokens=16)`; the README warns that "component labels, signs, and suitable targets must be established empirically for the exact Lens and layer".

**Reported results (abstract):** "On SAEBench, ICA is competitive with public SAEs in sparse probing and outperforms them in targeted probe perturbation under small-to-medium budgets." Read the TPP half with the SAEBench audit in mind — Targeted Probe Perturbation is one of the two metrics that audit says should not be used to rank SAEs.

**When to use it:** a first look at a layer before training or downloading an SAE; a baseline row in any SAE paper; quick steering experiments on a small model.

**When *not* to use it:** you need more directions than the activation dimension (standard ICA yields at most `d_model` components — whether `icalens` relaxes this was not checked); you need compatibility with circuit-tracer, Neuronpedia or SAELens tooling; as headline evidence on TPP.

## SAELens

Aliases: `sae-lens` on PyPI, `decoderesearch/SAELens` on GitHub (formerly under `jbloomAus`), "Joseph Bloom's SAE library", "the SAE Lens library". Maintained by Joseph Bloom, Curt Tigges, Anthony Duong, David Chanin. Latest v6.54.5 (2026-10-14, also on PyPI); requires Python `>=3.10,<4.0` and `transformer-lens>=2.16.1,<4.0.0`. **Upgrade to ≥6.54.2 if you use Gemma Scope 2 affine transcoders** (silent loading bug, below).

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
- **Gemma Scope 2 `*_affine` transcoders loaded wrong before 6.54.2 (no error).** Gemma Scope 2 stores `affine_skip_connection` as `(d_in, d_out)` applied as `x @ A`; SAELens's `SkipTranscoder` computes `x @ W_skip.T`, and the loader copied the matrix unchanged, so "the matrices are square, so nothing errored: every `*_affine` Gemma Scope 2 transcoder loaded fine and produced wrong output" (PR #761, fixing issue #760; released in v6.54.2, 2026-10-13). Measured in the PR (fraction of MLP-out variance explained, 16k width): 270m-pt layer 15 scored **−16.4** instead of 0.807, 1b-pt layer 7 **−3.45** instead of 0.959; per the PR, "the transposed skip connection did worse than leaving the skip connection out". Fix: `pip install -U "sae-lens>=6.54.2"`, and re-load from the original `google/gemma-scope-2-*` repo any affine transcoder you saved in SAELens format with an older version ("has the transposed matrix baked in"). Plain SAEs and non-affine transcoders were unaffected; circuit-tracer's own loader already transposes the matrix (`.T.contiguous()` in `single_layer_transcoder.py`), so only the SAELens path was wrong. Symptom: negative explained variance from an affine transcoder.
- **Hook point off-by-one.** Different SAEs are trained at different hook points: `blocks.{L}.hook_resid_pre` vs `hook_resid_post` vs `hook_mlp_out`. Read the SAE's metadata; loading at the wrong hook point gives you garbage features.
- **Sandwich-norm models (Gemma 2/3/4, OLMo 2/3): `hook_mlp_out` ≠ `mlp.hook_out`.** The block-level `hook_mlp_out` is the post-norm residual contribution; `mlp.hook_out` (and an HF hook on `model.model.layers[i].mlp`) is the raw MLP output. On gemma-2-2b, a Gemma Scope MLP SAE fed the raw output scored FVU 9.8 with L0 8 instead of FVU 0.26 with L0 81. Details in [`mech-interp.md`](mech-interp.md#the-sandwich-norm-hook-trap-gemma-234-olmo-23).
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

Aliases: `delphi`, `EleutherAI/delphi` on GitHub. Latest v0.1.3 (March 2026). **On PyPI as `eai-delphi` (0.1.3, the March 2026 release); fixes after it are on GitHub `main` only.** The codebase behind Paulo et al. 2024, "Automatically Interpreting Millions of Features" (arXiv:2410.13928).

**What it is.** A library for **automated interpretability** of SAE features and transcoder latents — generates and scores natural-language explanations using an explainer LLM. Scoring methods include **detection**, **recall**, and **fuzzing** for evaluating explanation quality. Pairs with sparsify; works with SAELens.

**When to use it:** You trained your own SAE and want to auto-generate explanations for the features. You want detection / recall / fuzz scoring of explanation quality.

**vs alternatives:** Use **Delphi** if your SAE is local (you trained it). Use **Neuronpedia auto-interp** if your SAE is already hosted on Neuronpedia — easier path, no infra.

**Pitfalls:**
- **Auto-interp quality scales with the explainer model.** Cheap explainer models (GPT-3.5, small open models) produce vague explanations. Budget for a strong model.
- **`pip install delphi` installs the wrong package.** The PyPI name `delphi` belongs to an unrelated ML4AI project ("A framework for assembling probabilistic models from text", last release 2018). EleutherAI's Delphi is `eai-delphi` on PyPI (0.1.3, 2026-03-12), or install from GitHub for the fixes below.
- **On transformers ≥5, token highlighting silently disappears in the v0.1.3 release.** `batch_decode` on a 1-D token tensor returns one joined string on transformers 5, so "token highlighting silently disappears from explainer and fuzz/detection prompts, the simulator's `ActivationRecord` gets a length-1 token list, and the intruder scorer raises `IndexError`" (PR #177, fixing #176). transformers is unpinned, so a fresh install hits this. Searchable symptom: `IndexError` from the intruder scorer, or explainer prompts with no highlighted tokens.
- **Explanation parsing took the *first* `[EXPLANATION]:` marker** (PR #179): a chain-of-thought explainer returned its whole reasoning chain as the label, and top-activating subject-model text containing the marker could inject a label that "flows verbatim through `ExplainerResult.explanation` into `DetectionScorer` / `IntruderScorer` / `OpenAISimulator` and into operator-facing auto-interp tooling".
- **Both fixes are on `main` only.** PRs #177 and #179 merged 2026-08-25; the latest release is still v0.1.3 (2026-03-12). Install from git (`pip install git+https://github.com/EleutherAI/delphi.git`) and check that an explainer prompt shows highlighted tokens before scoring a large run.
- **An alternative scorer:** Transluce's released simulator model scores any feature explanation by correlation with true activations (Llama-3.1-8B features only; see [`mech-interp.md`](mech-interp.md#automated-interpretability-and-interpretability-agents)).

## clt-training (EleutherAI)

Aliases: `clt-training`, `EleutherAI/clt-training` on GitHub, "cross-layer transcoders". **Fork of `EleutherAI/sparsify`** — sparsify configs partly transfer. Adds DTensor tensor parallelism, bfloat16, KL+FVU training, pre-layernorm hookpoints.

**What it is.** Library for training **cross-layer transcoders** (CLTs) — a 2025 architecture that learns sparse features explaining MLP behavior across layers jointly.

**Status (2026-10):** Small/research-grade fork (27 stars on 2026-10-12), last push 2025-11-14. Install via `uv venv --seed && uv sync` — no PyPI. Useful only for the specific CLT use case.

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

Aliases: `circuit-tracer`, **`decoderesearch/circuit-tracer` on GitHub** (canonical; `safety-research/circuit-tracer` is the old slug and still resolves to it), "the Anthropic Transformer Circuits team's transcoder circuit library", "attribution graphs library". Authors Michael Hanna, Mateusz Piotrowski, Jack Lindsey, Emmanuel Ameisen; maintained by Decode Research (`decoderesearch`). Latest tag **v0.5.3 (2026-10-14)** (auto-versioning via `hatch-vcs`); PyPI is still 0.5.0 (2026-03-29), so install from a clone (`pip install .`, as the README says) or a tag: `pip install "git+https://github.com/decoderesearch/circuit-tracer.git@v0.5.3"`. v0.5.3 brings the nnsight-0.8 backend into a tagged release ("NNsight backend bumped to 0.8", #113) and fixes three silent correctness bugs (below). An interp-engine backend is proposed (PR #111, "feat: interp-engine support", open since 2026-08-21).

**What it is.** A library for **circuit-level analysis on top of MLP transcoder features** — given trained transcoders, it discovers attribution graphs (which features at which layers drove a particular completion), renders them, and supports interventions on features. The transcoder-circuit approach was introduced by Dunefsky, Chlenski & Nanda 2024, "Transcoders Find Interpretable LLM Feature Circuits" (arXiv:2406.11944; NeurIPS 2024); circuit-tracer implements the attribution-graph methods from Anthropic's Transformer Circuits team (Ameisen et al. 2025, Lindsey et al. 2025). It runs three steps — attribution, graph-file creation (pruning), local visualization server (`circuit-tracer attribute --prompt ... --transcoder_set gemma --slug ... --graph_file_dir ... --server`) — and graphs can also be created on Neuronpedia with no install.

**Available transcoder sets (from the README, 2026-10):** Gemma-2 2B per-layer transcoders (PLTs) and cross-layer transcoders (CLTs; 426K and 2.5M features); Llama-3.2 1B PLTs and CLTs; Qwen-3 PLTs (0.6B, 1.7B, 4B, 8B, 14B); a GPT-OSS 20B CLT (`mntss/clt-131k`); **Gemma-3 PLTs from Gemma Scope 2 for 270M, 1B, 4B, 12B and 27B (pretrained and instruction-tuned; these require the `nnsight` backend)**; and **Llama-3.1-8B-Instruct TopK PLTs** (`facebook/crv-8b-instruct-transcoders`; license `cc-by-nc-4.0`, i.e. non-commercial). Locally trained transcoders load by passing their full root path. Added in v0.5.0 (April 2026): support for TopK transcoders and local CLT features in graphs. The `lazy_encoder` / `lazy_decoder` options need transcoders in `circuit-tracer`-compatible format; the README documents `save_transcoders_to_cache` for converting them.

**When to use it:** You've trained or loaded transcoders (via sparsify `--transcode`, dictionary_learning, CLT-Forge, or pretrained sets above) and you want to do circuit discovery — "which features explain this output?" — rather than just feature inspection. The natural next step after most SAE/transcoder projects.

**When *not* to use it:** You only have residual-stream SAEs (not transcoders) and just want feature dashboards — SAEDashboard or Neuronpedia is the right tool. You need attention-mechanism explanations — QK attributions and head loadings were requested (issue #53) and proposed (#114) but are not in a release.

**Automating the manual step.** Grouping features into *supernodes* is normally done by hand. Patel, Zhang & Hu, *LLMs Can Annotate Attribution Graphs* (arXiv:2608.02632, 2026-07-28; ICML 2026 Mechanistic Interpretability Workshop; code `maxh119Z/circuit-tracer-automation`, data `circuit-tracer-automation/pipeline_automation` on HuggingFace) feed feature descriptions (from top-activating text on Neuronpedia plus logit effects) to a language model that groups them into supernodes; on Gemma-2-2B with Gemma Scope transcoders the supernodes scored as interpretable as the 15 human-annotated reference graphs, and the pipeline recovered the intermediate-hop supernode on a two-hop "Capitals" task in 97 of 100 prompts. Limits stated by the authors: one model, one transcoder suite, one annotator LLM (GPT-5 mini), a naive grouping that ignores layer/position and attribution flow, and supernode labels too coarse for arithmetic circuits. Use it to triage many graphs, not to replace reading the graph for a claim you will publish.

**Pitfalls:**
- **Attribution graphs are computationally heavy on long prompts.** Start with short prompts and small token windows; the renderer can choke on dense graphs. A long-context OOM on an 80 GB H100 at ~6,000-token prompts is an open issue (#92); a long-context memory estimator is proposed (#109).
- **`ImportError: cannot import name 'HookedTransformer' from 'transformer_lens'` on `import circuit_tracer`** (issue #115, still open as of 2026-10-14). The default backend's `ReplacementModel` subclasses TransformerLens' `HookedTransformer`, which TransformerLens 4.0 (2026-09-21) removed; `pyproject.toml` declares `transformer-lens>=2.16.0` with no upper bound. Per the issue thread, `main` currently also caps `transformers<=4.57.3`, so a fresh resolve picks TransformerLens 3.2.1 — but lifting that cap would pull TL 4. Pin `transformer-lens<4`, or use `ReplacementModel.from_pretrained(model_name, backend='nnsight')` (experimental: slower and more memory-hungry, per the README).
- **nnsight version coupling.** `main` and the v0.5.3 tag require `nnsight>=0.8.0rc1,<0.9` (the nnsight backend was ported to 0.8 on 2026-09-11) and cap `transformers<=4.57.3`. nnsight 0.8 is a PyPI *pre-release* with breaking changes (see [`mech-interp.md`](mech-interp.md)); installing from a clone with an older pinned nnsight, or mixing with `nnterp`, can raise dependency conflicts.
- **CLT skip weights were dropped on save in ≤0.5.2 (fixed in v0.5.3, PR #117).** "Saving and reloading an affine CLT silently drops `W_skip`, so the reloaded model reconstructs different activations" (in the PR's small CPU reproduction a reconstructed value went from 20.5 to 8.5). The PR notes that "weights already discarded by older saves cannot be recovered": re-create such checkpoints from the original training run or source weights with ≥0.5.3, rather than re-saving the broken file.
- **Inactive trailing token positions were dropped in sparse CLT reconstruction (fixed in v0.5.3, PR #118).** Reconstruction inferred the token count from the last active feature, so it dropped trailing inactive tokens, crashed when no features survived the BOS mask, and "could silently broadcast a one-token reconstruction across later error vectors".
- **`prune_graph` kept zero-weight edges at `edge_threshold=1.0`** before v0.5.3 (PR #116).
- **Error-node ids changed in v0.5.1** (2026-07-12): error nodes are now `"{layer}_-1_{pos}"` instead of `"0_{layer}_{pos}"`, which previously collided with layer-0 transcoder feature ids. Graph files or analysis code written against the old id format misparse error nodes.
- **Replacement-model faithfulness.** Splicing SAEs or transcoders into several layers at once yields a model whose outputs can be badly degraded, which is why graphs carry *error nodes* for the unexplained residual. A 2026 blog post (Evan Lloyd, LessWrong 2026-07-27, unreviewed; code in `evan-lloyd/mechinterp-experiments`) argues for *replacement-aware training* — a loss term penalising distortion of the next layer's features — on Gemma-2-2B residual SAEs instead of relying on error nodes. Treat error-node mass as the first number to report with any graph.

## Lorsa (Low-Rank Sparse Attention)

Aliases: "Lorsa", "low-rank sparse attention", "attention SAE alternative", "attention superposition", He et al. 2025; code `OpenMOSS/Lorsa` (a pointer repo) → implementation in **`OpenMOSS/Llamascopium`** (the `OpenMOSS/Language-Model-SAEs` URL redirects there; verified, last push 2026-10-04), PyPI `llamascopium` (latest 2.0.0b34, a pre-release; Python ≥3.11, <3.13).

**What it is.** He, Wang, Lin, Ge, Shu, Tang, Zhang & Qiu, *Towards Understanding the Nature of Attention with Low-Rank Sparse Decomposition* (arXiv:2504.20938; ICLR 2026 per the Llamascopium README). A sparse *replacement model* for multi-head self-attention (MHSA): many low-rank attention heads of which only a few are active per token, trained to reproduce the attention layer's output. Motivation is *attention superposition* — behaviour computed collectively by several heads, so no single original head is interpretable. Reported results: Lorsa heads recover cleaner, finer-grained versions of induction heads, successor heads and attention-sink behaviour; a family of arithmetic-specific Lorsa heads in Llama-3.1-8B, each corresponding to one atomic operation; automated-interpretability scores at parity with SAEs, and "superior circuit discovery properties, especially for features computed collectively by multiple MHSA heads". The Llamascopium README (2026-02-12 entry) adds *Complete Replacement Models*, which combine transcoders and Lorsas to sparsify a whole model (blog post, not checked here).

**When to use it:** your circuit question runs through attention — which earlier-position feature is being moved, and why — where MLP transcoders and circuit-tracer's graphs say little (circuit-tracer has no QK attribution in a release; see above).

**When *not* to use it:** you want pretrained artifacts and mature tooling on your model — Lorsa needs training per model and layer, the pip package is a beta pre-release, and circuit-tracer's README does not mention Lorsa (2026-10-12), so attribution graphs that include Lorsa heads mean working inside Llamascopium.

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

> **Warning — affine transcoders and SAELens < 6.54.2.** Every Gemma Scope 2 transcoder whose ID ends in `_affine` (skip-transcoders with an `affine_skip_connection`) loaded through SAELens before **6.54.2 (2026-10-13)** had its skip matrix transposed: no error, wrong output (explained variance −16.4 instead of 0.807 on 270m-pt layer 15; −3.45 instead of 0.959 on 1b-pt layer 7, per SAELens PR #761). Upgrade (`pip install -U "sae-lens>=6.54.2"`) and reload from the original `google/gemma-scope-2-*` repo any affine transcoder you re-saved in SAELens format. The PR verified the fix on 270m and 1b pretrained transcoders; the `-it` repos, 262k widths and the 4b/12b/27b models "go through the same loader" but were not checked on real weights. circuit-tracer's own Gemma-3 transcoder loader was not affected.

**Pitfall:** `google/gemma-scope-2` is a landing page with **no weights** — "There are no model weights in this repo"; load from a size-specific repo. SAELens release names embed the repo and folder (`gemma-scope-2-4b-it-resid_post`).

## ViT-Prisma (SAEs, transcoders and hooks for vision models)

Aliases: ViT-Prisma, Prisma, `Prisma-Multimodal/ViT-Prisma` on GitHub, `vit-prisma` / `vit_prisma`, vision SAEs, CLIP SAEs, DINO SAEs, "TransformerLens for vision".

**What it is.** A library for vision and video mechanistic interpretability with TransformerLens-style hooked models (`from vit_prisma.models.model_loader import load_hooked_model`), activation caching, SAE training and evaluation notebooks, and a suite of pretrained SAEs "for all layers of CLIP and DINO", including transcoders for all layers of CLIP, on Hugging Face (table in `docs/sae_table.md`). It supports most ViTs, CLIP, DINO and JEPA models from OpenCLIP and Hugging Face. MIT; last push 2026-10-07.

```python
# Adapted from the README (see docs/sae_table.md for every SAE repo id). The README passes
# file_name= / config_name= keywords, which huggingface_hub.hf_hub_download does not accept
# (its parameter is `filename`), so the file name is passed positionally here. Not run.
from huggingface_hub import hf_hub_download
from vit_prisma.sae import SparseAutoencoder

repo_id = "Prisma-Multimodal/sparse-autoencoder-clip-b-32-sae-vanilla-x64-layer-10-hook_mlp_out-l1-1e-05"
sae_path = hf_hub_download(repo_id, "weights.pt")    # the README notes the file name can vary slightly per repo
hf_hub_download(repo_id, "config.json")              # lands in the same snapshot directory as weights.pt
sae = SparseAutoencoder.load_from_pretrained(sae_path)   # reads config.json next to the weights
```

The README recommends "starting with the vanilla CLIP SAEs, which are the highest quality", and the layer-11 `resid_post` CLIP SAE for first steering experiments.

**Pitfall: PyPI is far behind.** PyPI `vit-prisma` is 0.1.4 (2024-03-10) and the latest GitHub release is v2.0.0 (2024-09-07), while `main` is still updated; the README installs from source (`pip install -e .` in a clone, Python ≥3.10). Code written against `main` may not run on the PyPI package.

**When to use it:** feature-level work on CLIP or DINO image encoders; a vision-side testbed for SAE methods.

**When *not* to use it:** the language side of a vision-language model (use nnsight or TransformerLens on the LM); anything that needs a pinned, released version.

## Parameter decomposition (SPD, VPD) — weight-space alternative to SAEs

Aliases: "parameter decomposition", "APD" (Attribution-based Parameter Decomposition, Braun, Bushnaq, Heimersheim, Mendel & Sharkey, arXiv:2501.14926, January 2025 — the first version; toy settings only, and the authors note scaling to non-toy models remains a challenge), "SPD" (Stochastic Parameter Decomposition, Bushnaq, Braun & Sharkey, arXiv:2506.20790, June 2025), "VPD" (adVersarial Parameter Decomposition; Goodfire, *Interpreting Language Model Parameters*, 2026-05-05, https://www.goodfire.com/research/interpreting-lm-parameters), `goodfire-ai/param-decomp` on GitHub (MIT; verified, last push 2026-10-05).

**What it is.** Instead of decomposing *activations* into a dictionary (SAEs, transcoders, crosscoders), parameter decomposition decomposes a model's **weight matrices** into many rank-one "subcomponents" that sum back to the original parameters, are sparse (any one input token needs few of them) and are trained to be *mechanistically faithful* (ablating the unneeded ones leaves the output unchanged). VPD's change from SPD is training against adversarially chosen ablations instead of stochastic ones. Goodfire reports less feature splitting than transcoders and that it applies to attention layers too. The repository includes a handbook (`docs/handbook.md`), a compact `nano_param_decomp/` implementation, and JAX training configs.

**When to use it:** You are doing methods research on faithful, weight-space decompositions, or want a decomposition that explains a computation in the *network's own parameters* rather than in a learned activation basis.

**When *not* to use it:** You want to interpret a production-scale model — the paper's decomposition is of a **4-layer, ~67M-parameter language model** (38,912 subcomponents, ~10,000 alive); the reference config in the repo needs a 32-GPU mesh (`fsdp: 32`), Blackwell GPUs need the `cuda13` extra and driver r580+, and no pretrained decompositions of 1B+ models were found (2026-10). For "find the feature for a concept I can name" use a probe or SAE.

**Known limits (reported):**
- Goodfire's own numbers: validation cross-entropy 2.72 with unmasked subcomponents vs 2.71 for the target; Pareto-dominates transcoders on tested sparsity measures *but the advantage disappears under matched training objectives*; adversarial robustness is limited (KL divergence 0.83 after 20 adversarial steps, 25.26 after 160).
- An independent audit (Tom Angsten, LessWrong 2026-09-30; code `angsten/vpd-audit`, verified) of the *released* decomposition found that aggregating the components needed by many inputs makes the model's output drift away from the original — at 64 tokens' worth of components (~4,500) with no search, KL ≈ 0.80 nats, comparable to the paper's own 20-step adversary (0.83 nats); deleting all components never labelled "needed" moved the model 1.28 nats. It audits the paper's decomposition, not the newer unpublished recipe in the repo. Do not assume "removing these components only affects this behaviour".

## Weight-sparse transformers (interpretable by construction)

Aliases: "weight-sparse transformers", "circuit sparsity", "sparse circuits", "intrinsically interpretable models", "interpretable by design", Gao et al. 2025, `openai/circuit_sparsity` on GitHub (Apache-2.0; verified, last push 2026-09-04).

**What it is.** Instead of decomposing a dense model after the fact (SAEs, transcoders, parameter decomposition), train a transformer in which most weights are constrained to zero, so each neuron has only a few connections, then **prune** it on a narrow task to isolate the responsible circuit. Gao, Rajaram, Coxon, Govande, Baker & Mossing (OpenAI), *Weight-sparse transformers have interpretable circuits*, arXiv:2511.13653 (2025-11-17): the pruned circuits often contain neurons and residual channels corresponding to natural concepts with a few straightforwardly interpretable connections; sparser weights trade capability for interpretability, and scaling model size improves that frontier. The authors' own limit: "scaling sparse models beyond tens of millions of nonzero parameters while preserving interpretability remains a challenge." They also report preliminary results suggesting the method can be adapted to explain existing dense models. The repo provides a `GPT` inference implementation (`circuit_sparsity.inference.gpt.load_model`), released models and pruning sweeps hosted on `openaipublic` blob storage, and a Streamlit circuit visualizer (`streamlit run circuit_sparsity/viz.py`); install with `pip install -e .` from a clone. It also ships a minimal training script, `circuit_sparsity/train.py`, whose docstring says it "can train the models from the paper, albeit slowly". For the pruning algorithm itself, jacob_drori's replication (below) describes its reimplementation, `jacobcd52/sparse_pretrain_public` (small, no license file), as additionally implementing pruning, bridges training and multi-GPU support relative to the OpenAI release.

**Faithfulness caveat (read before building on it).** jacob_drori, *Weight-Sparse Circuits May Be Interpretable Yet Unfaithful* (LessWrong, 2026-02-09; Anthropic Fellows work) replicated the main result on two-layer models trained on SimpleStories, then found that the pruning step can produce circuits that do not reflect the model's computation: pruning reached task loss below 0.05 with about 30 nodes on a **nonsense task** (male name → "is", female name → "when"); a pruned circuit solved a pronoun task with *uniform* attention where the original head attended to the name; nodes took on different roles in the pruned model than in the original; and on simplified IOI (indirect object identification) pruned only on opposite-gender prompts, many seeds found a circuit that fails on **same-gender prompts**, although the original model handled them (81% correct). The author's scope note: the results "only show that the pruning algorithm is flawed", not that weight-sparse training is. A related design point from the post: switching from mean to zero ablation shrank circuits but may have made them less faithful.

**When to use it:** methods research on interpretable-by-construction models; small-model studies where you want circuits a person can read in a day (Leo Gao's *An Ambitious Vision for Interpretability* frames this as the route to "an interpretable GPT-1"; see [`mech-interp.md`](mech-interp.md#agenda-framing-pragmatic-ambitious-and-open-problems)). Close relatives: parameter decomposition (above), and *tensor/bilinear transformers* — Logan Riggs argues (LessWrong opinion post, 2026-09-02) that anyone interpreting models under 1B parameters should use bilinear MLP and attention variants so the whole network is analysable with linear algebra.

**When *not* to use it:** you need to interpret an existing production model — these are new models trained from scratch at small scale.

**Open problem and bar.** The open question is whether weight sparsity yields circuits that are *both* small and faithful at useful scale. The evidence that would settle it: circuits that keep their size advantage over dense models while passing (1) a **nonsense-task control** (pruning cannot reach low loss on a task the model does not perform), (2) **out-of-distribution checks** where two candidate mechanisms disagree (e.g. same-gender IOI), and (3) a stronger faithfulness test than loss-versus-circuit-size, such as frozen-LayerNorm pruning or causal scrubbing — and doing so past the tens-of-millions-of-nonzero-parameters ceiling.

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

**Reliability caveat: don't rank SAEs on TPP or SCR (as of 2026-10-14).** David Chanin, "Are Sparse Autoencoder Benchmarks Reliable?" (arXiv:2605.18229, 2026-05-18; code `decoderesearch/saebench-reliability-audit`, MIT) audits SAEBench three ways: reseed noise on a fixed canonical Gemma Scope SAE, correlation with ground truth on synthetic SAEs built on SynthSAEBench, and discriminability across training trajectories. Findings (abstract): "two of these metrics, Targeted Probe Perturbation (TPP) and Spurious Correlation Removal (SCR), fail multiple lenses at their canonical settings and should not be used to evaluate SAEs"; the other metrics "show higher reseed noise and lower discriminability than the field assumes"; and "the sae-probes variant of k-sparse probing is the most reliable metric we tested, but even sae-probes struggles to separate variants of the same SAE architecture". Practical reading: report the spread across several seeds for every SAEBench number, lean on the `sae-probes` k-sparse probing variant, and treat a TPP or SCR win (including ICA Lens's TPP result above) as weak evidence. Reseed run, verbatim from the audit README:

```bash
python -m saebench_audit.runners.reseed \
    --sae-release gemma-scope-2b-pt-res-canonical \
    --sae-id layer_12/width_65k/canonical \
    --seeds 42 123 456 789 2024 \
    --output-dir results/reseed
```

When not to over-read it: it is not a reason to drop SAEBench — the audit found one usable metric and judged the rest at canonical settings, and its own conclusion is that "the field needs better SAE benchmarks".

**When to use it:**
- You trained a new SAE variant and need to show it is better at *something a person cares about*, not just at reconstruction-per-L0. This is the standard the field now expects.
- You are choosing between pretrained SAEs for a downstream project and want a principled pick.
- You want a ready-made downstream task (unlearning, sparse probing) rather than inventing one. (SCR and TPP are also ready-made, but see the reliability caveat below before ranking SAEs on them.)

**When *not* to use it:**
- You just want L0 and loss-recovered — SAELens computes those directly, and the harness is overhead.
- Your SAE is for a model/hook not covered by the regex-selected families; you'll be writing config plumbing before you get a number.

**Pitfalls:**
- **Regex selection is silent when it matches nothing.** A typo in `--sae_regex_pattern` gives you an empty run rather than an error. Check how many SAEs were selected before interpreting an eval that finished suspiciously fast.
- **Feature absorption and SCR need probing data** and will download datasets on first run; a sandboxed/offline box fails here first.
- **Don't compare across sparsity levels without saying so.** Most of these metrics move with L0; a comparison table where SAEs sit at different L0 is not a comparison of architectures.
- **Unlearning eval ≠ unlearning research.** It measures whether SAE feature clamping suppresses a capability, which is one narrow probe — see [`unlearning.md`](../alignment-science/unlearning.md) for what the unlearning literature demands.

## SynthSAEBench (synthetic ground-truth features)

Aliases: "SynthSAEBench", "SynthSAEBench-16k", "synthetic SAE benchmark", `sae_lens.synthetic`, Chanin & Garriga-Alonso 2026. Paper: arXiv **2602.14687** (v2, 2026-07-13). Ships inside **SAELens** (docs page "SynthSAEBench" at `decoderesearch.github.io/SAELens`), not as a separate package.

**What it is.** A synthetic "model" whose activations are generated from 16,384 known ground-truth features in a 768-dimensional space, with realistic complications built in: Zipfian firing frequencies, a feature hierarchy (128 roots, branching factor 4, depth 3, mutually exclusive children), low-rank correlations and superposition. Because the true features and their firings are known, an SAE can be scored directly — **MCC** (mean correlation coefficient: Hungarian-matched mean |cosine| between decoder columns and true features), feature **uniqueness**, **precision/recall/F1** of latent firings, explained variance, L0, dead latents and shrinkage. The authors' motivation: "Current LLM-based SAE benchmarks are too noisy to differentiate architectural improvements". It reproduces known LLM SAE phenomena (reconstruction and latent quality disagree; poor SAE probing; a precision–recall trade-off set by L0) and identified a new failure mode: Matching Pursuit SAEs exploit superposition noise to improve reconstruction without learning the true features.

```python
# pip install sae-lens   (from the SAELens SynthSAEBench docs page)
from sae_lens.synthetic import SyntheticModel
model = SyntheticModel.from_pretrained("decoderesearch/synth-sae-bench-16k-v2", device="cuda")
```
Training goes through `SyntheticSAERunner(SyntheticSAERunnerConfig(...))`; the docs recommend SAE width 4,096, 200M samples, learning rate 3e-4, batch size 1,024, and report final `mcc`, `explained_variance`, `uniqueness` and `classification.f1_score`.

**Pitfall: use `-v2`.** The docs say v1 of SynthSAEBench-16k was uploaded without `scale_children_by_parent=True`, so it does not match the paper's model; v2 fixes only that. Results on `decoderesearch/synth-sae-bench-16k` (v1) are not comparable with the paper.

**When to use it:** iterating on an SAE *architecture or training trick* — a run takes about 20 minutes on one GPU (per chanind, below), and a method that fails here, where the linear representation hypothesis holds by construction, has little hope on an LLM. **When *not* to use it:** as evidence that an SAE is good on a real model — it is the paper's "controlled lower-bound test"; pair it with SAEBench.

**Autonomous agent result on SynthSAEBench.** chanind, *Letting Claude do Autonomous Research to Improve SAEs* (LessWrong, 2026-03-10; MATS 7.1; code and the `TASK.md` prompt at `chanind/claude-auto-research-synthsaebench`, MIT). Claude Code (Claude Opus 4.6), run unattended overnight in a loop of "research sprints" (idea → implement → run → report) with light steering through `TASK.md`, raised F1 on SynthSAEBench-16k "from 0.88 to 0.95"; within another day, with occasional input, it matched the logistic-regression probe ceiling of 0.97, and MCC rose from 0.78 to 0.84. The resulting "LISTA-Matryoshka" SAE combines a one-iteration LISTA encoder (adapted by Claude from a 2010 sparse-coding paper), annealing K downward during training, detaching inner Matryoshka levels, a TERM loss, and sorting Matryoshka levels by firing frequency. Caveats the author states: the gains are **not yet verified on LLM SAEs** (LISTA with eta = 0.3 "seems to break on LLMs"), some gains may come from hill-climbing one synthetic model, and validating a single change on SAEBench needs multiple seeds and L0s and can cost $1,000+ in compute; Claude also once declared an idea failed when an implementation bug meant the sprint had tested nothing. **Regime:** a long, largely unattended single-agent loop with a fast, unambiguous metric; transfer to short interactive researcher+agent sessions, or to slow noisy metrics, is untested.

**Open problem and bar.** An SAE architecture counts as an improvement when it beats the strongest SynthSAEBench baselines (the Matryoshka SAE in the paper; LISTA-Matryoshka since chanind's post) on MCC and F1 at matched L0 **and** that gain carries over to SAEBench on a real LLM across several seeds and L0 values — the step that, as of the post, had not been shown for the LISTA changes.

## Common SAE pitfalls (cross-cutting)

- **Reconstruction loss is not the goal.** A trivially-perfect-reconstruction SAE can still be uninterpretable. Check L0, % alive features, and qualitative feature inspection.
- **Dead features.** A nontrivial fraction of features may never activate. SAELens and sparsify both have "ghost grad" / "auxiliary loss" mechanisms; use them or expect 30%+ dead features.
- **Width matters.** A 16k-feature SAE on Gemma-2-2B residual stream is "narrow" by 2026 standards; 65k–1M is now common. Width changes feature granularity.
- **"Feature splitting."** As you increase width, what was one feature splits into several finer-grained ones. Don't assume a feature with the same description in two SAE widths is "the same."
- **Don't compare absolute reconstruction loss across models / hook points.** It's only meaningful within a fixed setup.
- **Sandwich-norm hook trap (Gemma 2/3/4, OLMo 2/3).** "MLP output" is two tensors on these models; Gemma Scope MLP SAEs read the post-`post_feedforward_layernorm` residual contribution, and fed the raw MLP output they look dead (FVU 9.8, L0 8 vs FVU 0.26, L0 81 on gemma-2-2b layer 4). Check FVU and L0 on both candidates — see [`mech-interp.md`](mech-interp.md#the-sandwich-norm-hook-trap-gemma-234-olmo-23).
- **Silent loader bugs exist; sanity-check explained variance after loading.** SAELens < 6.54.2 transposed Gemma Scope 2 affine skip connections; circuit-tracer ≤ 0.5.2 dropped CLT skip weights on save. A negative or near-zero explained variance on in-distribution text from a released dictionary is a loading problem until shown otherwise.
- **Single-seed benchmark numbers.** SAEBench metrics carry more reseed noise than assumed, and TPP/SCR fail an audit (see [SAEBench](#saebench)); report seed spread.

## Cross-references

- Mechanistic interp libraries SAEs run on top of: [`mech-interp.md`](mech-interp.md).
- High-throughput activation extraction (for SAE feature collection at scale): [`serving-and-activations.md`](serving-and-activations.md).
- SAE-based steering: [`steering.md`](steering.md).
- Reading a model's unspoken intermediate variables without training an SAE (J-Lens / R-Lens / J++ Lens, natural language autoencoders): [`mech-interp.md`](mech-interp.md#workspace-lenses-j-lens-r-lens-j-lens).
- Circuit-discovery methods and how to score them (EAP-IG, MIB — where SAE features did not beat raw neurons on causal-variable localization): [`mech-interp.md`](mech-interp.md#circuit-discovery-and-how-to-evaluate-it-eap-ig-mib-causal-abstraction).
- Belief-state geometry, singular learning theory and susceptibilities (a non-dictionary route to model structure; susceptibility clusters were compared against SAE features): [`slt-devinterp.md`](slt-devinterp.md).

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

Most common causes: (1) **hook point mismatch** — different SAEs are trained at `hook_resid_pre` vs `hook_resid_post` vs `hook_mlp_out`; loading at the wrong hook gives garbage. On Gemma 2/3/4 and OLMo 2/3 there is a second trap: the raw MLP output (`mlp.hook_out`, HF `model.model.layers[i].mlp`) is not the post-norm contribution (`hook_mlp_out`) that Gemma Scope MLP SAEs read ([details](mech-interp.md#the-sandwich-norm-hook-trap-gemma-234-olmo-23)). (2) **Tokenizer / chat-template mismatch** — pretrained SAEs were trained on raw text or specific chat format; applying to other formats degrades reconstruction. (3) **Width too narrow** for the model — 16k features on a 2B model is small by 2026 standards. (4) **A loader bug** — for Gemma Scope 2 affine transcoders, upgrade to `sae-lens>=6.54.2`.

### My Gemma Scope 2 transcoder has negative explained variance — why?

If its ID ends in `_affine` and you loaded it with SAELens before 6.54.2, the skip connection was applied transposed (SAELens PR #761: −16.4 instead of 0.807 on 270m-pt layer 15). `pip install -U "sae-lens>=6.54.2"` and reload from the original `google/gemma-scope-2-*` repo — a copy re-saved in SAELens format keeps the transposed matrix.

### Can I trust SAEBench's TPP and SCR scores?

Not for ranking SAEs, per Chanin's audit (arXiv:2605.18229): Targeted Probe Perturbation and Spurious Correlation Removal fail reseed, synthetic-ground-truth and training-trajectory checks at their canonical settings. The `sae-probes` k-sparse probing variant was the most reliable metric tested. Report several seeds for every SAEBench number.

### Is there something cheaper than training an SAE for a first look?

**ICA Lens** (`pip install icalens`; arXiv:2606.11722) fits independent component analysis to a layer's activations — "substantially more compute-efficient to fit than an SAE dictionary" (README) — and ships an interactive token-level explorer and published lenses for GPT-2 small and Qwen3.5-2B. Standard ICA yields no more components than the activation dimension (whether `icalens` relaxes this was not checked), so treat it as a first lens and a baseline, not a replacement for an overcomplete dictionary.

### Are there pretrained SAEs for Gemma 3?

Yes — **Gemma Scope 2** (`google/gemma-scope-2-{270m,1b,4b,12b,27b}-{pt,it}`, December 2025): SAEs, transcoders, crosscoders and cross-layer transcoders, loadable through SAELens (e.g. `release="gemma-scope-2-4b-it-resid_post"`). For Gemma 2 use the original Gemma Scope (`gemma-scope-2b-pt-res` etc.). Neuronpedia hosts a browser at `neuronpedia.org/gemma-scope-2`.

### `import sae_lens` fails with `cannot import name 'HookedTransformer' from 'transformer_lens'` — why?

TransformerLens 4.0.0 (2026-09-21) removed `HookedTransformer`. Upgrade to `sae-lens>=6.51.2` (pins `transformer-lens<4.0.0`) or `pip install "transformer-lens<4"`. Real TL 4 support is tracked in SAELens issue #739.

### How is parameter decomposition different from an SAE or transcoder?

SAEs and transcoders learn a dictionary over *activations*; parameter decomposition (SPD, VPD; `goodfire-ai/param-decomp`) splits the *weight matrices* into sparse rank-one subcomponents that sum to the original parameters. It has so far been demonstrated on a 4-layer, ~67M-parameter language model and an independent audit found aggregated explanations drift from the original model's outputs — treat it as a research direction, not a drop-in replacement for SAELens.

---

Last verified: 2026-10-14. SAELens 6.x current (v6.54.5, 2026-10-14; was v6.54.0 at the 2026-10-04 check). EleutherAI sparsify v1.3.3 on PyPI as `eai-sparsify` (2026-07-16). dictionary_learning last commit Aug 2025. Delphi v0.1.3 (March 2026; PyPI `eai-delphi` 0.1.3, later fixes on `main`). clt-training last activity Nov 2025. SAEDashboard v0.8.0 (Apr 2026); sae_vis deprecated by its author. circuit-tracer v0.5.3 tag (2026-10-14; PyPI still 0.5.0, canonical repo now `decoderesearch/circuit-tracer`). Goodfire SDK archived; Goodfire SAEs remain on HuggingFace. (Citation audit 2026-06: fixed the self-referential `HookedSAETransformer` wording, softened the sae_vis "deprecated" claim, and added Gemma Scope / Llama Scope arXiv IDs. Additions 2026-06: a "Should I use SAEs at all?" skeptic's reading list — Kantamneni 2502.16681, Leask 2502.04878, Korznikov 2602.14111, Peng 2506.23845 — and architecture citations for BatchTopK 2412.06410, Matryoshka 2503.17547, and transcoder circuits 2406.11944; all verified via arXiv.) (Additions 2026-08: SAEBench — `sae-bench` v0.6.0 on PyPI, arXiv 2503.09532, eval list and CLI verified from the repo README.) (Additions 2026-10: SAELens release notes v6.47–6.54 and the TransformerLens-4 `<4` pin (v6.51.2, issues #738/#739); sparsify v1.3.2/v1.3.3 bug-fix release notes and the 2026-07-20 default-optimizer commit; Gemma Scope 2 (HF model card `google/gemma-scope-2-4b-it`, landing page `google/gemma-scope-2`); circuit-tracer README, v0.5.1 release notes, `pyproject.toml` and issue #115 (TL-4 breakage); `LLMs Can Annotate Attribution Graphs` arXiv:2608.02632 (code `maxh119Z/circuit-tracer-automation`); CLT-Forge arXiv:2603.21014 (`LLM-Interp/CLT-Forge`); Stochastic Parameter Decomposition arXiv:2506.20790, VPD (Goodfire 2026-05-05, `goodfire-ai/param-decomp`) and the VPD audit (LessWrong KeBccWBGXnNXzZFBp, `angsten/vpd-audit`); Neuronpedia `v2.6.33`; corrected the stale `sae_lens.toolkit` import path to `sae_lens.loading.pretrained_saes_directory`; all verified via arXiv abs pages, `gh api` and the HuggingFace API.) (Additions 2026-10-12: superposition section — Toy Models of Superposition arXiv:2209.10652 and Superposition Yields Robust Neural Scaling arXiv:2505.10465 (abstracts via the arXiv API); Lorsa arXiv:2504.20938 (abstract), `OpenMOSS/Lorsa` README and the `Language-Model-SAEs` → `OpenMOSS/Llamascopium` redirect via `gh api`, `llamascopium` 2.0.0b34 on PyPI; APD arXiv:2501.14926 (abstract); weight-sparse transformers arXiv:2511.13653 (abstract), `openai/circuit_sparsity` README, file tree and `train.py` docstring via `gh api`, jacob_drori's post (LessWrong sHpZZnRDLg7ccX9aF, read in full via GraphQL), Logan Riggs's tensor-transformer post (LessWrong expsAXaBgiqgitFe6); SynthSAEBench arXiv:2602.14687 (abstract) and the SAELens SynthSAEBench docs page (config, v1/v2 note, API, metrics); chanind's post (LessWrong rbqJoxFZtae9x93mx, read in full) and `chanind/claude-auto-research-synthsaebench`; clt-training star count re-checked (27) via the GitHub API. The SynthSAEBench snippet is copied from the docs, not run.) (Additions 2026-10-14: SAELens v6.54.2 release notes and PR #761 (Gemma Scope 2 affine skip transpose; table and quotes read from the PR body), SAELens `pyproject.toml` (`transformer-lens<4.0.0` still pinned), circuit-tracer `single_layer_transcoder.py` (`.T.contiguous()`), circuit-tracer v0.5.3 release notes, PRs #116/#117/#118 and the v0.5.3 `pyproject.toml`, PR #111 (open); Delphi PRs #177/#179 (merged 2026-08-25, after v0.1.3) and the unrelated PyPI `delphi` package; the sandwich-norm trap from interp-engine `docs/PORTING.md`; SAEBench audit arXiv:2605.18229 (abstract) and `decoderesearch/saebench-reliability-audit` README; ICA Lens arXiv:2606.11722 (abstract; two authors) and README, PyPI `icalens` 0.4.0; AxBench arXiv:2501.17148 (abstract); sae-manifold arXiv:2604.28119 (abstract) and README; block-sparse-featurizer README; ViT-Prisma README, releases, PyPI 0.1.4 and the HF file list of the CLIP layer-10 SAE (the README's `file_name=` keyword does not match `hf_hub_download`'s `filename`, so the snippet here is adapted and not run). Repo metadata via `gh api` on 2026-10-14.)
