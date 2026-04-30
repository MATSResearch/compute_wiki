# Mechanistic Interpretability Tooling

Libraries for inspecting and intervening on the internals of transformer language models. The big three are **TransformerLens**, **nnsight**, and (for a no-library option) **baukit** + raw PyTorch hooks. **vLLM-Lens** covers the high-throughput case and is documented in [`07_serving_and_activations.md`](07_serving_and_activations.md).

## At a glance: which library?

| If you want… | Use |
|---|---|
| Maximum control, "I want to teach myself transformers from the inside out", small model (≤7B) | **TransformerLens** |
| Any HuggingFace model, exact HF behavior, modern intervention syntax, remote 70B+ models | **nnsight** |
| Just one quick hook, no library | **`register_forward_hook`** + **baukit** |
| Throughput / serving / 70B+ local | **vLLM-Lens** (see [`07_serving_and_activations.md`](07_serving_and_activations.md)) |
| SAE work specifically | **SAELens** (see [`02_saes.md`](02_saes.md)) |

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

Aliases: `nnsight` on PyPI, `ndif-team/nnsight` on GitHub, "the NDIF library", "David Bau's library".

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

Aliases: `nnterp` on PyPI, "nnsight standardized interface".

**What it is.** A thin wrapper around nnsight that gives you TransformerLens-like consistent naming (`model.layers[i].residual_stream`, etc.) across HuggingFace architectures. Published at ICLR 2025.

**When to use it:** You want nnsight's exact-HF-behavior + remote-backend story but TransformerLens's consistent-naming ergonomics.

**When *not* to use it:** You're already comfortable with nnsight's raw module paths; the abstraction is one more thing to debug.

## baukit

Aliases: `baukit`, "David Bau's earlier library", `baukit.TraceDict`.

**What it is.** A small, pre-nnsight library from the Bau lab. The most useful thing in it is `TraceDict`, a context manager that records activations from a list of named submodules.

**When to use it:** Quick one-off hook capture without committing to TransformerLens or nnsight. Works on any `nn.Module`, no architecture knowledge required.

**When *not* to use it:** Modifying activations (rather than just reading) — nnsight is cleaner for that.

```python
# pip install baukit
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

Aliases: `circuitsvis`, "Alan Cooney's attention visualization", "CV".

**What it is.** Interactive attention pattern and neuron-activation visualization, designed for Jupyter. Renders heads as the colored grids you see in mech interp papers.

**When to use it:** You want to look at attention patterns or neuron activations interactively in a notebook.

**When *not* to use it:** You're building a non-Jupyter pipeline (it's notebook-first).

## Captum

Aliases: `captum`, "PyTorch interpretability library", "Meta's interp library".

**What it is.** A general PyTorch interpretability library — saliency, integrated gradients, layer attribution, etc. Useful for non-LM models or feature attribution.

**When to use it:** You're doing classical attribution-style interpretability (saliency, IG) on any PyTorch model, not just transformers.

**When *not* to use it:** Mech-interp-style work on LMs — TransformerLens / nnsight are better fits.

## Cross-references

- For SAE work: [`02_saes.md`](02_saes.md).
- For activation extraction at vLLM throughput: [`07_serving_and_activations.md`](07_serving_and_activations.md).
- For probes built on extracted activations: [`06_probes.md`](06_probes.md).
- For activation steering (uses these libraries as backends): [`05_steering.md`](05_steering.md).

---

Last verified: 2026-04. TransformerLens 2.x removed `HookedSAETransformer` (now in SAELens). nnsight published at ICLR 2025; remote backend via NDIF. nnterp published at OpenReview 2025.
