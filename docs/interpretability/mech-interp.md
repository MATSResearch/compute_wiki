---
tags:
  - interpretability
---

# Mechanistic Interpretability Tooling

Libraries for inspecting and intervening on the internals of transformer language models, plus the **workspace lenses** (J-Lens, R-Lens, J++ Lens) used to read a model's unspoken intermediate variables off its activations. The big three libraries are **TransformerLens**, **nnsight**, and (for a no-library option) **baukit** + raw PyTorch hooks. **vLLM-Lens** covers the high-throughput case and is documented in [`serving-and-activations.md`](serving-and-activations.md).

> **Version alert (as of 2026-10-20).** TransformerLens **4.0** (2026-09-21) *removed* `HookedTransformer` — `from transformer_lens import HookedTransformer` now raises `ImportError`; use `TransformerBridge`. The current release is **4.2.0** (2026-10-10). nnsight **0.8.0** (2026-10-16) and **0.8.1** (2026-10-20) are now the stable PyPI releases, so a plain `pip install nnsight` gets the rewrite: `LanguageModel` warns (use `TransformersModel`), `.save()` outside a trace raises, `tracer.next()` is gone and `generate` returns token ids — pin `nnsight<0.8` for 0.7 code. SAELens (6.54.12, 2026-10-20) still pins `transformer-lens<4`, and circuit-tracer's TransformerLens backend breaks on TL 4.0 (issue #115, open). Agent skill packs written before these releases (for example Orchestra's mech-interp skills, below) still teach the removed APIs. Details in the sections below.
>
> **Hook-point trap on Gemma 2/3/4 and OLMo 2/3 (sandwich-norm models).** "MLP output" names two different tensors on these models: the raw MLP module output, and the post-norm *residual contribution*. Gemma Scope MLP SAEs read the contribution. See [The sandwich-norm hook trap](#the-sandwich-norm-hook-trap-gemma-234-olmo-23).

## At a glance: which library?

| If you want… | Use |
|---|---|
| Maximum control, "I want to teach myself transformers from the inside out", named hooks across architectures | **TransformerLens** (`TransformerBridge`, 3.x/4.x) |
| Any HuggingFace model, exact HF behavior, modern intervention syntax, remote 70B+ models | **nnsight** |
| Read what a model is "thinking" but not saying (unspoken intermediate variables) from activations | **Workspace lenses** — start with the **J++ Lens** (see [Workspace lenses](#workspace-lenses-j-lens-r-lens-j-lens)) |
| Just one quick hook, no library | **`register_forward_hook`** + **baukit** |
| Throughput / serving / 70B+ local | **vLLM-Lens** (see [`serving-and-activations.md`](serving-and-activations.md)) |
| One capture-and-steer API on HF eager *and* vLLM, with hook names standardized across architectures (Neuronpedia's engine) | **interp-engine** (see [`serving-and-activations.md`](serving-and-activations.md#interp-engine-neuronpedias-inference-engine)) |
| Which input tokens drove this output? (saliency, integrated gradients, AttnLRP) | See [Attribution](#attribution-which-tokens-or-components-drove-this-output) — **Captum**, **inseq**, **LXT** |
| SAE work specifically | **SAELens** (see [`saes.md`](saes.md)) |
| Interventions as first-class saveable objects; DAS; non-transformer architectures | **pyvene** |
| Compare a base model against its finetune | **diffing-toolkit** (see [`model-diffing.md`](model-diffing.md)) |
| Find a task circuit (edges between heads/MLPs) and score its faithfulness | **EAP-IG** (`hannamw/EAP-IG`), scored on **MIB** (see [Circuit discovery](#circuit-discovery-and-how-to-evaluate-it-eap-ig-mib-causal-abstraction)); **MAttr** for a full ranking over all sparsities; **CircuitKIT** for discover → evaluate → prune → export in one pipeline |
| Let an LLM agent run interpretability experiments, or benchmark one | See [Interpretability agents](#automated-interpretability-and-interpretability-agents) (MAIA, Predictive Concept Decoders, Seer, SAEScientist-Bench, CHIVE) |
| Check whether an interpretability tool beats just reading the transcript | **CHIVE** (`adamkarvonen/chive`; see [Interpretability agents](#automated-interpretability-and-interpretability-agents)) |
| A cheap analogue domain with crisp ground truth (chess transformers) | **chessformer_lens** (see [Analogue domains](#analogue-domains-chess-transformers-chessformer_lens)) |
| A live competition or open challenge to test a method against | See [Live challenges](#live-challenges-as-of-2026-10-14) (AIMO Interpretability Challenge, ARC White-Box Estimation, MIB leaderboard) |
| Interpret through loss-landscape geometry or training dynamics instead of activations | **devinterp** (see [`slt-devinterp.md`](slt-devinterp.md)) |

## TransformerLens

Aliases: `transformer_lens` on PyPI, `TransformerLensOrg/TransformerLens` on GitHub, "TL", "Neel Nanda's library" (originally; now community-maintained, current maintainers Bryce Meyer and Jonah Larson). **`TransformerBridge`** is the current model class (introduced in TL 3.0, 2026-04-17; the only path since TL 4.0, 2026-09-21). `HookedTransformer` is the legacy class, removed in 4.0.

**What it is.** A library that exposes every attention head, MLP layer, and residual-stream activation of a language model through a named hook system (`model.run_with_cache`, `model.run_with_hooks`). Since TL 3.0 this is done by **`TransformerBridge`**: it keeps the real HuggingFace implementation of the model and wraps it with an *architecture adapter* that registers uniform hook points — instead of re-implementing each architecture as the old `HookedTransformer` did. The README lists 15,000+ models across 140+ architecture families.

**When to use it:**
- You're learning mechanistic interpretability and want consistent naming across architectures (`blocks.5.hook_resid_post` still works as an alias of the canonical `blocks.5.hook_out`).
- You're doing classic mech interp: induction heads (Olsson et al. 2022, "In-context Learning and Induction Heads", arXiv:2209.11895), IOI-style circuit analysis (Wang et al. 2022, "Interpretability in the Wild: a Circuit for Indirect Object Identification in GPT-2 small", arXiv:2211.00593), attention pattern visualization.
- You need ablation, patching (resample, and **attribution patching** — the fast linear approximation from Syed, Rager & Conmy 2023, "Attribution Patching Outperforms Automated Circuit Discovery", arXiv:2310.10348), and activation arithmetic with a clean API. TL 4.0 also ships analysis tools under `transformer_lens.tools.analysis`: direct logit attribution, attribution patching (node and edge/EAP scoring), direct path patching, `JacobianLens` (see [Workspace lenses](#workspace-lenses-j-lens-r-lens-j-lens)), backward lens, SVD circuits, sparse probing.
- You need gradients (attribution patching, backward hooks, Jacobian-lens fitting): load with `TransformerBridge.boot_transformers(...)`, the transformers backend (the vLLM and Inspect backends have no autograd).

**New in TransformerLens 4.1 (2026-09-28) and 4.2 (2026-10-10)** (release notes and `docs/source/content/analysis_tools.md` / `sparse_probing.md`, read 2026-10-14):
- **Built-in logit lens (4.2).** `logit_lens(model, prompt)` or `cache.logit_lens()` reads every entry of the accumulated residual stream through the model's own `ln_final` (statistics recomputed), `W_U`, `b_U` and the adapter's output transform (Gemma-style softcap, Cohere logit scale); its final entry equals the model's logits on a raw bridge. `targets=` gives per-layer rank trajectories (`result.rank_trajectory(" Paris")`), `top_k=` / `vocab=` restrict the output, and `logit_readout` applies the same kernel to any `d_model` vector (a head output, steering direction or SAE decoder column). In compatibility mode `center_unembed` shifts logits by a per-position constant, so the docs say to compare `return_type="log_probs"` or ranks across processing modes, not raw logits. Rejected: encoder-only and encoder-decoder bridges, quantized unembeddings.
- **Leakage-safe k-sparse probing (4.1; tie-aware `roc_auc` / `average_precision` added in 4.2).** `fit_sparse_probe` and `sweep_sparse_probe` with random-coordinate and label-shuffle controls — see [`probes.md`](probes.md#sparse-probing-in-transformerlens-41-fit_sparse_probe).
- **Unreduced activation patching (4.2):** per the analysis-tools guide, the metric returns a scalar by default and a `[batch]` tensor under `reduce="mean"` or `"none"`, and per-example values are stored (`cells × batch` floats per metric) so statistics can be computed after the sweep without extra forwards.
- **Bridge fixes worth knowing if you produced numbers before 4.2:** `rmsnorm_uses_offset` set on the Qwen3.5, Qwen3Next and Nemotron adapters; Cohere/Cohere2 rotated with their own RoPE convention; HunYuan QK-norm applied after RoPE; `get_caching_hooks` keeps the batch dimension when batch > 1 (all from the 4.2.0 release notes). On those architectures it is worth re-running a result that came from a 4.0/4.1 bridge.

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

**Third-party mech-interp skill packs can be stale.** `Orchestra-Research/AI-Research-SKILLs` (MIT, 13.5k stars, release v1.7.2 of 2026-06-16; Claude Code marketplace install `/plugin marketplace add orchestra-research/AI-research-SKILLs`, then `/plugin install mechanistic-interpretability@ai-research-skills`) ships four mech-interp skills: TransformerLens, SAELens, pyvene and nnsight. As read on 2026-10-14, its TransformerLens and SAELens skills build models with `from transformer_lens import HookedTransformer` (removed in TL 4.0) and its nnsight skill uses `LanguageModel` (deprecated in nnsight 0.8). An agent following them on a fresh install will hit `ImportError: cannot import name 'HookedTransformer'` unless it pins `transformer-lens<4`. Worth checking a skill's code against the installed library version before letting an agent run it; `ndif-team/skills` is maintained by the nnsight authors.

**Versions (2026-10-20).** Stable on PyPI is **0.8.1** (2026-10-20); **0.8.0** (2026-10-16) promoted the rewrite that shipped as 0.8.0rc1 (2026-09-09) to a normal release, so unpinned installs now get it. 0.8 is a ground-up rewrite of the execution engine (greenlets instead of threads, `TransformersModel`, vLLM CUDA-graph taps, native tensor parallelism; the 0.8.0 notes add `import nnsight` dropping from 7.6 s to 1.6 s, support for the transformers 5.19 tensor/expert-parallel rework, and vLLM engines defaulting to prefix caching off). 0.8.1 carries `trust_remote_code` and the attention implementation with every remote request. The previous line is **0.7.0** (2026-05-05: lazy hooks, 10–50% faster traces, `nnsight-serve`); pin `pip install "nnsight<0.8"` for code written against it. The 0.8.0rc1 notes said *remote execution against NDIF stays on 0.7 until NDIF is upgraded*; the 0.8.0/0.8.1 notes do not repeat that caveat and add remote-job features, but whether NDIF's servers accept 0.8 clients was not confirmed here — check `nnsight.net/status` or the NDIF forum before switching remote code. Python 3.10–3.14.

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
- **0.8 breaking changes that do not raise** (from the 0.8.0rc1 release notes; they apply to the stable 0.8.0/0.8.1 releases): (1) **`.source` operation labels shifted** — every assignment in an instrumented forward is now its own operation, so e.g. GPT-2's `attention_interface_0` became `attention_interface_1`; requesting the old label returns the assigned value instead of raising. Print `module.source` and re-check hardcoded labels. (2) A bounded `tracer.iter[:N]` that outruns the generation is **cut short with a warning** and statements after the loop are discarded, so a result can look complete while shorter than the bound (use `min_new_tokens=` on transformers, `min_tokens=`/`ignore_eos=True` on vLLM).
- **0.8 breaking changes that do raise:** `LanguageModel(...)` and `VisionLanguageModel(...)` now warn on construction — use `TransformersModel(repo, task=...)`. `x.save()` / `nnsight.save(x)` **outside a trace now raises** (was a silent no-op); collect per-step values with `xs = nnsight.save([])` then `xs.append(...)`. `tracer.next()` / `module.next()` are gone; `with tracer.iter[...]` / `with tracer.all()` are deprecated for `for step in tracer.iter[...]:`. `model.generator.output` is deprecated for `tracer.result`. `model.generate(...)` now returns token ids; the old decoded-text return moved to `model.pipe(...)`. Reading an activation after the model has run past it raises `OutOfOrderError` (0.7 called this `MissedProviderError: ... Did you call an Envoy out of order?`).
- **Library pins.** `circuit-tracer` on GitHub `main` requires `nnsight>=0.8.0rc1,<0.9`; `nnterp` 1.3.0 declares only `nnsight>=0.6` (untested here against the 0.8 rewrite; see the nnterp section). Mixing the two in one environment is where version-conflict errors will appear.

**One-liner install / first call (nnsight 0.7; pin it, since an unpinned install now gets 0.8):**
```python
# pip install "nnsight<0.8"
from nnsight import LanguageModel
model = LanguageModel("meta-llama/Llama-3.2-1B", device_map="auto")
with model.trace("Hello world"):
    h = model.model.layers[5].output[0].save()
print(h.shape)
```

**nnsight 0.8 (the current stable release; `pip install nnsight`), from the repo README:**
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

**When *not* to use it:** You're already comfortable with nnsight's raw module paths; the abstraction is one more thing to debug. **Version caveat (2026-10):** nnterp 1.3.0 (Feb 2026) is still the latest PyPI release and declares `nnsight>=0.6` with no upper bound; a rewrite for the nnsight 0.8 engine ("nnterp 2", `ndif-team/nnterp` PR #62, open on 2026-10-09) removes the 1.x accessors (`layers_output`, `load_model`, …), and `diffing-toolkit` pins `nnterp<2.0` for that reason. Because nnsight 0.8 became the stable PyPI release on 2026-10-16, a fresh `pip install nnterp` now resolves nnsight 0.8.x (PR #62 still open on 2026-10-20). nnterp 1.3.0 has not been tested here against nnsight 0.8; if you see import errors, pin `nnsight<0.8` for nnterp work.

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
- **On Gemma 2/3/4 and OLMo 2/3, `model.model.layers[i].mlp` is not the MLP's residual contribution** — see the next section.

## The sandwich-norm hook trap (Gemma 2/3/4, OLMo 2/3)

Aliases: sandwich norms, post-sublayer norms, `post_feedforward_layernorm`, `post_attention_layernorm` trap, `hook_mlp_out` vs `mlp.hook_out`, `mlp_out_post`, "my Gemma MLP SAE features are dead".

**What goes wrong.** Gemma 2/3/4 and OLMo 2/3 normalize each sublayer's *output* before adding it to the residual stream ("sandwich" or post-sublayer norms; HF module `post_feedforward_layernorm` on the MLP side). So "the MLP output" is two different tensors: the raw MLP module output, and the normed residual *contribution*. TransformerLens has a name for each — `blocks.{i}.mlp.hook_out` is the raw module output, while the block-level `blocks.{i}.hook_mlp_out` is the residual contribution, i.e. post-norm on these models. A pure string translation of `hook_mlp_out` into another library's raw `mlp_out` (or an HF hook on `model.model.layers[i].mlp`) returns a tensor whose cosine with TransformerLens's is ~0.2–0.4, with no error (interp-engine `docs/PORTING.md`, read 2026-10-14).

**Measured consequence (same source).** On `gemma-2-2b` layer 4, the Gemma Scope MLP SAE `gemmascope-mlp-16k` reconstructs the post-norm contribution at FVU (fraction of variance unexplained) 0.26 with L0 81 (the SAE declares 85), and the raw MLP output at FVU 9.8 — worse than predicting the mean — with L0 8. A feature whose dashboard tops out at 23.5 fired at no position at all when fed the raw output. The SAE is not noisier on the wrong tensor; it is silently dead.

**The second half of the trap: `post_attention_layernorm` means two things.** In Llama, Qwen and Mistral blocks it is the *pre-MLP* norm (applied to the residual after the attention add); in Gemma 2/3/4 it is a true post-attention norm on the attention *output*; OLMo 2/3 have post-sublayer norms and no pre-attention norm at all; GLM-4 and HyperCLOVAX use the name for the pre-MLP norm again (interp-engine `docs/ARCHITECTURE_QUIRKS.md`). Code that keys "is this a sandwich block?" on that module name misidentifies whole model families; the reliable signal is the presence of an MLP-side post-norm (`post_feedforward_layernorm`).

**Symptoms to search for:** MLP SAE or transcoder with near-zero L0 on your prompts; FVU above 1; features that never fire on text where their Neuronpedia dashboard shows strong activations; a transcoder or MLP SAE that works through SAELens/TransformerLens but not through your own HF hooks.

**How to check (tips, not requirements):**
- When you attach an MLP SAE or MLP-output reader to a Gemma or OLMo 2/3 model outside TransformerLens, hook *after* the post-feedforward norm (the output of `post_feedforward_layernorm`), unless the SAE's config names a different site. For attention-side SAEs, read the config's hook name rather than guessing: post-norm attention output, raw attention output and pre-projection head outputs are all different tensors.
- Compute FVU and L0 on both candidate tensors before trusting a feature; the PORTING doc reports they separate by an order of magnitude in one run, and the right one should land near the SAE's declared L0.
- With **interp-engine**, request the `mlp_out_post` / `attn_out_post` points (aliased to the raw output on architectures without post-sublayer norms, so the request is safe everywhere), or call `tlens_hook_to_point("blocks.7.hook_mlp_out", model)` *with* the model argument, which resolves to `("mlp_out_post", 7)` on Gemma 3; without the model it does pure string translation.
- Architectures without post-sublayer norms (Llama, Qwen, Mistral, GPT-2) are unaffected: the two names coincide.

Related residual-stream mismatches (`hook_resid_pre` vs `hook_resid_post`) are in [`saes.md`](saes.md) under SAELens pitfalls.

## circuitsvis

Aliases: `circuitsvis` on PyPI, `TransformerLensOrg/CircuitsVis` on GitHub (originally `alan-cooney/CircuitsVis`), "Alan Cooney's attention visualization", "CV".

**What it is.** Interactive attention pattern and neuron-activation visualization, designed for Jupyter. Renders heads as the colored grids you see in mech interp papers.

**Status (2026-04):** Maintained but coasting — repo is touched (housekeeping commits) but no new components since late 2024. PyPI 1.43.3.

**When to use it:** You want to look at attention patterns or neuron activations interactively in a notebook — the JS bundle is stable and works fine.

**When *not* to use it:** You're building a non-Jupyter pipeline. You need novel viz components — build in matplotlib/plotly directly; circuitsvis isn't shipping new ones. For SAE feature dashboards, see `sae-dashboard` / Neuronpedia (in [`saes.md`](saes.md)).

## Attribution: which tokens or components drove this output?

Aliases: feature attribution, input attribution, saliency, token attribution, integrated gradients (IG), input × gradient, LRP (Layer-wise Relevance Propagation), AttnLRP, component attribution, circuit attribution.

Two different questions get called "attribution". **Input attribution** asks which *input tokens* (or image patches) a given output depends on. **Component attribution** asks which *internal components* — heads, MLPs, neurons, SAE latents, edges between them — carry the computation. Both produce scores, not causal proof: a high score is a hypothesis to test with patching or ablation.

| I want… | Use | Cost |
|---|---|---|
| Per-token saliency for one prompt on any PyTorch model; classical methods (IG, GradientShap, DeepLIFT) | **Captum** (`LLMAttribution`) | one to *m* backward passes |
| Per-generated-token attribution over a whole generation, with notebook/HTML visualization, decoder-only or encoder-decoder | **inseq** | as the chosen method (IG: *m* steps per generated token) |
| A more faithful gradient-style relevance for an output logit, per token *and* per neuron, in one backward pass | **LXT** (AttnLRP) | one backward pass |
| Which heads/MLPs/edges form the circuit for a task, scored for faithfulness | **EAP-IG** (training-free) or **MAttr** (learned ranking); see [Circuit discovery](#circuit-discovery-and-how-to-evaluate-it-eap-ig-mib-causal-abstraction) | EAP-IG: ~*m* × (2 forward + 1 backward); MAttr: a training run |
| Which SAE/transcoder features drove a completion (attribution graph) | **circuit-tracer** (see [`saes.md`](saes.md)) | heavy on long prompts |
| Which *training documents* caused a behaviour | not this — see [`data-attribution.md`](data-attribution.md) | |

**Cross-cutting pitfalls.**
- **Attribution is not causation.** Verify a top-scored token or component by patching or ablating it and measuring the output change; gradient-based scores can be large for components whose removal changes nothing.
- **State the target.** Scores depend on which scalar you differentiate: the logit of the generated token, a logit difference against a contrast token, or a log-probability. A logit-difference target is usually more interpretable for "why A rather than B".
- **Model-specific skews exist.** LXT's README marks Qwen 3 as "Attribution skewed toward first token"; first-position (BOS / attention-sink) tokens soak up attribution in many models, so check whether a result survives excluding position 0.

### Captum

Aliases: `captum` on PyPI, `meta-pytorch/captum` on GitHub (formerly `pytorch/captum`, which still redirects), "PyTorch interpretability library", "Meta's interp library".

**What it is.** A general PyTorch interpretability library — saliency, integrated gradients, DeepLIFT, GradientShap, layer/neuron conductance for any `nn.Module`. It has **LLM attribution** support (`LLMAttribution`, `LayerGradientXActivation`, `LayerGradientShap`, KV-cache-aware perturbation) dating back to ~v0.7 (2023); the more recent additions are `RemoteLLMAttribution` against hosted endpoints, a `VLLMProvider` for large models, and (v0.9.0, Apr 2026) multimodal image-segment attribution. Active, Meta-maintained, ~quarterly releases.

**When to use it:**
- Token-level input attribution / saliency on LLMs (`LLMAttribution` over a prompt to see which tokens drove a generation).
- Classical attribution methods (integrated gradients, GradientShap) on any PyTorch model — vision, multimodal, tabular.
- Attribution at vLLM scale via `VLLMProvider`.

**When *not* to use it:** Activation patching / circuit analysis / SAE features — TransformerLens / nnsight / SAELens are the right tools. Captum is for *attribution* (which inputs mattered), not mechanism analysis (which internal computations mattered).

### inseq

Aliases: `inseq` on PyPI, `inseq-team/inseq` on GitHub (Apache-2.0, 477 stars; last push 2026-10-07), "Inseq: an interpretability toolkit for sequence generation models".

**What it is.** A feature-attribution library built for *generation*: it attributes every generated token back to the input (and previously generated) tokens, for HF `ForCausalLM` (decoder-only) and `ForConditionalGeneration` (encoder-decoder) models, and renders the result in the console, a notebook or HTML. Methods (from `inseq.list_feature_attribution_methods()`, README 2026-10-14): `saliency`, `input_x_gradient`, `integrated_gradients`, `deeplift`, `gradient_shap`, `discretized_integrated_gradients`, `sequential_integrated_gradients`, `attention`, `occlusion`, `lime`, `value_zeroing`, `reagent`; it extends Captum's methods and supports contrastive attribution targets through step functions. Versions: GitHub release v0.7.0 (2026-02-02), PyPI `inseq` 0.7.1 (2026-03-06), Python ≥3.10 (the README says ≤3.13). Grad-ELLM token attribution for Llama and Mistral was added on `main` on 2026-10-07, after the latest release.

```python
# pip install inseq          (pip install "inseq[notebook,datasets]" for Jupyter) — verbatim from the README
import inseq

model = inseq.load_model("gpt2", "integrated_gradients")
model.attribute(
    "Hello ladies and",
    generation_args={"max_new_tokens": 9},
    n_steps=500,
    internal_batch_size=50
).show()
```

**When to use it:** you want "which input tokens drove each generated token" across a whole generation, with a visualization you can hand to a collaborator, or contrastive attribution ("why this token instead of that one").

**When *not* to use it:** internal-component questions (heads, neurons, circuits) — use TransformerLens/nnsight patching or EAP-IG; models too large for full backward passes on your GPU; you need a feature that exists only on `main` (install from git).

### LXT (LRP-eXplains-Transformers) and AttnLRP

Aliases: `lxt` on PyPI, `rachtibat/LRP-eXplains-Transformers` on GitHub, LXT, AttnLRP ("Attention-Aware Layer-Wise Relevance Propagation for Transformers", Achtibat et al., ICML 2024), LRP, "relevance propagation", "single backward pass attribution".

**What it is.** LXT implements AttnLRP, a Layer-wise Relevance Propagation (LRP) rule set for transformers that changes how relevance flows through non-linearities (softmax, normalization, gated MLPs). Its "efficient" implementation monkey-patches the HF model class so that ordinary input × gradient equals the AttnLRP relevance, so token-level and neuron-level relevance for an output logit comes from **one backward pass**. Supported per the README (2026-10-14): Llama 2/3, Gemma 3, Qwen 2, BERT, GPT-2 ("best paired with contrastive explanations"), Vision Transformers; Qwen 3 is marked experimental with "Attribution skewed toward first token". MAttr (below) scores AttnLRP as a baseline; the R-Lens and J++ Lens (above) also compute their Jacobians with an LRP backward pass.

```python
# Efficient implementation; code lines verbatim from the README, comments shortened. your_module is the HF modeling module:
# the repo's examples/quantized_llama.py does `from transformers.models.llama import modeling_llama`
# and then `monkey_patch(modeling_llama, verbose=True)` before loading the model.
from lxt.efficient import monkey_patch

monkey_patch(your_module)                                         # patch module first
outputs = model(inputs_embeds=input_embeds.requires_grad_())      # forward with gradient tracking
outputs.logits[...].backward()                                    # backward from the chosen logit
relevance = (input_embeds * input_embeds.grad).sum(-1)            # relevance per input token
```

**Versions.** GitHub releases v2.1 (2025-07-10) and v2.0; PyPI `lxt` is 2.1 (2025-07-10). The README states "Tested with: `transformers==5.9.0`, `torch==2.12.0`, `python==3.11`", but the "update to transformers==5.9.0" commits on `main` are dated 2026-08-11, after the PyPI release — so on transformers 5.x, installing from git may be needed (not tested here).

**When to use it:** you want token- or neuron-level relevance that is less noisy than raw gradients, at the cost of a single backward pass, e.g. to pick candidate components before patching, or for long prompts where integrated gradients is too expensive.

**When *not* to use it:** commercial work — the README states that "LRP is a patented technology that can only be used free of charge for personal and scientific purposes" (the code itself is described as BSD-3; GitHub reports the license as NOASSERTION); as causal evidence on its own (verify by patching); architectures not in the supported list without checking the patched module covers every non-linearity.

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
| **Natural Language Autoencoder, NLA** (Anthropic, transformer-circuits.pub/2026/nla, May 2026; `kitft/natural_language_autoencoders`) | A paragraph of text per activation (activation verbalizer + reconstructor, jointly trained with RL) | Released AV/AR pairs for Qwen2.5-7B, Gemma-3-12B/27B, Llama-3.3-70B; hosted at `neuronpedia.org/nla`; expensive to train | You want an expressive hypothesis generator and can verify claims against the model's behaviour | You need trustworthy factual specifics — WorkspaceBench found nearly every NLA readout contained a claim contradicted by the model's own output; you need to detect *internalized* behaviour — on Gemma-3-12B-it steganography, NLA readouts were incriminating far more often when the side task was instructed in the prompt than when the same behaviour was fine-tuned in (Shportko, Arcuschin, Lange & Meyer, LessWrong, 2026-10-08); you assume the reconstructor reads meaning — on a Qwen3.6-27B NLA, syntactically related word pairs interacted no more than matched controls and deleting nouns, verbs and adjectives cost the least reconstruction quality (martinveron, LessWrong, 2026-10-09) |
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

### U-Space / U-Lens: a label-free uncertainty readout built on the J-lens

Aliases: U-Space, U-space, U-Lens, U-lens, "uncertainty in the verbalizable workspace", `s2labres/U-Space` on GitHub (BSD-3-Clause; verified, pushed 2026-10-19). Paper: Braun, Loose, Herzog, Ceccatelli, Rohrbach, Eisenbarth & Cavallaro, "U-Space: Uncovering When and Why Uncertainty Arises in Language Models", arXiv:2610.09087 (2026-10-06); LessWrong write-up *Uncertainty in the Verbalizable Workspace* (2026-10-17).

**What it is.** An application of the workspace lens (J-lens = Jacobian lens) to uncertainty estimation. Published lists of uncertainty and certainty words are pulled back through a J-lens into residual-stream directions, contrasted per category, and orthogonalized into four directions — *ambiguity*, *incompleteness*, *conflicting evidence*, *general uncertainty* — that span the U-space. Projecting each reasoning token's hidden state onto them gives a token-level uncertainty map; the scalar **U-lens** score multiplies the readout at the end-of-thinking marker by the mean predictive entropy of the generated tokens. Per the abstract it needs "no correctness labels, repeated generations, or training". Tested on Gemma-4-31B-it, Qwen3.5-27B and Magistral-Small-2507 (readout layer fixed at two-thirds depth) over MMLU-Pro, Omni-MATH, SuperGPQA and TriviaQA.

**Result and the confound it exposes.** Per the post, generation length alone gave 68.6% AUROC for spotting wrong answers, nearly matching a supervised hidden-state probe (Feature-Gaps, 68.8%), but fell to 52.4% when answers of similar length were compared; the U-lens moved from 71.1% to 69.2% and "still claims the highest length-controlled AUROC". The gain over a length baseline is real but small.

**When to use it:** a training-free, per-token uncertainty map for reasoning traces on a model that has a released J-lens; a baseline for any lens- or probe-based error detector. **When *not* to use it:** as a calibrated correctness predictor (AUROC around 0.7); models without a J-lens; as evidence that a detector works unless you also report length-controlled numbers.

### Pitfalls (with searchable symptoms)

- **J-lens target layer: "readouts are mostly Chinese tokens on English text" / "one direction dominates every layer".** About 80% of 78 publicly released J-lenses target the *final* layer, though Anthropic's own paper used the *penultimate* layer for its Sonnet experiments (appendix: including the last layer "can sometimes increase the number of noisy artifacts"). On DeepSeek-V3 a final-layer lens inherits a language-separating direction from the last block (≈46% of mid-depth readouts on English text were majority-Chinese; ≈3% with a penultimate target). Check the target layer in a lens's provenance; if you fit your own, compare final vs penultimate and look at the top singular direction of each layer's Jacobian (Kaley Brauer, LessWrong, 2026-09-25 — single-model case study).
- **Token-frequency offset.** J- and R-lens scores carry a context-independent offset correlated with log token frequency (Spearman 0.48 at mid-depth on Qwen3.5-4B in one study); subtracting it directly degraded readouts 3.5–12×, while z-scoring against base-model variance helped on a secret-word (taboo organism) task — 0.805 vs 0.665 leave-one-out accuracy (against the published protocol, re-run by the author) on Gemma-2-9B-it, a point estimate on n = 20 words (p ≈ 0.19), so "calibration helps" is suggestive, not established (Ameya Panchal, LessWrong, 2026-09-17).
- **Attention-sink positions and outlier prompts.** Skip the first positions when fitting (16 in J++, 4 in Nanda's replication) and pre-filter fit prompts whose Jacobian norm exceeds ~5× the median; on DeepSeek-V3 four prompts carried 84% of the summed Jacobian norm and the lens read out a space or hyphen as top token for most inputs.
- **MoE (Mixture-of-Experts) routing.** Single-prompt Jacobians depend on what else is in the batch (38% of token positions changed experts between batch 1 and batch 64 on DeepSeek-V3); averaged readouts agreed ~95% top-1. J++ freezes expert-routing weights (and the manifold-constrained hyper-connection, mHC, mixing coefficients of DeepSeek-V4-Flash) in its LRP pass.
- **Compare lenses fitted on the same data and budget.** The J++ authors found the *released* J-lens for Qwen3.6-27B scored worse than their own refit, so for that model they refit J and R lenses with identical data and budget for the headline comparison (the other five models use released J-lenses; R-lenses are released ones for three models and self-fitted for Gemma 4 31B and Olmo 3 32B). A "better lens" that differs in fit data is not a better method.
- **Single-token and tokenizer limits.** Readouts are bags of single tokens: no word order ("thief chases policeman" vs the reverse), and multi-digit numbers are invisible on digit-by-digit tokenizers (Qwen) — J++ could not evaluate arithmetic on Qwen models. A model that shortcuts to the answer without an intermediate variable gives no lens anything to find.
- **Causal evidence is weaker on open models than on Claude.** Mirella Zeisler (LessWrong, 2026-09-28) replicated the multi-hop intermediate-swap experiment on Qwen3.6-27B and Gemma-3-27B-it: top-1 flip rates for J-lens intermediate swaps were 6–11% (Anthropic reports 54–70% on Claude), and swapping the *counterfactual answer* usually beat swapping the intermediate, as in Nanda's review. Do not treat "lens vector changes the answer" as proof the J-space is the model's workspace; compare against an answer-swap control. (R-lens matched J-lens in three of four conditions.)
- **Monitoring claims need baselines.** Two unreviewed single-model pilots found J-space readouts tracked *topics* rather than intent — a J-lens separated guideline-sensitive prompts from controls at AUC 0.97 on proper nouns but 0.55 pooled, and belief-injection fine-tuning *raised* the conflict signal (Melchior de Polignac, 2026-08-11, DeepSeek-R1-Distill-Qwen-14B) — and added no discrimination over the transcript for reward-hacking audits (Kartikay Luthra, 2026-09-16, Qwen3-8B). Authors of the J++ post motivate lenses for eval-awareness and unverbalised-scheming monitoring but do not test it. A positive but model-specific case: Jimmy Liu (*On Qwen, the J-lens readouts at the newline token reveal lies*, LessWrong, 2026-10-19; code `MPJL9/jlens-lie-readouts`, MIT) read Neuronpedia's prefitted J-lenses at chat-template boundary tokens on MASK `provided_facts` pressure scenarios: on Qwen3.6-27B, at the newline right after the response, the `lie` word family appeared after 84% of lies and 9% of truths, and a training-free detector from eight word families reached held-out AUROC 0.87 — but a difference-of-means probe at the same token reached 0.96 (0.69–0.81 at the neighbouring template tokens); the signal was weaker and spread out on two Gemma-3 models and absent on gpt-oss-20b, which has no post-response newline token; and `truth`/`truthful` appeared after two thirds of lies, so a readout word's meaning is not its verdict. The author notes readouts and probes were fitted and tested on the same kind of scenario. Always report the transcript-only and prompt-only baselines, and a linear probe at the same position.
- **Length confounds "internals predict correctness".** In the U-Space study (see "U-Space / U-Lens" above), reasoning length alone gave 68.6% AUROC for wrong answers — nearly matching a supervised probe (68.8%) — and fell to 52.4% when answers of similar length were compared. Report length-binned (length-controlled) metrics for any lens- or probe-based uncertainty or error detector.
- **`git clone https://github.com/koayon/jpp_lens` 404s.** The J++ README's install line points at `koayon/jpp_lens`; the repository that exists (verified) is `safety-research/jpp_lens`. `anthropics/jacobian-lens` is marked "reference implementation, not maintained, not accepting contributions" and is `pip install -e .`, not on PyPI.

**Related:** the plotting recipes for lens figures (pass@10 vs layer, per-layer gradient norm, expert-vs-pooled bars, ablation curves) are in [`research-plots.md`](../engineering/research-plots.md#j-lens-r-lens-and-j-lens-reading-the-global-workspace).

## Circuit discovery and how to evaluate it (EAP-IG, MIB, causal abstraction)

Aliases: "circuit discovery", "circuit localization", "edge attribution patching", "EAP", "EAP-IG", "attribution patching with integrated gradients", "MIB", "Mechanistic Interpretability Benchmark", "causal abstraction", "interchange intervention", "IIA".

A **circuit** is the subgraph of a model's computation graph (attention heads, MLPs and the residual-stream edges between them) that performs a task. Hanna, Pezzelle & Belinkov define the property that justifies studying one: "A circuit is faithful if all model edges outside the circuit can be ablated without changing the model's performance on the task". The methods differ in how they score each edge:

| Method | What it does | Cost |
|---|---|---|
| Edge activation patching | Patch each edge from a corrupted (counterfactual) run, one at a time; exact per-edge effect | One forward pass per edge; infeasible beyond small models |
| **EAP** (edge attribution patching; Syed, Rager & Conmy, arXiv:2310.10348) | First-order gradient approximation of every edge's patching effect at once | Two forward passes (clean and corrupted) + one backward pass |
| **EAP-IG** (EAP with integrated gradients; Hanna, Pezzelle & Belinkov, COLM 2024, arXiv:2403.17806) | Averages the gradient over *m* interpolation steps between clean and corrupted inputs | About *m* times EAP |
| Mask optimization (e.g. UGS, uniform gradient sampling, one of MIB's baselines) | Optimizes which edges to keep so that behaviour is preserved | An optimization run per task |
| **MAttr** (Matryoshka Attribution; Arora et al., arXiv:2609.25518) | Learns a mask with a sigmoid top-*k* operator while sampling *k* at random each step, so one run yields a *ranking* of all components and the whole faithfulness-vs-sparsity curve | One training run per task (the paper's node-level recipe: 500 steps) |

**Key result (EAP-IG paper).** Circuits found with EAP were less faithful than those found with EAP-IG, even though both had high node overlap with circuits found previously using causal interventions; the authors conclude that faithfulness, not overlap with a reference circuit, is what to measure.

**Code: `hannamw/EAP-IG`** (MIT; verified, last push 2026-05-23; install from a clone with `pip install .`, or `pip install .[viz]` for graph drawing, which needs the graphviz C library). Pipeline from the README: `graph = Graph.from_model(model)`, `attribute(model, graph, dataloader, metric, method='EAP-IG-inputs', ig_steps=5)`, `graph.apply_topn(n)`, then `evaluate_graph(model, graph, dataloader, metric)` to measure the circuit with everything outside it corrupted. Graphs can be edge-level (default), node-level or neuron-level.

**Pitfalls:**
- **`ImportError: cannot import name 'HookedTransformer' from 'transformer_lens'`** — EAP-IG's `attribute.py` imports `HookedTransformer` and its `pyproject.toml` declares `transformer-lens>=2.15.0` with no upper bound, so a fresh install resolves TransformerLens 4.x, which removed that class (read from the source, not run). Pin `pip install "transformer-lens<4"`.
- **Grouped-query attention (GQA) models** (Llama 3, Qwen, Gemma): set `model.cfg.ungroup_grouped_query_attention = True` first (README), at the cost of GQA's memory savings.
- **Pre-LayerNorm only.** The README notes the residual stream must stay a sum of component outputs; post-LayerNorm architectures break this (Gemma works through a workaround).
- **Ablation type changes the circuit.** The README's author advises avoiding zero ablation; MIB found that circuits found with counterfactual (CF) ablations "outperform those found with mean or optimal ablations". State the ablation you used for discovery *and* for evaluation.
- **Whether a behaviour "looks localised" depends on the component budget and the probe prompts.** Kumar, Joshi, Maity & Saha, "Causal Syntax Circuits in CodeLMs: Budget and Probe Decide What Looks Localised" (arXiv:2610.20683, 2026-10-14; NeurIPS 2026 LP4FM workshop) ran one pipeline (mean ablation, activation patching, greedy circuit extraction, a random-control significance test, steering) over 55 model–language settings on ten open code models. With a budget of 12 components, 1 of 15 settings yielded a circuit that beat size-matched random controls after multiple-comparison correction; with a budget of 40, 6 of 15 did. Swapping the probe prompts for XLCoST parallel functions took the same measurement "from about 1.6 to about 0.01", and every significant circuit pointing the *wrong* way came from a setting where extraction had failed. Report the component budget, the probe set and a size-matched random-control test with any localisation (or non-localisation) claim; the authors release the full grid.
- **Try the neuron basis too.** Circuits can be traced directly on MLP neurons: Arora, Wu, Steinhardt & Schwettmann (Transluce), arXiv:2601.22594, find "MLP neurons are as sparse a feature basis as SAEs" and a circuit of about 100 neurons that controls subject-verb agreement (code `TransluceAI/circuits`, ADAG, no license file). See [`saes.md`](saes.md#should-i-use-saes-at-all-the-skeptics-reading-list) for the transcoder-vs-neuron comparison.

### MIB, the Mechanistic Interpretability Benchmark

Mueller, Geiger, Wiegreffe, … Bau, Belinkov, *MIB: A Mechanistic Interpretability Benchmark*, ICML 2025, arXiv:2504.13151; landing repo `aaronmueller/MIB` (Apache-2.0), website `mib-bench.github.io`, datasets in the Hugging Face collection `mib-bench`, leaderboard Space `mib-bench/leaderboard`.

- **Two tracks.** *Circuit localization* (code `hannamw/MIB-circuit-track`) scores methods that find causal subgraphs. *Causal variable localization* (code `atticusg/CausalAbstraction`, which now redirects to `goodfire-ai/causalab`, verified via the GitHub API) scores *featurization* methods — sparse autoencoders (SAEs), principal component analysis (PCA), distributed alignment search (DAS) — by how well a feature aligns with a causal variable of a known high-level algorithm.
- **Tasks and models.** Indirect object identification (IOI), Arithmetic, multiple-choice question answering (MCQA) and the AI2 Reasoning Challenge (ARC) across GPT-2 Small, Qwen-2.5 (0.5B), Gemma-2 (2B) and Llama-3.1 (8B), plus an **InterpBench** model trained to contain a known ground-truth IOI circuit (scored by AUROC, area under the ROC curve). The README also lists RAVEL among the datasets.
- **Metrics.** The paper splits faithfulness in two: **CPR** (integrated circuit performance ratio; higher is better) rewards finding components that *help* the task; **CMD** (integrated circuit-model distance; 0 is best) rewards finding everything with a strong effect, including components that hurt it. Both are integrated over a range of circuit sizes; a leaderboard submission is 9 circuits of varying sizes per model/task. The causal-variable track reports **interchange intervention accuracy (IIA)**: the fraction of interventions where the intervened model and the high-level causal model give the same output (for every task except IOI, which uses a logit-based metric).
- **Findings.** "attribution and mask optimization methods perform best on circuit localization", with EAP-IG on inputs and counterfactual ablations generally best on both CPR and CMD; exact edge activation patching did not always win. For causal variables, supervised DAS performed best, and "SAE features are not better than neurons" (raw hidden dimensions).
- **Private test set.** The leaderboard scores a held-out private split and allows 2 submissions per user per week, to discourage hill-climbing.
- **Current top method (as of 2026-10-14).** The MAttr paper (arXiv:2609.25518, 2026-09-22) reports "number 1 on the official leaderboard"; its node and edge circuits for every MIB subtask are on Hugging Face as `aryaman/mattr-mib-circuits`. Leaderboard rank is the authors' claim, read from the abstract, not re-checked against the Space.

### MAttr (Matryoshka Attribution): a learned ranking over all sparsities

Aliases: MAttr, Matryoshka Attribution, "sigmoid top-k mask", `aryamanarora/matryoshka-attribution` on GitHub, `aryamanarora/matryoshka-attribution-parameters` (weight-attribution sibling repo). Paper: Arora, Acharya, Hu, Zhang, Goodman, Jurafsky & Potts, "Matryoshka attribution: Learning to attribute language model outputs to representations and weights", arXiv:2609.25518 (2026-09-22).

**What it is.** Attribution framed as finding *nested* subsets of components that minimise a downstream loss. A mask over components is parametrised with a differentiable sigmoid top-*k* operator, and *k* is randomised during training, so the learned scores are an ordering: the top-*k* set for every *k* comes from one run, unlike mask-learning methods that fix a budget. One API (`trainer.learn_scores`, which "takes a `loss_fn(mask)` and a node count") covers nodes, edges, MLP neurons, SAE latents and ViT patches. Baselines (Node/Edge Pruning, UGS, EAP-IG, AtP*, RelP, AttnLRP, input × gradient, IG, Expected Gradients) are all scored with MIB's own `evaluate_area_under_curve`. The paper also trains a weight-attribution variant with reinforcement learning on refusal-judge scores and reports that "restoring 1% of Llama 3.1 8B Instruct's weights to their base model state is sufficient to remove refusals while maintaining capabilities" — a weight-level take on model diffing (see [`model-diffing.md`](model-diffing.md)).

```bash
# Verbatim from the README: setup clones the pinned MIB fork into deps/, then a node-level MIB cell
git clone git@github.com:aryamanarora/matryoshka-attribution.git
cd matryoshka-attribution
bash scripts/setup.sh
uv run python scripts/mib/eval_mib.py --model gpt2 --task ioi \
  --steps 500 --k-schedule uniform --masking topk --mode iso --lr 0.05 \
  --split validation --train-split train --include-input \
  --output results/mib_node_topk_uniform_lr05
```

**Pitfalls (from the README):** three `uv` environments exist because their torch / transformers / TransformerLens stacks conflict; every Gemma-2 cell and the Node/Edge Pruning and UGS baselines need the `tl2` group (TransformerLens **2.15.4**), because "TL 3.x has a Gemma-2 forward bug". `meta-llama/*` and `google/gemma-2*` are gated (`HF_TOKEN`).

**When to use it:** you want a faithfulness-vs-sparsity curve without re-running a method per budget, a MIB submission against the current top method, or attribution over a non-standard basis (neurons, SAE latents, weights).

**When *not* to use it:** a quick, training-free first look (EAP-IG or attribution patching is cheaper); code you need to redistribute or vendor — neither repository has a license file (GitHub API, 2026-10-14), so default copyright applies.

### CircuitKIT: discovery → faithfulness scoring → pruned checkpoint in one pipeline

Aliases: CircuitKIT, `circuitkit` on PyPI, `Lexsi-Labs/CircuitKIT` on GitHub, Lexsi Labs. Paper: Seth, Gosalia, Kasliwal & Sankarapu, "CircuitKIT: Circuit Discovery, Evaluation, and Application Toolkit for Mechanistic Interpretability", arXiv:2607.19317 (2026-07-21).

**What it is.** A library that connects circuit discovery, evaluation and downstream use through one typed, serializable circuit object: run a discovery algorithm (six "stable" ones per the README — EAP, EAP-IG, EAP-GP, ACDC, IBCircuit, CD-T — plus research ones), score the circuit on a "6-pillar faithfulness" suite (causal patching, ablation, stability, robustness, baselines, generalization), then prune, quantize, edit, steer or fine-tune and export a reloadable Hugging Face checkpoint. Releases 0.2.0 and 0.1.11 (both 2026-10-08); PyPI `circuitkit` 0.2.0. The GPT-2 quickstart runs on CPU.

```python
# Verbatim from the README (CPU is fine for GPT-2)
from circuitkit import Pipeline

pipe = Pipeline("gpt2", task="ioi")
pipe.discover(algorithm="eap-ig", sparsity=0.3)
pipe.evaluate()
pipe.prune()
pipe.export("./checkpoint")
```

**Pitfalls:**
- **Pinned to TransformerLens 3.8.0** (with transformers 5); the README says to import `circuitkit` before `transformer_lens`. Expect a conflict in an environment that has moved to TransformerLens 4.x for other work — a separate environment is the simple fix.
- **Vision-language models are rejected** with an error (TransformerLens has no vision tower); ACDC is excluded from the README's standard validation gate.

**When to use it:** you want circuit discovery and an *action* on the circuit (pruning, editing) in one tool, or a quick comparison of several discovery algorithms under one evaluation.

**When *not* to use it:** the license matters for your project — it is the **Lexsi Labs Source Available License (LSAL) v1.2**, not an OSI open-source license: "free for academic research and teaching on MIT-like terms; use by any organization requires written acknowledgement or permission (Section 1A); commercial use requires a separate license" (README); frontier-size models; when you need MIB-comparable numbers (score the circuit with MIB's own evaluator as well).

### Causal abstraction (the theory underneath)

Geiger, Ibeling, Zur, … Potts, Icard, *Causal Abstraction: A Theoretical Foundation for Mechanistic Interpretability*, arXiv:2301.04709 (v4, May 2025). It formalizes "this network implements that algorithm" as a causal-abstraction relation tested by **interchange interventions** (swap a representation from one input into another and check the output matches what the high-level algorithm predicts), and recasts activation and path patching, causal mediation analysis, causal scrubbing, causal tracing, circuit analysis, concept erasure, SAEs, differential binary masking, DAS and steering in that one language. Read it when you need a precise statement of what your circuit or feature claim asserts; DAS and interchange interventions are implemented in **pyvene** (above).

### What counts as progress here (evidence bar)

A new circuit-discovery or featurization method is convincing when it **reports MIB scores** — CPR and CMD on the circuit track, or IIA on the causal-variable track — against the paper's baselines (EAP-IG with counterfactual ablations; DAS), on the public test split and ideally the private leaderboard. Two further controls address failure modes that a loss-versus-circuit-size curve hides (both shown for pruned weight-sparse circuits; see [`saes.md`](saes.md)): run the method on a **nonsense task** that the model should not be able to solve with a tiny circuit, and check the circuit **out of distribution** (e.g. same-gender IOI prompts when discovery used only opposite-gender ones). When not to use MIB: your claim is about a model or behaviour outside its four tasks and five models — there, the InterpBench-style move (train a model with a known circuit and check recovery) is the closest substitute.

## Automated interpretability and interpretability agents

Aliases: "auto-interp", "interpretability agent", "investigator agent", "MAIA", "Predictive Concept Decoder", "PCD", "Seer", "secret elicitation", "de-censoring".

Two related ideas: **automated interpretability** (an LLM labels or explains units — features, neurons — at scale; for SAE features use **Delphi**, see [`saes.md`](saes.md)), and **interpretability agents** (an LLM runs a whole investigation: forms hypotheses, calls white-box and black-box tools, writes a conclusion). For agents auditing models with implanted hidden behaviours, the benchmark is **AuditBench** (see [`model-organisms.md`](../alignment-science/model-organisms.md)), whose headline finding is a *tool-to-agent gap*: a tool that surfaces good evidence on its own often does not improve the agent's audit.

| I want… | Use |
|---|---|
| An agent that explains neurons/features of a **vision** model with tool-driven experiments | **MAIA** (`multimodal-interpretability/maia`) |
| A trained model that answers natural-language questions about a language model's activations through a sparse concept bottleneck | **Predictive Concept Decoders** (Transluce; no official code found) |
| Infrastructure to give a Claude Code / Claude Agent SDK agent GPU-backed white-box tools | **Seer** (`ajobi-uhc/seer`) |
| A testbed of *naturally occurring* secrets (facts a model knows but lies about) | The **de-censoring Chinese models** tasks (`ajobi-uhc/chinese-models-investigations`) |
| Auditing-game targets with implanted hidden behaviours | **AuditBench** (see [`model-organisms.md`](../alignment-science/model-organisms.md)) |
| A trained explainer that describes SAE features, patching effects or input-ablation effects of Llama-3.1-8B / Qwen3-8B, plus a released *simulator* to score any feature explanation | **Transluce `introspective-interp`** (arXiv:2511.08579) |
| To measure whether a coding agent can find the right SAE feature for a concept (rank, selectivity, steering) against expert picks | **SAEScientist-Bench** (`Trae1ounG/SAEScientist`, arXiv:2609.09113) |
| To test whether an activation-reading tool (activation oracle, NLA, SAE) helps an agent predict behaviour better than the transcript alone | **CHIVE** (`adamkarvonen/chive`, arXiv:2608.16747) |

**MAIA, a Multimodal Automated Interpretability Agent** (Rott Shaham, Schwettmann, Wang, Rajaram, Hernandez, Andreas & Torralba, arXiv:2404.14394; code `multimodal-interpretability/maia`, verified, last push 2025-10-22, no license file per the GitHub API). A pretrained vision-language model equipped with tools for synthesizing and editing inputs, computing maximally activating dataset exemplars, and summarizing results; it composes them into experiments. On a dataset of synthetic vision neurons with ground-truth descriptions, its neuron descriptions were comparable to those of expert human experimenters. **When not to use it:** language-model work — it targets computer-vision models.

**Investigator agents for behaviour elicitation** (Li, Chowdhury, Johnson, Hashimoto, Liang, Schwettmann & Steinhardt, Transluce, arXiv:2502.01236). Trains *investigator models* (supervised finetuning, DPO, and a Frank–Wolfe objective for diversity) to map a target behaviour to prompts that elicit it; reported 100% attack success on a subset of AdvBench (Harmful Behaviors) and an 85% hallucination rate. This is black-box elicitation, not internals; no public code was found under the `TransluceAI` GitHub organization (2026-10-12).

**Predictive Concept Decoders, PCDs** (Huang, Choi, Johnson, Schwettmann & Steinhardt, Transluce, arXiv:2512.15712; project page `transluce.org/pcd`). An encoder compresses a subject model's activations into a sparse list of concepts; a decoder reads only that list plus a question about the model and must answer it, so the bottleneck has to carry a general-purpose explanation. Setup: Llama-3.1-8B-Instruct as subject, 32,768 concepts read from layer 15, pretrained on FineWeb with next-token prediction, then the decoder finetuned on question answering. The abstract reports that "PCDs can detect jailbreaks, secret hints, and implanted latent concepts", and the paper reports they beat direct prompting and LatentQA (the same idea without a sparse bottleneck). No official code was found; community reproductions exist (e.g. `Ky-Ng/repro-pcd`, unvetted). Related trained readers — Activation Oracles and natural language autoencoders — are in the [lens decision table](#which-lens-should-i-use-decision-table).

**De-censoring Chinese models as an interpretability testbed** (Khoi Tran, aryaj, Senthooran Rajamanoharan & Neel Nanda, *Test your interpretability techniques by de-censoring Chinese models*, LessWrong, 2026-01-15; MATS 9.0). Chinese open-weight models refuse, downplay or lie about facts they know, which makes them *natural* model organisms of secret-keeping (instilled by extensive post-training, not narrow finetuning). Four tasks: Falun Gong on Qwen3-32B, a verbatim Harry Potter quote from gpt-oss-20b (refusal without lying), and two tasks on `kimi-k2-0905` about the November 2024 Zhuhai car attack — the only fact the authors found that the target knows and conceals but the investigator model (Claude Sonnet 3.7, GPT-5) does not, so the agent cannot fall back on prior knowledge. An LLM judge gives a **correctness** score and a **consistency ("Bayesian") score** for whether conclusions follow from the evidence gathered, which catches agents that "find" what they already knew. The investigator was the Claude Agent SDK with Claude Sonnet 3.7 and a notebook; giving it a logit-lens tool did not improve the main tasks, which the authors call a preliminary result that should not be taken as a meaningful update. Code: `ajobi-uhc/seer` (MIT; infrastructure for interpretability agents — GPU environments and white-box tools for Claude Code-driven investigations) and `ajobi-uhc/chinese-models-investigations` (MIT; task YAMLs, transcripts, judge prompts). Pitfalls: target behaviour is stochastic, so single transcripts do not replicate; a test fact must post-date the *investigator's* knowledge cutoff, and the authors note Kimi appears only lightly pretrained on events after June 2024.

**Trained explainer models and a released simulator scorer (Transluce `introspective-interp`).** Li, Guo, Huang, Steinhardt & Andreas, "Training Language Models to Explain Their Own Computations" (arXiv:2511.08579; code `TransluceAI/introspective-interp`, MIT, last push 2026-07-07). They finetune LMs to describe (1) SAE features (LlamaScope features of Llama-3.1-8B, labels from Neuronpedia), (2) the effects of activation patching (CounterFact; Llama-3.1-8B and Qwen3-8B) and (3) the effects of removing hint tokens (MMLU + hint; Llama-3.1-8B-Instruct and Qwen3-8B). Headline from the abstract: "using a model to explain its own computations generally works better than using a *different* model to explain its computations (even if the explainer model is significantly more capable than the target)". The reusable artifact for auto-interp pipelines is the **simulator model** `Transluce/features_explain_llama3.1_8b_simulator`, which predicts where a described feature should fire so that any explanation can be scored by correlation with the true activations (the "simulator score"). Evaluation, from the README with `--model_path` set to its example checkpoint: `uv run --env-file .env evaluate.py --config config/feature_descriptions/base_131k.yaml --target_model_path meta-llama/Llama-3.1-8B --task features_explain --model_path Transluce/features_explain_llama3.1_8b_llama3.1_8b --output_dir /PATH/TO/RESULTS/ --batch_size 64`; `--model_path self_explanations` runs the untrained SelfIE baseline and `--model_path nearest_neighbor` a retrieval baseline. Configs assume 2× 80 GB H100s, and the LM-judge evaluation needs an OpenAI API key. **When not to use it:** target models other than the released ones (the checkpoints are model-specific, and the paper's point is that self-explanation beats cross-model explanation).

**SAEScientist-Bench: can an agent do SAE feature-finding research?** Tan, He, Zhao & Liu, arXiv:2609.09113 (2026-09-08); code `Trae1ounG/SAEScientist` (no license file; last push 2026-09-10). 20 tasks over 17 concepts on Gemma-2-9B-IT with Gemma Scope 131,072-feature residual dictionaries at layers 9 and 20: the agent writes contrastive probe texts, inspects activations and submits one feature, scored against Neuronpedia-anchored expert features on activation rank, concept selectivity on contrastive texts, and causal steering. Abstract: frontier agents "remain well behind the expert baseline, approaching expert levels on separating target concepts from contrastive controls while lagging substantially in causal generation steering", and "although agents can design contrasts to rule out spurious candidates, they frequently misinterpret experimental measurements". Run one task (README): `python scripts/run_benchmark.py --config configs/benchmark.json --task-id gemma_cat_001 --replicates 1 --output-dir outputs/cat`. **When not to use it:** as a general interpretability-agent benchmark (it tests one narrow skill); without a GPU that holds Gemma-2-9B-IT plus the dictionary; with Claude Code as the agent unless you write an adapter — the provided harnesses are Codex and Cursor, and the judge is an Azure OpenAI GPT-4o deployment. **Tip for agent-driven SAE work:** its failure mode suggests asking the agent to restate what each measurement shows before it draws a conclusion from it.

**CHIVE: does an interpretability tool beat reading the transcript?** Karvonen, Ong, Kantamneni & Marks, "Would this change your answer? Evaluating Explanations of LLM Behavior In The Wild with Counterfactual Experiments" (arXiv:2608.16747, 2026-08-17; LessWrong 2026-08-21; code `adamkarvonen/chive`, MIT; data `adamkarvonen/chive-data` on Hugging Face). CHIVE (Counterfactual Hypothesis Investigation Via Edits) is an agentic pipeline: sample a target model on real prompts (30 responses per prompt), screen for unexpected behaviours, run 5–15 counterfactual prompt edits per behaviour, and record the measured outcome of each edit. The measured outcomes become labels for a binary evaluation: a predictor agent sees a transcript and a claim that a specific edit would change the behaviour, and outputs a probability. Predictors given 5 read-only calls to an **activation oracle**, a **natural language autoencoder** or an **SAE** were compared with a transcript-only predictor (Claude Opus 4.8 as predictor in the main experiments). Result (post): "activation-reading interpretability tools provide no uplift: agents given the tools predict the outcomes of these experiments no better than agents that just read the transcript", holding "across many variations, including two target models, three predictor model families, sweeps of hyperparameters, and manual and automated attempts to elicit better tool use". The authors' own caveats: the discovered behaviours are mostly simple (a coding mistake, an unusual story choice), and they "still believe these tools can be valuable"; their recommendation is that causal claims based on tool outputs be treated as suggestive until a tool shows uplift. The same data trains models (Qwen3-8B, Qwen3.5-397B-A17B) to predict how prompt edits change their own behaviour, which generalized to a held-out hint setting. Setup: `uv sync`, `python scripts/download_data.py`; `uv sync --extra gpu` for vLLM serving, activation-oracle capture and SAE/NLA precomputes; entry points `chive/pipeline/README.md` (run on your own model) and `chive/binary_eval/README.md` (run the eval). **When not to use it:** when you need ground truth about an internal mechanism — CHIVE's labels are counterfactual prompt-edit effects, not internals.

**Testing a neuron or feature label (evidence bar, 2026-10).** Top-activating examples cannot establish a label, because "X matches Y is not commutative" (Gao, LessWrong 2026-10-17): the unit may fire only on a subset of X, and activation magnitudes may matter. Gao's bar is simulation from the label, substituting simulated activations and measuring downstream KL on a large dataset. Cheaper checks from Cammarata's essay (Goodfire, 2026-10-15): a **blind maximum** (a second agent sees only the explanation and writes an input meant to activate the unit maximally) and **near misses** written from the explanation alone before measurement — in his Qwen3-32B gallery, new examples fired their neurons strongly 76% of the time and near misses 11%. For gated-MLP neurons, label the positive and negative poles separately and split by SwiGLU sign regime. Neuronpedia v2.8.0 (2026-10-20) now hosts neuron sources and ranks neuron search by both tails; `moridinamael/bonsai-interp` is an open, pre-registered, CI-re-scored neuron map of the 1-bit Bonsai-8B that runs on an 8 GB GPU or Apple Silicon (community labels, unreviewed; see [`saes.md`](saes.md#neuronpedia)).

**Open problem and bar.** Agents with white-box tools have not yet clearly beaten agents with black-box tools on realistic audits (AuditBench's tool-to-agent gap; the logit-lens result above; CHIVE's no-uplift result on naturally occurring behaviours). A convincing interpretability-agent result shows a white-box tool **raising agent success over the best black-box scaffold** on a task where the investigator cannot know the answer in advance (the Kimi tasks, AuditBench with adversarially trained organisms, or CHIVE's binary counterfactual-prediction eval against its transcript-only baseline), reports a consistency-style score alongside correctness, and uses enough runs per condition to separate the effect from run-to-run variance. Regime note: these benchmarks score unattended agent runs; how much they transfer to a researcher steering an agent interactively is untested.

## Agenda framing: pragmatic, ambitious, and open problems

Short reads that set the terms of current mechanistic-interpretability (mech interp) debates. Useful when choosing or justifying a project's goal; none is a tool.

| I want… | Read |
|---|---|
| The field's own map of unsolved problems, across labs | Sharkey, Chughtai, Batson, Lindsey, … McGrath, *Open Problems in Mechanistic Interpretability*, arXiv:2501.16496 (January 2025; 29 authors) |
| How to pick and validate a project when the goal is safety impact | Nanda, Engels, Conmy, Rajamanoharan, Chughtai, McDougall, Kramár, Smith, *A Pragmatic Vision for Interpretability*, LessWrong, 2025-12-01 |
| The case for full reverse-engineering and how to measure it | Leo Gao, *An Ambitious Vision for Interpretability*, LessWrong, 2025-12-05 |
| A concrete, unsolved full-understanding challenge on tiny models | Jacob Hilton (ARC), *AlgZoo: uninterpreted models with fewer than 1,500 parameters*, LessWrong, 2026-01-26; `alignment-research-center/alg-zoo` |
| The live 2026-10 dispute over whether neurons are already interpretable, and what evidence would settle it | Nick Cammarata (Goodfire), *Neural Networks Are Already Clean*, 2026-10-15 (`already-clean.goodfire.com`), and Leo Gao, *Neural networks are not already clean*, LessWrong, 2026-10-17 |

**Pragmatic vision (Google DeepMind mech interp team).** The team describes a pivot from ambitious reverse-engineering to work grounded by a **North Star** (a stepping-stone goal toward AGI going well) and a **proxy task** (empirical feedback that tracks progress toward it and "stops you fooling yourself"). It recommends **method minimalism** — try prompting, steering, probing and reading chain of thought before building new methods — and time-boxing curiosity-driven exploration. Its SAE case study says the team made slower progress optimizing reconstruction/sparsity frontiers than it would have with proxy tasks. It explicitly welcomes complex methods: "If ambitious reverse-engineering, singular learning theory, or similar produce a complex method that verifiably works, that is fantastic".

**Ambitious vision (ambitious mechanistic interpretability, AMI).** Gao argues the full-understanding goal has good feedback loops: metrics for *feature quality* (replace activations with explanation-simulated ones without degrading the model) and *circuit faithfulness* (causal scrubbing or a successor), noting that "the strongest metrics we can come up with give a score of precisely zero for all extant interp techniques". He points to weight-sparse circuits (see [`saes.md`](saes.md)), parameter decomposition (SPD/APD), singular learning theory and computational mechanics (see [`slt-devinterp.md`](slt-devinterp.md)) as routes.

**"Already clean" vs "not already clean" (2026-10, contested).** Cammarata argues that canonical polysemanticity was mostly tool and architecture failure plus "recursive generalization", not superposition, and reports from "preliminary audits of Qwen3-32B" that "roughly 90% of neuron poles have one main job", with neuron-only attribution graphs on Qwen3-32B and Kimi K3. He calls this "our leading hypothesis", says the share "depends on where you set thresholds", and defers the evidence to a companion paper not yet released (no code as of 2026-10-20). Gao agrees polysemanticity was overestimated but holds to the feature-quality metric of his ambitious-vision post: an explanation counts only if simulated neuron values can replace the real ones without degrading the model, scored by "downstream KL instead [of correlation]" and "on a large dataset"; he reports his "best guess" that ablating small neuron activations substantially degrades performance, with results to come. Neither side has yet published the measurement that would settle it: downstream-KL simulation scores for a random sample of neurons on a large dataset. Practical checks from the essay (negative poles, SwiGLU sign regimes, blind-maximum and near-miss tests) are summarised in [`saes.md`](saes.md#should-i-use-saes-at-all-the-skeptics-reading-list). **When not to lean on either:** as an established result in a paper — cite both, with their status.

**AlgZoo (Alignment Research Center, ARC).** RNNs and transformers of 8 to 1,408 parameters trained on algorithmic tasks (RNN families: 2nd argmax, argmedian, median; transformer family: longest cycle). ARC treats an *explanation* as a **mechanistic estimate of the model's loss** (for these models, its accuracy) and grades it two ways: mean squared error versus compute (does it beat random sampling at the same compute?) and *surprise accounting* (full understanding = total surprise no larger than the bits of optimization that selected the model). The largest model ARC believes it more or less fully understands has 32 parameters; a 432-parameter 2nd-argmax RNN, `M_{16,10}`, remains unexplained. **Stated bar (ARC's challenge):** design a method for mechanistically estimating the accuracy of the 432-parameter model that matches the performance of random sampling in mean squared error versus compute; the post suggests measuring error by adding noise to the weights and averaging over noisy models. Install: `git clone` the repo, `pip install -e alg-zoo`, then `from alg_zoo import example_2nd_argmax` (MIT-0; verified, last push 2026-08-19). **When not to use it:** if your question is about LLM behaviour at scale — AlgZoo is a test of explanation methods, not of LLM phenomena.

## Live challenges (as of 2026-10-14)

Aliases: interpretability competition, interp challenge, AIMO Interpretability Challenge, AIMO-interp, NeurIPS 2026 competition, ARC White-Box Estimation Challenge, WhestBench, flopscope, MIB leaderboard.

Open problems with a scoreboard. Dates go stale fast; each entry says where the authoritative terms live.

| Challenge | Task | Deadline / status (as read 2026-10-14) | Where |
|---|---|---|---|
| **AIMO Interpretability Challenge** (NeurIPS 2026 competition) | From model internals, predict whether a reasoning model is *robust* on each math problem (its accuracy holds under every perturbation the organisers apply) | Main phase Aug 15 – Nov 1, 2026; **final submission deadline Nov 1, 2026**; technical reports Nov 1–15; workshop at NeurIPS 2026 in Paris on Dec 12 | `aimo-interp.github.io`; starter kit `aimo-interp/getting-started`; details in [`probes.md`](probes.md#aimo-interpretability-challenge-neurips-2026-deadline-2026-11-01) |
| **ARC White-Box Estimation Challenge** (Alignment Research Center + AIcrowd) | Given the weights of a random ReLU MLP (first rounds: width 256, 8 hidden layers), estimate its expected output under a FLOP budget, better than sampling | Warm-up round began June 2026; later rounds have "a total prize pool of at least $100,000" (ARC post, 2026-06-02). The AIcrowd page deliberately carries no dates — the Official Rules there are binding | `aicrowd.com/challenges/arc-white-box-estimation-challenge-2026`; FLOP counter `AIcrowd/flopscope`; see [`theory-research.md`](../engineering/theory-research.md) |
| **MIB leaderboard** (circuit localization, causal variable localization) | Score a circuit-discovery or featurization method on a private test split | Ongoing; 2 submissions per user per week | `mib-bench/leaderboard` Space; see [MIB](#mib-the-mechanistic-interpretability-benchmark) |

**AIMO Interpretability Challenge, in brief.** You submit a Codabench zip exposing `are_robust(model_id, reasoning_effort, problems) -> list[bool]`, which runs offline on one NVIDIA RTX PRO 6000 (96 GB) with 3,600 s for the entire prediction run. Evaluated models: `Qwen/Qwen3.5-4B`, `Skywork/Skywork-OR1-Math-7B`, `allenai/Olmo-3-7B-Think`, `deepseek-ai/DeepSeek-R1-0528-Qwen3-8B`, plus `openai/gpt-oss-120b` on the main track only (a small-models track excludes it). Per the rules, "teams can use weights, activations, token probabilities, or any other model internal signals as inputs for their methods." Prizes: "$12,500 in prizes" — main track $3,000 / $1,000 / $600, small-models track $2,000 / $600 / $300, and $5,000 for selected technical reports. **When not to use it:** after Nov 1, 2026 it stops being a competition and becomes a probe-on-reasoning-models example with development labels only.

**ARC White-Box Estimation Challenge, in brief.** Jacob Hilton (ARC), "Announcing the ARC White-Box Estimation Challenge" (LessWrong, 2026-06-02). Black-box methods are permitted, but ARC expects the best algorithms to be "mechanistic", as in its wide-random-MLP paper; LLM use is encouraged, and later rounds have a prize for the best-performing submission and one for the favourite algorithmic contribution in a technical report. Submissions are scored by analytical FLOP cost through **flopscope** (`flopscope` on PyPI, v0.12.1, 2026-08-29; `import flopscope.numpy as fnp` in place of `import numpy as np`; "Every arithmetic call deducts from a fixed budget; exceed it and execution stops immediately"). The post warns that the FLOP counter "is definitely hackable in ways that would be very unambiguously hacking once pointed out" and that contestants are responsible for not doing so, including via LLM-written code. **When not to use flopscope:** as a general profiler — it counts analytical FLOPs over a NumPy subset, not wall-clock time. It is the natural next step after [AlgZoo](#agenda-framing-pragmatic-ambitious-and-open-problems) (same organisation, same "estimate the model's behaviour mechanistically" framing).

## Analogue domains: chess transformers (chessformer_lens)

Aliases: chessformer_lens, `chessformer-lens` on PyPI, `chessformer-lens/chessformer_lens` on GitHub, chess interpretability, Leela Chess Zero BT4, Maia-3, "Fork Around and Find Out" (LessWrong series), David Litman.

**What it is.** A TransformerLens-style hook, analysis and visualization toolkit for square-tokenized chess transformers — Leela's BT4 network (downloads itself on first use) and Maia-3 — with an interactive app runnable in Colab. Releases v3.0 (2026-10-13) and v2.0 (2026-10-11); PyPI `chessformer-lens` 3.0. The companion paper is Litman, "Increasing Skill Level Recruits Deeper Attention Layers in a Frozen Chess Transformer" (arXiv:2609.23917, 2026-09-20): Maia-3 takes Elo as an input, so the skill it is conditioned on can be varied with no weight change; ablating every attention head at Elo 700–2500, higher skill pushes the causal centre of mass of the computation deeper, most strongly for tactics such as knight forks.

```bash
# Verbatim from the README
pip install chessformer_lens
# for Maia-3 models, first: pip install https://github.com/CSSLab/maia3/archive/1e13597c42d4858b7cfd7cfdae01e297263364b2.zip
```

**Why an analogue domain.** A move has a clear evaluation (an engine score), board-structured attention has interpretable roles, and there is a human concept hierarchy (squares → threats → tactics → strategy) to compare features against — a cheap testbed for circuit or feature claims before an LLM.

**When *not* to use it:** you need language-model findings directly (chess results are an analogue, not evidence about LLMs); the license matters (GitHub reports NOASSERTION — read the repo's LICENSE file before reuse); you want a mature library (single author, first GitHub release v0.1.0 on 2026-08-10, nine stars as of 2026-10-14).

## Cross-references

- For SAE work: [`saes.md`](saes.md).
- For activation extraction at vLLM throughput: [`serving-and-activations.md`](serving-and-activations.md).
- For probes built on extracted activations: [`probes.md`](probes.md).
- For activation steering (uses these libraries as backends): [`steering.md`](steering.md).
- For singular learning theory, developmental interpretability (local learning coefficient, susceptibilities) and belief-state geometry: [`slt-devinterp.md`](slt-devinterp.md).
- For weight-sparse (intrinsically interpretable) models, parameter decomposition and attention decomposition (Lorsa): [`saes.md`](saes.md).

---

## Common questions

### Is TransformerLens still maintained?

Yes. `TransformerLensOrg/TransformerLens` on GitHub is actively maintained (maintainers Bryce Meyer and Jonah Larson; releases 4.0.0 on 2026-09-21, 4.1.0 on 2026-09-28 and 4.2.0 on 2026-10-10, which is also the current PyPI `transformer-lens` version as of 2026-10-14). TL 3.0 (2026-04-17) introduced `TransformerBridge`; **TL 4.0 removed `HookedTransformer`** and the other `Hooked*` classes. Bug fixes for the legacy classes continue only on the 3.x branch. The `HookedSAETransformer` was moved out of TransformerLens 2.0 into **SAELens**, which also offers `SAETransformerBridge` for TL 3+ and currently pins `transformer-lens<4`.

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

### My Gemma (or OLMo 2/3) MLP SAE features never fire — why?

Most likely the sandwich-norm hook trap: on Gemma 2/3/4 and OLMo 2/3 the raw MLP module output (`model.model.layers[i].mlp`, TransformerLens `blocks.{i}.mlp.hook_out`) is not the post-norm residual contribution (`blocks.{i}.hook_mlp_out`), and Gemma Scope MLP SAEs read the contribution. On gemma-2-2b layer 4 the wrong tensor gave FVU (fraction of variance unexplained) 9.8 and L0 8 instead of FVU 0.26 and L0 81 (interp-engine `docs/PORTING.md`). Hook after `post_feedforward_layernorm` and compare FVU on both candidates. See [The sandwich-norm hook trap](#the-sandwich-norm-hook-trap-gemma-234-olmo-23).

### Which library tells me which input tokens drove an output?

**Captum** (`LLMAttribution`) for single-prompt saliency and classical methods; **inseq** for attribution of every generated token with built-in visualization; **LXT** (AttnLRP) for token- and neuron-level relevance in one backward pass (free only for personal and scientific use — LRP is patented). For *internal components* use EAP-IG or MAttr instead. See [Attribution](#attribution-which-tokens-or-components-drove-this-output).

### Do interpretability tools beat just reading the transcript?

Not yet, on the checkable proxies that exist. In CHIVE (Karvonen et al., arXiv:2608.16747) agents given an activation oracle, a natural language autoencoder or an SAE predicted the effect of counterfactual prompt edits no better than a transcript-only agent; AuditBench found a similar tool-to-agent gap. The CHIVE authors still consider the tools valuable and suggest treating tool-based causal claims as suggestive. Reporting a transcript-only baseline next to any tool result is the cheap way to show uplift. See [Interpretability agents](#automated-interpretability-and-interpretability-agents).

### What is the J++ Lens (Jacobian Filtering)?

A drop-in improvement to Anthropic's J-Lens (a per-layer averaged-Jacobian readout of a model's workspace representations). It clusters each layer's activations (k-means, 8 clusters), averages one Jacobian per cluster, learns weights that down-weight clusters giving noisy readouts (*Jacobian Filtering*), computes the Jacobians with a Layer-wise Relevance Propagation backward pass (as in the R-Lens), and drops non-semantic tokens from the readout (*Readout Filtering*). Inference cost is identical to the J-Lens. Limits: single tokens only, tokenizer-dependent, poetry-planning recall ≤5% for every lens. Full details above.

---

Last verified: 2026-10-20. TransformerLens 2.x removed `HookedSAETransformer` (now in SAELens). nnsight published at ICLR 2025; remote backend via NDIF. nnterp 1.3.0 (Feb 2026), NeurIPS 2025 Mech Interp Workshop (arXiv:2511.14465). baukit not on PyPI, last commit Feb 2024. circuitsvis 1.43.3 (Dec 2024) under TransformerLensOrg. Captum 0.9.0 (Apr 2026) with LLM attribution. (Citation audit 2026-06: corrected canonical repo paths to `meta-pytorch/captum` and `ndif-team/nnterp`, added the nnsight paper arXiv:2407.14561, and noted LLM attribution predates v0.7. Additions 2026-06: cited the mech-interp methods named in the TransformerLens bullets — induction heads (Olsson et al. 2209.11895), IOI (Wang et al. 2211.00593), attribution patching (Syed et al. 2310.10348); all verified via arXiv.) (Additions 2026-08: pyvene — `pyvene` on PyPI, arXiv 2403.07809, example structured after the repo's Basic_Intervention tutorial — and its sibling pyreft (ReFT, arXiv 2404.03592; last repo activity March 2026).) (Additions 2026-10: TransformerLens 3.0/4.0 `TransformerBridge` migration — `HookedTransformer` removed in 4.0.0 (PyPI 2026-09-21; GitHub 4.1.0 2026-09-28), verified from the repo README, `migrating_to_v3.md`/`migrating_to_v4.md`, `drivers.md` and PyPI release dates; SAELens `<4` pin (v6.51.2) and the circuit-tracer issue #115 TL-4 breakage verified on GitHub; nnsight 0.7.0 / 0.8.0rc1 release notes and README; new **Workspace lenses** section — J-Lens (Gurnee et al., transformer-circuits.pub/2026/workspace, 2026-07-06; `anthropics/jacobian-lens`), R-Lens (LessWrong nv8oedrnLXKRzNEL9, 2026-08-05), J++ Lens (Ayonrinde & Lindsey, LessWrong nc9dHfcB22JdMzGbr, 2026-10-08; `safety-research/jpp_lens`, `koayon/jpp-lenses`), WorkspaceBench (`camilablank/workspace-bench`, LessWrong Zeg2JztbdhguL48uH, 2026-09-23), NLA (`kitft/natural_language_autoencoders`), pitfalls from LessWrong posts Adb55vLqt33LEyBfz, Qe3jdphWCg9kny3e5, pnDjvdo6cX2H7Ddsy, GZCMmCHZiF8vhsczr, 69fachkoAs2ZHeSst; GitHub repos and HuggingFace lens repos verified via `gh api` / HF API, arXiv IDs 2303.08112, 2401.06102, 2512.15674 verified via abs pages. J++ numbers are from the authors' non-peer-reviewed post.) (Additions 2026-10-12: **Circuit discovery** — EAP-IG arXiv:2403.17806 (abstract) and `hannamw/EAP-IG` README, `pyproject.toml` and `src/eap/attribute.py` imports read via `gh api` (the TransformerLens-4 `ImportError` is inferred from the unpinned dependency plus the `HookedTransformer` import, not run); MIB arXiv:2504.13151 (abstract and HTML full text for CPR/CMD/IIA definitions, the EAP-IG and counterfactual-ablation findings), `aaronmueller/MIB` README (models, 9-circuit submissions, 2 submissions per week), `hannamw/MIB-circuit-track` and the `atticusg/CausalAbstraction` → `goodfire-ai/causalab` redirect via the GitHub API, leaderboard Space returns HTTP 200; causal abstraction arXiv:2301.04709 (abstract). **Interpretability agents** — MAIA arXiv:2404.14394 and `multimodal-interpretability/maia`; investigator agents arXiv:2502.01236; Predictive Concept Decoders arXiv:2512.15712 (abstract and HTML for setup); the de-censoring post (LessWrong 7gp76q4rWLFi6sFqm, 2026-01-15, read in full via GraphQL), `ajobi-uhc/seer` and `ajobi-uhc/chinese-models-investigations` via the GitHub API; no official code found for investigator agents or PCDs. **Agenda framing** — arXiv:2501.16496 (author list), Pragmatic Vision (LessWrong StENzDcD3kpfGJssR), Ambitious Vision (LessWrong Hy6PX43HGgmfiTaKu) and AlgZoo (LessWrong x8BbjZqooS4LFXS8Z) read via GraphQL, `alignment-research-center/alg-zoo` README and license via `gh api`. All quotations checked as exact substrings of the source. Verification pass 2026-10-12: 78 claims checked, 4 corrected — EAP cost (two forward passes + one backward, per the 2310.10348 abstract), EAP-IG's overlap baseline (circuits found with causal interventions, not hand-found), IIA's IOI exception (MIB PDF §4), and ARC's definition of an explanation (estimate of loss).) (Additions 2026-10-14: TransformerLens 4.1.0/4.2.0 release notes and the `analysis_tools.md` / `sparse_probing.md` docs (logit lens, sparse probing, unreduced patching, bridge fixes); Orchestra `AI-Research-SKILLs` mech-interp SKILL.md files read via `gh api` (`HookedTransformer`, `LanguageModel` usage) and its `marketplace.json`; the sandwich-norm trap from interp-engine `docs/PORTING.md` and `docs/ARCHITECTURE_QUIRKS.md` (raw, pushed 2026-10-13); Attribution section: inseq README (method list, versions; PyPI 0.7.1), LXT README and `examples/quantized_llama.py` (PyPI `lxt` 2.1 of 2025-07-10 vs the 2026-08-11 transformers-5.9 commits), MAttr arXiv:2609.25518 (abstract) and README, CircuitKIT arXiv:2607.19317 and README (LSAL v1.2, TL 3.8.0 pin), introspective-interp arXiv:2511.08579 and README, SAEScientist-Bench arXiv:2609.09113 and README, CHIVE arXiv:2608.16747, README and LessWrong post ExB6KYDcznaFS72eT (read in full); AIMO challenge site (raw HTML) and `aimo-interp/getting-started` README; ARC White-Box Estimation post (LessWrong Kben8CzS4awCwNw5c), AIcrowd challenge page (no dates on it) and `AIcrowd/flopscope` README; chessformer_lens README, releases and arXiv:2609.23917. Repo metadata via `gh api`, PyPI via the JSON API, all on 2026-10-14.) (Additions 2026-10-20: nnsight v0.8.0 (2026-10-16) and v0.8.1 (2026-10-20) release notes and the v0.8.0rc1 breaking-changes list via `gh api`, PyPI JSON (latest 0.8.1; 0.8.0 uploaded 2026-10-16), current README quickstart; nnterp PyPI 1.3.0 (`nnsight>=0.6`) and PR #62 (still open); NLA caveats re-extracted from the two LessWrong posts (BcCcSfTHqz74kdTMF, Gemma-3-12B-it steganography; Q5fwBiZCwHGeKucmo, Qwen3.6-27B NLA) via GraphQL; J-lens lie readouts (LessWrong bhvaAbSPZgiG3oJPu, `MPJL9/jlens-lie-readouts` MIT); U-Space arXiv:2610.09087 abstract, LessWrong hcpiLD8XjK7cqG6Lr and `s2labres/U-Space` (BSD-3-Clause); Kumar et al. arXiv:2610.20683 abstract; Arora et al. arXiv:2601.22594 abstract and `TransluceAI/circuits`; Cammarata's essay (`already-clean.goodfire.com/essay.md`) and Gao's reply (LessWrong Dkh7pXKjoNWkkxQDz) read in full; Neuronpedia v2.8.0 release notes. Whether NDIF accepts nnsight 0.8 clients was not confirmed.)
