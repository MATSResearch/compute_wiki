---
tags:
  - interpretability
---

# Mechanistic Interpretability Tooling

Libraries for inspecting and intervening on the internals of transformer language models. The big three are **TransformerLens**, **nnsight**, and (for a no-library option) **baukit** + raw PyTorch hooks. **vLLM-Lens** covers the high-throughput case and is documented in [`serving-and-activations.md`](serving-and-activations.md).

## At a glance: which library?

| If you want… | Use |
|---|---|
| Maximum control, "I want to teach myself transformers from the inside out", small model (≤7B) | **TransformerLens** |
| Any HuggingFace model, exact HF behavior, modern intervention syntax, remote 70B+ models | **nnsight** |
| Just one quick hook, no library | **`register_forward_hook`** + **baukit** |
| Throughput / serving / 70B+ local | **vLLM-Lens** (see [`serving-and-activations.md`](serving-and-activations.md)) |
| SAE work specifically | **SAELens** (see [`saes.md`](saes.md)) |

## TransformerLens

Aliases: `transformer_lens` on PyPI, `TransformerLensOrg/TransformerLens` on GitHub, "TL", "Neel Nanda's library" (originally; now community-maintained).

**What it is.** A library that re-implements transformer architectures with a clean, named hook system. Loading `gpt2` or `pythia-70m` or `gemma-2-2b` gives you a `HookedTransformer` whose every attention head, MLP layer, and residual stream activation is named and accessible via `model.run_with_cache` or `model.add_hook`.

**When to use it:**
- You're learning mechanistic interpretability and want consistent naming (`blocks.5.attn.hook_z`, `blocks.5.hook_resid_post`) across architectures.
- You're doing classic mech interp: induction heads, IOI-style circuit analysis, attention pattern visualization.
- The model you care about is in the supported list and is small (≤7B fits comfortably; 27B is feasible on an 80GB GPU).
- You need ablation, patching (resample, attribution), and activation arithmetic with a clean API.

**When *not* to use it:**
- The model isn't supported (TL re-implements architectures one at a time; brand-new models lag).
- You need exact-bit-for-bit equivalence with HuggingFace generation (TL approximates; small numerical drift exists).
- You're working at vLLM scale, or on 70B+ models you can't fit on one node.
- You want to use SAEs — the `HookedSAETransformer` was removed from TransformerLens 2.0 and lives in **SAELens** now.

**Pitfalls (with searchable error symptoms):**
- **"Model not in `loading_from_pretrained.OFFICIAL_MODEL_NAMES`"** — TransformerLens has a hand-curated list. Use `from_pretrained_no_processing()` for closer-to-HF behavior, or fall back to nnsight.
- **Numerical drift vs HuggingFace.** TL applies extra processing (folding LayerNorm, centering writing weights) by default. If you compare logits to HF, use `from_pretrained(..., fold_ln=False, center_writing_weights=False, center_unembed=False)` or just use nnsight.
- **First-token / BOS weirdness.** Many TL workflows skip position 0 because Llama-family models put unusually large activations there. If your patching results look wild at pos 0, that's why.
- **`HookedSAETransformer` ImportError after upgrading to TL 2.x.** Moved to SAELens. `pip install sae-lens` and import from there.
- **Memory blowup with `run_with_cache`.** Caches every named activation by default. Pass `names_filter=lambda name: "hook_resid_post" in name` (or similar) for any non-tiny model.

**One-liner install / first call:**
```python
# pip install transformer_lens
import transformer_lens
model = transformer_lens.HookedTransformer.from_pretrained("gpt2")
logits, cache = model.run_with_cache("Hello world")
```

## nnsight

Aliases: `nnsight` on PyPI, `ndif-team/nnsight` on GitHub, "the NDIF library", "David Bau's library". Paper: "NNsight and NDIF: Democratizing Access to Open-Weight Foundation Model Internals" (Fiotto-Kaufman, Bau et al., ICLR 2025, arXiv:2407.14561).

**What it is.** A library that wraps any PyTorch / HuggingFace model in a tracing context where you can read and modify activations using a deferred-execution syntax. The same code runs locally on a small model or remotely on a 405B model hosted by NDIF (the National Deep Inference Fabric).

**When to use it:**
- Your model is on HuggingFace and you want exact HF behavior with no architecture rewrite.
- You want to intervene on a 70B+ model without owning the GPUs (use NDIF remote backend).
- You like the explicit tracing API: `with model.trace("Hello"): h = model.model.layers[5].output[0].save()`.
- You want a single API across architectures (HF, vLLM via plugin, custom).

**When *not* to use it:**
- You want the consistent named-hook namespace TransformerLens provides — nnsight gives you raw module paths (`model.model.layers[5].mlp.down_proj.output`), which differ between architectures.
- You want SAE-specific helpers — use SAELens (works alongside nnsight).
- You need maximum throughput on local GPUs — use vLLM-Lens.

