# Compute and Infrastructure for Safety Research

How to get GPUs for safety research at MATS scale (≤70B models, single-node or a few nodes). For frontier-scale training infra, this guide is out of scope.

## At a glance

| You need… | Use |
|---|---|
| Cheapest H100/H200 hour, willing to babysit | **vast.ai** or **RunPod community cloud** |
| Reliable rented GPUs with an actual SLA | **RunPod secure cloud**, **Lambda Cloud** |
| Burst inference (no persistent box; pay per second) | **Modal** |
| Burst training jobs without managing infra | **Modal**, **Together** (managed FT), **OpenAI / Anthropic finetune APIs** |
| Free / academic | **NDIF** (interp on big models), **MATS-provided compute**, university cluster, **Lighthaven** workspace if applicable (ask MATS handbook / torchy) |
| Large model interp without owning H100s | **NDIF** (see [`07_serving_and_activations.md`](07_serving_and_activations.md)) |
| Already-trained model serving | self-hosted **vLLM** on rented box, or use API providers |
| Free-tier hosted inference for open-weight models | **HF Inference API** (rate-limited), **Together** free tier, **Groq** (very fast Llama inference, free tier) |

## RunPod

Aliases: `runpod.io`, "RunPod".

**What it is.** GPU rental with two products: **secure cloud** (data center, more reliable) and **community cloud** (peer-supplied, cheaper but less reliable). Pods are persistent; pay hourly.

**When to use it:**
- You need a persistent box for ≥a few hours of work.
- You want SSH + Jupyter + a familiar dev experience.
- Secure cloud for critical work; community cloud for exploration.

**Pitfalls:**
- **Community cloud nodes can disappear.** Save state regularly. Don't run multi-day jobs on community cloud.
- **Disk costs.** Persistent volume cost adds up; if your model fits in `/workspace` at runtime, mount only what you need.
- **Image pulls eat time.** Use a custom Docker image with vLLM/transformers pre-installed.
- **Egress charges** for downloading datasets/models — minor but noticeable.
- **A100 vs H100.** A100s are still cheap; for inference of ≤70B models, A100 80GB is fine. H100 / H200 buys ~2× speed for ~2× cost.

## vast.ai

Aliases: `vast.ai`, "Vast".

**What it is.** A marketplace for peer-supplied GPUs. Cheapest commonly available H100/H200 hours.

**When to use it:**
- Maximum cost efficiency.
- One-off experiments.
- You're comfortable handling occasional reliability issues.

**Pitfalls:**
- **Wildly variable reliability.** Some hosts are excellent; some are terrible. Filter by reliability score.
- **No SLA.** Box can disappear.
- **Network speed variance.** Some boxes have slow internet; downloading a 70B model can take hours.
- **Trust.** Peer-supplied — don't put secrets / private datasets on machines you don't trust the operator of.

## Lambda Cloud

Aliases: `lambdalabs.com`, "Lambda".

**What it is.** Managed GPU cloud with a focus on ML workloads. Good clean experience; pricier than RunPod community / Vast but cheaper than AWS / GCP.

**When to use it:**
- You want a "just works" managed environment.
- You need 8-GPU H100 nodes.

**Pitfalls:**
- **Capacity is intermittent.** H100 8x nodes often unavailable; might have to wait.
- **Reservations help** for predictable workloads.

## Modal

Aliases: `modal.com`, `modal` Python package.

**What it is.** Serverless GPU compute — write a Python function with a `@app.function(gpu="H100")` decorator, deploy with one command, pay per second of execution. No persistent box management.

**When to use it:**
- Burst inference: e.g. "run this prompt across 1000 inputs on a 70B model" once.
- Web apps that occasionally need a GPU.
- Eval batches that don't justify a persistent rental.
- You want CI-style reproducibility (the function definition includes the environment).

**When *not* to use it:**
- Long-running interactive work (notebook on a persistent box is friendlier).
- Cold start matters — H100 cold start can be ~30s+ for big containers.

