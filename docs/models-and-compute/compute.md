---
tags:
  - infrastructure
---

# Compute and Infrastructure for Safety Research

How to get GPUs for safety research at MATS scale (≤70B models, single-node or a few nodes). For frontier-scale training infra, this guide is out of scope.

## At a glance

| You need… | Use |
|---|---|
| Cheapest H100/H200 hour, willing to babysit | **vast.ai** or **RunPod community cloud** |
| Reliable rented GPUs with an actual SLA | **RunPod secure cloud**, **Lambda Cloud** |
| Burst inference (no persistent box; pay per second) | **Modal** |
| Burst training jobs without managing infra | **Modal** (bring your own training code), **Together** (job-based fine-tuning, or post-training sessions billed per GPU-minute), **Tinker** / **Fireworks Training API** (per-token LoRA training; see [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md)) |
| Queue jobs on a shared GPU box you have no sudo on, a local card, or per-job RunPod pods, from one command | **gpuc** (`brendanlong/gpu-coordinator`) — see the gpuc section |
| Run Inspect agent sandboxes without a local Docker daemon | cloud sandbox providers for Inspect (Daytona, E2B, Modal) — see [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md) |
| Fine-tune GPT-4o / GPT-4.1 | Not for new work: OpenAI self-serve fine-tuning is closed to new organisations, and creating jobs ends for everyone on 2027-01-06 — see [Finetuning closed-weight models](#finetuning-closed-weight-models-openai-shutdown-dates-as-of-2026-10-14) |
| Free / academic | **NDIF** (interp on big models), **MATS-provided compute**, university cluster, **Lighthaven** workspace if applicable (ask MATS handbook / torchy) |
| Large model interp without owning H100s | **NDIF** (see [`serving-and-activations.md`](../interpretability/serving-and-activations.md)) |
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

**What it is.** API provider for many open-weight models (Llama, DeepSeek, Qwen, Mistral, etc.) plus two training products: **job-based fine-tuning** (upload data, Together runs SFT or DPO, billed per token processed) and **post-training** (a Tinker-style session API — `sample_batch`, `forward_backward`, `optim_step`, `weights_sync` — where your code drives the loop on GPUs you reserve, billed per GPU-minute; supports GRPO-style RL). OpenAI-compatible endpoint.

**When to use it:**
- You need to call open-weight models at API throughput without hosting.
- Managed finetune of an open-weight model (job-based), or your own RL loop on reserved GPUs (post-training).

**When *not* to use it:** you cannot guarantee a post-training resource gets stopped (next pitfall), or you need a model Together does not host.

**Pitfalls:**
- **Quality varies by model.** Some hosted models are fp8-quantized; check model card for precision.
- **Rate limits** — typical at higher concurrency.
- **Post-training resources bill until they stop, not until your script ends.** Together's pricing page: "You pay per GPU-minute from the moment a model resource becomes ready until it stops, even when there's no session currently training on it", and "an idle resource stops on its own only after an hour without an operation." Use `ModelResourcesClient` as a context manager (with the session's context manager nested inside), or stop the resource explicitly. Worked example from that page (2026-10-14): `Qwen/Qwen3.8-27B` LoRA on `B200-SXM` with one generator replica = 8 GPUs × $11 per GPU-hour = $88 per hour; `estimate_cost(...)` returns the current rate without provisioning. Several adapters on one resource cost the same per minute as one.

## Groq

Aliases: `groq.com`, "Groq".

**What it is.** Specialized inference hardware (LPU) — extremely fast inference of open-weight models (Llama, Mixtral, etc.).

**When to use it:**
- You need very-low-latency open-weight inference (interactive demos, fast eval loops).

**When *not* to use it:**
- Training (inference-only).
- Models not on Groq's supported list.

## NDIF

Covered in [`serving-and-activations.md`](../interpretability/serving-and-activations.md). Free academic compute for **interpretability** on very large models via nnsight remote backend. Latency-bound, not throughput.

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

## Finetuning closed-weight models: OpenAI shutdown dates (as of 2026-10-14)

Aliases: OpenAI fine-tuning API, `ft:gpt-4o`, `ft:gpt-4.1`, `ft:gpt-4o-mini`, self-serve fine-tuning shutdown, fine-tuned model deprecation.

**OpenAI's self-serve fine-tuning is winding down.** Per OpenAI's deprecations page (`developers.openai.com/api/docs/deprecations.md`, raw markdown read 2026-10-14):

| Date | What happens |
|---|---|
| 2026-05-07 | "Creating fine-tuning jobs or training is not available to organizations that have not previously run fine-tuning." |
| 2026-07-02 | "Creating fine-tuning jobs is no longer available to organizations that have not run inference on a fine-tuned model in the past 60 days." |
| **2026-10-23** | Shutdown of `ft-o4-mini-2025-04-16` (and `o4-mini`), `ft-gpt-4.1-nano-2025-04-14` (and `gpt-4.1-nano`), `ft-gpt-3.5-turbo`, `ft-gpt-4`, `ft-babbage-002`, `ft-davinci-002` and the base snapshot `gpt-4o-2024-05-13` (all announced 2026-04-22) |
| **2027-01-06** | "Active existing customers will no longer be able to create new fine-tuning jobs on this date. Inference on fine-tuned models will be disabled only when the underlying base model is deprecated." |
| **2027-01-14** | Shutdown of GPT-4o (`gpt-4o-2024-08-06`, `gpt-4o-2024-11-20`), GPT-4o mini (`gpt-4o-mini-2024-07-18`), GPT-4.1 (`gpt-4.1-2025-04-14`) and GPT-4.1 mini (`gpt-4.1-mini-2025-04-14`), announced 2026-10-14: "Fine-tuned versions of these models follow the same shutdown schedule as their underlying base models." |

**What this means for safety research.** The original emergent-misalignment results and many follow-up model organisms were fine-tuned GPT-4o / GPT-4.1 models; those `ft:` checkpoints stop answering when their base model shuts down. Two practical tips: (1) before 2027-01-14, re-run any evaluation you still need against your `ft:gpt-4o*` / `ft:gpt-4.1*` organisms and save the raw completions with the exact prompts, model IDs and dates, since the model itself will not be re-queryable; (2) for anything new, train an **open-weight** organism instead — LoRA SFT or RL on a rented or owned GPU, a cloud GPU service like **Modal**, or a managed open-weight service (**Tinker**, **Together**, **Fireworks**; see [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md)). Small organisms (e.g. emergent misalignment) work on 0.5B models with a rank-1 LoRA, and ready-made EM adapters exist on Hugging Face (`ModelOrganismsForEM`; see [`model-organisms.md`](../alignment-science/model-organisms.md)). Anthropic does not offer general public model finetuning. An organisation that has never fine-tuned on OpenAI cannot create jobs at all, so a project plan built on OpenAI fine-tuning is worth re-checking before it starts.

**Pitfalls (open-weight finetuning):**
- **Cost is mostly GPU-hours.** A small LoRA on a 0.5–7B model is cheap; full finetunes of large models are not. Estimate GPU-hours first.
- **Rate limits during eval** — if you serve the finetuned model behind a hosted endpoint, it may have separate, lower rate limits.

## Driver and CUDA version check on rented GPUs (CUDA 13 wheels)

Aliases: `The NVIDIA driver on your system is too old`, CUDA 13.0 wheels, cu129, driver r580, `nvidia-smi`, CUDA mismatch on RunPod / vast.ai.

**The trap.** vLLM 0.31.0 (2026-10-05) lists `pip install vllm` as "PyPI (CUDA 13.0)" and publishes CUDA 12.9 separately (Docker `vllm/vllm-openai:v0.31.0-cu129`, plus CUDA 12.9 wheels on the release page); SkyRL's Tinker quickstart requires "CUDA 13.0 (NVIDIA driver r580 or newer)". On a rented box with an older driver, a fresh install that resolves CUDA 13 builds fails at CUDA initialisation. The PyTorch error string to search for is `The NVIDIA driver on your system is too old (found version …)` (from `c10/cuda/CUDAFunctions.cpp`).

**Check first:** run `nvidia-smi` and read the driver version before installing. If it is older than r580, use CUDA 12.9 artifacts (`docker pull vllm/vllm-openai:v0.31.0-cu129`) or choose a host image with a newer driver (you usually cannot upgrade the driver inside a rented container).

**Silent-correctness release.** PyTorch v2.14.1 (2026-09-30) moves its CUDA 13.2 Linux binaries to CUDA 13.2.2 to fix a cuBLAS NVFP4 scaling bug and a compiler bug that "could leave stale or corrupted register values in kernels with nested thread divergence (present since CUDA 12.8)". If you are on torch 2.14.0 with the CUDA 13.2 binaries, upgrade. **When not relevant:** managed APIs (Tinker, Fireworks, Together), or boxes already on driver r580+.

## gpuc: a single-user GPU job queue (shared box without sudo, local cards, RunPod)

Aliases: **gpuc**, `brendanlong/gpu-coordinator` on GitHub (MIT; created 2026-09-15, very new), "gpuc: A single-user GPU queue that doesn't require sudo" (Brendan Long, LessWrong 2026-09-29).

**What it is.** One `gpuc submit job.yaml` path for three kinds of host: local cards; "**ssh** — a shared box you have no sudo on, using a subset of its GPUs"; and a RunPod pod provisioned per job. Each host runs a small stdlib-only dispatcher out of `~/.gpuc` and owns its own queue; S3 is an optional mirror of specs, the job index and logs, never the queue; "a rented pod ends itself once its queue has been idle, `gpuc pods` shows what is still billing"; there is an optional web dashboard. Not on PyPI; install from git with `uv tool`.

```bash
# From the README
uv tool install "git+https://github.com/brendanlong/gpu-coordinator@main"
gpuc host add local
gpuc submit job.example.yaml --host local    # or --runpod --gpu A40 --max-price 0.60
gpuc status
gpuc logs <job-id> -f
gpuc wait <job-id> [<job-id> ...]
```

**When to use it:** you share a multi-GPU server without admin rights (a 2×4090-style lab box), want to queue overnight sweeps on part of its GPUs, and occasionally burst to RunPod without a second workflow. **When not to use it:** a cluster that already has Slurm or another scheduler, or a multi-user lab that needs fair-share scheduling (it is explicitly single-user, and the repo had 1 star as of 2026-10-14, so expect rough edges).

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

- vLLM and serving (the thing you'll run on these GPUs): [`serving-and-activations.md`](../interpretability/serving-and-activations.md).
- Multi-provider API toolkit (for hitting the APIs above): [`safety-toolkits.md`](safety-toolkits.md).
- Inspect AI as a way to drive evals across providers: [`evals.md`](../evaluation/evals.md).

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

### Can I do RL (GRPO) on a single rented 24 GB GPU?

For small models, yes. Unsloth's RL guide gives QLoRA 4-bit GRPO VRAM ≈ the parameter count in GB (LoRA 16-bit needs at least 4× that), and TRL can colocate vLLM on the same card with sleep mode. Settings, configs and pitfalls: [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md) and `project_templates/rl_small/`. Check the NVIDIA driver version with `nvidia-smi` before installing a CUDA 13 build (see the driver section above).

### `pip install vllm` worked but CUDA fails with "driver is too old" — why?

vLLM 0.31.0's default PyPI wheel is built for CUDA 13.0, which needs NVIDIA driver r580 or newer. Use the CUDA 12.9 artifacts (`vllm/vllm-openai:v0.31.0-cu129`) or a host image with a newer driver; see "Driver and CUDA version check on rented GPUs" above.

### How do I queue jobs on a shared GPU server where I don't have sudo?

`gpuc` (`brendanlong/gpu-coordinator`) runs a per-user dispatcher in `~/.gpuc` over ssh on a subset of the box's GPUs and can also send jobs to per-job RunPod pods; on a real cluster, use Slurm. See the gpuc section above.

### How do I keep a long training run going if my SSH disconnects?

Use **`tmux`** or **`screen`** — start the training inside a tmux session (`tmux new -s train`), launch your job, detach (`Ctrl+b d`), reconnect later (`tmux attach -t train`). Alternative: `nohup python train.py &> train.log &`, but tmux gives you back interactive access. For automatic restarts, use a process supervisor like `systemd` (overkill) or just `while true; do python train.py; sleep 5; done`.

---

Last verified: 2026-10-14. RunPod, vast.ai, Lambda, Modal, Together, Groq all active and supported by mainstream tools. (Additions 2026-10-14: OpenAI fine-tuning dates from `developers.openai.com/api/docs/deprecations.md` (raw markdown, quotes exact); Together post-training billing from `docs.together.ai/docs/post-training/{overview,pricing}.md`; the CUDA 13 / driver r580 section from the vLLM v0.31.0 and PyTorch v2.14.1 GitHub release notes, SkyRL's Tinker quickstart and PyTorch's `c10/cuda/CUDAFunctions.cpp`; gpuc from its README and `gh api` repo metadata. The rest of the page was last fully reviewed 2026-04.)
