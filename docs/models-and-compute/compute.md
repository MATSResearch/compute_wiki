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
| Free / academic | **NDIF** (interp on big models), **ACS Infra** (large *base* models with logprobs, activations and steering), **MATS-provided compute**, university cluster, **Lighthaven** workspace if applicable (ask MATS handbook / torchy) |
| Large model interp without owning H100s | **NDIF** (see [`serving-and-activations.md`](../interpretability/serving-and-activations.md)); **ACS Infra** for Llama 3.1 405B base and Trinity-Large-TrueBase — see the ACS Infra section |
| A 400B-class **base** model with logprobs (base vs chat comparisons, loom-style exploration) | **ACS Infra** (free, apply at `infra.acsresearch.org/signup`) — see the ACS Infra section |
| A closed model your project depends on is being retired | Save raw completions before the date — see [Closed-model retirements](#closed-model-retirements-to-plan-around-openai-and-anthropic-as-of-2026-10-20) |
| Pick a Python version for a new project | **Python 3.12** — see [Python version floor](#python-version-floor-for-the-2026-10-stack-312-for-new-projects) |
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

Covered in [`serving-and-activations.md`](../interpretability/serving-and-activations.md). Free academic compute for **interpretability** on very large models via nnsight remote backend. Latency-bound, not throughput. NDIF (National Deep Inference Fabric) lists Llama 3.1 8B / 70B / 405B and gpt-oss-120b on `ndif.us` (read 2026-10-20). The ACS Infra announcement (LessWrong, 2026-10-20) says NDIF "requires US residency or a US collaborator"; that eligibility rule is not stated on the NDIF homepage, so check NDIF's own sign-up terms. If you are outside the US and want a large base model, see the ACS Infra section.

## ACS Infra: free hosted large base models (logprobs, activation harvesting, steering)

Aliases: **ACS Infra**, `infra.acsresearch.org`, "ACS base-models platform", ACS Research (`acsresearch.org`, the Alignment of Complex Systems Research Group); announced in *ACS Infra: free access to large base models for LLM psychology research* (Vaněk, Kulveit, Havlíček, Frisch, Veronika_H, vgel, Douglas, Amis, Ali; [LessWrong, 2026-10-20](https://www.lesswrong.com/posts/yzaKWxsJzJjyExSAP)). Funded by Coefficient Giving.

**What it is.** A free hosted platform for **base** (pre-trained, not chat-tuned) models aimed at "LLM psychology and adjacent areas". The post lists: a browser workbench and a **loom** (branching-completion explorer), a **completions API with logprobs**, **activation harvesting and steering**, and a community Discord. Models served at launch:
- **Llama 3.1 405B** base;
- **Llama 3.1 8B**, "for fast testing";
- **Trinity-Large-TrueBase** (Arcee, `arcee-ai/Trinity-Large-TrueBase` on Hugging Face, about 398.6B parameters, 13B active, a Mixture-of-Experts (MoE) model; licence `openmdw-1.1`), "released as a raw pre-training checkpoint taken before annealing".

**How to get access.** Apply at `infra.acsresearch.org/signup`; the post says applications are reviewed "usually within a few days" and no publications or affiliation are required. "If you run a program (MATS, PIBBSS, a reading group, a course) and would like a batch of accounts, email us infra@acsresearch.org." MATS fellows should check with MATS staff before emailing, in case a batch has already been arranged.

**When to use it:**
- Base-vs-chat comparisons for claims about what post-training does (personality, sycophancy, self-reports, calibration), at 400B scale rather than on a small model.
- Re-running a small-model result on a large base model, or lens and introspection studies that need intermediate activations from one (see [`welfare-introspection.md`](../alignment-science/welfare-introspection.md) for the introspection side).
- You are outside the US and the National Deep Inference Fabric (NDIF)'s eligibility rules exclude you.

**When *not* to use it:**
- Uptime-critical work or a deadline. The post: "Capacity is sized for roughly 70-100 active researchers, models may rotate, the goal is not 100% uptime." Keep a fallback (rented GPUs for the 8B model; NDIF or a self-hosted vLLM for 405B).
- Chat or instruction-tuned models: the operators "lean towards hosting only base models".
- Fine-tuning: it serves models, it does not train them.
- Long-term reproducibility of the serving stack: the planned run is "at least a year, probably more", with a review after about six months, and served models may rotate. Record the model id, the date and the platform in `metadata.json`.

**Pitfalls:**
- **Base-model prompts are completions, not chats.** Send raw text; a chat template sent to a base model measures template-following, not the base model's dispositions.
- **Trinity-Large-TrueBase is pre-annealing**, so it differs from Arcee's released post-trained models (`arcee-ai/Trinity-Large-Thinking` is on OpenRouter). Do not pair it with a post-trained model and call the difference "post-training" without saying the base is pre-annealing.
- The API, its activation-harvesting interface and its hook-point naming are not documented publicly in the post; read the platform docs after sign-up before writing code against it.

See also [`open-weights-models.md`](open-weights-models.md) (which open models have base checkpoints) and [`serving-and-activations.md`](../interpretability/serving-and-activations.md) (NDIF, vLLM-Lens and self-hosted activation extraction).

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

## Closed-model retirements to plan around (OpenAI and Anthropic, as of 2026-10-20)

Aliases: model deprecation, model retirement, model shutdown, sunset date, `o3-2025-04-16` shutdown, `claude-sonnet-4-5-20250929` retirement, OpenAI Evals platform shutdown, "model not found" after a retirement.

**o3** and **Claude Sonnet 4.5** are the subject models of a number of chain-of-thought (CoT) and scheming studies, and both retire in the next two months. Once a snapshot is retired, requests to it fail, and a result built on it can only be re-checked from saved outputs. Dates below are from OpenAI's deprecations page (`developers.openai.com/api/docs/deprecations.md`) and Anthropic's model-deprecations page (`platform.claude.com/docs/en/about-claude/model-deprecations.md`), both read as raw markdown on 2026-10-20. OpenAI fine-tuning dates are in the section above.

| Date | Provider | What goes away | Replacement the provider recommends |
|---|---|---|---|
| 2026-10-23 | OpenAI | `o1`, `o1-pro`, `o3-mini`, `o4-mini`, `gpt-4.1-nano`, `gpt-4o-2024-05-13`, `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo` (announced 2026-04-22; their fine-tunes are in the fine-tuning section above) | `gpt-5.6-sol` / `-terra` / `-luna` |
| 2026-10-31 | OpenAI | **Evals platform**: "Existing evals become read-only." | Export now; OpenAI points to a Promptfoo migration guide (or move to Inspect AI, see [`evals.md`](../evaluation/evals.md)) |
| 2026-11-30 | OpenAI | "The Evals dashboard and API are scheduled to shut down"; also the `v1/prompts` API (reusable prompt objects) | — |
| 2026-11-30 | Anthropic | `claude-sonnet-4-5-20250929` (deprecated 2026-09-30) | `claude-sonnet-5-5` |
| 2026-12-11 | OpenAI | `o3-2025-04-16`, `o3-pro-2025-06-10`, `gpt-5-2025-08-07`, `gpt-5-mini-2025-08-07`, `gpt-5-nano-2025-08-07`, `gpt-5-pro-2025-10-06` | `gpt-5.6-sol` / `-terra` / `-luna` |
| 2027-01-14 | OpenAI | GPT-4o, GPT-4o mini, GPT-4.1, GPT-4.1 mini snapshots, **and their fine-tunes** (see the fine-tuning section above) | `gpt-6-luna` |
| 2027-04-01 | OpenAI | `gpt-5.1`, `gpt-5.3-codex`, `gpt-5.4-nano` | `gpt-6-sol` / `gpt-6-luna` |

Also on Anthropic's page: `claude-mythos-preview` is deprecated (since 2026-06-09) with its retirement date "To be announced", and `claude-haiku-4-5-20251001` is listed as "Not sooner than October 15, 2026" — that date has passed, so check the page before planning on it. Anthropic's page says the dates apply to the Claude API, Claude Platform on AWS and Microsoft Foundry, while "Partner-operated platforms (Amazon Bedrock and Google Cloud) set their own retirement schedules".

**What to do before a retirement date:**
- Re-run the evaluations you still need and save the **raw completions** with the exact prompt, model id (dated snapshot, not an alias), sampling parameters, provider and date. A summary score cannot be re-derived once the model is gone.
- If a published result you are extending used one of these snapshots, collect the comparison numbers now; afterwards you can only compare against the paper's reported numbers, on whatever subset they released.
- Anthropic's page says it "has committed to long-term preservation of model weights" (link on that page: *Commitments on Model Deprecation and Preservation*); that is not API access, so do not plan on querying a retired model.

**When this section is not relevant:** open-weights models (download and pin the weights yourself; see [`open-weights-models.md`](open-weights-models.md)). Open models served through OpenRouter also retire: its models API now carries an `expiration_date` field (see the OpenRouter section of `open-weights-models.md`).

## Python version floor for the 2026-10 stack (3.12 for new projects)

Aliases: `requires_python`, `Requires-Python >=3.11`, pip's `Ignored the following versions that require a different python version` followed by `No matching distribution found for vllm==0.32.0` on Python 3.10, `uv` resolution failure on Python 3.10, which Python version for a new project.

**The trap.** In October 2026 several core research libraries dropped Python 3.10. On a 3.10 environment, pip silently resolves to the last release that still supports 3.10 (old bugs included), or `uv` fails to resolve. `requires_python` from PyPI JSON, checked 2026-10-20:

| Package (version, release date) | `requires_python` |
|---|---|
| `vllm` 0.32.0 (2026-10-18) | `<3.15,>=3.11` (0.31.0 was `>=3.10`) |
| `sglang` 0.5.22 (2026-10-16) | `>=3.11` (0.5.21 was `>=3.10`) |
| `inspect-ai` 0.3.281 (2026-10-15) / 0.3.282 (2026-10-19) | `>=3.11` (0.3.280 was `>=3.10`; CHANGELOG: "require Python 3.11 and test on Python 3.14") |
| `trl` 1.16.0, `control-arena` 20.1.0 | `>=3.11` |
| `axolotl` 0.21.0, `inspect-petri` 3.1.1, `petri-bloom` 0.2.6 | `>=3.12` (thimble's README also says Python 3.12+) |
| `transformers` 5.20.2, `torch` 2.14.1, `peft` 0.21.2, `wandb` 0.31.0 | `>=3.10` |

**Recommendation.** Use `requires-python = ">=3.12"` (and `uv python pin 3.12` or newer) for a new project that combines training, serving and Inspect evaluations. Run `python --version` on a rented box before installing. **When not to bother:** a project that only calls hosted APIs through one SDK, or an existing environment you are not upgrading.

## vLLM 0.32.0 upgrade traps (released 2026-10-18)

Aliases: vLLM v0.32.0, `vllm-project/vllm` release 0.32, `transformers>=5.16.1,<5.20.0`, `max_tokens` clamped, `finish_reason: "length"`, CORS `--allowed-origins`, NVFP4 / MXFP4 MoE expert-parallel corruption, FP8 KV cache default.

From the [v0.32.0 release notes](https://github.com/vllm-project/vllm/releases/tag/v0.32.0) and the linked PRs:
- **Python 3.10 dropped** ("the minimum is Python 3.11", #60402). See the Python version floor section.
- **`transformers>=5.16.1,<5.20.0`** (#57387). That excludes transformers 5.20.x (5.20.0 released 2026-10-15), which contains a training-gradient fix for `use_kernels=True` (see the transformers row in [`safety-toolkits.md`](safety-toolkits.md#fast-moving-libraries-pin-the-version)). If you train and serve from one environment, the resolver will hold transformers below 5.20; keep training and vLLM serving in **separate environments**, or pin both explicitly and know which fix you are missing.
- **`max_tokens` is now an upper bound, not a reservation** (#57035). Before, a request whose prompt plus `max_tokens` exceeded the context was rejected; now "prompt accepted, sampling `max_tokens` clamped" to what fits. Long prompts that used to error now silently get a shorter generation budget, so check `finish_reason == "length"` and count truncated samples, especially in long-context or long-CoT evaluations.
- **Silent MoE corruption fixed** (#59042, merged 2026-10-12): CUTLASS NVFP4 / MXFP4 Mixture-of-Experts (MoE) kernels under **expert parallelism** ignored the expert map, "so tokens were [routed] to the wrong experts". The PR's example was "~0% GSM8K on RedHatAI/GLM-5.3-MXFP4 with DP=8 / EP=8". If you served an FP4 / MXFP4 MoE checkpoint with `--enable-expert-parallel` on an earlier version, re-check those results.
- **New default KV-cache dtype for GLM-5.x on SM100 (Blackwell)**: an FP8 key/value (KV) cache with `--kv-cache-dtype auto` (#60140, #60281). Outputs can differ slightly from a bf16 KV cache; record the KV-cache dtype and the vLLM version in `metadata.json`.
- **CORS (Cross-Origin Resource Sharing)**: default origins changed "from `*` to none" (#61009); a browser front-end (a loom, a notebook widget) talking to a local vLLM server needs `--allowed-origins`.
- **CUDA builds**: `pip install vllm` is still the CUDA 13.0 build; the CUDA 12.9 Docker image is `vllm/vllm-openai:v0.32.0-cu129` (see the driver section below).

**When not to upgrade yet:** a running study whose numbers you will compare against earlier runs — finish it on the pinned version, or re-run the baseline on 0.32.0. RL-specific vLLM changes (weight sync, colocated training) are in [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

## Driver and CUDA version check on rented GPUs (CUDA 13 wheels)

Aliases: `The NVIDIA driver on your system is too old`, CUDA 13.0 wheels, cu129, driver r580, `nvidia-smi`, CUDA mismatch on RunPod / vast.ai.

**The trap.** vLLM 0.31.0 (2026-10-05) and 0.32.0 (2026-10-18) list `pip install vllm` as "PyPI (CUDA 13.0)" and publish CUDA 12.9 separately (Docker `vllm/vllm-openai:v0.32.0-cu129`, plus CUDA 12.9 wheels on the release page); SkyRL's Tinker quickstart requires "CUDA 13.0 (NVIDIA driver r580 or newer)". On a rented box with an older driver, a fresh install that resolves CUDA 13 builds fails at CUDA initialisation. The PyTorch error string to search for is `The NVIDIA driver on your system is too old (found version …)` (from `c10/cuda/CUDAFunctions.cpp`).

**Check first:** run `nvidia-smi` and read the driver version before installing. If it is older than r580, use CUDA 12.9 artifacts (`docker pull vllm/vllm-openai:v0.32.0-cu129`) or choose a host image with a newer driver (you usually cannot upgrade the driver inside a rented container).

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

vLLM's default PyPI wheel (0.31.0 and 0.32.0) is built for CUDA 13.0, which needs NVIDIA driver r580 or newer. Use the CUDA 12.9 artifacts (`vllm/vllm-openai:v0.32.0-cu129`) or a host image with a newer driver; see "Driver and CUDA version check on rented GPUs" above. If instead pip says `Ignored the following versions that require a different python version`, or quietly installs an older vLLM, you are on Python 3.10, which vLLM 0.32.0 dropped; see the Python version floor section.

### Which Python version should a new research project use?

Python 3.12. vLLM 0.32.0, SGLang 0.5.22, Inspect AI 0.3.281+, TRL 1.16.0 and ControlArena need at least 3.11, and axolotl 0.21.0, Inspect Petri 3.x and Petri Bloom need at least 3.12 (PyPI `requires_python`, checked 2026-10-20). See the Python version floor section above.

### My vLLM outputs got shorter after upgrading — why?

vLLM 0.32.0 treats `max_tokens` as an upper bound and clamps it to whatever fits after the prompt, instead of rejecting prompts that leave too little room (PR #57035). Check `finish_reason == "length"`. Other 0.32.0 changes that move numbers: an FP8 KV cache by default for GLM-5.x on Blackwell (SM100), and a fix for wrong-expert routing in NVFP4 / MXFP4 MoE models under expert parallelism. See "vLLM 0.32.0 upgrade traps" above.

### How do I get logprobs or activations from a 405B base model for free?

Two options: **NDIF** (Llama 3.1 405B via the nnsight remote backend; see [`serving-and-activations.md`](../interpretability/serving-and-activations.md)) and **ACS Infra** (Llama 3.1 405B base and Arcee's Trinity-Large-TrueBase, with a completions API with logprobs, activation harvesting and steering; apply at `infra.acsresearch.org/signup`; MATS can request a batch of accounts). Neither promises full uptime. See the ACS Infra section above.

### Which closed models are being retired soon?

As of 2026-10-20: `o1`, `o3-mini`, `o4-mini`, `gpt-4.1-nano`, `gpt-4-turbo` and `gpt-4o-2024-05-13` shut down 2026-10-23; OpenAI Evals becomes read-only 2026-10-31 and shuts down 2026-11-30; `claude-sonnet-4-5-20250929` retires 2026-11-30; `o3-2025-04-16`, `o3-pro-2025-06-10` and the 2025 GPT-5 snapshots go 2026-12-11; GPT-4o / GPT-4.1 and their fine-tunes go 2027-01-14. Save raw completions before then. Full table: "Closed-model retirements to plan around" above.

### How do I queue jobs on a shared GPU server where I don't have sudo?

`gpuc` (`brendanlong/gpu-coordinator`) runs a per-user dispatcher in `~/.gpuc` over ssh on a subset of the box's GPUs and can also send jobs to per-job RunPod pods; on a real cluster, use Slurm. See the gpuc section above.

### How do I keep a long training run going if my SSH disconnects?

Use **`tmux`** or **`screen`** — start the training inside a tmux session (`tmux new -s train`), launch your job, detach (`Ctrl+b d`), reconnect later (`tmux attach -t train`). Alternative: `nohup python train.py &> train.log &`, but tmux gives you back interactive access. For automatic restarts, use a process supervisor like `systemd` (overkill) or just `while true; do python train.py; sleep 5; done`.

---

Last verified: 2026-10-20. RunPod, vast.ai, Lambda, Modal, Together, Groq all active and supported by mainstream tools. (Additions 2026-10-20: ACS Infra from the announcement post (LessWrong GraphQL markdown) and `arcee-ai/Trinity-Large-TrueBase` metadata from the Hugging Face API; NDIF's model list from `ndif.us` (its eligibility rule not found on the homepage); closed-model retirement dates from the raw markdown of OpenAI's and Anthropic's deprecation pages; `requires_python` values from PyPI JSON per version and the Inspect AI CHANGELOG; vLLM 0.32.0 traps from its GitHub release notes and PRs #57035 and #59042. Not verified: ACS Infra's API and activation interface, which are behind sign-up.) (Additions 2026-10-14: OpenAI fine-tuning dates from `developers.openai.com/api/docs/deprecations.md` (raw markdown, quotes exact); Together post-training billing from `docs.together.ai/docs/post-training/{overview,pricing}.md`; the CUDA 13 / driver r580 section from the vLLM v0.31.0 and PyTorch v2.14.1 GitHub release notes, SkyRL's Tinker quickstart and PyTorch's `c10/cuda/CUDAFunctions.cpp`; gpuc from its README and `gh api` repo metadata. The rest of the page was last fully reviewed 2026-04.)