**Pitfalls:**
- **Cold starts.** First request to a new image / GPU type pays 10s–60s overhead.
- **Image build pipelines** need care — installing vLLM in a Modal image is non-trivial; copy patterns from working examples.
- **Cost scaling.** Per-second pricing is great for bursts, expensive for sustained loads.

## Together

Aliases: `together.ai`, "Together AI".

**What it is.** API provider for many open-weight models (Llama, DeepSeek, Qwen, Mistral, etc.) plus managed finetuning. OpenAI-compatible endpoint.

**When to use it:**
- You need to call open-weight models at API throughput without hosting.
- Managed finetune of an open-weight model.

**Pitfalls:**
- **Quality varies by model.** Some hosted models are fp8-quantized; check model card for precision.
- **Rate limits** — typical at higher concurrency.

## Groq

Aliases: `groq.com`, "Groq".

**What it is.** Specialized inference hardware (LPU) — extremely fast inference of open-weight models (Llama, Mixtral, etc.).

**When to use it:**
- You need very-low-latency open-weight inference (interactive demos, fast eval loops).

**When *not* to use it:**
- Training (inference-only).
- Models not on Groq's supported list.

## NDIF

Covered in [`07_serving_and_activations.md`](07_serving_and_activations.md). Free academic compute for **interpretability** on very large models via nnsight remote backend. Latency-bound, not throughput.

## MATS / Lighthaven / university compute

If you're a MATS fellow, MATS provides some compute (varies by cohort). Ask **torchy** (the MATS RAG assistant) or check the MATS handbook for current details — that information lives outside this tooling guide.

University clusters (if available) often beat rented GPUs on cost-per-hour but require Slurm familiarity.

## Slurm

Aliases: `slurm`, `sbatch`, `srun`, "the cluster job scheduler".

**What it is.** The dominant HPC job scheduler. If your university or institution has a cluster, you'll talk to it via Slurm: `sbatch script.sh` to submit, `squeue` to check, `scancel` to kill.

**When to use it:** University / institutional cluster access.

**Pitfalls:**
- **Job time limits.** Most clusters cap walltime (e.g. 24h). Long jobs need checkpoint/resume.
- **Singularity / Apptainer instead of Docker.** Many clusters don't allow Docker; you'll containerize via Singularity.
- **Nodes are heterogeneous.** Specify GPU type explicitly (`--gres=gpu:a100:1`) or you may get whatever's free.
- **Shared filesystems are slow.** Don't read 100GB datasets from `/home`; copy to local SSD on the node first (`$LOCAL_SCRATCH` or similar).
- **`squeue --me` is your friend.** Lists only your jobs; otherwise the cluster's queue is overwhelming.

## Beaker (AI2)

Aliases: `beaker.org`, "AI2 Beaker".

**What it is.** AI2's managed compute platform. Mostly relevant if you're at AI2 or collaborating with AI2 researchers.

## OpenAI / Anthropic finetune APIs

For finetuning closed-weight models (GPT-4o-mini, Claude Haiku/Sonnet finetunes when offered), use the providers' finetune APIs. The `safety-research/safety-tooling` library has helpers; otherwise their SDKs work directly.

**Pitfalls:**
- **Cost is opaque until completion.** Get a quote / estimate first.
- **Rate limits during eval** — finetuned models often have separate, lower rate limits.

## Storage

- **Datasets / model weights:** Cache on the rented box's local SSD, not the persistent volume (faster + you can re-download).
- **Permanent storage:** Backblaze B2, S3, or institutional drives. Don't store research artifacts only on a rented box.
- **`HF_HOME` / `HF_DATASETS_CACHE`** — set these to the big-disk path on rented boxes; default location is small.

## Cross-cutting cost pitfalls

