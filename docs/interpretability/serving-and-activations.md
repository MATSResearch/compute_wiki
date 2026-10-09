---
tags:
  - interpretability
  - infrastructure
---

# Model Serving and Activation Extraction at Scale

How to run inference on big models efficiently, and how to get internal activations / apply steering at production-scale throughput. Relevant when you have more than a small experiment: 70B+ models, millions of prompts, multi-GPU / multi-node.

## At a glance: which tool?

| If you want… | Use |
|---|---|
| Fast inference of an open-weight model on your own GPUs (no activations) | **vLLM** or **sglang** |
| Fast inference + extract residual-stream activations + apply steering + per-layer Python hooks | **vLLM-Lens** (UK AISI, v1.3.0) |
| Attention patterns from a vLLM-served model | **vLLM-Lens** `output_qk` (captures post-RoPE Q/K, reconstructs the matrix offline) |
| Same hook names / intervention code on a vLLM-served model as on a local one | **TransformerLens 4 `RemoteBridge.boot_vllm`** (declarative interventions) or **nnsight 0.8 on vLLM** (taps) |
| Run interpretability on a 405B / 1T model you can't host | **NDIF** (nnsight remote backend) |
| Read out a Jacobian lens / J-space on a served model | **vLLM-Lens** `examples/jacobian_lens*.py` (see [`mech-interp.md`](mech-interp.md#workspace-lenses-j-lens-r-lens-j-lens)) |
| Plain HuggingFace `transformers.generate()` with hooks | OK for small-scale experiments only |
| OpenAI-compatible local API for any HF model | **vLLM** (`--served-model-name`), **TGI**, or **llama.cpp**'s server |
| One-off CPU inference for tiny models / tests | `transformers` or `llama.cpp` |

## vLLM

Aliases: `vllm` on PyPI, `vllm-project/vllm` on GitHub, "vLLM serving engine", "PagedAttention server".

**What it is.** The dominant high-throughput LLM serving engine: PagedAttention KV cache (Kwon et al. 2023, "Efficient Memory Management for Large Language Model Serving with PagedAttention", arXiv:2309.06180, SOSP'23 — paging-inspired KV-cache management that near-eliminates fragmentation), continuous batching, tensor parallelism, OpenAI-compatible HTTP API. Industry standard for open-weight inference in 2026.

**When to use it:**
- You're running >100 prompts and want speed.
- You want an OpenAI-compatible local API to drop into your eval framework (Inspect, lm-eval-harness, safety-tooling).
- You need tensor-parallel for a model that won't fit on one GPU.

**When *not* to use it:**
- You need to extract activations or apply hooks — vanilla vLLM doesn't expose internals. Use **vLLM-Lens** instead.
- You're doing training or fine-tuning — vLLM is inference-only.

**Pitfalls:**
- **`gpu_memory_utilization` default 0.9 OOMs at long context.** Drop to 0.85 if you see CUDA OOM at startup.
- **Tensor parallel size must divide attention heads.** A 70B model with 64 heads supports `--tensor-parallel-size {1,2,4,8}` but not 3.
- **First-token latency is high; throughput is high.** vLLM is for batched throughput; for low-latency single-prompt use, sglang or TGI may be faster.
- **Quantization options change frequently.** AWQ, GPTQ, FP8, INT4 — check vLLM's current support matrix for your model.
- **Chat templates.** vLLM uses the model's HF chat template by default; verify with `--chat-template` or by inspecting `tokenizer.apply_chat_template` output.

```bash
# pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.85
# Now reachable at http://localhost:8000/v1/chat/completions
```

## vLLM-Lens

Aliases: `vllm-lens` on PyPI (v1.3.0, 2026-10-02), `UKGovernmentBEIS/vllm-lens` on GitHub (MIT; verified, pushed 2026-10-02), "AISI's vLLM activation lens", "the fast interp tool". UK AISI.

**What it is.** A vLLM plugin + Inspect AI model provider that adds **activation extraction**, **steering vectors** and **per-layer Python hooks** to vLLM serving — at near-vLLM throughput, with tensor and pipeline parallelism (across GPUs and nodes) and all of these techniques usable concurrently in the same dynamic batch. Auto-registers as a vLLM general plugin (`vllm.general_plugins` entry point) and as an Inspect provider (`vllm-lens/<model>`) on install. Features per the README (v1.3.0):
- **Residual-stream capture** — `extra_args={"output_residual_stream": [layers]}` (offline `SamplingParams`) or `vllm_xargs` / client `capture_layers=[...]` over HTTP.
- **Steering vectors** — `apply_steering_vectors` with a `SteeringVector(activations, layer_indices, scale, norm_match, position_indices)`.
- **Generic hooks (v1.2.0, 2026-07-17)** — `Hook(fn, layer_indices, pre=False)`: an arbitrary Python function `fn(ctx, hidden_states) -> Tensor | None` that runs per request, per layer, can save to `ctx.saved` and/or *replace* the hidden states by returning a tensor; per-request (`apply_hooks`), persistent (`register_hooks` → many requests → `collect_hook_results`), and pre-hooks (modify layer inputs, e.g. corrupt embeddings for causal tracing). `ctx.get_parameter("lm_head.weight")` gathers a full parameter across TP/PP ranks (so a logit lens is ~5 lines). Hooks are Garçon-inspired.
- **Attention Q/K capture (v1.3.0)** — `output_qk` captures post-RoPE query/key tensors plus kernel parameters (softmax scale, sliding window, soft-cap, ALiBi, sinks); `vllm_lens.attention.attention_patterns` reconstructs the true attention matrix offline (GQA, sliding window, Gemma soft-cap handled; MLA models rejected).
- **Binary activation transport (v1.3.0)** — `activations_transport="binary"` fetches large captures from `GET /v1/activations/{handle}` as raw bytes, avoiding the ~33% base64 inflation and one giant JSON blob.
- **Examples** — causal tracing, logit lens, **Jacobian lens / J-space** (`jacobian_lens.py`, `jacobian_lens_chat.py`, fitter with `--rules lrp` for R-lens), Apollo-style deception probe, emotion-concept tracker, **Activation Oracle** (arXiv:2512.15674).

**When to use it:**
- You need activations from a 70B / 405B / 1T model at scale — TransformerLens won't fit, nnsight + vLLM was 10× slower in the announcement benchmark.
- You want to apply steering vectors, or small per-layer interventions, during a large eval run.
- You want to run probes ("activation oracles") online during generation, e.g. for safety-monitor classifiers.
- You're combining black-box (just generate) and white-box (probe activations) techniques in the same batch.

**Performance** (per the vLLM-Lens announcement [LessWrong post](https://www.lesswrong.com/posts/3bs27nZQuEcKhXf7q/vllm-lens-fast-interpretability-tooling-that-scales-to), April 2026; headline benchmark run on OPT-30B):
- **8.1× faster** than HuggingFace `transformers` with hooks.
- **10.6× faster** than nnsight 0.6.3 + vLLM.
- **44.8× faster** than TransformerLens.
- Only **~20% slower** than vanilla vLLM (no extraction).
- Used on models from ~27B up to 1T (the latter via downstream work, e.g. evaluation-awareness on Kimi K2.5), across 1–5 nodes.

**When *not* to use it:**
- You need hook points *inside* a layer — per-head ablation, MLP-internal activations, attention-pattern *edits*. Hooks fire at **decoder-layer inputs and outputs** (the residual stream), not inside attention or the MLP; attention *patterns* are reconstructed offline from captured Q/K, not hookable. For arbitrary hook points use TransformerLens or nnsight.
- You need gradients — serving engines are not autograd engines; fit things like Jacobian lenses in a separate backward-capable environment.
- Small experiments where TransformerLens / nnsight is enough.

**Pitfalls:**
- **Extra-arg key names.** Activations are requested with `extra_args={"output_residual_stream": [...]}` and steering with `"apply_steering_vectors"`; for Inspect these go under `GenerateConfig.extra_body["extra_args"]`. Keys such as `extract_residual` or `steering_vectors` are not part of the plugin's `extra_args` / `extra_body` API (`extract_residual` appears in neither the v1.0.0 nor the v1.3.0 README; `steering_vectors` exists only as a keyword of the v1.3.0 `VLLMLensClient.generate(...)`); a misspelled key is the likeliest reason a request "works" but returns no activations.
- **Steering silently did nothing via `LLM.chat` (fixed in v1.2.1, 2026-07-23).** In v1.2.0 and earlier, offline steering through `LLM.chat` raised a msgpack `TypeError` for live `SteeringVector` objects and **ran silently unsteered** for JSON-serialized vectors. Upgrade to ≥1.2.1 and sanity-check that a large steering scale visibly changes output.
- **`norm_match=True` got stronger in v1.2.0.** The fused-residual fix (Qwen / Gemma / Llama) makes the injected magnitude `‖residual‖ · scale`; old `norm_match` steering coefficients from earlier versions are now too large.
- **Pinned vLLM.** v1.3.0 pins `vllm==0.30.0` (GPU-validated; V1/eager execution only; V2 model runner and native CUDA graphs are outside the validated configuration — the plugin gives a clear error on the V2 runner; the README's serve example sets `VLLM_USE_V2_MODEL_RUNNER=0`). Other vLLM versions may import but are untested.
- **The plugin auto-loads in *every* vLLM process and forces `enforce_eager=True`** (disabling CUDA graphs) so hooks can fire. Installing `vllm-lens` into the environment of a production vLLM server changes that server; set `VLLM_LENS_DISABLE=1` to make the plugin a complete no-op.
- **Hooks run on every tensor-parallel rank.** `fn` must be deterministic across ranks; with TP > 1 a hook that appends to a plain list in `ctx.saved` sees each entry duplicated `tp_size`× (save tensors, or guard writes to one rank). Over HTTP `fn` is shipped with cloudpickle — **arbitrary code execution on the server**; only use with trusted clients.
- **Binary transport is process-local.** Handles are valid only on the frontend that minted them: use `--api-server-count=1` or sticky routing; the store is bounded (`VLLM_LENS_ACT_MAX_BYTES` default 8 GiB, `VLLM_LENS_ACT_TTL_S` default 300 s).
- **`output_qk=True` on a deep model at high TP is slow** (copies each layer's Q/K to host every step on every TP rank) — pass an explicit layer list; reconstructing a full pattern materializes `(num_heads, n, n)` client-side, so do it per layer.
- **fp32 on vLLM is not fp32 end-to-end by default.** vLLM's Triton attention kernel uses TF32 for fp32 inputs (≈3e-3 error in attention probabilities, up to 0.17 in residual-stream values measured on Qwen2.5-0.5B); vLLM-Lens defaults `TRITON_F32_DEFAULT=ieee` for fp32 models (v1.3.0). If you compare activations with HuggingFace fp32, check that setting.
- **Plugin auto-registration.** On install, it registers as a vLLM plugin and Inspect model provider with the `vllm-lens/` prefix. If you don't see it, check `inspect cache list` / restart.

```python
# Inspect AI integration (README, v1.3.0): activations come back in output.metadata["activations"]
from inspect_ai.model import GenerateConfig
config = GenerateConfig(temperature=0.0, max_tokens=1, extra_body={
    "extra_args": {"output_residual_stream": [15, 20]},
    "chat_template_kwargs": {"enable_thinking": False},
})
# output = await model.generate(messages, config=config)
# residual_stream = output.metadata["activations"]["residual_stream"]
# inspect eval my_eval --model vllm-lens/meta-llama/Llama-3.1-70B-Instruct

# Offline (no Inspect): steering vector + a per-layer hook on a vLLM LLM
import torch
from vllm import LLM, SamplingParams
from vllm_lens import SteeringVector, Hook
def ablate_neuron(ctx, h):                    # h: (seq_len, hidden_dim) for this request
    ctx.saved[f"pre_L{ctx.layer_idx}"] = h[:, 42].cpu()
    h = h.clone(); h[:, 42] = 0
    return h                                  # return None to leave unchanged
sp_hook = SamplingParams(temperature=0.0, max_tokens=10,
                         extra_args={"apply_hooks": [Hook(fn=ablate_neuron, layer_indices=[15, 16])]})
sv = SteeringVector(activations=torch.randn(1, 4096), layer_indices=[15], scale=4.0, norm_match=True)
sp_steer = SamplingParams(max_tokens=20, extra_args={"apply_steering_vectors": [sv]})
# llm = LLM("meta-llama/Llama-3.1-8B-Instruct"); out = llm.generate(["Hello world"], sp_hook)
# out[0].hook_results -> {"0": {"pre_L15": tensor, "pre_L16": tensor}}
```

## sglang

Aliases: `sglang` on PyPI, `sgl-project/sglang` on GitHub.

**What it is.** A serving engine optimized for **structured generation** and **agent-style multi-turn workflows** with KV cache reuse across turns (RadixAttention — an LRU radix-tree cache of KV blocks; Zheng et al. 2023, "SGLang: Efficient Execution of Structured Language Model Programs", arXiv:2312.07104). Often faster than vLLM for agent traces with shared prefixes.

**When to use it:**
- Multi-turn agent evals where prompts share long prefixes (system prompt + tool history).
- Constrained generation with structured outputs.
- You're already familiar with it.

**When *not* to use it:**
- Pure batch inference on independent prompts — vLLM is the safer default and better-supported by ecosystem tools.
- You want activation extraction — no native equivalent of vLLM-Lens for sglang yet (as of 2026-04).

## NDIF and nnsight remote backend

Aliases: NDIF = "National Deep Inference Fabric", `ndif.us`, "nnsight remote", "the nnsight cluster".

**What it is.** A research compute pool (NSF-funded) that hosts very large models (Llama-3.1-405B, etc.) for academic interpretability research, accessed via the **nnsight** library's remote backend.

**When to use it:**
- You're an academic researcher (or affiliated) and need to run interp on a 405B model you can't host.
- Your experiment fits in a few intervention calls per prompt; latency is OK.

**When *not* to use it:**
- You need millions of forward passes — the network round-trip dominates; better to host yourself with vLLM-Lens.
- Your work is commercial — NDIF is for academic research.

**Pitfalls:**
- **Latency, not throughput.** Each remote `.trace()` call = network round-trip. Batch your interventions.
- **Quotas.** NDIF is shared. Check current quotas; don't assume unlimited compute.
- **Client/server version split.** The nnsight 0.8.0rc1 release notes say remote execution against NDIF stays on v0.7 until NDIF is upgraded — if you install the 0.8 pre-release for local work, remote `trace(..., remote=True)` code should be run in an environment with nnsight 0.7.
- **Activation-shape sanity.** Same code runs locally on a 1B model and remotely on a 405B model — but shape and behavior may differ in subtle ways. Test locally with the same architecture family first.

## nnsight on vLLM (`nnsight-serve`, CUDA-graph taps)

Aliases: `nnsight.modeling.vllm.VLLM`, `nnsight-serve`, "nnsight vLLM runtime", `ndif-team/nnsight`. nnsight 0.7.0 (2026-05-05) added `nnsight-serve`; nnsight 0.8.0rc1 (2026-09-09, pre-release: `pip install --pre nnsight`) made vLLM a first-class runtime.

**What it is.** nnsight's trace syntax (`with model.trace(...)`) running *inside* a vLLM engine worker, so PagedAttention, continuous batching and tensor parallelism keep working under a trace. Per the release notes: **0.7** — `nnsight-serve <model> --port 6677 --tensor-parallel-size 4 --api-key ...` starts one vLLM engine behind an HTTP server, and a GPU-less client runs `with model.trace("...", serve="http://host:6677"):` with a meta model (`VLLM("Qwen/Qwen3-30B-A3B")`). **0.8** — `VLLM(..., taps=["model.layers.*.output"])` records the named locations into the CUDA graph as breaks and serves them on every replay, keeping CUDA graphs on; measured against vanilla vLLM the release notes report **96%** of throughput at 8B on one GPU, 93% at tp=4, 91% at tp=8 and 95% at 70B / tp=8. 0.8 also adds engine-wide `model.edit()` (installed once; every later request, including from clients that never heard of nnsight, gets a scoped copy, selectable per request with `edits=[...]`), `mode="async"` streaming, `n > 1`, and a prefix-cache recompute so cached tokens still reach interventions.

**When to use it:** You want nnsight-style arbitrary intervention code (not just additive steering) on a served model, with the same syntax as local experiments; or an intervention-capable HTTP endpoint without running an NDIF cluster.

**When *not* to use it:** You only need residual-stream capture and steering at maximum throughput with Inspect integration → vLLM-Lens (benchmarked ~20% below vanilla vLLM, with eager mode). You need NDIF remote execution — it stays on nnsight 0.7 until NDIF upgrades. You need production stability — 0.8 is a pre-release with breaking changes (listed in [`mech-interp.md`](mech-interp.md)).

**Pitfall:** the `nnsight-serve` / 0.8 vLLM figures above are the maintainers' own measurements on their hardware, not independently reproduced here; benchmark your own model and tap list before relying on 91–96%.

## TransformerLens `RemoteBridge` (vLLM and Inspect drivers)

Aliases: `RemoteBridge.boot_vllm`, `RemoteBridge.boot_inspect`, "TransformerLens drivers", `transformer-lens[vllm]` / `transformer-lens[inspect]` extras. New in TransformerLens 4.0 (2026-09-21).

**What it is.** TransformerLens 4 separates *what you study* (the bridge's hook names, cache and intervention surface) from *what runs the forward pass* (a **driver**): local HuggingFace `transformers` (full hooks and gradients), **vLLM** (`RemoteBridge.boot_vllm("meta-llama/Llama-3.2-1B", dtype=torch.float16, max_model_len=2048)`), or an **Inspect AI provider** (`RemoteBridge.boot_inspect(...)`, with a `capture_activations([...])` solver to save activations during an eval; `provider="vllm-lens"` targets a running vLLM-Lens server, residual-only and additive-steering-only). On vLLM, capture hooks are installed inside the worker before `torch.compile`; each hook also applies an affine transform `output * scale + bias`, so **declarative interventions** (`suppress` / `scale` / `add` / `set`, optionally position-scoped) propagate to downstream layers, e.g. `bridge.run_with_cache("Hello", intervene={"embed.hook_out": {"op": "suppress"}})`. Fireable vLLM hooks: `embed.hook_out`, `blocks.{i}.hook_out` / `attn.hook_out` / `mlp.hook_out`, `ln_final.hook_normalized`. Single-node tensor parallelism and pipeline parallelism are supported and GPU-validated per the docs; multi-node (Ray) is unsupported. Install `pip install "transformer-lens[vllm]"` (Linux-only extra; pins a validated vLLM 0.20.x band — which is *not* the vLLM version vllm-lens pins).

**When to use it:** You already work in TransformerLens and want the same named hooks for large-scale activation collection (SAE or probe data) or declarative interventions on a vLLM-served model; or to run interpretability inside an Inspect eval harness with the HF-backed `tl_bridge` provider.

**When *not* to use it:**
- You need gradients, attention patterns or arbitrary Python hook functions mid-forward — **serving engines are not autograd engines**: no gradients (attribution patching, backward hooks, Jacobian-lens fitting need `boot_transformers`); `attn.hook_pattern` / `attn.hook_attn_scores` and pre/post-RoPE Q/K are non-fireable (fused kernels); interventions are declarative specs only. (vLLM-Lens can reconstruct attention from captured Q/K; TransformerLens's vLLM driver cannot.)
- You want the vLLM-Lens Inspect/HTTP workflow with per-request hooks — use vLLM-Lens directly.

**Pitfalls:**
- **Returned logits are reconstructed.** vLLM's sampler bypasses `lm_head`, so the driver rebuilds full-sequence logits host-side as `ln_final @ lm_head.weight.T`; if the unembedding weight is unreachable it falls back to final-position log-probs and the bridge rejects `return_type="loss"`.
- **`ln_final` convention.** vLLM materializes `ln_final` post-weight; the driver un-folds the capture so `ln_final.hook_normalized` matches the `boot_transformers` value — if the norm weight is unreachable it warns and serves the raw post-weight value.
- **`tensor_parallel_size` is incompatible with `enable_batching`.** Batched capture (`enable_batching=True`, for `batch_size > 1` / chunked prefill) uses an eager path; TP and PP compose with each other but not with batching.
- **Parity scripts exist.** `scripts/vllm_parity_report.py` (GPU-only) diffs every fireable hook against `boot_transformers`; run it before trusting a new model on the vLLM driver.

## Plain HuggingFace `transformers`

`transformers` is fine for:
- Tiny experiments (a few hundred prompts on a small model).
- Hook-based interpretability with `register_forward_hook` (see [`mech-interp.md`](mech-interp.md)).
- Loading models for one-shot fine-tuning.

For batched inference at any scale, switch to vLLM. `transformers.generate()` is dramatically slower than vLLM (often 5–20×).

## TGI and llama.cpp server

- **TGI** (Text Generation Inference, HuggingFace) — was the standard before vLLM ate the world; still used. OpenAI-compatible.
- **llama.cpp server** — for CPU/Mac inference of GGUF-quantized models. Fine for tiny experiments or laptop work.

## Activation extraction tradeoff matrix

| Method | Speed | Flexibility | Max model size | Notes |
|---|---|---|---|---|
| `register_forward_hook` (HF) | slow | high | one GPU's worth | The lowest-level option |
| TransformerLens | medium | very high (named hooks) | ~one GPU | Re-implements arch; supported model list |
| nnsight (local) | medium | very high | up to multi-GPU | Exact HF behavior |
| nnsight (NDIF remote) | latency-bound | very high | 405B / 1T | Free-ish, academic |
| vLLM-Lens | very high (≈vLLM, eager mode) | medium (residual stream + Python hooks at layer boundaries + Q/K capture; no intra-layer edits) | up to 1T tested | Production-scale; pins vLLM 0.30.0 (v1.3.0) |
| nnsight 0.8 on vLLM (`taps`) | high (91–96% of vLLM per release notes) | very high (nnsight trace syntax) | 70B / tp=8 reported | Pre-release; NDIF remote stays on 0.7 |
| TransformerLens 4 `RemoteBridge.boot_vllm` | high (vLLM) | medium (declarative `suppress`/`scale`/`add`/`set` on layer-boundary hooks; no gradients or attention patterns) | single-node TP/PP | Same hook names as local `boot_transformers` |
| baukit `TraceDict` | medium | low (read-only) | ~one GPU | Quick & dirty |

## Cross-cutting pitfalls

- **Don't mix dtypes silently.** vLLM's default is bfloat16; HF default is fp32 in many places. If you load a model in HF and an SAE trained on vLLM-extracted activations, do an explicit `.to(torch.bfloat16)` somewhere consistent.
- **Tokenizer drift.** vLLM uses HF tokenizers; subtle template differences (esp. for Llama / Gemma chat templates) shift activations. Always print and inspect a rendered prompt.
- **vLLM cache directory pressure.** vLLM caches compiled CUDA graphs and KV blocks; on rented boxes, set `VLLM_CACHE_ROOT` to a big disk.
- **"fp32" vLLM activations are TF32 in attention unless told otherwise.** vLLM's Triton attention kernel computes fp32 inputs in TF32; vLLM-Lens sets `TRITON_F32_DEFAULT=ieee` for fp32 models since v1.3.0, but a plain vLLM server or an older plugin leaks ~1e-3 relative error per layer into activations. Compare against HuggingFace fp32 only after checking this.
- **OpenAI-compatible API ≠ identical behavior.** vLLM's `/v1/chat/completions` accepts the OpenAI schema but not every parameter (logit_bias, etc.) is implemented for every backend.

## Cross-references

- Mech interp libraries: [`mech-interp.md`](mech-interp.md).
- Steering at scale: [`steering.md`](steering.md).
- Eval framework integration: [`evals.md`](../evaluation/evals.md) (Inspect AI works with all of these as model providers).
- Compute (GPUs to host vLLM on): [`compute.md`](../models-and-compute/compute.md).

---

## Common questions

### Should I use vLLM or HuggingFace transformers?

For ≥100 prompts: **vLLM**. It's typically 5–20× faster for batched inference. Use HF `transformers` only for tiny one-off experiments, hook-based interpretability, or single-shot loads. For a large eval, switching the model provider from `hf/...` to `vllm/...` in your eval framework is usually the single biggest speedup available.

### How do I get activations from a 70B+ model?

Four options: (1) **vLLM-Lens** (`pip install vllm-lens`) — fast residual-stream extraction at vLLM throughput; supports tensor-parallel and 1T-parameter models. Pass extraction config via `SamplingParams.extra_args={"output_residual_stream": [layers]}` (offline) or `GenerateConfig.extra_body={"extra_args": {...}}` (Inspect). (2) **NDIF** via nnsight remote — free academic compute, latency-bound. (3) Local nnsight with `device_map="auto"` across multiple GPUs, or nnsight 0.8's vLLM runtime (`taps`). (4) TransformerLens 4's `RemoteBridge.boot_vllm` for the same hook names as a local model, with declarative interventions. Plain TransformerLens `boot_transformers` scales poorly above ~27B.

### What is vLLM-Lens?

vLLM-Lens (UK AISI; `UKGovernmentBEIS/vllm-lens` on GitHub, v1.3.0) is a **vLLM plugin + Inspect AI model provider** that adds **residual-stream activation extraction**, **steering vector application**, **per-layer Python hooks** (v1.2.0) and **attention Q/K capture with offline pattern reconstruction** (v1.3.0) to vLLM serving at near-vLLM throughput. Benchmarks (April 2026 announcement, OPT-30B): 8.1× faster than HF Transformers with hooks, 10.6× faster than nnsight + vLLM, 44.8× faster than TransformerLens, ~20% slower than vanilla vLLM. It pins `vllm==0.30.0` and forces eager mode (`VLLM_LENS_DISABLE=1` turns it off).

### What is NDIF?

NDIF = **National Deep Inference Fabric** (nsf-funded). A research compute pool hosting very large models (Llama-3.1-405B, etc.) accessible via the **nnsight** library's remote backend. Free for academic use; latency-bound (network round-trip per intervention). Use for small experiments on huge models you can't host yourself; not for high-throughput.

### How do I host a Llama model with an OpenAI-compatible API?

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct \
    --port 8000 --gpu-memory-utilization 0.85
```
Reachable at `http://localhost:8000/v1/chat/completions`. Inspect AI, safety-tooling, lm-eval-harness, and most other tools support OpenAI-compatible endpoints — point them at this URL.

### vLLM is slow on the first request — why?

vLLM compiles CUDA graphs and warms up the KV cache on first call. Subsequent requests are fast. If first-request latency matters (interactive demos), use **sglang** instead (similar API, lower cold-start) or **Groq** (very-fast hosted Llama inference). vLLM is throughput-optimized, not latency-optimized.

### What does `gpu_memory_utilization` do?

vLLM allocates this fraction of GPU memory for KV cache + model. Default 0.9. If you're hitting OOM at startup or with long context, drop to 0.85 or 0.80. The remaining memory is left for CUDA workspace and other overhead.

### How do I run a 70B model on one A100 80GB?

Quantize. `vllm serve meta-llama/Llama-3.1-70B-Instruct-AWQ-INT4 --quantization awq` — fits in ~40GB, runs at ~half the speed of fp16. Quality loss is small for most tasks. For interpretability that needs un-quantized activations, you'll need ≥2 GPUs or use NDIF.

---

Last verified: 2026-10. vLLM-Lens released by UK AISI (`UKGovernmentBEIS/vllm-lens`). NDIF active under nnsight. vLLM and sglang both in rapid development; check release notes. (Citation audit 2026-06: corrected the vLLM-Lens benchmark post date to April 2026, added its URL, and clarified the OPT-30B benchmark vs the 1T downstream-use figure. Additions 2026-06: cited the two named serving techniques — PagedAttention (Kwon et al. 2309.06180) and RadixAttention/SGLang (Zheng et al. 2312.07104); both verified via arXiv.) (Additions 2026-10: vLLM-Lens v1.2.0/v1.2.1/v1.3.0 release notes and README — generic hooks, Q/K capture, binary transport, steering-via-`LLM.chat` bug, vLLM 0.30.0 pin, TF32 default — and corrected the Inspect `extra_body` key names (`output_residual_stream`, `apply_steering_vectors`; checked against the v1.0.0 and v1.3.0 READMEs); nnsight 0.7.0 `nnsight-serve` and 0.8.0rc1 vLLM-taps release notes; TransformerLens 4.0 `drivers.md` (`RemoteBridge.boot_vllm` / `boot_inspect`); all verified via `gh api` and PyPI. Throughput figures for nnsight 0.8 and TL drivers are the maintainers' own.)
