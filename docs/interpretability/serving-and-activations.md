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
| Same hook names / intervention code on a vLLM-served model as on a local one | **TransformerLens 4 `RemoteBridge.boot_vllm`** (declarative interventions) or **nnsight 0.8 on vLLM** (taps; use ≥0.8.3: 0.8.2 fixed tensor-parallel and concurrent-request results, 0.8.3 fixed saves read over `serve=`) |
| One API for capture + steering on HF eager *or* vLLM, with 34 standardized hook "points" checked against TransformerLens/nnsight/nnterp, and a GPU sizer | **interp-engine** (Neuronpedia's engine, v1.14.3) |
| Watch logit-lens / J-lens readouts live while an existing app or agent talks to a local model through an OpenAI-compatible endpoint | **brainscope** (single-author instrument; see Common questions) |
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

- **`gpu_memory_utilization`: the default changed from 0.92 to 1.0 in vLLM 0.34.0 (2026-11-16).** In vLLM 0.20 through 0.33 the default is 0.92 (`vllm/config/cache.py` at those tags; it was 0.9 through 0.19) and can OOM at long context; drop to 0.85 if you see CUDA OOM at startup. From 0.34.0 the "extensible KV cache" is on by default, the KV cache is sized "from memory actually free **after** CUDA graph capture and warmup", and `gpu_memory_utilization` "defaults to 1.0" when unset; the release notes say "In most cases it's now best to not set `gpu_memory_utilization`" and to "Use it to share a GPU with other processes or when extensible kv cache is disabled." So on ≥0.34.0 a second process on the same GPU (a training job, a probe-fitting script, another server) finds the memory taken unless you pass `--gpu-memory-utilization` explicitly; the release notes' opt-out is `--gpu-memory-utilization 0.9` or `--no-enable-extensible-kv-cache` (with the extensible KV cache off, the 0.34.0 default is again 0.92). Symptom: `CUDA out of memory` in the *other* process right after a vLLM upgrade.
- **Tensor parallel size must divide attention heads.** A 70B model with 64 heads supports `--tensor-parallel-size {1,2,4,8}` but not 3.
- **First-token latency is high; throughput is high.** vLLM is for batched throughput; for low-latency single-prompt use, sglang or TGI may be faster.
- **Quantization options change frequently.** AWQ, GPTQ, FP8, INT4 — check vLLM's current support matrix for your model.
- **Chat templates.** vLLM uses the model's HF chat template by default; verify with `--chat-template` or by inspecting `tokenizer.apply_chat_template` output.
- **vLLM 0.32.0 (2026-10-18) traps that matter for activation work** (release notes): Python 3.10 is dropped (minimum 3.11) and vLLM now requires `transformers>=5.16.1,<5.20.0`, so a training environment on transformers 5.20.x cannot share an environment with it; `max_tokens` "is an upper bound instead of a reservation", so long prompts are accepted and generation is silently clamped — check `finish_reason == "length"` before treating a capture as a complete response; GLM-5.x now defaults to an **FP8 KV cache** on SM100 (Blackwell) under `--kv-cache-dtype auto`, which changes attention numerics, so record the KV-cache dtype with any activations and pin it when comparing runs; and it fixes "silent CUTLASS NVFP4/MXFP4 MoE corruption under EP" (expert parallelism; PR #59042 reports ~0% GSM8K on an MXFP4 GLM-5.3 with EP=8), so re-check activations or outputs from FP4/MXFP4 MoE models served with expert parallelism on earlier versions. Most activation plugins below pin older vLLMs (vLLM-Lens 1.3.0: 0.30.0; interp-engine 1.14.3: 0.28.0; nnsight ≤0.8.2's `[vllm]` extra: 0.27), so these changes reach you only on a plain or newer-pinned vLLM; nnsight 0.8.3+ and nnterp 2.0.0 pin vLLM 0.33, which has them.
- **vLLM 0.33.0 (PyPI, 2026-11-02)** requires `transformers>=5.16.1,<5.21.0` and pins `torch==2.14.0`, with `requires-python` `>=3.11,<3.15`. Python, CUDA and driver consequences (including uv ≥ 0.13 downloading Python 3.15 when nothing is pinned and no compatible Python is installed; vLLM cannot install there) are written up in [`code-recipes.md`](../engineering/code-recipes.md). nnsight 0.8.3+ and nnterp 2.0.0 target 0.33 (`vllm>=0.33,<0.34`); the other activation plugins on this page pin older versions. Per the nnsight 0.8.3 notes, "0.33 is the last vLLM release with the V1 runner".
- **vLLM 0.34.0 (PyPI, 2026-11-16) is current, and it removes Model Runner V1.** From the release notes' "Before you upgrade" table: "Model Runner V1 removed | Remove `VLLM_USE_V2_MODEL_RUNNER=0`; it now fails at startup. Port V1 logits processors to `vllm.v1.worker.gpu.sample.logits_processor`"; "Default `--block-size` is 64 (was 16)"; "`huggingface_hub >= 2.0.0` required" (also `tokenizers >= 0.23.3`). PyPI metadata: `transformers>=5.16.1,<5.23.0`, `torch==2.14.0`, `requires-python` `>=3.11,<3.15`. Consequences for activation work: any plugin that relies on the V1 runner (vLLM-Lens 1.3.0 sets `VLLM_USE_V2_MODEL_RUNNER=0` in its README) cannot be moved to 0.34 by overriding its pin; no activation plugin on this page targets 0.34 as of 2026-11-23; and the stated trade-off of the new KV-cache sizing is "TPOT +6–18% on some H200 models at concurrency 128" (TPOT = time per output token), so re-measure throughput rather than reusing a 0.33 number.
- **LoRA adapters served by vLLM before 0.34.0 could be applied only in part, with no warning.** Two fixes listed in the 0.34.0 changelog (the first affected version is not stated for either): "LoRA adapters on modules vLLM does not wrap are refused (#63489)" — before, "vLLM loaded these adapters and ignored those weights without a warning, so outputs differed from transformers + PEFT" (the PR's measured example is a `bert-base-uncased` emotion-classifier adapter with LoRA weights on `bert.pooler.dense`, the kind `target_modules="all-linear"` produces: 94.2% accuracy with transformers + PEFT and 88.2% with vLLM on the first 500 rows of the `dair-ai/emotion` test split); and "embedding LoRA scaled by `embed_scale` (#62470)" — on Transformers-backend models with a scaled input embedding (VaultGemma; Gemma with `--model-impl transformers`), "an `embed_tokens` LoRA adapter gets only `1 / embed_scale` of its effect". If your model organism is a LoRA (Low-Rank Adaptation) adapter served by vLLM, and the adapter targets embeddings or modules outside the usual attention/MLP projections (`target_modules="all-linear"`, `modules_to_save`), compare a few prompts' logits against transformers + PEFT before trusting activations or eval scores from the served model. From 0.34.0 the first case fails at adapter load (HTTP 500 from `/v1/load_lora_adapter`) instead of serving a partly applied adapter.
- **Do not expose a vLLM server to the network without an API key (security advisories, 2026-10-27 to 2026-11-18).** `vllm-project/vllm` published thirteen advisories in that period (repository security-advisories API, read 2026-11-23), two rated high: GHSA-q9v9-qpjp-fc24 ("Unauthenticated EngineCore crash via out-of-range prompt token id under skip_tokenizer_init", affected `>= 0.28.0, < 0.33.0`) and GHSA-5r3c-5x4v-8gjh ("Missing request-wide media budget allows single-request frontend resource exhaustion", `>= 0.6.0, < 0.33.0`). GHSA-qrj2-j723-m6w8 (medium, `< 0.33.0`) is about what gets served: a repository whose `config.json` carries a `speculators_config` key "redirects the whole served model identity — weights, config and tokenizer — to a directory the artifact names", with `trust_remote_code` left `False`. GHSA-xgh8-qwjh-q853 (medium) lets a caller of `POST /v1/systemone` supply a chat template although the server disallows request-supplied templates; its text says it "affects vLLM 0.32.0rc0 through 0.33.0. Version 0.34.0 applies the template trust check", while its machine-readable range reads `>= 0.32.0rc0, <= 0.34.0` with patched version 0.34.0 — the two are inconsistent as published. The older pinned vLLMs of the activation plugins (0.20.x, 0.27, 0.28.0, 0.30.0) each fall inside the ranges of several of the advisories patched in 0.31.0 and 0.33.0 (GHSA-5r3c and GHSA-qrj2 cover all four), and the plugins cannot move forward yet, so bind those servers to localhost or an SSH tunnel and set `--api-key`. Body text was read only for GHSA-xgh8 and the summary of GHSA-qrj2; for the other eleven, only titles, severities and version ranges.
- **vLLM pins `torch==2.14.0`, which is inside a PyTorch advisory for `torch.load(weights_only=True)`.** PyTorch advisory GHSA-v32g-mr63-3j83 (published 2026-11-10, high): "A malicious PyTorch checkpoint can read text files from the computer loading it, even when it is loaded with `weights_only=True`"; "Tested vulnerable on PyTorch `2.14.0+cpu` and `2.14.1`"; the advisory metadata gives the vulnerable range `>=2.14.0` and patched version `2.15.0`. vLLM 0.33.0 and 0.34.0 pin `torch==2.14.0` and SGLang 0.5.23 pins `torch==2.14.1` (PyPI `requires_dist`), so a serving environment cannot simply upgrade torch. In such an environment do not `torch.load` third-party pickle-format files (`.pt`, `.bin`, `.pth`: community probes, steering vectors, SAEs (sparse autoencoders), adapters); use `.safetensors` files, or load untrusted checkpoints in a separate torch ≥2.15 environment. Not stated in the advisory: whether torch versions before 2.14 are affected, and whether a patched 2.14.x release is planned (PyPI had none as of 2026-11-23). Details and the list of other packages that hold torch below 2.15: [`code-recipes.md`](../engineering/code-recipes.md#standard-pyprojecttoml-baseline).
- **Two models on one vLLM engine are not isolated from each other (2026-11).** Deshpande & Africa (LessWrong, 2026-11-19; Qwen3-8B on one L40S, a contrived setup by the author's description) trained models to signal through the engine's step size and through its shared KV cache. The mitigations the post lists: serve the two roles (for example policy and monitor) from different engine instances; turn on vLLM's batch-invariant kernels (`VLLM_BATCH_INVARIANT=1`, see [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md#reproducibility-checklist-for-safety-research)), which closes the step-size channel; and per-user cache isolation / cache salting, which closes the KV-cache channel. Not verified: the vLLM documentation pages for batch invariance and cache salting as they bear on this attack. Numbers and the untrusted-monitoring demonstration: [`ai-control.md`](../oversight-and-control/ai-control.md#untrusted-monitoring-and-collusion-what-2026-work-adds).

```bash
# pip install vllm
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --tensor-parallel-size 4 \
    --gpu-memory-utilization 0.85   # on vLLM >=0.34.0 omit this unless the GPU is shared (default is now 1.0)
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
- **Pinned vLLM.** v1.3.0 pins `vllm==0.30.0` (GPU-validated; V1/eager execution only; V2 model runner and native CUDA graphs are outside the validated configuration — the plugin gives a clear error on the V2 runner; the README's serve example sets `VLLM_USE_V2_MODEL_RUNNER=0`). Other vLLM versions may import but are untested. vLLM 0.34.0 (2026-11-16) removed Model Runner V1 — per its release notes `VLLM_USE_V2_MODEL_RUNNER=0` "now fails at startup" — so vLLM-Lens 1.3.0 (still the latest release on 2026-11-23) cannot be carried to vLLM ≥0.34 by overriding the pin; it needs a new vLLM-Lens release.
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

## interp-engine (Neuronpedia's inference engine)

Aliases: interp-engine, `interp-engine` on PyPI, `interp_engine` (import name), `decoderesearch/interp-engine` on GitHub, interp-engine.org, "Neuronpedia inference engine", Johnny Lin / Decode Research, "points" / "addresses" (`resid_post.10`), `vllm-static`, GPU sizer.

**What it is.** A capture-and-steering engine with one API over four backends: `eager` (HF transformers; low VRAM, low speed), `vllm` (the default; every point, chosen per request), `vllm-static` (CUDA-graph taps on a declared set of points only — highest throughput, more VRAM) and `vllm-generate` (generation only, no capture or steering). Hook locations are standardized as **34 "points"** across architectures (all 34 on eager, 28 on vLLM), e.g. `Address("resid_post", 10)` or the string `"resid_post.10"`, and a bundled `validator/` compares them against TransformerLens and nnsight/nnterp across 50+ models; a per-point "cheat sheet" is at interp-engine.org. Per the README, it "powers all of Neuronpedia's inference" (the Neuronpedia inference server moved to interp-engine 1.13.2 on 2026-10-10). Apache-2.0; created 2026-08-05; release **v1.14.3 (2026-10-27)**, also on PyPI; Python ≥3.11, <3.14. Patch releases since v1.14.0 (release notes): **1.14.1** (2026-10-16) "a tool call is a turn's content, not its header" — per the commit (46929d9), on Qwen3.6 an assistant turn that only calls a tool had the whole call, up to the turn-end token, marked as message header rather than content (shown in the J-Lens chat as dim chips); the commit does not say whether captured token positions also changed, so recheck tool-call transcripts captured with 1.14.0 that rely on header/content masks; **1.14.2** (2026-10-16) declares the `value` and `k_norm` points KV-head wide and corrects the vLLM point docs; **1.14.3** (2026-10-27) cuts an additive steer at a tensor-parallel-sharded point (`mlp_act`, `z`) to each rank's slice — before, a full-width vector there failed with an error from inside the forward, and ops that project onto the whole vector, and KV-head points, are now refused under TP at registration — and reads Granite's MoE router in the default order from transformers 5.21. Neuronpedia's inference server moved to 1.14.3 on 2026-10-27.

```bash
pip install 'interp-engine[vllm]'   # vLLM backend (Linux/CUDA only); pins vllm==0.28.0
pip install interp-engine           # eager backend only (CPU/CUDA/MPS); needs transformers>=4.57.1
```

```python
# From the README (its comments shortened)
from interp_engine import Address, capture, load_model

model = load_model("Qwen/Qwen3-8B")                       # backend="vllm" by default
# model = load_model("Qwen/Qwen3-8B", backend="vllm-static")   # only the points you declare
# model = load_model("Qwen/Qwen3-8B", backend="eager")

point = Address("resid_post", 10)      # or string: "resid_post.10"
cache = capture(model, model.to_tokens("Hello, world"), [point])
cache[point]  # [batch, pos, ...]
```

**What else is in it** (`docs/USAGE.md`, read 2026-10-14):

- **Steering** with six ops applied identically on every backend: `AddSpec` (`scale * vector`), `OrthogonalDecompSpec`, `ProjectionCapSpec`, `NormScaledAddSpec` (`strength * ‖h‖ * vector`, capped at `max_fraction * ‖h‖`, so one strength means the same fraction of the residual at every layer), `AblateSpec` and `SwapSpec`. Use a spec per request (`steering_spec=`) or as a context: `with steer(model, spec): completion, acts = capture_generation(model, tokens, ["resid_post.10"], max_tokens=8)`. On vLLM the context registers the steer per request, so a co-batched request is unaffected.
- **Logit lens through the real final norm**: `model.decode_residuals(residuals)` sends `[n_rows, d_model]` through the model's `final_norm` and `lm_head` and applies the family's logit softcapping itself.
- **Hook-name translators for porting code**: `tlens_hook_to_point`, `point_to_tlens_hook`, `nnsight_accessor_to_point`; unmappable names raise `UnmappedHook` instead of guessing. Pass the model to `tlens_hook_to_point` — that is what makes it correct on sandwich-norm models (Gemma 2/3/4, OLMo 2/3); see [`mech-interp.md`](mech-interp.md#the-sandwich-norm-hook-trap-gemma-234-olmo-23).
- **GPU sizer** (interp-engine.org/sizer/<model>) for choosing hardware and backend before you OOM.

**When to use it:** you want the same capture/steering code to run on a laptop (eager) and at vLLM throughput, standardized hook names across many architectures, Neuronpedia-compatible points, or a model family other tools do not reach yet (the README benchmarks DeepSeek-V4-Flash and Qwen3.8-27B).

**When *not* to use it:**

- You need gradients **through** the model at vLLM speed (attribution patching, Jacobian-lens fitting): on vLLM, `grad_support.through_forward` is "never" and requests raise `GradientsUnsupported`; "a linear probe on captured activations trains fine on either backend. Attribution that needs a gradient *of the model* is eager-only" (`docs/GRADIENTS.md`). Use the eager backend, TransformerLens or nnsight.
- Your environment is pinned to a vLLM other than **0.28.0** — the `[vllm]` extra is an exact pin because the engine patches vLLM internals. That is a different vLLM from vLLM-Lens 1.3.0 (`vllm==0.30.0`), nnsight's `[vllm]` extra (`>=0.33,<0.34` from nnsight 0.8.3; `>=0.27.1,<0.28` in 0.8.2) and TransformerLens's `[vllm]` extra (a 0.20.x band), so these cannot share one environment.
- You want Inspect AI integration out of the box (vLLM-Lens has it).

**Pitfalls (README caveats and `docs/USAGE.md`; searchable names in code font):**

- **`await model.shutdown()` "is required before loading a second model in the same process on vLLM"** — the KV cache lives in a child process that dropping the Python reference does not reap.
- **`ForeignEventLoop`.** A vLLM model is bound to the event loop that first built its engine; awaiting it from another loop raises `ForeignEventLoop`. `asyncio.run(startup())` closes its loop on exit, so a server whose engine was built that way never answers its first request. In notebooks and scripts, use the sync free functions or `sync_model(load_model(...))`, which holds one loop for the model's life.
- **A capture taken with `steering_spec=` returns the *steered* forward pass's activations**, not a second unsteered one.
- **Not portable between backends, by design:** `GenStep.logits` is `None` on vLLM (ask for `n_logprobs=k`), and the free function `interp_engine.decode_residuals` is eager-only and returns raw logits (use the method, which softcaps on both). Anything else unsupported raises `CapabilityUnsupported` naming the alternative.
- **Gemma 4 needs `transformers==5.14.1`**; **gpt-oss MXFP4 checkpoints need `interp-engine[quant]`**, otherwise transformers dequantizes them to bf16 "at roughly 3x the weights"; **`gemma-4-26B-A4B-it` on `vllm-static` on B200/B300 needs `VLLM_BATCH_INVARIANT=1`** (the engine refuses the combination at load and names the flag).

## sglang

Aliases: `sglang` on PyPI, `sgl-project/sglang` on GitHub.

**What it is.** A serving engine optimized for **structured generation** and **agent-style multi-turn workflows** with KV cache reuse across turns (RadixAttention — an LRU radix-tree cache of KV blocks; Zheng et al. 2023, "SGLang: Efficient Execution of Structured Language Model Programs", arXiv:2312.07104). Often faster than vLLM for agent traces with shared prefixes.

**When to use it:**

- Multi-turn agent evals where prompts share long prefixes (system prompt + tool history).
- Constrained generation with structured outputs.
- You're already familiar with it.

**When *not* to use it:**

- Pure batch inference on independent prompts — vLLM is the safer default and better-supported by ecosystem tools.
- You want activation extraction — no public equivalent of vLLM-Lens for sglang turned up in a GitHub search on 2026-10-20. Goodfire reports running probes *inside* an extended SGLang engine on Kimi K3 with "a less than 2% decrease, which is within noise" in throughput (goodfire.com/research/production-cyber-monitors-on-kimi-k3, 2026-10-08), but that code is not released; see [`probes.md`](probes.md#frontier-scale-deception-probes-far-caught-in-the-act-and-fibs).

**Pitfalls:**

- **SGLang 0.5.22 (2026-10-19) requires Python ≥3.11** and fixes a bug its notes flag as an "Important fix": "Hybrid linear models could resume from wrong mamba states when speculative decoding and structured output were used together" (PR #43029), plus "wrong tokens from compact-verify CUDA graphs when a token tier is captured more than once" (PR #42709). If you generated data from a hybrid linear-attention model with speculative decoding *and* structured output on an earlier version, regenerate it.

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
- **Client/server version split.** nnsight 0.8 became the stable PyPI release on 2026-10-16 (0.8.1 on 2026-10-20, 0.8.2 on 2026-11-02, 0.8.3 on 2026-11-18, 0.8.4 on 2026-11-23), so an unpinned install is now 0.8. 0.8.2 caps `httpx<1` because "The httpx 1.0 previews remove `Timeout` and `AsyncClient`, so every remote call failed with an `AttributeError`" — if you see that error from a remote trace on an older nnsight, pin `httpx<1`. The 0.8.0rc1 release notes said remote execution against NDIF stays on v0.7 until NDIF is upgraded; the 0.8.0–0.8.2 notes do not repeat that caveat and add remote-request features (0.8.1 carries `trust_remote_code` in the model key and the attention implementation with every remote request), but NDIF's support for 0.8 clients was not confirmed here. Two later notes touch remote use: 0.8.3 fixes a failure under anyio 4.15 (`TypeError: Attribute 'save' is missing its type annotation`) that "broke any FastAPI app that imports nnsight, and on NDIF it rejected every request over 1 MB"; and 0.8.4 fixes the meta-model build for vision-language checkpoints under `task="text-generation"` (PR #851 names Llava and the Inkling models), where before "a server can load such a deployment and no client can reach it". Which nnsight version NDIF's hosted service runs was not checked. Check `nnsight.net/status` or the NDIF forum, and keep a `nnsight<0.8` environment for existing remote code until it is confirmed.
- **Activation-shape sanity.** Same code runs locally on a 1B model and remotely on a 405B model — but shape and behavior may differ in subtle ways. Test locally with the same architecture family first.

**Alternative for large *base* models without US residency: ACS Infra.** Vaněk, Kulveit, Havlíček, Frisch, Veronika_H, vgel, Douglas, Amis & Ali, *ACS Infra: free access to large base models for LLM psychology research* (LessWrong, 2026-10-20). A free hosted platform (apply at `infra.acsresearch.org/signup`) serving Llama 3.1 405B base, Llama 3.1 8B and Arcee's Trinity-Large-TrueBase (398B, 13B active, a pre-annealing checkpoint), with a completions API with logprobs, "activation harvesting and steering", a browser workbench and a loom. Per the post, NDIF "requires US residency or a US collaborator"; the post states no such requirement for ACS, and programs such as MATS can request batches of accounts by emailing `infra@acsresearch.org`. **When not to use it:** uptime-critical runs ("Capacity is sized for roughly 70-100 active researchers, models may rotate, the goal is not 100% uptime"); arbitrary intervention code (the post describes harvesting and steering, not a general tracing API — check what hooks it exposes before planning around it); post-trained chat models.

## nnsight on vLLM (`nnsight-serve`, CUDA-graph taps)

Aliases: `nnsight.modeling.vllm.VLLM`, `nnsight-serve`, "nnsight vLLM runtime", `ndif-team/nnsight`, `nnsight[vllm]`. nnsight 0.7.0 (2026-05-05) added `nnsight-serve`; nnsight 0.8 (0.8.0rc1 on 2026-09-09; stable 0.8.0 on 2026-10-16, 0.8.1 on 2026-10-20, 0.8.2 on 2026-11-02, 0.8.3 on 2026-11-18, **0.8.4 on 2026-11-23**) made vLLM a first-class runtime; 0.8.3 moved the integration to vLLM 0.33 and its V2 model runner. The 0.8.0 release adds "vllm: saved logits stay as read, saves ship their own rows, engines default to prefix caching off" (#743).

**What it is.** nnsight's trace syntax (`with model.trace(...)`) running *inside* a vLLM engine worker, so PagedAttention, continuous batching and tensor parallelism keep working under a trace. Per the release notes: **0.7** — `nnsight-serve <model> --port 6677 --tensor-parallel-size 4 --api-key ...` starts one vLLM engine behind an HTTP server, and a GPU-less client runs `with model.trace("...", serve="http://host:6677"):` with a meta model (`VLLM("Qwen/Qwen3-30B-A3B")`). **0.8** — `VLLM(..., taps=["model.layers.*.output"])` records the named locations into the CUDA graph as breaks and serves them on every replay, keeping CUDA graphs on; measured against vanilla vLLM the release notes report **96%** of throughput at 8B on one GPU, 93% at tp=4, 91% at tp=8 and 95% at 70B / tp=8. 0.8 also adds engine-wide `model.edit()` (installed once; every later request, including from clients that never heard of nnsight, gets a scoped copy, selectable per request with `edits=[...]`), `mode="async"` streaming, `n > 1`, and a prefix-cache recompute so cached tokens still reach interventions.

**nnterp on the same runtime.** `nnterp` 2.0.0 (stable on PyPI since 2026-11-18; `nnsight>=0.8`, `transformers>=5.19`, `vllm>=0.33,<0.34` in its `vllm` extra) adds `StandardizedVLLM`, described in its release notes as "the standard names and values on nnsight's vLLM engine" (added for 25 model families, then "35 more families"; on vLLM 0.33 "nine families on the transformers backend, MPT gone"). Use it when you want nnterp's cross-architecture names on a served model (library overview in [`mech-interp.md`](mech-interp.md)). **When not to use it:** as a drop-in upgrade for nnterp 1.x code — 2.0.0 is "a rewrite on nnsight 0.8" (PR #106) and is what a plain `pip install nnterp` now installs; the 1.x → 2.0 renames, two of which change the value returned, are listed in [`mech-interp.md`](mech-interp.md#nnterp), so pin `nnterp<2` until you have ported and re-checked your code.

**When to use it:** You want nnsight-style arbitrary intervention code (not just additive steering) on a served model, with the same syntax as local experiments; or an intervention-capable HTTP endpoint without running an NDIF cluster.

**When *not* to use it:** You only need residual-stream capture and steering at maximum throughput with Inspect integration → vLLM-Lens (benchmarked ~20% below vanilla vLLM, with eager mode). You need NDIF remote execution from the same environment before NDIF's 0.8 support is confirmed (see the NDIF section above). You have 0.7 code you cannot port yet — 0.8 has breaking changes (listed in [`mech-interp.md`](mech-interp.md#nnsight)); pin `nnsight<0.8`.

**Pitfalls:**

- **Re-run vLLM-runtime results from nnsight ≤ 0.8.1 that used tensor parallelism, LoRA or concurrent requests** — they could come back wrong without an error (0.8.2 release notes: "If you used any of the setups below on 0.8.1 or earlier, re-run those results on 0.8.2"). Under `tensor_parallel_size > 1`, gathered `qkv_proj` / `gate_up_proj` outputs were in rank order (`[q0 k0 v0 | q1 k1 v1]`), so per-head slices and `gate, up = x.chunk(2, -1)` were wrong (relative error vs tp=1 of 0.78 and 0.99 on Qwen2.5-0.5B at tp=2; 0.0046 and 0.0076 after the fix), and with fewer KV heads than ranks K and V came back once per rank; with `enable_lora=True` a block read one rank's shard; with several requests in flight, saves were shared across requests ("In a sustained run, 20 of 60 requests came back with such a name") and a `logits_processor` edit to one request's row could change another's token. Details in [`mech-interp.md`](mech-interp.md#nnsight).
- **Re-run results read over `serve=` (the `nnsight-serve` HTTP path) on nnsight ≤ 0.8.2 if a trace had several invokes or `n > 1`.** 0.8.3 release notes: "Over `serve=`, a trace returns what a local engine returns (#834). A name saved in several invokes came back as the last invoke's value alone, and a name saved under `n > 1` as the first sequence's alone." No error was raised; a local (in-process) engine was not affected by this one. The same release changes the shape under `n > 1` everywhere on vLLM: "every saved name is a list, one entry per sampled sequence, `tracer.result` included (#835). Read `result[1].outputs[0].text` where you read `result.outputs[1].text`. Traces with `n = 1` are unchanged." Also fixed in 0.8.3: "A `tracer.stop()` in one invoke swallowed a real error raised in another" over `serve=`.
- **Pin the vLLM version to what your nnsight release targets.** nnsight 0.8.3 and 0.8.4 pin the `vllm` extra to `vllm>=0.33,<0.34` (PyPI `requires_dist`) and run on vLLM's V2 model runner; the 0.8.3 notes add that vLLM 0.33 "needs Python 3.11 or newer and `transformers<5.21`, and publishes only a CUDA 13 wheel". nnsight 0.8.2 pinned `vllm>=0.27.1,<0.28`, and unpinned `nnsight[vllm]` before 0.8.2 installed vLLM 0.32, "where taps stop firing after the prefill without an error" (symptom: saved tensors only for prompt tokens, nothing for generated steps). If you install vLLM yourself next to nnsight, keep it at 0.33.x for nnsight ≥0.8.3 and 0.27.x for 0.8.2; vLLM 0.34 is outside every nnsight pin as of 2026-11-23.
- **0.8.3 refuses three more engine setups at startup**, "each with a message that says what to change (#838): a fallback to the V1 runner, `enable_batch_sharded_sampling=True`, and `taps` with a `cudagraph_mode` that has full graphs." Other 0.8.3 behaviour changes on vLLM: "a trace that raises binds none of its saved names" (code that read partial results after catching a trace's error no longer finds them), and `tracer.stop()` on a request with `min_tokens` "ends it at once, not after `min_tokens` tokens".
- **A pinned model `revision` could get the main branch's tokenizer on nnsight ≤ 0.8.2 (a `TransformersModel` loading bug on three load paths, not a vLLM one).** 0.8.3 notes: "A `cache_dir`, `token` or `revision` now reaches the tokenizer and other preprocessors on every load path: the lazy build, a `config=` load, and a pre-loaded module. Before, those paths fetched the tokenizer from the default cache and the main branch. ... a pinned `revision` got main's tokenizer with no error." If you extracted activations from a checkpoint pinned by revision (a training-step revision, a model-organism commit) whose tokenizer or chat template differs from `main`, re-extract on ≥0.8.3. Same release, Gemma: "Gemma returns noise unless its input starts with `<bos>`, and the Gemma 4 `-it` tokenizers leave it off a plain string. `model.trace("...")` ran without it and returned garbage with no error. nnsight now sets such a tokenizer to add `<bos>` when the model loads"; consequence: "a string that already starts with `<bos>`, such as a chat template rendered to text, now gets a second one. Pass the chat itself". And PEFT (Parameter-Efficient Fine-Tuning) adapters: "Attaching an adapter no longer freezes the base model (#824). On Qwen2.5-0.5B, 290 of 290 parameters required grad before an attach and detach, and 0 after"; new `disable_adapters()` / `enable_adapters()` switch an attached adapter off and on ("Switched off, the forward is the base model's, bit for bit"), which is the cheap way to capture base-vs-adapter activations from one loaded model.
- **Tensor parallelism on a local `TransformersModel` and the vLLM runtime now need separate environments.** 0.8.3 notes: "Tensor parallelism on a `TransformersModel` needs transformers 5.23 or newer ... Because vLLM 0.33 needs `transformers<5.21`, the two need separate environments." On nnsight ≤0.8.2 with transformers 5.23, lazy loading fails with `Impossible to guess which tokenizer to use` and every tensor-parallel load fails. `local_files_only=True` now "raises a `TypeError` when the model is built"; set `HF_HUB_OFFLINE=1` instead.
- **Refused at build time since 0.8.2** (`NotImplementedError`, naming the alternative): `speculative_config`, `data_parallel_size > 1` (on `mode="async"`, earlier versions returned "no saves and no error" for every engine but the first) and Ray's compiled-graph executor (`VLLM_USE_RAY_V2_EXECUTOR_BACKEND=0`).
- **Generation steps can overrun a stop.** Under `tracer.iter` or `tracer.all()` on vLLM, a block can see one step past a stop token or stop string, because async scheduling starts the next step before the token is known (0.8.2 docs).
- The `nnsight-serve` / 0.8 vLLM throughput figures above are the maintainers' own measurements on their hardware, not independently reproduced here; benchmark your own model and tap list before relying on 91–96%.

## TransformerLens `RemoteBridge` (vLLM and Inspect drivers)

Aliases: `RemoteBridge.boot_vllm`, `RemoteBridge.boot_inspect`, "TransformerLens drivers", `transformer-lens[vllm]` / `transformer-lens[inspect]` extras. New in TransformerLens 4.0 (2026-09-21).

**What it is.** TransformerLens 4 separates *what you study* (the bridge's hook names, cache and intervention surface) from *what runs the forward pass* (a **driver**): local HuggingFace `transformers` (full hooks and gradients), **vLLM** (`RemoteBridge.boot_vllm("meta-llama/Llama-3.2-1B", dtype=torch.float16, max_model_len=2048)`), or an **Inspect AI provider** (`RemoteBridge.boot_inspect(...)`, with a `capture_activations([...])` solver to save activations during an eval; `provider="vllm-lens"` targets a running vLLM-Lens server, residual-only and additive-steering-only). On vLLM, capture hooks are installed inside the worker before `torch.compile`; each hook also applies an affine transform `output * scale + bias`, so **declarative interventions** (`suppress` / `scale` / `add` / `set`, optionally position-scoped) propagate to downstream layers, e.g. `bridge.run_with_cache("Hello", intervene={"embed.hook_out": {"op": "suppress"}})`. Fireable vLLM hooks: `embed.hook_out`, `blocks.{i}.hook_out` / `attn.hook_out` / `mlp.hook_out`, `ln_final.hook_normalized`. Single-node tensor parallelism and pipeline parallelism are supported and GPU-validated per the docs; multi-node (Ray) is unsupported. Install `pip install "transformer-lens[vllm]"` (Linux-only extra; pins a validated vLLM 0.20.x band — `vllm>=0.20.2,<0.21` in `transformer-lens` 4.4.0, PyPI 2026-11-12 — which is *not* the vLLM version vllm-lens pins).

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
| nnsight 0.8 on vLLM (`taps`) | high (91–96% of vLLM per release notes) | very high (nnsight trace syntax) | 70B / tp=8 reported | Stable since 0.8.0 (2026-10-16); use ≥0.8.3 (0.8.2: TP/concurrency fixes; 0.8.3: `serve=` multi-invoke and `n > 1` saves, pinned-revision tokenizer); `[vllm]` extra pins vLLM 0.33 from 0.8.3 (0.27 in 0.8.2); breaks 0.7 code |
| TransformerLens 4 `RemoteBridge.boot_vllm` | high (vLLM) | medium (declarative `suppress`/`scale`/`add`/`set` on layer-boundary hooks; no gradients or attention patterns) | single-node TP/PP | Same hook names as local `boot_transformers` |
| interp-engine (`vllm` / `vllm-static`) | high; `vllm-static` higher (README B200 table: e.g. qwen3-4b 973 vs 2,219 aggregate tok/s at 8 concurrent requests, eager 61) | high (34 standardized points, 28 on vLLM; six steering ops; no gradients through the forward on vLLM) | per GPU sizer; README benchmarks up to DeepSeek-V4-Flash (fp8) | Pins vLLM 0.28.0; eager backend for gradients |
| baukit `TraceDict` | medium | low (read-only) | ~one GPU | Quick & dirty |

## Cross-cutting pitfalls

- **Don't mix dtypes silently.** vLLM's default is bfloat16; HF default is fp32 in many places. If you load a model in HF and an SAE trained on vLLM-extracted activations, do an explicit `.to(torch.bfloat16)` somewhere consistent.
- **Tokenizer drift.** vLLM uses HF tokenizers; subtle template differences (esp. for Llama / Gemma chat templates) shift activations. Always print and inspect a rendered prompt.
- **vLLM cache directory pressure.** vLLM caches compiled CUDA graphs and KV blocks; on rented boxes, set `VLLM_CACHE_ROOT` to a big disk.
- **"fp32" vLLM activations are TF32 in attention unless told otherwise.** vLLM's Triton attention kernel computes fp32 inputs in TF32; vLLM-Lens sets `TRITON_F32_DEFAULT=ieee` for fp32 models since v1.3.0, but a plain vLLM server or an older plugin leaks ~1e-3 relative error per layer into activations. Compare against HuggingFace fp32 only after checking this.
- **Each activation-serving tool pins its own vLLM.** As of 2026-11-23 (PyPI `requires_dist`): vLLM-Lens 1.3.0 pins `vllm==0.30.0`, interp-engine 1.14.3's `[vllm]` extra pins `vllm==0.28.0`, nnsight 0.8.3 / 0.8.4's `[vllm]` extra pins `vllm>=0.33,<0.34` (0.8.2: `>=0.27.1,<0.28`), `nnterp` 2.0.0's `vllm` extra pins `vllm>=0.33,<0.34` (the 2.0.0rc1 extra was unpinned), and TransformerLens 4.4.0's `[vllm]` extra pins `vllm>=0.20.2,<0.21`; EasySteer 0.29.0 overlays vLLM 0.29.0 (as of 2026-11-04, not re-checked). Plain vLLM is at 0.34.0 (2026-11-16), which no tool here targets and which removed the V1 model runner that vLLM-Lens 1.3.0 uses. Give each its own environment; a resolver error at install is the good outcome, a silently mismatched vLLM the bad one — nnsight before 0.8.2 left the extra unpinned, and on vLLM 0.32 its taps stopped after prefill with no error.
- **Storing activations for SAE (sparse autoencoder) training: you may need far fewer unique activations than tokens trained on.** Koriagin, Balagansky & Gavrilov, "Scaling Laws for SAE Training Data" (arXiv:[2611.07756](https://arxiv.org/abs/2611.07756), 2026-11-05) fix the total training budget and vary how many *unique* activations are stored: "Quality improves rapidly as the buffer grows, then reaches a plateau where replaying the buffer is nearly as effective as using fresh activations throughout training." Their rule: "choose the smallest buffer that reaches the quality plateau and replay it for the remaining budget"; in their experiments this cut activation storage by 8–64× "with negligible quality loss". Measured (per the abstract) across dictionary sizes and token budgets, early, middle and late layers of Llama-3.1, Qwen3 model sizes, and BatchTopK, TopK and JumpReLU SAEs, with explained variance, reconstruction MSE (mean squared error), feature absorption, automated interpretability and sparse probing as metrics. **When not to rely on it:** the plateau size is found empirically per setting (the abstract gives no universal number), so run a small buffer-size sweep on your own model and layer before deleting activations; a different activation source (the paper sweeps mathematical text and Python code) can move it. Abstract only was read; SAE training details are in [`saes.md`](saes.md).
- **Compressing an activation cache (fp16 / bf16 / int8 / int4) changes which SAE features you get, and "fraction of features retained" has no natural scale.** Yeung, "How Small Can We Go? Calibrating Activation-Cache Compression for SAE Training" (arXiv:[2611.08551](https://arxiv.org/abs/2611.08551), 2026-11-05): retraining an SAE on a compressed cache and counting how many original features still exist, "On a GPT-2 cache, rounding everything to fp16 keeps 60.6% of features, but changing one value in a million by the smallest step fp32 allows ... keeps only 70.5%. Meanwhile, changing the random seed keeps 23.0%." So a codec that "keeps 60%" is far above what a plain reseed keeps, and a number like that means nothing without both anchors. The paper's calibration: "retraining on identical bytes sets the ceiling, and a reseed sets the floor". With TopK SAEs on GPT-2 small and Pythia-1.4B, "naïve per-token int4 loses more features than a reseed everywhere we tested, as do PCA and random projection on GPT-2"; "Standardizing each channel before quantizing brings int4 back above the floor ... at the same raw file size"; and "a bf16 forward pass, which some pipelines use to save memory, loses slightly more features than rotated 8-bit storage" at the smallest budget tested. Practical reading: record the storage dtype *and* the forward-pass dtype of every activation cache; standardize per channel before any integer quantization; and do not claim a storage scheme "preserves the features" (or that two SAEs "found the same feature") without a reseed baseline. Small models and TopK SAEs only; abstract only was read.
- **Looped and non-residual architectures break "one hook per layer, one residual stream".** Inkling 2 Mini (Thinking Machines, open weights; added to `transformers` in 5.24.0, 2026-11-21) has 24 layers in 4 blocks of 6, where the two middle blocks run three times per forward pass (the `transformers` notes say "layers 6 to 17 run three times", counting from 0; Goodfire's write-up counts from 1: "the two core blocks (layers 7-18), which are looped three times"). Per Lee, Krishnamurthy, Merullo, Balsam & Lubana, "Interpreting Inkling 2 Mini" (goodfire.com/research/interpreting-inkling-2-mini, 2026-11-20), the model uses "attention residuals": "each layer reads from previous layer outputs using attention, rather than reading from a cumulative residual stream", so "there is no single residual stream running through the network. Instead, each block keeps a running sum of its own layers' outputs, starting from zero." What follows for extraction code (an inference from the architecture, not a tested statement about any tool on this page): a forward hook on a looped layer fires three times per token position, so a capture keyed by layer index alone overwrites or concatenates passes — index activations by (layer, loop pass); "residual stream at layer ℓ" (`resid_post`, `output_residual_stream`, a logit lens at layer ℓ, a per-layer SAE or steering vector) has no direct analogue, and the nearest objects are block outputs and each layer's attention-weighted input. No tool on this page documents support for this architecture as of 2026-11-23 (nnsight 0.8.4's notes mention only that the Inkling checkpoints can now be loaded under `task="text-generation"`); check a capture's shape and count before building on it.
- **On sandwich-norm models (Gemma 2/3/4, OLMo 2/3), check which "MLP output" a serving tool captures** before feeding it to an MLP SAE — the raw output and the post-norm contribution differ (cosine ~0.2–0.4); see [`mech-interp.md`](mech-interp.md#the-sandwich-norm-hook-trap-gemma-234-olmo-23).
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

Five options: (1) **vLLM-Lens** (`pip install vllm-lens`) — fast residual-stream extraction at vLLM throughput; supports tensor-parallel and 1T-parameter models. Pass extraction config via `SamplingParams.extra_args={"output_residual_stream": [layers]}` (offline) or `GenerateConfig.extra_body={"extra_args": {...}}` (Inspect). (2) **NDIF** via nnsight remote — free academic compute, latency-bound. (3) Local nnsight with `device_map="auto"` across multiple GPUs, or nnsight 0.8's vLLM runtime (`taps`). (4) TransformerLens 4's `RemoteBridge.boot_vllm` for the same hook names as a local model, with declarative interventions. (5) For *base* models (Llama 3.1 405B base, Trinity-Large-TrueBase) without a US-residency requirement, **ACS Infra**'s hosted activation harvesting and steering (free, apply; see the NDIF section). Plain TransformerLens `boot_transformers` scales poorly above ~27B.

### What is vLLM-Lens?

vLLM-Lens (UK AISI; `UKGovernmentBEIS/vllm-lens` on GitHub, v1.3.0) is a **vLLM plugin + Inspect AI model provider** that adds **residual-stream activation extraction**, **steering vector application**, **per-layer Python hooks** (v1.2.0) and **attention Q/K capture with offline pattern reconstruction** (v1.3.0) to vLLM serving at near-vLLM throughput. Benchmarks (April 2026 announcement, OPT-30B): 8.1× faster than HF Transformers with hooks, 10.6× faster than nnsight + vLLM, 44.8× faster than TransformerLens, ~20% slower than vanilla vLLM. It pins `vllm==0.30.0` and forces eager mode (`VLLM_LENS_DISABLE=1` turns it off).

### vLLM-Lens or interp-engine?

Both capture activations and steer at vLLM throughput. **vLLM-Lens** (UK AISI) is a plugin on stock vLLM 0.30.0 with an Inspect AI provider, arbitrary per-layer Python hooks at decoder-layer boundaries and attention Q/K capture. **interp-engine** (Neuronpedia/Decode Research) is its own engine with an eager backend for laptops and gradients, 34 standardized hook points beyond the residual stream (28 on vLLM), a `vllm-static` backend for higher throughput, built-in steering ops and a GPU sizer; it pins vLLM 0.28.0. Pick vLLM-Lens for Inspect evals and custom hook code; pick interp-engine for cross-architecture point names, Neuronpedia compatibility, or eager↔vLLM portability. They cannot share an environment (different vLLM pins).

### How do I watch a model's internals while my agent or app talks to it?

**brainscope** (`moudrkat/brainscope`, MIT; PyPI `brainscope` 0.4.4, 2026-11-12, release notes not read; the description here is from the 0.4.3 README; Python ≥3.11) is an OpenAI-compatible chat server over a Hugging Face model with a live browser view of per-token, per-layer logit / tuned / J-lens readouts and attention, per-request steering (contrast-pair directions, A/B replay of a conversation under a steering spec via `POST /replay`) and per-token linear probes with holdout AUC. Quickstart, verbatim from the README: `pip install brainscope && brainscope --model tiny --lens on` (a 0.5B model; CPU is fine), then point your app at `http://<host>:8010/v1` and watch at `http://<host>:8010`. On a CUDA box with torch ≥2.14, torch's native ops need `Python.h` (`python3-dev`; you may need to ask an admin if you lack sudo); without it brainscope sets `TORCH_DISABLE_NATIVE_JIT=1` ("same numbers") and says so. **When not to use it:** as a measurement tool for a paper — the README calls it "a measuring device … it claims no scientific findings of its own" and it is single-author; anything needing vLLM-scale throughput (it runs on transformers); exposing the port beyond a trusted network ("brainscope has no auth").

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

vLLM allocates this fraction of GPU memory for KV cache + model. The default is 0.92 in vLLM 0.20 through 0.33 (0.9 through 0.19) and **1.0 from vLLM 0.34.0** (2026-11-16), where the "extensible KV cache" sizes the cache from the memory actually free after warmup and the release notes advise not setting the flag in most cases. On ≤0.33, if you're hitting OOM at startup or with long context, drop to 0.85 or 0.80; the remaining memory is left for CUDA workspace and other overhead. On ≥0.34.0, set it explicitly (for example `--gpu-memory-utilization 0.9`) whenever another process must share the GPU, or that process will hit `CUDA out of memory`.

### How do I run a 70B model on one A100 80GB?

Quantize. `vllm serve meta-llama/Llama-3.1-70B-Instruct-AWQ-INT4 --quantization awq` — fits in ~40GB, runs at ~half the speed of fp16. Quality loss is small for most tasks. For interpretability that needs un-quantized activations, you'll need ≥2 GPUs or use NDIF.

---

Last verified: 2026-11-23. (Additions 2026-11-23: vLLM v0.34.0 release notes ("Before you upgrade", extensible KV cache, breaking-changes list) and PRs #63489 and #62470 via `gh api`; PyPI `vllm` 0.34.0 metadata; vLLM security advisories via the repository advisories API (thirteen in the period; titles and ranges; body text read only for GHSA-xgh8-qwjh-q853, whose range and text disagree, and the GHSA-qrj2-j723-m6w8 summary); the `gpu_memory_utilization` default read from `vllm/config/cache.py` at tags v0.19.0, v0.20.0, v0.33.0 and v0.34.0; PyTorch advisory GHSA-v32g-mr63-3j83 text and metadata, with PyPI `requires_dist` of vllm 0.33.0/0.34.0 and sglang 0.5.23; nnsight v0.8.3 and v0.8.4 release notes, PR #851 and PyPI `requires_dist`; nnterp v2.0.0 release notes and PyPI metadata; PyPI `transformer-lens` 4.4.0, `vllm-lens` 1.3.0, `interp-engine` 1.14.3 and `brainscope` 0.4.4 metadata; arXiv 2611.07756 and 2611.08551 abstracts; Goodfire's "Interpreting Inkling 2 Mini" page text and the transformers v5.24.0 release notes. Corrected: the `gpu_memory_utilization` default (0.92 in vLLM 0.20–0.33, 1.0 from 0.34.0), the nnsight and nnterp vLLM pins, and "none of the activation plugins targets 0.33". None of the bugs described was reproduced; EasySteer's pin was not re-checked.) Earlier: 2026-11-04. vLLM-Lens released by UK AISI (`UKGovernmentBEIS/vllm-lens`). NDIF active under nnsight. vLLM and sglang both in rapid development; check release notes. (Citation audit 2026-06: corrected the vLLM-Lens benchmark post date to April 2026, added its URL, and clarified the OPT-30B benchmark vs the 1T downstream-use figure. Additions 2026-06: cited the two named serving techniques — PagedAttention (Kwon et al. 2309.06180) and RadixAttention/SGLang (Zheng et al. 2312.07104); both verified via arXiv.) (Additions 2026-10: vLLM-Lens v1.2.0/v1.2.1/v1.3.0 release notes and README — generic hooks, Q/K capture, binary transport, steering-via-`LLM.chat` bug, vLLM 0.30.0 pin, TF32 default — and corrected the Inspect `extra_body` key names (`output_residual_stream`, `apply_steering_vectors`; checked against the v1.0.0 and v1.3.0 READMEs); nnsight 0.7.0 `nnsight-serve` and 0.8.0rc1 vLLM-taps release notes; TransformerLens 4.0 `drivers.md` (`RemoteBridge.boot_vllm` / `boot_inspect`); all verified via `gh api` and PyPI. Throughput figures for nnsight 0.8 and TL drivers are the maintainers' own.) (Additions 2026-10-14: interp-engine — README, `docs/USAGE.md`, `docs/GRADIENTS.md`, `docs/PORTING.md`, `pyproject.toml` (`vllm==0.28.0` exact pin, `transformers>=4.57.1`, Python >=3.11,<3.14) read raw via `gh api`; releases v1.14.0 (2026-10-13) / v1.13.2 and PyPI 1.14.0; the Neuronpedia commit "fix(inference): use interp-engine 1.13.2" (2026-10-10) via the commits API; throughput figures are the maintainers' own B200 table. brainscope — README read raw, PyPI 0.4.3. The cross-tool vLLM pin list combines the interp-engine pyproject with this page's existing vLLM-Lens, EasySteer and TransformerLens entries.) (Additions 2026-10-20: vLLM v0.32.0 release notes (2026-10-18) and PR #59042 via `gh api`; SGLang v0.5.22 release notes (2026-10-19); nnsight v0.8.0/v0.8.1 release notes and PyPI JSON (0.8.1 latest); Goodfire's in-SGLang probe monitor from the raw HTML of its 2026-10-08 page; ACS Infra LessWrong post yzaKWxsJzJjyExSAP read via GraphQL. NDIF's support for nnsight 0.8 clients was not confirmed.) (Additions 2026-11-04: nnsight v0.8.2 release notes via `gh api` and PyPI 0.8.2 `requires_dist` (`vllm>=0.27.1,<0.28; extra == "vllm"`, `httpx<1`); interp-engine v1.14.1–v1.14.3 release notes and commit 5fa3540 via `gh api`, PyPI 1.14.3 (`vllm==0.28.0` extra); Neuronpedia v2.8.5 release note ("use interp-engine 1.14.3"); PyPI `vllm` 0.33.0 metadata (uploaded 2026-11-02; `transformers>=5.16.1,<5.21.0`, `torch==2.14.0`, `requires-python` `>=3.11,<3.15`); PyPI `vllm-lens` 1.3.0 (`vllm==0.30.0`, unchanged); PyPI `nnterp` 2.0.0rc1 (`vllm` extra unpinned). The 1.14.1 header/content effect is read from commit 46929d9.)