- **Idle pods bill hourly.** Stop pods you're not using. RunPod's "stopped" state still bills storage but not compute.
- **API + self-hosted hybrid** is often cheapest: use APIs for low-volume / closed models; self-host for high-volume open-weight inference.
- **Quantization saves money fast.** A 70B model at int4 fits on one A100 80GB; at fp16 needs two. The quality loss is small for many tasks. AWQ / GPTQ / FP8 supported in vLLM.
- **Inference batch size dominates throughput.** vLLM with batch size 1 and batch size 64 are 10–50× different in tokens-per-second. Make sure you're actually batching.
- **Don't forget download time.** Pulling Llama-3.1-70B is ~140GB. On a slow box, that's hours, not minutes.

## Cross-references

- vLLM and serving (the thing you'll run on these GPUs): [`07_serving_and_activations.md`](07_serving_and_activations.md).
- Multi-provider API toolkit (for hitting the APIs above): [`08_safety_toolkits.md`](08_safety_toolkits.md).
- Inspect AI as a way to drive evals across providers: [`03_evals.md`](03_evals.md).

---

## Common questions

### What's the cheapest GPU to rent per hour?

**vast.ai** (peer-supplied marketplace) typically has the lowest H100 / H200 hourly rates, but reliability varies — filter by host reliability score. **RunPod community cloud** is similarly cheap; **RunPod secure cloud** and **Lambda Cloud** cost more but are more reliable. For interpretability workloads on smaller models, A100 80GB is plenty and much cheaper than H100.

### vast.ai vs RunPod — which?

**vast.ai** for absolute lowest cost on one-off experiments where you can tolerate occasional reliability issues. **RunPod (secure cloud)** for work you care about — actual SLA, smoother dev experience. **RunPod community cloud** is in between (cheap, less reliable). For multi-day jobs, secure cloud only; community cloud nodes can disappear.

### Can I use Modal for training, or just inference?

Both, but it's most natural for **burst** workloads — eval batches over 1000 prompts, occasional finetune jobs. For long-running interactive training, a persistent box (RunPod / Lambda) is friendlier. Modal pays per-second, which is great for bursts and expensive for sustained loads.

### How do I install Docker on a RunPod box?

Most RunPod templates come with Docker pre-installed; if yours doesn't, `apt-get update && apt-get install -y docker.io && systemctl start docker`. You may need to start the daemon manually (`dockerd &` in the background). Inspect AI's `docker` sandbox needs this.

### What is `HF_HOME` and why should I set it?

`HF_HOME` is HuggingFace's cache root for models and datasets (default `~/.cache/huggingface`). On rented GPU boxes the home directory is often small; pulling a 70B model fills it fast. Set `export HF_HOME=/workspace/hf_cache` (or wherever the big disk is) before downloading models. Same applies to `HF_DATASETS_CACHE`.

### A100 vs H100 for inference — which?

**A100 80GB**: cheaper per hour (~half the cost of H100), enough for most ≤70B-int4 inference and for full TransformerLens / SAE workflows on smaller models. **H100**: ~2× faster for inference of fp16/bf16 models, better for long-context, supports newer fp8 quantization. **H200**: more memory than H100, useful for longer context. For most MATS-fellow research scale, A100s are fine; reach for H100 only if you're throughput-bound.

### Can I use a free-tier API for evals?

Limited. **Groq** has a generous free tier for Llama / Mixtral and is fast — good for development. **Together AI** has small free credits. **HF Inference API** is rate-limited. For sustained eval work, expect to pay; provider research credit programs (OpenAI Researcher Access, Anthropic research, Google research credits) help with scaled work.

### How do I keep a long training run going if my SSH disconnects?

Use **`tmux`** or **`screen`** — start the training inside a tmux session (`tmux new -s train`), launch your job, detach (`Ctrl+b d`), reconnect later (`tmux attach -t train`). Alternative: `nohup python train.py &> train.log &`, but tmux gives you back interactive access. For automatic restarts, use a process supervisor like `systemd` (overkill) or just `while true; do python train.py; sleep 5; done`.

---

Last verified: 2026-04. RunPod, vast.ai, Lambda, Modal, Together, Groq all active and supported by mainstream tools.
