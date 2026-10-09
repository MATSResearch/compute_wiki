---
tags:
  - interpretability
---

# Mechanistic Interpretability Tooling

Libraries for inspecting and intervening on the internals of transformer language models, plus the **workspace lenses** (J-Lens, R-Lens, J++ Lens) used to read a model's unspoken intermediate variables off its activations. The big three libraries are **TransformerLens**, **nnsight**, and (for a no-library option) **baukit** + raw PyTorch hooks. **vLLM-Lens** covers the high-throughput case and is documented in [`serving-and-activations.md`](serving-and-activations.md).

> **Version alert (2026-10).** TransformerLens **4.0** (2026-09-21) *removed* `HookedTransformer` — `from transformer_lens import HookedTransformer` now raises `ImportError`; use `TransformerBridge`. nnsight **0.8.0rc1** (2026-09-09, pre-release) deprecated `LanguageModel` in favour of `TransformersModel`. SAELens pins `transformer-lens<4`, and circuit-tracer's TransformerLens backend breaks on TL 4.0 (open issue). Details in the sections below.

## At a glance: which library?

| If you want… | Use |
|---|---|
| Maximum control, "I want to teach myself transformers from the inside out", named hooks across architectures | **TransformerLens** (`TransformerBridge`, 3.x/4.x) |
| Any HuggingFace model, exact HF behavior, modern intervention syntax, remote 70B+ models | **nnsight** |
| Read what a model is "thinking" but not saying (unspoken intermediate variables) from activations | **Workspace lenses** — start with the **J++ Lens** (see [Workspace lenses](#workspace-lenses-j-lens-r-lens-j-lens)) |
| Just one quick hook, no library | **`register_forward_hook`** + **baukit** |
| Throughput / serving / 70B+ local | **vLLM-Lens** (see [`serving-and-activations.md`](serving-and-activations.md)) |
| SAE work specifically | **SAELens** (see [`saes.md`](saes.md)) |
| Interventions as first-class saveable objects; DAS; non-transformer architectures | **pyvene** |
| Compare a base model against its finetune | **diffing-toolkit** (see [`model-diffing.md`](model-diffing.md)) |

## TransformerLens

Aliases: `transformer_lens` on PyPI, `TransformerLensOrg/TransformerLens` on GitHub, "TL", "Neel Nanda's library" (originally; now community-maintained, current maintainers Bryce Meyer and Jonah Larson). **`TransformerBridge`** is the current model class (introduced in TL 3.0, 2026-04-17; the only path since TL 4.0, 2026-09-21). `HookedTransformer` is the legacy class, removed in 4.0.

**What it is.** A library that exposes every attention head, MLP layer, and residual-stream activation of a language model through a named hook system (`model.run_with_cache`, `model.run_with_hooks`). Since TL 3.0 this is done by **`TransformerBridge`**: it keeps the real HuggingFace implementation of the model and wraps it with an *architecture adapter* that registers uniform hook points — instead of re-implementing each architecture as the old `HookedTransformer` did. The README lists 15,000+ models across 140+ architecture families.

**When to use it:**
- You're learning mechanistic interpretability and want consistent naming across architectures (`blocks.5.hook_resid_post` still works as an alias of the canonical `blocks.5.hook_out`).
- You're doing classic mech interp: induction heads (Olsson et al. 2022, "In-context Learning and Induction Heads", arXiv:2209.11895), IOI-style circuit analysis (Wang et al. 2022, "Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small", arXiv:2211.00593), attention pattern visualization.
- You need ablation, patching (resample, and **attribution patching** — the fast linear approximation from Syed, Rager & Conmy 2023, "Attribution Patching Outperforms Automated Circuit Discovery", arXiv:2310.10348), and activation arithmetic with a clean API. TL 4.0 also ships analysis tools under `transformer_lens.tools.analysis`: direct logit attribution, attribution patching (node and edge/EAP scoring), direct path patching, `JacobianLens` (see [Workspace lenses](#workspace-lenses-j-lens-r-lens-j-lens)), backward lens, SVD circuits, sparse probing.
- You need gradients (attribution patching, backward hooks, Jacobian-lens fitting): load with `TransformerBridge.boot_transformers(...)`, the transformers backend (the vLLM and Inspect backends have no autograd).

**When *not* to use it:**
- You want exact HuggingFace behaviour with zero abstraction and a deferred-execution syntax → **nnsight**.
- You're working at vLLM scale and need only residual-stream capture or steering → **vLLM-Lens** (see [`serving-and-activations.md`](serving-and-activations.md)). TL 4.0 has its own `RemoteBridge.boot_vllm` for hooks over vLLM, but it cannot give gradients or attention patterns.
- You want SAEs or circuit-tracer *and* TransformerLens together on TL 4.x — **SAELens pins `transformer-lens<4`** (since 6.51.2, 2026-09-24) and circuit-tracer's TransformerLens backend raised an `ImportError` on TL 4.0.0 as of 2026-10 (open issue); stay on `transformer-lens<4` for those workflows (details below and in [`saes.md`](saes.md)).

**Pitfalls (with searchable error symptoms):**
- **`ImportError: cannot import name 'HookedTransformer' from 'transformer_lens'`** (also `HookedTransformerConfig`, `HookedEncoder`, `HookedEncoderDecoder`) — TL 4.0 removed the `Hooked*` model classes. Fix: `TransformerBridge.boot_transformers("gpt2")` and, if you need the old numerics, `bridge.enable_compatibility_mode()`. The same error surfaces *inside other libraries* that subclass `HookedTransformer` (older **SAELens** releases, **circuit-tracer**'s TransformerLens backend): pin `pip install "transformer-lens<4"` or upgrade the library. Because the error is an `ImportError`, `hasattr(transformer_lens, "HookedTransformer")` raises instead of returning False.
- **Numerics changed: the bridge does *not* fold LayerNorm or center weights by default.** `HookedTransformer.from_pretrained` applied `fold_ln`, `center_writing_weights`, `center_unembed` automatically; `TransformerBridge` preserves raw HF weights, so logits and activations match HuggingFace (*not* the old TL). Per the migration guide's table, raw logits differ from old TL output by a per-row constant, and logit lens, direct logit attribution (DLA), KL divergence and cached `hook_resid_*` norms (the gap grows with depth) also differ, unless you call `bridge.enable_compatibility_mode()` after booting; generated text, cross-entropy (CE) loss and argmax/top-k are identical either way. **Method-specific:** DLA wants compatibility mode; `JacobianLens` and backward-lens want *raw* weights — load a separate model for each.
- **Load-time flags moved.** `fold_ln=`, `center_writing_weights=`, `center_unembed=`, `fold_value_biases=` are no longer arguments of the load call; they are arguments of `enable_compatibility_mode(...)`. `move_to_device` and `first_n_layers` were removed.
- **"Model not in `OFFICIAL_MODEL_NAMES`"** (TL 2.x) — gone with `loading_from_pretrained` in 4.0; supported names now live in `transformer_lens.supported_models`. If you are stuck on TL 2.x (`pip install 'transformer_lens~=2.0'`, e.g. Python 3.8/3.9), the old advice applies: `from_pretrained_no_processing()` or fall back to nnsight.
- **Renamed modules.** `transformer_lens.utils` → `transformer_lens.utilities` (same function names, e.g. `get_act_name`); `transformer_lens.train` → `transformer_lens.tools.training`; `HookedTransformerConfig` → `TransformerBridgeConfig`; legacy TL-format checkpoints load via `TransformerBridge.boot_tl_legacy(name)`. `HookedRootModule` and `HookPoint` are **kept** (the supported way to hook your own `nn.Module`).
- **`transformers` floor.** TL 3.3 raised the `transformers` floor to 5.4+; TL 4.0 requires `transformers>=5.9.0` (per the circuit-tracer issue thread). A project pinned to `transformers<=4.57` will silently resolve an older TL (3.2.1 in that thread) rather than 4.x.
- **Hook-name aliases.** Canonical bridge names are `hook_in` / `hook_out`; legacy names (`blocks.0.hook_resid_pre`) are kept as aliases. `hook_mlp_in` fires pre-`ln2` and must be switched on (`bridge.set_use_hook_mlp_in(True)`); `hook_q_input`/`hook_k_input`/`hook_v_input`/`hook_attn_in` need `use_split_qkv_input` / `use_attn_in`.
- **First-token / BOS weirdness.** Many TL workflows skip position 0 because Llama-family models put unusually large activations there. If your patching results look wild at pos 0, that's why.
- **`HookedSAETransformer` ImportError after upgrading to TL 2.x.** Moved to SAELens. `pip install sae-lens` and import from there. (With TL 3+, SAELens also offers `SAETransformerBridge`; see [`saes.md`](saes.md).)
- **Memory blowup with `run_with_cache`.** Caches every named activation by default. Pass `names_filter=lambda name: "hook_resid_post" in name` (or similar) for any non-tiny model.

**One-liner install / first call (TL 3.x / 4.x):**
```python
# pip install transformer_lens
from transformer_lens.model_bridge import TransformerBridge
bridge = TransformerBridge.boot_transformers("gpt2", device="cpu")
bridge.enable_compatibility_mode()   # optional: old HookedTransformer numerics (fold LN, centre weights)
logits, cache = bridge.run_with_cache("Hello world")
```
Gated models (Llama, Gemma, Mistral) need `HF_TOKEN` in the environment. Multi-GPU loading: `boot_transformers(..., n_devices=N)` or `device_map="auto"` / `max_memory=` (mutually exclusive with `device=`). Legacy code you cannot migrate yet: `pip install "transformer-lens<4"` (HookedTransformer works, with a `DeprecationWarning`, through 3.x).

## nnsight

Aliases: `nnsight` on PyPI, `ndif-team/nnsight` on GitHub, "the NDIF library", "David Bau's library". Paper: "NNsight and NDIF: Democratizing Access to Open-Weight Foundation Model Internals" (Fiotto-Kaufman, Bau et al., ICLR 2025, arXiv:2407.14561).

**What it is.** A library that wraps any PyTorch / HuggingFace model in a tracing context where you can read and modify activations using a deferred-execution syntax. The same code runs locally on a small model or remotely on a 405B model hosted by NDIF (the National Deep Inference Fabric).

**Agent-friendly docs.** The nnsight repo (0.8) carries a `CLAUDE.md` plus 105 recipe-style pages under `docs/`, and `ndif-team/skills` ("Teach LLMs to use NNSight with Skills"; verified, pushed 2026-10-08) packages them as agent skills — useful if you drive nnsight from Claude Code.

**Versions (2026-10).** Stable on PyPI is **0.7.0** (2026-05-05: lazy hooks, 10–50% faster traces, `nnsight-serve`). **0.8.0rc1** (2026-09-09, `pip install --pre nnsight`) is a ground-up rewrite of the execution engine (greenlets instead of threads, `TransformersModel`, vLLM CUDA-graph taps, native tensor parallelism); the release notes say *remote execution against NDIF stays on 0.7 until NDIF is upgraded*. Python 3.10–3.14.

**When to use it:**
- Your model is on HuggingFace and you want exact HF behavior with no architecture rewrite.
- You want to intervene on a 70B+ model without owning the GPUs (use NDIF remote backend).
- You like the explicit tracing API: `with model.trace("Hello"): h = model.model.layers[5].output[0].save()`.
- You want a single API across architectures (HF, vLLM via plugin, custom) — in 0.8, vLLM runs *inside* the trace, so the same intervention code works on a served model (see [`serving-and-activations.md`](serving-and-activations.md)).

**When *not* to use it:**
- You want the consistent named-hook namespace TransformerLens provides — nnsight gives you raw module paths (`model.model.layers[5].mlp.down_proj.output`), which differ between architectures.
- You want SAE-specific helpers — use SAELens (works alongside nnsight).
- You need maximum throughput on local GPUs — use vLLM-Lens.

**Pitfalls:**
- **"Module path not found"** — every architecture has different paths. `print(model)` to see the tree, or use `nnterp` (a standardized-interface wrapper, ICLR 2025) to abstract the differences.
- **`.save()` on the wrong tensor.** Inside a trace, intermediate values are proxies; you must `.save()` the ones you want to read after the trace exits. Forgetting to save = `AttributeError` or empty value.
- **Remote NDIF latency.** Each remote forward pass has network round-trip cost. Batch your interventions; don't do per-token loops to a remote model.
- **Memory on long sequences.** Like TransformerLens, saving every position's activation across all layers OOMs fast. Slice positions and layers explicitly.
- **0.8 breaking changes that do not raise** (from the 0.8.0rc1 release notes): (1) **`.source` operation labels shifted** — every assignment in an instrumented forward is now its own operation, so e.g. GPT-2's `attention_interface_0` became `attention_interface_1`; requesting the old label returns the assigned value instead of raising. Print `module.source` and re-check hardcoded labels. (2) A bounded `tracer.iter[:N]` that outruns the generation is **cut short with a warning** and statements after the loop are discarded, so a result can look complete while shorter than the bound (use `min_new_tokens=` on transformers, `min_tokens=`/`ignore_eos=True` on vLLM).
- **0.8 breaking changes that do raise:** `LanguageModel(...)` and `VisionLanguageModel(...)` now warn on construction — use `TransformersModel(repo, task=...)`. `x.save()` / `nnsight.save(x)` **outside a trace now raises** (was a silent no-op); collect per-step values with `xs = nnsight.save([])` then `xs.append(...)`. `tracer.next()` / `module.next()` are gone; `with tracer.iter[...]` / `with tracer.all()` are deprecated for `for step in tracer.iter[...]:`. `model.generator.output` is deprecated for `tracer.result`. `model.generate(...)` now returns token ids; the old decoded-text return moved to `model.pipe(...)`. Reading an activation after the model has run past it raises `OutOfOrderError` (0.7 called this `MissedProviderError: ... Did you call an Envoy out of order?`).
- **Library pins.** `circuit-tracer` on GitHub `main` requires `nnsight>=0.8.0rc1,<0.9`; `nnterp` 1.3.0 declares only `nnsight>=0.6` (untested here against the 0.8 rewrite; see the nnterp section). Mixing the two in one environment is where version-conflict errors will appear.

**One-liner install / first call (nnsight 0.7):**
```python
# pip install nnsight
from nnsight import LanguageModel
model = LanguageModel("meta-llama/Llama-3.2-1B", device_map="auto")
with model.trace("Hello world"):
    h = model.model.layers[5].output[0].save()
print(h.shape)
```

**nnsight 0.8 (pre-release; `pip install --pre nnsight`), from the repo README:**
```python
from nnsight import TransformersModel
model = TransformersModel("openai-community/gpt2", dispatch=True)
with model.trace("The Eiffel Tower is in the city of"):
    model.transformer.h[0].output[:] = 0          # edit a layer's output in place
    hidden = model.transformer.h[6].output.save() # read a hidden state
    logits = model.output.logits.save()
```
A GPT-2 block's `.output` is a plain tensor; some modules (attention) return a tuple, so you index `.output[0]` — `print(model)` or `print(module.source)` shows which. Re-check this after upgrading, because a tuple-vs-tensor mismatch changes shapes without an obvious error.

## nnterp

Aliases: `nnterp` on PyPI, `ndif-team/nnterp` on GitHub (canonical; `butanium/nnterp`, the author Clément Dumas's handle, redirects there), "Clément Dumas's nnsight wrapper", "NDIF nnterp", "nnsight standardized interface".

**What it is.** A thin wrapper around nnsight that gives you TransformerLens-like consistent naming (LLaMA-style `model.layers[i].residual_stream`, attention/MLP submodule paths) across 50+ HuggingFace model variants spanning 16 architecture families. Published at the **Mechanistic Interpretability Workshop, NeurIPS 2025** (arXiv:2511.14465). Latest PyPI 1.3.0 (Feb 2026), actively maintained.

**When to use it:** You want nnsight's exact-HF-behavior + remote-backend story but TransformerLens's consistent-naming ergonomics, especially across many architectures (Llama, Gemma, Qwen, Mistral, Phi, GPT-OSS, etc.).

**When *not* to use it:** You're already comfortable with nnsight's raw module paths; the abstraction is one more thing to debug. **Version caveat (2026-10):** nnterp 1.3.0 (Feb 2026) is still the latest PyPI release and declares `nnsight>=0.6` with no upper bound; a rewrite for the nnsight 0.8 engine ("nnterp 2", `ndif-team/nnterp` PR #62, open on 2026-10-09) removes the 1.x accessors (`layers_output`, `load_model`, …), and `diffing-toolkit` pins `nnterp<2.0` for that reason. nnterp 1.3.0 has not been tested here against nnsight 0.8; if you see import errors after `pip install --pre nnsight`, pin `nnsight<0.8` for nnterp work.

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

## pyvene (and pyreft)

Aliases: `pyvene` on PyPI, `stanfordnlp/pyvene` on GitHub, "the Stanford intervention library", "Wu et al.'s intervention library". Paper: arXiv **2403.07809** / NAACL 2024 System Demonstrations, "pyvene: A Library for Understanding and Improving PyTorch Models via Interventions".

**What it is.** A library where the **intervention is the primitive**. You declare *where* (layer, component, unit — position, head, neuron subset) and *what kind* (swap in a source activation, zero it, add a vector, a learned intervention), and pyvene builds an `IntervenableModel` wrapper around any PyTorch model. Interventions are dicts, so they serialise and can be shared on HuggingFace like weights. Works beyond transformers — the README notes RNNs, ResNets, CNNs, Mamba.

```bash
pip install pyvene
```

Activation patching / interchange intervention, structured verbatim after the repo's basic tutorial:

```python
import pyvene
from pyvene import RepresentationConfig, IntervenableConfig, IntervenableModel
from pyvene import VanillaIntervention

def simple_position_config(model_type, component, layer):
    return IntervenableConfig(
        model_type=model_type,
        representations=[
            RepresentationConfig(
                layer,        # layer
                component,    # e.g. "mlp_output", "attention_input"
                "pos",        # intervention unit
                1,            # max number of units
            ),
        ],
        intervention_types=VanillaIntervention,
    )

base = tokenizer("The capital of Spain is", return_tensors="pt")
sources = [tokenizer("The capital of Italy is", return_tensors="pt")]

config = simple_position_config(type(gpt), "mlp_output", layer_i)
intervenable = IntervenableModel(config, gpt)
_, counterfactual_outputs = intervenable(base, sources, {"sources->base": pos_i})
```

Sweeping `layer_i` × `pos_i` and reading off the probability of the counterfactual token (" Madrid" vs " Rome") is exactly the causal-tracing heatmap in [`research-plots.md`](../engineering/research-plots.md).

**When to use it:**
- Interchange interventions / activation patching where you want the *specification* of the intervention to be a first-class, saveable object rather than a closure buried in a hook.
- Non-transformer or unusual architectures, where no TransformerLens architecture adapter (`TransformerBridge`) exists.
- **Distributed Alignment Search (DAS)** and learned interventions — pyvene ships trainable intervention types, which raw hooks make you build yourself.

**When *not* to use it:**
- Standard mech-interp on a supported model where you want the community's shared vocabulary of hook names — **TransformerLens** is more idiomatic and far more of the published code you'll want to read is written against it.
- You need remote execution on a model too big for your GPU — that's **nnsight**/NDIF.
- A one-off "grab the residual stream at layer 12" — plain PyTorch hooks are three lines.

**pyreft** (`stanfordnlp/pyreft`) is the sibling library for **ReFT — Representation Finetuning** (arXiv **2404.03592**): instead of updating weights (LoRA), you train an intervention on hidden representations, giving a parameter-efficient finetune whose learned object is a *representation edit*. Relevant to safety work as a model-organism method that produces something intrinsically more interpretable than a LoRA — but note its last repo activity was March 2026, so check maintenance before depending on it.

**Pitfalls:**
- **Component names are pyvene's, not TransformerLens's.** `"mlp_output"` / `"attention_input"` here vs `blocks.4.hook_mlp_out` there. Copying a hook name across libraries gives a key error or, worse, an unmatched component. Symptom: interventions that run and change nothing.
- **`{"sources->base": pos_i}` is a position mapping.** Base and source must be tokenised to the same length for a positional swap to mean what you think; different-length prompts misalign silently.
- **Serialised interventions carry a model assumption.** A shared intervention config is only valid for the architecture it was authored against.

## Workspace lenses (J-Lens, R-Lens, J++ Lens)

Aliases: "Jacobian lens", "J-lens", "J-space", "global workspace lens", "workspace lens", "R-lens" (RelP / LRP lens), "J++ lens", "Jacobian Filtering". Code and weights: `anthropics/jacobian-lens` (`jlens`, Anthropic's reference implementation), `safety-research/jpp_lens` (`workspace_lens`, J++ code + eval harness), `koayon/jpp-lenses` and `camilablank/workspace-lenses` and `neuronpedia/jacobian-lens` (pre-fitted lens weights on HuggingFace), `camilablank/workspace-bench` (WorkspaceBench evals), TransformerLens `JacobianLens` (`transformer_lens.tools.analysis`), UK AISI `vllm-lens` examples. Interactive demo: `neuronpedia.org/jlens`.

**What they are.** A *lens* reads an intermediate residual-stream activation `h` at layer ℓ as the vocabulary tokens the model is disposed to say later. The **logit lens** applies the unembedding directly. A **workspace lens** first transports `h` through one fixed linear map per layer — the *averaged Jacobian* `J_ℓ = E[∂h_final / ∂h_ℓ]`, averaged over prompts, source positions and later target positions — then applies the final norm and unembedding: `lens_ℓ(h) = unembed(J_ℓ · h)`. The rows of `W_U · J_ℓ` are the per-token **lens vectors**; they can be used to read out, to probe, and to *write* (patch a lens vector in place of an intermediate concept, e.g. swap "spider" for "ant" and the answer to "legs on the animal that spins webs" flips from 8 to 6). The map is *estimated*, not trained as a network: fitting is a batch of backward passes over a few dozen to a thousand short prompts (about `d_model` backward passes per prompt), and inference is a single matrix multiply per layer. The **J-space** is the set of activations expressible as sparse non-negative combinations of lens vectors (typically k ≤ 25).

**Lineage (all 2026).**
- **J-Lens** — Gurnee, Sofroniew, Pearce, Piotrowski, Kauvar, … Lindsey (Anthropic), *Verbalizable Representations Form a Global Workspace in Language Models*, transformer-circuits.pub/2026/workspace, 2026-07-06. Claim: the J-space behaves like a global workspace — contents are reportable, reusable, selective and causally used for multi-step inference (multi-hop intermediate-swap success 54% Haiku 4.5, 70% Sonnet 4.5, 70% Opus 4.5). The same paper introduces the multi-token **Template Lens** and **Oracle Lens** (below). Neel Nanda's public review (LessWrong, 2026-07-06) replicated the core claims on Qwen3.6-27B (poetry and arithmetic did not replicate) and recommends it as a *hypothesis-generation* tool for audits, less so for validating hypotheses.
- **R-Lens** — camilablank, agam_bhatia, Neel Nanda, *R-lens: Making J-lens More Faithful on Early Layers*, LessWrong, 2026-08-05 (MATS work). Computes the Jacobians with a Layer-wise Relevance Propagation (LRP) backward pass — stop-gradients on RMSNorm denominators and gated-MLP activations — so noise does not compound toward early layers. Forward pass and lens file format unchanged.
- **J++ Lens** — Kola Ayonrinde (Anthropic Fellows) & Jack Lindsey (Anthropic), *J++ Lens: Jacobian Filtering Enables More Faithful Workspace Lenses*, LessWrong, 2026-10-08, https://www.lesswrong.com/posts/nc9dHfcB22JdMzGbr/paper-j-lens-jacobian-filtering-enables-more-faithful . Code `safety-research/jpp_lens` (Apache-2.0; verified: exists, not archived, pushed 2026-10-08), lenses `koayon/jpp-lenses`. A **drop-in replacement for the J-Lens with no extra inference cost** (one linear map per layer, same shape). Three changes: (1) **Jacobian Filtering** — k-means-cluster each layer's activations into E = 8 clusters, average one "expert" Jacobian per cluster, then combine the experts with *learned signed weights* fit on a small dev set so that experts giving incoherent readouts get zero or negative weight; (2) the **Layer-wise Relevance Propagation (LRP) backward pass** from the R-Lens; (3) **Readout Filtering** — drop non-semantic tokens (no letter or digit; 6,116 tokens for Qwen3.6-27B) from the ranked readout.

**Measured gains (J++ post; macro-average of five latent-variable extraction tasks — multihop, multilingual, typo, association, poetry; recall@10 = target appears in the top-10 readout at any of seven equally spaced layers).** On Qwen3.6-27B: J++ **55.2%** vs R-Lens 37.7% vs J-Lens 35.7% (logit lens 31.1%). Across six models (Qwen3.5-9B, Qwen3.6-27B, Gemma 4 31B, Olmo 3 32B, Qwen3.5-122B-A10B, DeepSeek-V4-Flash 284B) the median relative uplift is **+63.5% over J-Lens and +42.2% over R-Lens**, largest on the two biggest models (+98% and +101%). Causal check (intermediate-swap, 67 trials, Qwen3.6-27B): J++ vectors change the answer as intended in **59.7%** of trials vs 49.3% (J) and 50.7% (R) — "at least as causally important". Ablation (Qwen3.6-27B): removing Jacobian Filtering costs 11.7 pp (of the 19.5 pp total gain over J), removing LRP 6.6 pp, removing Readout Filtering 2.9 pp. Fitting cost: ≈9 H200 GPU-hours for all 63 layers of Qwen3.6-27B (64 WikiText-103 sequences × 128 tokens, first 16 positions skipped), about 7% more than a J-Lens fit plus a one-off clustering step. These are the authors' own numbers on their own harness, from a non-peer-reviewed LessWrong post published the day before this section was written; do not compare them with numbers from other papers' datasets.

### Which lens should I use? (decision table)

| Lens | What it reads out | Cost | Use it when | Do *not* use it when |
|---|---|---|---|---|
| **Logit lens** | Unembedding applied directly to the residual stream (nostalgebraist) | None, ~10 lines | Quick look at *late* layers; sanity baseline | Early/middle layers of large models (basis drift); median recall@10 31% vs 55% for J++ in the J++ post |
| **Tuned lens** (`tuned-lens`, Belrose et al., arXiv:2303.08112) | Per-layer learned affine map trained to match the final next-token distribution | Training run per model; no support for Llama-3 / Gemma-2/3 / Qwen-3 in the PyPI release (see [`probes.md`](probes.md)) | "What is the model *predicting* at layer ℓ" | Surfacing *intermediate* variables — Gurnee et al. report it tends to skip past intermediate computation to the answer |
| **J-Lens** (Anthropic) | Single tokens, via the averaged Jacobian | ~100 prompts usable; paper used 1,000; Nanda used 25 (n = 10 "almost as good") | You need the exact Anthropic protocol or a released J-lens is all you have | A J++ lens exists for your model (prefer it), or early layers matter (J-Lens readouts are mostly coherent only in the latter half of the network) |
| **R-Lens** | Same as J-Lens; LRP backward pass | ≈ J-Lens fit cost (the R-lens post calls its backward-pass changes "low-overhead") | A released R-lens exists for your model and J++ does not (`camilablank/workspace-lenses`: Qwen3.5-4B/9B/27B/122B-A10B, Qwen3.6-27B/35B-A3B, Gemma-3-27B-it, DeepSeek-V4-Flash) | Superseded by J++ wherever a J++ lens exists; the vllm-lens R-lens fitter is dense-model only (MoE fails fast) |
| **J++ Lens** | Same as J-Lens, with Jacobian Filtering + LRP + Readout Filtering | ≈ J-Lens + 7%, plus clustering; no extra inference cost | **Default for single-token readouts of unspoken intermediate variables** on open models 9B–284B; early-layer readouts; monitoring prototypes | Multi-token concepts, multi-digit numbers on digit-tokenizing models (Qwen), planned-rhyme / poetry (≤5% for every lens), or as a validated lie/intent detector (see pitfalls) |
| **Template Lens** (Gurnee appendix) | Ranked words/phrases from a fixed ~12,700-word dictionary, via per-word linear discriminant directions | A few hundred forward passes per word; vocabulary fixed in advance | You need multi-token words in a known dictionary, or steering/swap vectors for them | You want a faithful J-space readout — it is closer to a tuned lens and can skip to the answer; some words appear spuriously |
| **Oracle Lens** (Gurnee appendix; checkpoint `agu18dec/olens_and_ar` for Qwen3.6-27B) | Free-form phrases from a fine-tuned model, trained to reconstruct the activation | Fine-tune two auxiliary models + RL; explains ~31% of whitened variance | Single tokens are not expressive enough (compositional or relational content) | You cannot afford the training; you need guaranteed no confabulation |
| **Natural Language Autoencoder, NLA** (Anthropic, transformer-circuits.pub/2026/nla, May 2026; `kitft/natural_language_autoencoders`) | A paragraph of text per activation (activation verbalizer + reconstructor, jointly trained with RL) | Released AV/AR pairs for Qwen2.5-7B, Gemma-3-12B/27B, Llama-3.3-70B; hosted at `neuronpedia.org/nla`; expensive to train | You want an expressive hypothesis generator and can verify claims against the model's behaviour | You need trustworthy factual specifics — WorkspaceBench found nearly every NLA readout contained a claim contradicted by the model's own output |
| **Activation Oracle, AO** (Karvonen et al., arXiv:2512.15674) | Answers to natural-language questions about activations | A fine-tuned oracle model; see [`welfare-introspection.md`](../alignment-science/welfare-introspection.md) | Targeted questions about a few tokens' activations | Single-token inputs or one sample: Karvonen's 2026-09-28 tips are to pass activations from many tokens, take a consensus of ~10 samples at temperature 1, and score binary questions with AUC (area under the ROC curve) rather than accuracy |
| **SAE, Sparse Autoencoder** (see [`saes.md`](saes.md)) | Descriptions of the most active dictionary features | Pretrained SAEs exist for some models | You want named, reusable features across many prompts | You want a *workspace* readout — SAEs are not targeted at the workspace and quality depends on label accuracy |
| **Patchscopes** (Ghandeharioun et al., arXiv:2401.06102) | Patch an activation into a target prompt and let the model describe it | One forward pass per query | Flexible, training-free multi-token description | You need a calibrated, comparable score across layers |

### How do I read a J++ / J / R lens on my model?

Use a published lens when one exists — fitting is the expensive part. `neuronpedia/jacobian-lens` (Apache-2.0) hosts J-lenses for 40 open models (Gemma 2/3/4, Qwen 3/3.5/3.6, Llama 3.1/3.3, OLMo 3, gpt-oss-20b, …), J++ lenses for nine (Qwen3.6-27B, Qwen3.5-9B, Gemma 4 31B, Olmo 3 32B, Qwen3.5-122B-A10B, DeepSeek-V4-Flash, plus Neuronpedia-fitted Qwen3.5-0.8B/2B and Qwen3-4B) and Oracle lenses for four Qwen models; `koayon/jpp-lenses` holds the authors' six J++ files. Lens files are `torch.save` dicts `{J: {layer: [d_model, d_model]}, source_layers, d_model, n_prompts, provenance}`, loadable with `torch.load(path, weights_only=True)`.

```python
# J++ repo quickstart (safety-research/jpp_lens; uv + Python 3.12; Qwen3.6-27B bf16 needs ~54 GB GPU memory)
import torch as t
from workspace_lens import get_hf_model
from workspace_lens.lenses.base_lens import BaseLens

lens = BaseLens.from_pretrained("koayon/jpp-lenses", filename="qwen3.6-27b/lens.pt")
model = get_hf_model("Qwen/Qwen3.6-27B", attn_implementation="sdpa")
prompt = "Fact: The number of legs on the animal that spins webs is"
lens_logits, model_logits, input_ids = lens.apply(
    model, prompt, layers=[16, 32, 48], token_positions_for_residuals=[-1])
for layer, logits_1V in lens_logits.items():
    print(layer, [model.tokenizer.decode([i]) for i in logits_1V[0].topk(10).indices.tolist()])
```
Apply Readout Filtering yourself by masking `lens_evals.readout_evals.readout_eval_items.non_semantic_token_ids` before ranking (the repo's `scripts/quickstart.py` shows how; `--no-readout-filter` ranks the full vocabulary).

In TransformerLens 4.x: `lens = JacobianLens.from_pretrained("gemma-2-2b", model=bridge)` (from `transformer_lens.tools.analysis`), then `lens.readout(bridge, prompt, top_k=10)` or `lens.decompose(...)` for the sparse J-space coordinates. It needs a *fresh, raw-weights* `TransformerBridge` (no `enable_compatibility_mode()`), and `lens.validate_model(model)` checks the artifact matches. TL's docs also give a sharded fit-and-merge recipe (`JacobianLens.fit` + `JacobianLens.merge`; "around 100 prompts of 128 tokens gives a usable first fit"). Whether TL's loader reads the J++ `.pt` files is unverified here.

For models served with vLLM, UK AISI's `vllm-lens` (v1.2.0+) ships `examples/jacobian_lens.py` (live readout on served residuals), `jacobian_lens_chat.py` (hover-over-token readout chat page) and `jacobian_lens_fit.py` (fitting runs in a separate prime-rl/torchtitan environment because it needs the backward pass; `--rules lrp`, added in v1.3.0, fits an R-lens). See [`serving-and-activations.md`](serving-and-activations.md).

### How do I evaluate a workspace lens? (WorkspaceBench)

`camilablank/workspace-bench` (MIT; verified pushed 2026-09-24) — Blank, Bhatia, Ong, Nanda, *WorkspaceBench: Evaluating Interpretability Methods for the Global Workspace*, LessWrong, 2026-09-23 (MATS). 3,356 questions across 27 eval families (basic readout, multihop, directed modulation, chained arithmetic, buggy code, agentic misalignment, jailbreak recognition, association, relational multihop, moral rationale, plus a **hallucination eval**), built for Qwen3.6-27B; items are filtered so the model answers correctly without chain of thought and the intermediate never appears in the prompt. `uv run wsbench produce family=multihop method=jlens out=...` generates readouts (methods `logit_lens | jlens | rlens | olens | nla`), `wsbench judge` scores them with an LLM judge (Gemini Flash via OpenRouter; two families pinned to Claude and six scored by regex), `wsbench report` prints the table beside two floors — a *lucky-guess* baseline and a *prompt-only* baseline (an LLM reasons from the prompt alone, which is strong because many tasks are inferable from text). Use a judge at the same capability level or better — the authors found weaker or regex judges let false positives through. Single-token readouts are first summarised into concepts by an LLM before judging. It needs `OPENROUTER_API_KEY` / `ANTHROPIC_API_KEY`; ports to other models need re-deriving read positions.

### Pitfalls (with searchable symptoms)

- **J-lens target layer: "readouts are mostly Chinese tokens on English text" / "one direction dominates every layer".** About 80% of 78 publicly released J-lenses target the *final* layer, though Anthropic's own paper used the *penultimate* layer for its Sonnet experiments (appendix: including the last layer "can sometimes increase the number of noisy artifacts"). On DeepSeek-V3 a final-layer lens inherits a language-separating direction from the last block (≈46% of mid-depth readouts on English text were majority-Chinese; ≈3% with a penultimate target). Check the target layer in a lens's provenance; if you fit your own, compare final vs penultimate and look at the top singular direction of each layer's Jacobian (Kaley Brauer, LessWrong, 2026-09-25 — single-model case study).
- **Token-frequency offset.** J- and R-lens scores carry a context-independent offset correlated with log token frequency (Spearman 0.48 at mid-depth on Qwen3.5-4B in one study); subtracting it directly degraded readouts 3.5–12×, while z-scoring against base-model variance helped on a secret-word (taboo organism) task — 0.805 vs 0.665 leave-one-out accuracy (against the published protocol, re-run by the author) on Gemma-2-9B-it, a point estimate on n = 20 words (p ≈ 0.19), so "calibration helps" is suggestive, not established (Ameya Panchal, LessWrong, 2026-09-17).
- **Attention-sink positions and outlier prompts.** Skip the first positions when fitting (16 in J++, 4 in Nanda's replication) and pre-filter fit prompts whose Jacobian norm exceeds ~5× the median; on DeepSeek-V3 four prompts carried 84% of the summed Jacobian norm and the lens read out a space or hyphen as top token for most inputs.
- **MoE (Mixture-of-Experts) routing.** Single-prompt Jacobians depend on what else is in the batch (38% of token positions changed experts between batch 1 and batch 64 on DeepSeek-V3); averaged readouts agreed ~95% top-1. J++ freezes expert-routing weights (and the manifold-constrained hyper-connection, mHC, mixing coefficients of DeepSeek-V4-Flash) in its LRP pass.
- **Compare lenses fitted on the same data and budget.** The J++ authors found the *released* J-lens for Qwen3.6-27B scored worse than their own refit, so for that model they refit J and R lenses with identical data and budget for the headline comparison (the other five models use released J-lenses; R-lenses are released ones for three models and self-fitted for Gemma 4 31B and Olmo 3 32B). A "better lens" that differs in fit data is not a better method.
- **Single-token and tokenizer limits.** Readouts are bags of single tokens: no word order ("thief chases policeman" vs the reverse), and multi-digit numbers are invisible on digit-by-digit tokenizers (Qwen) — J++ could not evaluate arithmetic on Qwen models. A model that shortcuts to the answer without an intermediate variable gives no lens anything to find.
- **Causal evidence is weaker on open models than on Claude.** Mirella Zeisler (LessWrong, 2026-09-28) replicated the multi-hop intermediate-swap experiment on Qwen3.6-27B and Gemma-3-27B-it: top-1 flip rates for J-lens intermediate swaps were 6–11% (Anthropic reports 54–70% on Claude), and swapping the *counterfactual answer* usually beat swapping the intermediate, as in Nanda's review. Do not treat "lens vector changes the answer" as proof the J-space is the model's workspace; compare against an answer-swap control. (R-lens matched J-lens in three of four conditions.)
- **Monitoring claims need baselines.** Two unreviewed single-model pilots found J-space readouts tracked *topics* rather than intent — a J-lens separated guideline-sensitive prompts from controls at AUC 0.97 on proper nouns but 0.55 pooled, and belief-injection fine-tuning *raised* the conflict signal (Melchior de Polignac, 2026-08-11, DeepSeek-R1-Distill-Qwen-14B) — and added no discrimination over the transcript for reward-hacking audits (Kartikay Luthra, 2026-09-16, Qwen3-8B). Authors of the J++ post motivate lenses for eval-awareness and unverbalised-scheming monitoring but do not test it. Always report the transcript-only and prompt-only baselines.
- **`git clone https://github.com/koayon/jpp_lens` 404s.** The J++ README's install line points at `koayon/jpp_lens`; the repository that exists (verified) is `safety-research/jpp_lens`. `anthropics/jacobian-lens` is marked "reference implementation, not maintained, not accepting contributions" and is `pip install -e .`, not on PyPI.

**Related:** the plotting recipes for lens figures (pass@10 vs layer, per-layer gradient norm, expert-vs-pooled bars, ablation curves) are in [`research-plots.md`](../engineering/research-plots.md#j-lens-r-lens-and-j-lens-reading-the-global-workspace).

## Cross-references

- For SAE work: [`saes.md`](saes.md).
- For activation extraction at vLLM throughput: [`serving-and-activations.md`](serving-and-activations.md).
- For probes built on extracted activations: [`probes.md`](probes.md).
- For activation steering (uses these libraries as backends): [`steering.md`](steering.md).

---

## Common questions

### Is TransformerLens still maintained?

Yes. `TransformerLensOrg/TransformerLens` on GitHub is actively maintained (maintainers Bryce Meyer and Jonah Larson; releases through 4.1.0 on 2026-09-28; PyPI `transformer_lens` 4.0.0 on 2026-09-21). TL 3.0 (2026-04-17) introduced `TransformerBridge`; **TL 4.0 removed `HookedTransformer`** and the other `Hooked*` classes. Bug fixes for the legacy classes continue only on the 3.x branch. The `HookedSAETransformer` was moved out of TransformerLens 2.0 into **SAELens**, which also offers `SAETransformerBridge` for TL 3+ and currently pins `transformer-lens<4`.

### TransformerLens or nnsight for a beginner?

If you're learning mech interp from scratch, start with **TransformerLens** (`TransformerBridge`) for the consistent named-hook namespace (`blocks.5.hook_resid_post`) and the ARENA tutorials, which are written in TransformerLens (if a tutorial's code imports `HookedTransformer`, pin `transformer-lens<4` to run it unchanged). If you want exact HuggingFace behavior, a deferred-execution trace syntax, or to scale to remote 70B+ models, use **nnsight**.

### Why do TransformerLens logits differ slightly from HuggingFace?

Old `HookedTransformer` applied extra processing by default — folding LayerNorm into adjacent weights, centering writing weights, centering the unembed. In TL 3.x/4.x, `TransformerBridge` preserves raw HuggingFace weights by default, so logits and activations *match HuggingFace* and differ from old TL by per-row constants. Call `bridge.enable_compatibility_mode()` to reproduce the old numerics (needed for direct logit attribution and for comparing with old TL results); skip it for Jacobian-lens fitting and backward-lens.

### How do I get attention patterns?

In TransformerLens: `_, cache = model.run_with_cache(prompt, names_filter=lambda n: "pattern" in n)` then `cache["blocks.5.attn.hook_pattern"]`. For visualization, use `circuitsvis` in a Jupyter notebook. In nnsight, access `model.model.layers[5].self_attn.attention_weights.save()` (path varies by architecture). Under vLLM, attention patterns are not materialized by the fused kernels; vLLM-Lens v1.3.0 captures post-RoPE Q/K and reconstructs the matrix offline (see [`serving-and-activations.md`](serving-and-activations.md)).

### Does TransformerLens support [latest model]?

Since TL 3.0 the bridge wraps the real HuggingFace implementation, so support is far broader than the old hand-ported list: the README states 15,000+ models across 140+ architecture families (inventory in `transformer_lens/tools/model_registry/data/supported_models.json`; names in `transformer_lens.supported_models`). A brand-new architecture may still need an architecture adapter — the repo ships an adapter-development guide. If yours isn't supported, fall back to **nnsight** (works with any HF model out of the box).

### How do I get activations from a 70B+ model?

Four options: (1) **vLLM-Lens** (UK AISI) — fast residual-stream extraction at vLLM throughput, see [`serving-and-activations.md`](serving-and-activations.md). (2) **NDIF** via nnsight remote — free academic compute on hosted big models (remote execution stays on nnsight 0.7 until NDIF upgrades). (3) **nnsight 0.8** local with `VLLM(..., taps=[...])` or tensor-parallel `TransformersModel`. (4) TransformerLens 4's `RemoteBridge.boot_vllm` (capture plus declarative interventions, no gradients). Plain TransformerLens/`boot_transformers` scales poorly at this size.

### Which lens should I use to read what a model is "thinking" but not saying?

For single-token readouts of unspoken intermediate variables on open models, the **J++ Lens** (Ayonrinde & Lindsey, 2026-10-08) currently has the best reported numbers (55.2% recall@10 on Qwen3.6-27B vs 37.7% R-Lens vs 35.7% J-Lens; code `safety-research/jpp_lens`, lenses `koayon/jpp-lenses`); fall back to the **R-Lens** or **J-Lens** when no J++ lens exists for your model. Use a multi-token reader (Template Lens, Oracle Lens, natural language autoencoder) only when single tokens cannot express the content, and verify any text it produces. See the decision table in [Workspace lenses](#workspace-lenses-j-lens-r-lens-j-lens).

### What is the J++ Lens (Jacobian Filtering)?

A drop-in improvement to Anthropic's J-Lens (a per-layer averaged-Jacobian readout of a model's workspace representations). It clusters each layer's activations (k-means, 8 clusters), averages one Jacobian per cluster, learns weights that down-weight clusters giving noisy readouts (*Jacobian Filtering*), computes the Jacobians with a Layer-wise Relevance Propagation backward pass (as in the R-Lens), and drops non-semantic tokens from the readout (*Readout Filtering*). Inference cost is identical to the J-Lens. Limits: single tokens only, tokenizer-dependent, poetry-planning recall ≤5% for every lens. Full details above.

---

Last verified: 2026-10. TransformerLens 2.x removed `HookedSAETransformer` (now in SAELens). nnsight published at ICLR 2025; remote backend via NDIF. nnterp 1.3.0 (Feb 2026), NeurIPS 2025 Mech Interp Workshop (arXiv:2511.14465). baukit not on PyPI, last commit Feb 2024. circuitsvis 1.43.3 (Dec 2024) under TransformerLensOrg. Captum 0.9.0 (Apr 2026) with LLM attribution. (Citation audit 2026-06: corrected canonical repo paths to `meta-pytorch/captum` and `ndif-team/nnterp`, added the nnsight paper arXiv:2407.14561, and noted LLM attribution predates v0.7. Additions 2026-06: cited the mech-interp methods named in the TransformerLens bullets — induction heads (Olsson et al. 2209.11895), IOI (Wang et al. 2211.00593), attribution patching (Syed et al. 2310.10348); all verified via arXiv.) (Additions 2026-08: pyvene — `pyvene` on PyPI, arXiv 2403.07809, example structured after the repo's Basic_Intervention tutorial — and its sibling pyreft (ReFT, arXiv 2404.03592; last repo activity March 2026).) (Additions 2026-10: TransformerLens 3.0/4.0 `TransformerBridge` migration — `HookedTransformer` removed in 4.0.0 (PyPI 2026-09-21; GitHub 4.1.0 2026-09-28), verified from the repo README, `migrating_to_v3.md`/`migrating_to_v4.md`, `drivers.md` and PyPI release dates; SAELens `<4` pin (v6.51.2) and the circuit-tracer issue #115 TL-4 breakage verified on GitHub; nnsight 0.7.0 / 0.8.0rc1 release notes and README; new **Workspace lenses** section — J-Lens (Gurnee et al., transformer-circuits.pub/2026/workspace, 2026-07-06; `anthropics/jacobian-lens`), R-Lens (LessWrong nv8oedrnLXKRzNEL9, 2026-08-05), J++ Lens (Ayonrinde & Lindsey, LessWrong nc9dHfcB22JdMzGbr, 2026-10-08; `safety-research/jpp_lens`, `koayon/jpp-lenses`), WorkspaceBench (`camilablank/workspace-bench`, LessWrong Zeg2JztbdhguL48uH, 2026-09-23), NLA (`kitft/natural_language_autoencoders`), pitfalls from LessWrong posts Adb55vLqt33LEyBfz, Qe3jdphWCg9kny3e5, pnDjvdo6cX2H7Ddsy, GZCMmCHZiF8vhsczr, 69fachkoAs2ZHeSst; GitHub repos and HuggingFace lens repos verified via `gh api` / HF API, arXiv IDs 2303.08112, 2401.06102, 2512.15674 verified via abs pages. J++ numbers are from the authors' non-peer-reviewed post.)