**Pitfalls:**
- **"Module path not found"** — every architecture has different paths. `print(model)` to see the tree, or use `nnterp` (a standardized-interface wrapper, ICLR 2025) to abstract the differences.
- **`.save()` on the wrong tensor.** Inside a trace, intermediate values are proxies; you must `.save()` the ones you want to read after the trace exits. Forgetting to save = `AttributeError` or empty value.
- **Remote NDIF latency.** Each remote forward pass has network round-trip cost. Batch your interventions; don't do per-token loops to a remote model.
- **Memory on long sequences.** Like TransformerLens, saving every position's activation across all layers OOMs fast. Slice positions and layers explicitly.

**One-liner install / first call:**
```python
# pip install nnsight
from nnsight import LanguageModel
model = LanguageModel("meta-llama/Llama-3.2-1B", device_map="auto")
with model.trace("Hello world"):
    h = model.model.layers[5].output[0].save()
print(h.shape)
```

## nnterp

Aliases: `nnterp` on PyPI, `ndif-team/nnterp` on GitHub (canonical; `butanium/nnterp`, the author Clément Dumas's handle, redirects there), "Clément Dumas's nnsight wrapper", "NDIF nnterp", "nnsight standardized interface".

**What it is.** A thin wrapper around nnsight that gives you TransformerLens-like consistent naming (LLaMA-style `model.layers[i].residual_stream`, attention/MLP submodule paths) across 50+ HuggingFace model variants spanning 16 architecture families. Published at the **Mechanistic Interpretability Workshop, NeurIPS 2025** (arXiv:2511.14465). Latest PyPI 1.3.0 (Feb 2026), actively maintained.

**When to use it:** You want nnsight's exact-HF-behavior + remote-backend story but TransformerLens's consistent-naming ergonomics, especially across many architectures (Llama, Gemma, Qwen, Mistral, Phi, GPT-OSS, etc.).

**When *not* to use it:** You're already comfortable with nnsight's raw module paths; the abstraction is one more thing to debug.

## baukit

Aliases: `baukit`, `davidbau/baukit` on GitHub, "David Bau's earlier library", `baukit.TraceDict`.

**What it is.** A small, pre-nnsight library from the Bau lab. The most useful thing in it is `TraceDict`, a context manager that records activations from a list of named submodules.

**Status (2026-04):** Effectively in maintenance hibernation — last meaningful commit Feb 2024, **not on PyPI** (install via `pip install git+https://github.com/davidbau/baukit`). For new projects, prefer **nnsight + nnterp**, which cover the same `TraceDict` pattern with active maintenance and broader architecture support.

**When to use it:** Reading legacy code that uses `TraceDict`. Quick one-off hook capture in a vanilla HF model when you want zero abstraction. Works on any `nn.Module`, no architecture knowledge required.

**When *not* to use it:** New projects (use nnsight or nnterp). Modifying activations (rather than just reading) — nnsight is cleaner for that. You expect bug fixes or new model support — none are coming.

```python
# pip install git+https://github.com/davidbau/baukit  (NOT on PyPI)
from baukit import TraceDict
layers = [f"model.layers.{i}" for i in range(32)]
with TraceDict(model, layers) as tr:
    out = model(input_ids)
hidden = tr["model.layers.15"].output[0]
```

## Plain PyTorch hooks (no library)

`module.register_forward_hook(fn)` and `module.register_forward_pre_hook(fn)` work on any HuggingFace model. For a one-shot experiment, this is fine — and worth knowing because **every** library above is built on top of this primitive.

**Pitfalls:**
- **Hooks persist until removed.** Save the handle (`h = module.register_forward_hook(fn)`) and call `h.remove()`, or you get cumulative state across calls.
- **In-place modifications to hook inputs/outputs are silently lost** in some PyTorch versions. Return the modified tensor explicitly.
- **DDP / FSDP wrap modules.** The path you hook may be `model.module.model.layers[5]` once wrapped.

## circuitsvis

Aliases: `circuitsvis` on PyPI, `TransformerLensOrg/CircuitsVis` on GitHub (originally `alan-cooney/CircuitsVis`), "Alan Cooney's attention visualization", "CV".

**What it is.** Interactive attention pattern and neuron-activation visualization, designed for Jupyter. Renders heads as the colored grids you see in mech interp papers.

**Status (2026-04):** Maintained but coasting — repo is touched (housekeeping commits) but no new components since late 2024. PyPI 1.43.3.

**When to use it:** You want to look at attention patterns or neuron activations interactively in a notebook — the JS bundle is stable and works fine.

**When *not* to use it:** You're building a non-Jupyter pipeline. You need novel viz components — build in matplotlib/plotly directly; circuitsvis isn't shipping new ones. For SAE feature dashboards, see `sae-dashboard` / Neuronpedia (in [`saes.md`](saes.md)).

## Captum

Aliases: `captum` on PyPI, `meta-pytorch/captum` on GitHub (formerly `pytorch/captum`, which still redirects), "PyTorch interpretability library", "Meta's interp library".

**What it is.** A general PyTorch interpretability library — saliency, integrated gradients, DeepLIFT, GradientShap, layer/neuron conductance for any `nn.Module`. It has **LLM attribution** support (`LLMAttribution`, `LayerGradientXActivation`, `LayerGradientShap`, KV-cache-aware perturbation) dating back to ~v0.7 (2023); the more recent additions are `RemoteLLMAttribution` against hosted endpoints, a `VLLMProvider` for large models, and (v0.9.0, Apr 2026) multimodal image-segment attribution. Active, Meta-maintained, ~quarterly releases.

**When to use it:**
- Token-level input attribution / saliency on LLMs (`LLMAttribution` over a prompt to see which tokens drove a generation).
- Classical attribution methods (integrated gradients, GradientShap) on any PyTorch model — vision, multimodal, tabular.
- Attribution at vLLM scale via `VLLMProvider`.

**When *not* to use it:** Activation patching / circuit analysis / SAE features — TransformerLens / nnsight / SAELens are the right tools. Captum is for *attribution* (which inputs mattered), not mechanism analysis (which internal computations mattered).

## Cross-references

- For SAE work: [`saes.md`](saes.md).
- For activation extraction at vLLM throughput: [`serving-and-activations.md`](serving-and-activations.md).
- For probes built on extracted activations: [`probes.md`](probes.md).
- For activation steering (uses these libraries as backends): [`steering.md`](steering.md).

---

## Common questions

### Is TransformerLens still maintained?

Yes. `TransformerLensOrg/TransformerLens` on GitHub is actively maintained by the community after Neel Nanda's original authorship; new architectures and TL 2.x changes shipped through 2025. The `HookedSAETransformer` was moved out of TransformerLens 2.0 into **SAELens** — that's the most common breaking change you'll hit.

### TransformerLens or nnsight for a beginner?

If you're learning mech interp from scratch and your model is small (≤7B) and supported, start with **TransformerLens** for the consistent named-hook namespace (`blocks.5.hook_resid_post`). If you need to use a model TL doesn't support, or you want exact HuggingFace behavior, or you want to scale to remote 70B+ models, use **nnsight**.

### Why do TransformerLens logits differ slightly from HuggingFace?

TransformerLens applies extra processing by default — folding LayerNorm into adjacent weights, centering writing weights, centering unembed. For numerical equivalence with HF, load with `from_pretrained(..., fold_ln=False, center_writing_weights=False, center_unembed=False)`, or use nnsight (which wraps the actual HF model).

### How do I get attention patterns?

In TransformerLens: `_, cache = model.run_with_cache(prompt, names_filter=lambda n: "pattern" in n)` then `cache["blocks.5.attn.hook_pattern"]`. For visualization, use `circuitsvis` in a Jupyter notebook. In nnsight, access `model.model.layers[5].self_attn.attention_weights.save()` (path varies by architecture).

### Does TransformerLens support [latest model]?

Check `transformer_lens.loading_from_pretrained.OFFICIAL_MODEL_NAMES`. Brand-new models lag — TL re-implements architectures one at a time. If yours isn't listed, fall back to **nnsight** (works with any HF model out of the box) or use `from_pretrained_no_processing()` for a thinner TL wrapper.

### How do I get activations from a 70B+ model?

Three options: (1) **vLLM-Lens** (UK AISI) — fast residual-stream extraction at vLLM throughput, see [`serving-and-activations.md`](serving-and-activations.md). (2) **NDIF** via nnsight remote — free academic compute on hosted big models. (3) **Tensor-parallel nnsight** locally if you have multi-GPU. TransformerLens scales poorly at this size.

---

Last verified: 2026-04-30. TransformerLens 2.x removed `HookedSAETransformer` (now in SAELens). nnsight published at ICLR 2025; remote backend via NDIF. nnterp 1.3.0 (Feb 2026), NeurIPS 2025 Mech Interp Workshop (arXiv:2511.14465). baukit not on PyPI, last commit Feb 2024. circuitsvis 1.43.3 (Dec 2024) under TransformerLensOrg. Captum 0.9.0 (Apr 2026) with LLM attribution. (Citation audit 2026-06: corrected canonical repo paths to `meta-pytorch/captum` and `ndif-team/nnterp`, added the nnsight paper arXiv:2407.14561, and noted LLM attribution predates v0.7.)
