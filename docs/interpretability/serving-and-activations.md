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
| Fast inference + extract residual-stream activations + apply steering | **vLLM-Lens** (UK AISI) |
| Run interpretability on a 405B / 1T model you can't host | **NDIF** (nnsight remote backend) |
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

Aliases: `vllm-lens` on PyPI, `UKGovernmentBEIS/vllm-lens` on GitHub, "AISI's vLLM activation lens", "the fast interp tool". UK AISI.

**What it is.** A vLLM plugin + Inspect AI model provider that adds **residual-stream activation extraction** and **steering vector application** to vLLM serving — at near-vLLM throughput. Auto-registers as a vLLM plugin and Inspect provider on install.

**When to use it:**
- You need activations from a 70B / 405B / 1T model at scale — TransformerLens won't fit, nnsight + vLLM was 10× slower.
- You want to apply steering vectors during a large eval run.
- You want to run probes ("activation oracles") online during generation, e.g. for safety-monitor classifiers.
- You're combining black-box (just generate) and white-box (probe activations) techniques in the same batch.

**Performance** (per the vLLM-Lens announcement [LessWrong post](https://www.lesswrong.com/posts/3bs27nZQuEcKhXf7q/vllm-lens-fast-interpretability-tooling-that-scales-to), April 2026; headline benchmark run on OPT-30B):
- **8.1× faster** than HuggingFace `transformers` with hooks.
- **10.6× faster** than nnsight 0.6.3 + vLLM.
- **44.8× faster** than TransformerLens.
- Only **~20% slower** than vanilla vLLM (no extraction).
- Used on models from ~27B up to 1T (the latter via downstream work, e.g. evaluation-awareness on Kimi K2.5), across 1–5 nodes.

**When *not* to use it:**
- You need flexibility — vLLM-Lens is **residual-stream only**; for arbitrary hook points (attn pattern, mlp internal, head output), use TransformerLens or nnsight.
- You want to *modify* internal MLP/attention computation — not supported; only residual-stream addition.
- Small experiments where TransformerLens / nnsight is enough.

**Pitfalls:**
- **Subset of techniques.** Don't expect attention pattern hooks or per-head ablation; the abstraction is residual-stream-only.
- **Extending requires editing the source.** Adding new hook types isn't a per-call config; it's a code change. Plan accordingly.
- **Steering vectors are passed via `GenerateConfig.extra_body`.** Tensors are auto-serialized for HTTP transport (PyTorch tensors → bytes; activations come back base64-encoded). Read the docs for the format.
- **Plugin auto-registration.** On install, it registers as a vLLM plugin and Inspect model provider with the `vllm-lens/` prefix. If you don't see it, check `inspect cache list` / restart.

```python
# Inspect AI integration:
from inspect_ai.model import GenerateConfig
config = GenerateConfig(extra_body={
    "extract_residual": {"layers": [15, 20], "positions": [-1]},
    "steering_vectors": [{"layer": 15, "vector": my_vec, "scale": 1.0}],
})
# inspect eval my_eval --model vllm-lens/meta-llama/Llama-3.1-70B-Instruct
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
- **Activation-shape sanity.** Same code runs locally on a 1B model and remotely on a 405B model — but shape and behavior may differ in subtle ways. Test locally with the same architecture family first.

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
| vLLM-Lens | very high (≈vLLM) | low (residual only) | up to 1T tested | Production-scale |
| baukit `TraceDict` | medium | low (read-only) | ~one GPU | Quick & dirty |

## Cross-cutting pitfalls

- **Don't mix dtypes silently.** vLLM's default is bfloat16; HF default is fp32 in many places. If you load a model in HF and an SAE trained on vLLM-extracted activations, do an explicit `.to(torch.bfloat16)` somewhere consistent.
- **Tokenizer drift.** vLLM uses HF tokenizers; subtle template differences (esp. for Llama / Gemma chat templates) shift activations. Always print and inspect a rendered prompt.
- **vLLM cache directory pressure.** vLLM caches compiled CUDA graphs and KV blocks; on rented boxes, set `VLLM_CACHE_ROOT` to a big disk.
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

Three options: (1) **vLLM-Lens** (`pip install vllm-lens`) — fast residual-stream extraction at vLLM throughput; supports tensor-parallel and 1T-parameter models. Pass extraction config via `GenerateConfig.extra_body`. (2) **NDIF** via nnsight remote — free academic compute, latency-bound. (3) Local nnsight with `device_map="auto"` across multiple GPUs. TransformerLens scales poorly above ~27B.

### What is vLLM-Lens?

vLLM-Lens (UK AISI; `UKGovernmentBEIS/vllm-lens` on GitHub) is a **vLLM plugin + Inspect AI model provider** that adds **residual-stream activation extraction** and **steering vector application** to vLLM serving at near-vLLM throughput. Benchmarks: 8.1× faster than HF Transformers with hooks, 10.6× faster than nnsight + vLLM, 44.8× faster than TransformerLens, ~20% slower than vanilla vLLM.

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

Last verified: 2026-06. vLLM-Lens released by UK AISI (`UKGovernmentBEIS/vllm-lens`). NDIF active under nnsight. vLLM and sglang both in rapid development; check release notes. (Citation audit 2026-06: corrected the vLLM-Lens benchmark post date to April 2026, added its URL, and clarified the OPT-30B benchmark vs the 1T downstream-use figure. Additions 2026-06: cited the two named serving techniques — PagedAttention (Kwon et al. 2309.06180) and RadixAttention/SGLang (Zheng et al. 2312.07104); both verified via arXiv.)
