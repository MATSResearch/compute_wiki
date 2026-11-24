---
tags:
  - infrastructure
---

# Compute and Infrastructure for Safety Research

How to get GPUs for safety research at MATS scale (≤70B models, single-node or a few nodes). For frontier-scale training infra, this guide is out of scope.

## At a glance

| You need… | Use |
|---|---|
| Cheapest H100/H200 hour, willing to babysit | **vast.ai** or **Runpod community cloud** |
| Reliable rented GPUs with an actual SLA | **Runpod secure cloud**, **Lambda Cloud** |
| Burst inference (no persistent box; pay per second) | **Modal** |
| Burst training jobs without managing infra | **Modal** (bring your own training code), **Together** (job-based fine-tuning, or post-training sessions billed per GPU-minute), **Tinker** / **Fireworks Training API** (per-token LoRA training; see [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md)) |
| Queue jobs on a shared GPU box you have no sudo on, a local card, or per-job Runpod pods, from one command | **gpuc** (`brendanlong/gpu-coordinator`) — see the gpuc section |
| Let a coding agent (Claude Code, Codex) start Runpod pods, push code, run jobs, fetch results and stop the pods, with cost and data-loss guardrails | **runpod-tools** (`rpt`, `kmerkelbach/runpod-tools`) — see the runpod-tools section |
| Run Inspect agent sandboxes without a local Docker daemon | cloud sandbox providers for Inspect (Daytona, E2B, Modal) — see [`agent-scaffolds.md`](../evaluation/agent-scaffolds.md) |
| Fine-tune GPT-4o / GPT-4.1 | Not for new work: OpenAI self-serve fine-tuning is closed to new organisations, and creating jobs ends for everyone on 2027-01-06 — see [Finetuning closed-weight models](#finetuning-closed-weight-models-openai-shutdown-dates) |
| Free / academic | **NDIF** (interp on big models), **ACS Infra** (large *base* models with logprobs, activations and steering), **MATS-provided compute**, university cluster, **Lighthaven** workspace if applicable (ask MATS handbook / torchy) |
| Large model interp without owning H100s | **NDIF** (see [`serving-and-activations.md`](../interpretability/serving-and-activations.md)); **ACS Infra** for Llama 3.1 405B base and Trinity-Large-TrueBase — see the ACS Infra section |
| A 400B-class **base** model with logprobs (base vs chat comparisons, loom-style exploration) | **ACS Infra** (free, apply at `infra.acsresearch.org/signup`) — see the ACS Infra section |
| A closed model your project depends on is being retired | Save raw completions before the date — see [Closed-model retirements](#closed-model-retirements-to-plan-around-openai-anthropic-and-google) |
| Pick a Python version for a new project | **Python 3.12** — see [Python version floor](#python-version-floor-for-the-2026-10-stack-312-for-new-projects) |
| Already-trained model serving | self-hosted **vLLM** on rented box, or use API providers |
| Free-tier hosted inference for open-weight models | **HF Inference API** (rate-limited), **Together** free tier, **Groq** (very fast Llama inference, free tier) |

## Runpod

Aliases: `runpod.io`, "Runpod", "RunPod" (the company's styling before June 2025; Runpod's docs now call it deprecated).

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
- **REST API v1 is retired.** Runpod's migration guide: "REST API v1 is deprecated and will be retired on November 15, 2026." A script or tool that calls `https://rest.runpod.io/v1` needs moving to `https://api.runpod.io/v2` (the guide covers v1 and GraphQL → v2, e.g. `cloudType: ALL` is gone; v2 takes `SECURE` or `COMMUNITY`).
- **Stop wipes everything outside `/workspace`.** Stop/resume recreates the container: `/root`, `/tmp`, packages installed after start and running processes are gone. A stopped pod is pinned to its host and can fail to resume ("not enough free GPUs on the host"), so fetch results before you stop as if you were terminating.
- **`ssh pod 'python job.py'` does not see template env vars or secrets** (`HF_TOKEN` is unset). They live in PID 1's environment only; Runpod's base images write `/etc/rp_environment`, which a non-interactive shell must `source` first.
- **The `RUNPOD_API_KEY` injected into every pod cannot stop or terminate that pod** (403). A pod-side time cap needs your account key delivered separately, never on a command line.
- Agent-driven pod work: see the runpod-tools (`rpt`) section for a CLI and a longer list of these lessons.

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

**What it is.** Managed GPU cloud with a focus on ML workloads. Good clean experience; pricier than Runpod community / Vast but cheaper than AWS / GCP.

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
- **Post-training resources bill until they stop, not until your script ends.** Together's post-training pricing page (`docs.together.ai/docs/post-training/pricing.md`, wording re-read 2026-11-23): "You pay per GPU-minute from the moment a model resource becomes ready until it stops, even while no session is training on it", and "Left running, an idle resource stops on its own only after its idle timeout (one hour by default), and that idle time is billed." Use `ModelResourcesClient` as a context manager (with the session's context manager nested inside), or stop the resource explicitly. Worked example from that page (unchanged since 2026-10-14): `Qwen/Qwen3.8-27B` LoRA on `B200-SXM` with one generator replica = 8 GPUs × $11 per GPU-hour = $88 per hour; `estimate_cost(...)` returns the current rate without provisioning. Several adapters on one resource cost the same per minute as one.
- **Together post-training needs four hours of credit up front, and a run is shut down when credit runs out** (pricing page, read 2026-11-23). "Creating a model resource requires enough credit to run it for four hours at its hourly rate" — the $88-per-hour example "needs \$352". Otherwise "the create request fails with HTTP `402` (`insufficient_balance`) and the message `project balance cannot cover 4 hours of this model resource`, before anything is provisioned." Once a resource is running, Together "checks your credit about once a minute and starts shutting down the resource when your balance goes past your credit limit", which ends its sessions, so checkpoint regularly and top up before a long run. Refunds: "If a resource fails after reaching `READY` (`READY` → `ERROR`), Together AI refunds a trailing window of its runtime: the last three hours for a LoRA resource, or the last six hours for a full-weight resource."

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
- **Trinity-Large-TrueBase is pre-annealing**, so it differs from Arcee's released post-trained models (`arcee-ai/Trinity-Large-Thinking` on Hugging Face; its OpenRouter slug `arcee-ai/trinity-large-thinking` was gone from the models API on 2026-11-23, so the post-trained side of the pair now needs self-hosting or another provider). Do not pair it with a post-trained model and call the difference "post-training" without saying the base is pre-annealing.
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

## Finetuning closed-weight models: OpenAI shutdown dates

Last checked: 2026-11-23.

Aliases: OpenAI fine-tuning API, `ft:gpt-4o`, `ft:gpt-4.1`, `ft:gpt-4o-mini`, self-serve fine-tuning shutdown, fine-tuned model deprecation.

**OpenAI's self-serve fine-tuning is winding down.** Per OpenAI's deprecations page (`developers.openai.com/api/docs/deprecations.md`, full raw markdown read 2026-11-23; earlier reads 2026-10-14 and 2026-11-04) and its fine-tuning guides (`.../guides/supervised-fine-tuning.md`, `.../guides/model-optimization.md`, read the same day); the supervised fine-tuning guide opens with "OpenAI is winding down the fine-tuning platform. The platform is no longer accessible to new users.":

| Date | What happens |
|---|---|
| 2026-05-07 | "Creating fine-tuning jobs or training is not available to organizations that have not previously run fine-tuning." |
| 2026-07-02 | "Creating fine-tuning jobs is no longer available to organizations that have not run inference on a fine-tuned model in the past 60 days." |
| 2026-09-28 (passed) | Shutdown of `babbage-002` and `davinci-002` (notice 2025-09-26); new fine-tuning training on them had already ended on 2024-10-28 |
| 2026-10-23 (passed) | Shutdown of `ft-o4-mini-2025-04-16` (listed as its own row, with `o4-mini`), and of `gpt-4.1-nano-2025-04-14`, `gpt-3.5-turbo`, `gpt-4`, `gpt-4-turbo` and the base snapshot `gpt-4o-2024-05-13` (all announced 2026-04-22). Their fine-tunes went with them: "Fine-tuned versions of the legacy GPT models shut down in October 2026 followed the same shutdown schedule as their underlying base models." |
| 2026-11-30 | The Evals "dashboard, API, and graders for eval workflows" shut down; for graders used in fine-tuning the page points to the fine-tuning timeline (the rows of this table) |
| **2027-01-06** | "Active existing customers will no longer be able to create new fine-tuning jobs on this date. Inference on fine-tuned models will be disabled only when the underlying base model is deprecated." |
| **2027-01-14** | Shutdown of GPT-4o (`gpt-4o-2024-08-06`, `gpt-4o-2024-11-20`), GPT-4o mini (`gpt-4o-mini-2024-07-18`), GPT-4.1 (`gpt-4.1-2025-04-14`) and GPT-4.1 mini (`gpt-4.1-mini-2025-04-14`), announced 2026-10-14; recommended replacement `gpt-6-luna`. "Fine-tuned versions of the models listed above follow the same shutdown schedule as their underlying base models." |

**What can still be fine-tuned (2026-11-23), for an organisation that is still eligible.** The model-optimization guide's method table lists supervised fine-tuning and direct preference optimization (DPO) on `gpt-4.1-2025-04-14`, `gpt-4.1-mini-2025-04-14` and `gpt-4.1-nano-2025-04-14`, and vision fine-tuning on `gpt-4o-2024-08-06`. Of these, `gpt-4.1-nano-2025-04-14` is already shut down ("`gpt-4.1-nano-2025-04-14` and its fine-tuned versions shut down on October 23, 2026", supervised fine-tuning guide), so in practice it is GPT-4.1, GPT-4.1 mini and GPT-4o, all of which shut down on 2027-01-14. The table no longer has a reinforcement fine-tuning row, the reinforcement fine-tuning guide URL now redirects to the API reference, and its model's fine-tunes (`ft-o4-mini-2025-04-16`) shut down on 2026-10-23. A fine-tune created today therefore has at most until 2027-01-14 to be used: "Eligible existing customers can create training jobs until January 6, 2027, unless the base model shuts down earlier."

**What this means for safety research.** The original emergent-misalignment results and many follow-up model organisms were fine-tuned GPT-4o / GPT-4.1 models; those `ft:` checkpoints stop answering when their base model shuts down. Fine-tunes of `gpt-4.1-nano`, `gpt-3.5-turbo`, `gpt-4` and `gpt-4o-2024-05-13` are already gone (2026-10-23); results built on them can only be re-checked from saved outputs. Two practical tips: (1) before 2027-01-14, re-run any evaluation you still need against your `ft:gpt-4o*` / `ft:gpt-4.1*` organisms and save the raw completions with the exact prompts, model IDs and dates, since the model itself will not be re-queryable; (2) for anything new, train an **open-weight** organism instead — LoRA SFT or RL on a rented or owned GPU, a cloud GPU service like **Modal**, or a managed open-weight service (**Tinker**, **Together**, **Fireworks**; see [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md)). Small organisms (e.g. emergent misalignment) work on 0.5B models with a rank-1 LoRA, and ready-made EM adapters exist on Hugging Face (`ModelOrganismsForEM`; see [`model-organisms.md`](../alignment-science/model-organisms.md)). Anthropic does not offer general public model finetuning. An organisation that has never fine-tuned on OpenAI cannot create jobs at all, so a project plan built on OpenAI fine-tuning is worth re-checking before it starts.

**Pitfalls (open-weight finetuning):**

- **Cost is mostly GPU-hours.** A small LoRA on a 0.5–7B model is cheap; full finetunes of large models are not. Estimate GPU-hours first.
- **Rate limits during eval** — if you serve the finetuned model behind a hosted endpoint, it may have separate, lower rate limits.

## Closed-model retirements to plan around (OpenAI, Anthropic and Google)

Last checked: 2026-11-23.

Aliases: model deprecation, model retirement, model shutdown, sunset date, `o3-2025-04-16` shutdown, `claude-sonnet-4-5-20250929` retirement, `claude-opus-4-5-20251101` retirement, Claude Opus 4.5 deprecated, `gemini-2.5-pro` / `gemini-2.5-flash` automatic routing, OpenAI Evals platform shutdown, `shutdown_date`, "model not found" after a retirement.

**This section was re-read on 2026-11-23 and covers Google's Gemini API as well as OpenAI and Anthropic.** **o3**, **Claude Sonnet 4.5** and **Claude Opus 4.5** are the subject models of a number of chain-of-thought (CoT), alignment-faking and scheming studies; Sonnet 4.5 retires on 2026-11-30, o3 on 2026-12-11 and Opus 4.5 on 2027-01-22. Once an OpenAI or Anthropic snapshot is retired, requests to it fail, and a result built on it can only be re-checked from saved outputs. **Google does something different for Gemini 2.5: the old model id keeps answering, from a different model** (next paragraph but one). Dates below are from OpenAI's deprecations page (`developers.openai.com/api/docs/deprecations.md`), Anthropic's model-deprecations page (`platform.claude.com/docs/en/about-claude/model-deprecations.md`) and Google's Gemini deprecations page (`ai.google.dev/gemini-api/docs/deprecations`), read as raw markdown on 2026-11-23 (OpenAI and Anthropic were also read on 2026-10-20 and 2026-11-04). New since 2026-11-04: Anthropic deprecated Claude Opus 4.5 on 2026-11-23; OpenAI added notices for `gpt-5.5-cyber-preview` (shutdown 2027-02-01), `gpt-image-2` (2027-02-10) and for GPT-5.2 / GPT-5.4 / GPT-5.4 mini with EU data residency and `service_tier: fast` or `priority` (2027-01-11), and its recommended replacements for the 2026-12-11 models now name the GPT-6.1 family. OpenAI fine-tuning dates are in the section above.

| Date | Provider | What goes away | Replacement the provider recommends |
|---|---|---|---|
| 2026-10-23 (passed) | OpenAI | `o1`, `o1-pro`, `o3-mini`, `o4-mini`, `gpt-4.1-nano`, `gpt-4o-2024-05-13`, `gpt-4-turbo`, `gpt-4`, `gpt-3.5-turbo` (announced 2026-04-22; their fine-tunes are in the fine-tuning section above) | `gpt-5.6-sol` / `-terra` / `-luna` |
| 2026-10-31 (passed) | OpenAI | **Evals platform**: "Existing evals become read-only." | Export before the 2026-11-30 shutdown; OpenAI points to a Promptfoo migration guide (or move to Inspect AI, see [`evals.md`](../evaluation/evals.md)) |
| 2026-11-30 | OpenAI | The Evals dashboard, API and graders for eval workflows shut down; also `/v1/prompts` (reusable prompt objects) and **Agent Builder** (notice dated 2026-06-03 on the page) | Promptfoo migration guide for Evals; for Agent Builder, "Agents SDK or ChatGPT Workspace Agents" |
| 2026-11-30 | Anthropic | `claude-sonnet-4-5-20250929` (deprecated 2026-09-30) | `claude-sonnet-5-5` |
| **2026-12-01** | Google | `gemini-2.5-pro` and `gemini-2.5-flash` are **not shut down: requests are re-routed** to `gemini-3.8-flash` and `gemini-3.5-flash-lite` respectively, under the old id and billed at the new model's rates (`gemini-2.5-flash-lite` "is not deprecated") | Stop using the 2.5 ids before the date; see the paragraph below |
| 2026-12-11 | OpenAI | `o3-2025-04-16`, `o3-pro-2025-06-10`, `gpt-5-2025-08-07`, `gpt-5-mini-2025-08-07`, `gpt-5-nano-2025-08-07`, `gpt-5-pro-2025-10-06` (and the undated aliases `o3`, `o3-pro`, `gpt-5`, `gpt-5-mini`, `gpt-5-nano`, `gpt-5-pro`) | As of 2026-11-23: `gpt-6.1-sol` for `o3` and `gpt-5`, `gpt-6.1-terra` for `gpt-5-mini`, `gpt-6-luna` for `gpt-5-nano`, and "`gpt-6.1-sol` (`reasoning.mode: pro`) in the Responses API" for `o3-pro` and `gpt-5-pro` (the page named `gpt-5.6-sol` / `-terra` / `-luna` on 2026-11-04) |
| 2027-01-11 | OpenAI | GPT-5.2, GPT-5.4 and GPT-5.4 mini "with EU data residency and `service_tier: fast` or `priority`" (notice 2026-11-18) | The same models with Standard processing, or the GPT-6.2 family |
| 2027-01-14 | OpenAI | GPT-4o, GPT-4o mini, GPT-4.1, GPT-4.1 mini snapshots, **and their fine-tunes** (see the fine-tuning section above) | `gpt-6-luna` |
| **2027-01-22** | Anthropic | `claude-opus-4-5-20251101` (**deprecated 2026-11-23**; until then it was listed as Active with "Not sooner than November 24, 2026"). "This retirement includes `claude-opus-4-5`, the same model’s ID without a date." | `claude-opus-5-5` |
| 2027-02-01 | OpenAI | `gpt-5.5-cyber-preview` (notice 2026-11-05) | "The most capable cyber model available to you." |
| 2027-04-01 | OpenAI | `gpt-5.1`, `gpt-5.3-codex`, `gpt-5.4-nano` | `gpt-6-sol` / `gpt-6-luna` |

**Gemini 2.5 Pro and 2.5 Flash: retirement by substitution, with no error (2026-12-01).** Google's deprecations page (read 2026-11-23; the date the notice was first posted is not stated on it): "Effective December 1, 2026, all API requests to `gemini-2.5-pro` will automatically route to `gemini-3.8-flash` and be billed at Gemini 3.8 Flash rates", and likewise "all API requests to `gemini-2.5-flash` will automatically route to `gemini-3.5-flash-lite`". API access to the 2.5 models is already "limited to users who have actively used them in the past". The same page shows the pattern for other ids (`gemini-3.7-flash` routes to `gemini-3.8-flash`, `gemini-3.5-flash` to `gemini-3.6-flash`), and lists `gemini-2.0-flash` as shut down on 2026-06-01. Consequence: a rerun of a Gemini 2.5 baseline after 2026-12-01 returns HTTP 200 from a different, newer model, so a "replication" silently measures Gemini 3.8 Flash or 3.5 Flash-Lite. What to do: finish Gemini 2.5 runs and save raw completions before 2026-12-01; log the model version the **response** reports alongside the id you requested, and fail the run if they differ (not verified: which response field carries the routed model's name after the switch); never treat a provider alias or a deprecated id as a pinned snapshot. **When this does not matter:** work that only ever used Gemini 3.x ids that are not on the deprecations page.

**Check retirements from code (OpenAI).** OpenAI's deprecations page now says: "To monitor model shutdowns **programmatically**, call the List models endpoint (`GET /v1/models`) and check each model's optional `shutdown_date` field." A pre-flight check in a long eval can read that field for every model id in the config and stop if a shutdown date falls inside the planned run. OpenRouter's models API has the comparable `expiration_date` field (it listed the 2026-12-11 OpenAI models with that date on 2026-11-23).

Also on Anthropic's page: `claude-mythos-preview` is deprecated (since 2026-06-09) with its retirement date "To be announced", and `claude-haiku-4-5-20251001` is still listed as Active with "Not sooner than October 15, 2026" — that date has passed without a deprecation notice (as of 2026-11-23). Opus 4.5 shows what that status is worth: it was deprecated one day before its "not sooner than" date, with 60 days' notice to retirement, so treat an "Active, not sooner than" model as one that can get a 60-day clock at any time. The Sonnet 4.5 retirement on 2026-11-30 likewise "includes `claude-sonnet-4-5`, the same model’s ID without a date". Separately from retirements, the Anthropic API version `2026-10-21` removed `temperature`, `top_p` and `top_k` for every model, so a temperature-0 rerun of an older Claude result is no longer possible on the current SDK ([`experiment-tracking.md`](experiment-tracking.md#anthropic-api-version-2026-10-21-removes-temperature-top_p-and-top_k-claude-evals)). Anthropic's page says the dates apply to "Anthropic-operated platforms" (the Claude API, Claude Platform on AWS, Claude Models on Google Cloud (Anthropic managed) and Microsoft Foundry), while "Partner-operated platforms, Claude Models on Google Cloud (Google managed) and Amazon Bedrock, set their own retirement schedules".

**What to do before a retirement date:**

- Re-run the evaluations you still need and save the **raw completions** with the exact prompt, model id (dated snapshot, not an alias), sampling parameters, provider and date. A summary score cannot be re-derived once the model is gone.
- If a published result you are extending used one of these snapshots, collect the comparison numbers now; afterwards you can only compare against the paper's reported numbers, on whatever subset they released.
- Anthropic's page says it "has committed to long-term preservation of model weights" (link on that page: *Commitments on Model Deprecation and Preservation*); that is not API access, so do not plan on querying a retired model.

**When this section is not relevant:** open-weights models (download and pin the weights yourself; see [`open-weights-models.md`](open-weights-models.md)). Open models served through OpenRouter also retire: its models API carries an `expiration_date` field, though models have outlived their listed date (see the OpenRouter section of `open-weights-models.md`).

## Python version floor for the 2026-10 stack (3.12 for new projects)

Aliases: `requires_python`, `Requires-Python >=3.11`, pip's `Ignored the following versions that require a different python version` followed by `No matching distribution found for vllm==0.32.0` on Python 3.10, `uv` resolution failure on Python 3.10, `torch==2.14.0 has no wheels with a matching Python ABI tag (e.g., cp315)` on Python 3.15, which Python version for a new project.

**The trap.** In October 2026 several core research libraries dropped Python 3.10. On a 3.10 environment, pip silently resolves to the last release that still supports 3.10 (old bugs included), or `uv` fails to resolve. At the other end, uv ≥ 0.13.0 downloads Python 3.15 when no version is requested or pinned and no compatible Python is installed, and vLLM 0.33.0 cannot install there (details in [`code-recipes.md`](../engineering/code-recipes.md#standard-pyprojecttoml-baseline)). `requires_python` from PyPI JSON, checked 2026-10-20 and re-checked 2026-11-04 and 2026-11-23:

| Package (version, release date) | `requires_python` |
|---|---|
| `vllm` 0.32.0 (2026-10-18), 0.33.0 (2026-11-02), 0.34.0 (2026-11-16, current) | `<3.15,>=3.11` (0.31.0 was `>=3.10`) |
| `sglang` 0.5.22 (2026-10-16), 0.5.23 (2026-10-30, current) | `>=3.11` (0.5.21 was `>=3.10`) |
| `inspect-ai` 0.3.281 (2026-10-15) through 0.3.292 (2026-11-23, current) | `>=3.11` (0.3.280 was `>=3.10`; CHANGELOG: "require Python 3.11 and test on Python 3.14") |
| `trl` 1.16.0 through 1.18.2 (2026-11-19, current), `control-arena` 20.1.0 / 20.1.1 | `>=3.11` |
| `transformers` 5.21.0 (2026-10-26) and later (current 5.24.0, 2026-11-21), `torch` 2.15.0 (2026-10-28) | `>=3.11` (transformers 5.20.2 and torch 2.14.x were `>=3.10`) |
| `peft` 0.22.0 (2026-11-19, current), `accelerate` 1.16.0 (2026-11-16, current) | `>=3.11` (new on 2026-11-23: `peft` 0.21.2 and 0.21.3 were `>=3.10`; transformers 5.24.0's notes say "`peft>=0.22.0` is now required") |
| `axolotl` 0.21.0 / 0.21.1, `inspect-petri` 3.1.1, `petri-bloom` 0.2.6 | `>=3.12` (thimble's README also says Python 3.12+) |
| `wandb` 0.31.0 through 0.31.2, `anthropic` 2.13.0, `circuit-tracer` 0.5.4, `sae-lens` 6.56.1, `transformer-lens` 4.4.0, `nnsight` 0.8.4 | `>=3.10` |

**Recommendation.** Use `requires-python = ">=3.12"` and pin the interpreter with `uv python pin 3.12` (or 3.13; not 3.15 while you need vLLM) for a new project that combines training, serving and Inspect evaluations. Run `python --version` on a rented box before installing. **When not to bother:** a project that only calls hosted APIs through one SDK, or an existing environment you are not upgrading.

## vLLM 0.32.0 upgrade traps (released 2026-10-18)

Aliases: vLLM v0.32.0, `vllm-project/vllm` release 0.32, `transformers>=5.16.1,<5.20.0`, `max_tokens` clamped, `finish_reason: "length"`, CORS `--allowed-origins`, NVFP4 / MXFP4 MoE expert-parallel corruption, FP8 KV cache default.

From the [v0.32.0 release notes](https://github.com/vllm-project/vllm/releases/tag/v0.32.0) and the linked PRs:

- **Python 3.10 dropped** ("the minimum is Python 3.11", #60402). See the Python version floor section.
- **`transformers>=5.16.1,<5.20.0`** (#57387). That excludes transformers 5.20.x (5.20.0 released 2026-10-15), which contains a training-gradient fix for `use_kernels=True` (see the transformers row in [`safety-toolkits.md`](safety-toolkits.md#fast-moving-libraries-pin-the-version)). If you train and serve from one environment, the resolver will hold transformers below 5.20; keep training and vLLM serving in **separate environments**, or pin both explicitly and know which fix you are missing.
- **`max_tokens` is now an upper bound, not a reservation** (#57035). Before, a request whose prompt plus `max_tokens` exceeded the context was rejected; now "prompt accepted, sampling `max_tokens` clamped" to what fits. Long prompts that used to error now silently get a shorter generation budget, so check `finish_reason == "length"` and count truncated samples, especially in long-context or long-CoT evaluations.
- **Silent MoE corruption fixed** (#59042, merged 2026-10-12): CUTLASS NVFP4 / MXFP4 Mixture-of-Experts (MoE) kernels under **expert parallelism** ignored the expert map, "so tokens were [routed] to the wrong experts". The PR's example was "~0% GSM8K on RedHatAI/GLM-5.3-MXFP4 with DP=8 / EP=8". If you served an FP4 / MXFP4 MoE checkpoint with `--enable-expert-parallel` on an earlier version, re-check those results.
- **New default KV-cache dtype for GLM-5.x on SM100 (Blackwell)**: an FP8 key/value (KV) cache with `--kv-cache-dtype auto` (#60140, #60281). Outputs can differ slightly from a bf16 KV cache; record the KV-cache dtype and the vLLM version in `metadata.json`.
- **CORS (Cross-Origin Resource Sharing)**: default origins changed "from `*` to none" (#61009); a browser front-end (a loom, a notebook widget) talking to a local vLLM server needs `--allowed-origins`.
- **CUDA builds**: `pip install vllm` is still the CUDA 13.0 build; the CUDA 12.9 Docker image is `vllm/vllm-openai:v0.32.0-cu129` (see the driver section below). 0.32.0 is the last release with CUDA 12.9 builds.

**vLLM 0.33.0 (PyPI 2026-11-02; the GitHub release is titled v0.33.0 but tagged `v0.33.0rc3`).** Its release notes: "**CUDA 12.9 dropped**: release wheels and images are CUDA 13.0 only" (#62575); `torch==2.14.0` and `transformers>=5.16.1,<5.21.0` (so transformers 5.20.2 now fits); beam-search scores are normalised by generated length (#62928); Medusa and the MLP speculator are removed; requests sent while generation is paused get HTTP 503; GLM-5.3-Flash defaults to an FP8 KV cache (#61228); and "a silent MoE weight corruption fix with packed NCCL transfer plus layerwise reload" (#62555) for RL weight sync. Python 3.15 and separate-environment consequences: [`code-recipes.md`](../engineering/code-recipes.md#standard-pyprojecttoml-baseline); RL weight-sync details: [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md#vllm-hooks-for-a-hand-rolled-rl-loop-sleep-weight-transfer-pauseresume).

**vLLM 0.34.0 (PyPI 2026-11-16; current on 2026-11-23).** From its release notes ("Before you upgrade") and PyPI metadata:

- **`gpu_memory_utilization` now defaults to 1.0** (it was 0.92 from v0.20 through v0.33, and 0.9 before that; with the extensible KV cache turned off, 0.34.0 still resolves to 0.92 — `vllm/config/cache.py` at each tag), because the "Extensible KV cache" is on by default and sizes the key/value (KV) cache "from memory actually free **after** CUDA graph capture and warmup". The notes: "**In most cases it's now best to not set `gpu_memory_utilization`** … Use it to share a GPU with other processes or when extensible kv cache is disabled." So a second process on the same GPU — a training job, a colocated RL trainer, an activation-extraction script, a second server — now finds the memory taken unless you pass `--gpu-memory-utilization` explicitly. Symptom: `CUDA out of memory` in the *other* process after upgrading vLLM.
- **Model Runner V1 is removed.** "Remove `VLLM_USE_V2_MODEL_RUNNER=0`; it now fails at startup. Port V1 logits processors to `vllm.v1.worker.gpu.sample.logits_processor`." Anything that depends on the V1 runner (older activation plugins, custom logits processors) must stay on vLLM ≤ 0.33.
- **Default `--block-size` is 64 (was 16)**; "Pass `--block-size 16` to keep the old behavior."
- **Dependencies:** `transformers<5.23.0,>=5.16.1` (so transformers 5.22.x now fits, 5.23.0 and 5.24.0 do not), still `torch==2.14.0`, `huggingface_hub>=2.0.0`, `tokenizers>=0.23.3`, Python `<3.15,>=3.11`.
- **LoRA adapters that vLLM used to part-apply are now refused** (#63489). Before, when a PEFT adapter carried LoRA weights for a module vLLM keeps as a plain `nn.Linear` (the PR's example: `bert.pooler.dense` in BERT models trained with `target_modules="all-linear"`), "vLLM loaded these adapters and ignored those weights without a warning, so outputs differed from transformers + PEFT"; now loading fails with a `ValueError` naming the modules. The notes also list "embedding LoRA scaled by `embed_scale`" (#62470). If a model organism is a LoRA adapter that targets embeddings, heads or `all-linear`, and you evaluated it through vLLM before 0.34.0, compare a few prompts' logits against transformers + PEFT before trusting those numbers. Not verified: the first affected version, or how many decoder-only chat adapters are affected (the PR's worked examples are BERT and RoBERTa classifiers).
- **New models** include Mistral Large 4 (#64534).

**Security: keep a rented vLLM server off the public internet, and serve community checkpoints on ≥ 0.33.0.** Thirteen vLLM security advisories were published between 2026-10-27 and 2026-11-18 (the `vllm-project/vllm` repository security-advisories API, read 2026-11-23). Two are rated high and both are fixed in 0.33.0: GHSA-q9v9-qpjp-fc24, "Unauthenticated EngineCore crash via out-of-range prompt token id under skip_tokenizer_init" (affects `>= 0.28.0, < 0.33.0`), and GHSA-5r3c-5x4v-8gjh, "Missing request-wide media budget allows single-request frontend resource exhaustion" (`>= 0.6.0, < 0.33.0`). GHSA-qrj2-j723-m6w8 (medium, `< 0.33.0`) is a directory traversal through a served repository's speculators config, i.e. a downloaded model repo can influence what the server reads. GHSA-xgh8-qwjh-q853 (medium, fixed in 0.34.0; the advisory text says it "affects vLLM 0.32.0rc0 through 0.33.0", while its machine-readable range reads `>= 0.32.0rc0, <= 0.34.0`, so a dependency scanner may still flag 0.34.0): `POST /v1/systemone` accepted a request-supplied chat template even when the server's trust setting disallowed it, for architectures including `Qwen3ForCausalLM` and `Qwen3_5ForConditionalGeneration`, so a caller could replace the system block the operator pinned. The other nine (all medium) were already fixed in older releases: five in 0.31.0 (request-driven CPU or memory exhaustion in image / video preprocessing, and a heap-address leak), and four in 0.30.0, 0.28.0 or 0.21.0 (a prompt-embeds denial of service, error-response amplification, and two bugs that leak tokens or state between co-batched requests). On a rented box, bind to localhost or set `--api-key`; none of the advisories carried a CVE id in the API response.

**The `torch==2.14.0` pin has a security cost (2026-11-10).** PyTorch advisory GHSA-v32g-mr63-3j83 (high; "torch.load(weights_only=True) allows arbitrary file read"; vulnerable `>=2.14.0`, patched `2.15.0`): "A malicious PyTorch checkpoint can read text files from the computer loading it, even when it is loaded with `weights_only=True`", including "`.env`, configuration files, source code, credentials"; "Tested vulnerable on PyTorch `2.14.0+cpu` and `2.14.1`." vLLM 0.33.0 and 0.34.0 pin `torch==2.14.0` and axolotl 0.21.1 caps `torch<2.15.0`, so those environments cannot take the fix. In a torch 2.14 environment, do not `torch.load` third-party `.pt` / `.bin` / pickle-format files (community SAEs, probes, lenses, adapters) from sources you do not trust; prefer `.safetensors`, or load them in a separate torch ≥ 2.15 environment with no credentials on disk. Not verified: whether torch < 2.14 is affected (the advisory text says "In Torch-2.14").

**When not to upgrade yet:** a running study whose numbers you will compare against earlier runs — finish it on the pinned version, or re-run the baseline on the new one. RL-specific vLLM changes (weight sync, colocated training) are in [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md).

## Driver and CUDA version check on rented GPUs (CUDA 13 wheels)

Aliases: `The NVIDIA driver on your system is too old`, CUDA 13.0 wheels, cu129, driver r580, `nvidia-smi`, CUDA mismatch on Runpod / vast.ai.

**The trap.** vLLM 0.31.0 (2026-10-05) and 0.32.0 (2026-10-18) list `pip install vllm` as "PyPI (CUDA 13.0)" and publish CUDA 12.9 separately (Docker `vllm/vllm-openai:v0.32.0-cu129`, plus CUDA 12.9 wheels on the release page); vLLM 0.33.0 (2026-11-02) publishes CUDA 13.0 only. PyTorch 2.15.0 (2026-10-28) moves its default wheel to CUDA 13.2 (`cu132` and `cu134`; `cu126` and `cu130` are no longer built), and its notes say CUDA 13 wheels "need NVIDIA driver 580 or newer and a GPU of Turing (`sm_75`) or newer, so Maxwell, Pascal and Volta GPUs and hosts with a CUDA 12.x driver should stay on 2.14"; SkyRL's Tinker quickstart requires "CUDA 13.0 (NVIDIA driver r580 or newer)". On a rented box with an older driver, a fresh install that resolves CUDA 13 builds fails at CUDA initialisation. The PyTorch error string to search for is `The NVIDIA driver on your system is too old (found version …)` (from `c10/cuda/CUDAFunctions.cpp`).

**Check first:** run `nvidia-smi` and read the driver version before installing. If it is older than r580, stay on vLLM 0.32.0's CUDA 12.9 artifacts (`docker pull vllm/vllm-openai:v0.32.0-cu129`; there is no CUDA 12.9 build of 0.33.0; vLLM 0.32.0 itself pins `torch==2.13.0`) and, outside vLLM, torch 2.14, or choose a host image with a newer driver (you usually cannot upgrade the driver inside a rented container).

**Silent-correctness release.** PyTorch v2.14.1 (2026-09-30) moves its CUDA 13.2 Linux binaries to CUDA 13.2.2 to fix a cuBLAS NVFP4 scaling bug and a compiler bug that "could leave stale or corrupted register values in kernels with nested thread divergence (present since CUDA 12.8)". If you are on torch 2.14.0 with the CUDA 13.2 binaries, upgrade. **When not relevant:** managed APIs (Tinker, Fireworks, Together), or boxes already on driver r580+.

## gpuc: a single-user GPU job queue (shared box without sudo, local cards, Runpod)

Aliases: **gpuc**, `brendanlong/gpu-coordinator` on GitHub (MIT; created 2026-09-15, very new), "gpuc: A single-user GPU queue that doesn't require sudo" (Brendan Long, LessWrong 2026-09-29).

**What it is.** One `gpuc submit job.yaml` path for three kinds of host: local cards; "**ssh** — a shared box you have no sudo on, using a subset of its GPUs"; and a Runpod pod provisioned per job. Each host runs a small stdlib-only dispatcher out of `~/.gpuc` and owns its own queue; S3 is an optional mirror of specs, the job index and logs, never the queue; "a rented pod ends itself once its queue has been idle, `gpuc pods` shows what is still billing"; there is an optional web dashboard. Not on PyPI; install from git with `uv tool`.

```bash
# From the README
uv tool install "git+https://github.com/brendanlong/gpu-coordinator@main"
gpuc host add local
gpuc submit job.example.yaml --host local    # or --runpod --gpu A40 --max-price 0.60
gpuc status
gpuc logs <job-id> -f
gpuc wait <job-id> [<job-id> ...]
```

**When to use it:** you share a multi-GPU server without admin rights (a 2×4090-style lab box), want to queue overnight sweeps on part of its GPUs, and occasionally burst to Runpod without a second workflow. **When not to use it:** a cluster that already has Slurm or another scheduler, or a multi-user lab that needs fair-share scheduling (it is explicitly single-user, and the repo had 1 star as of 2026-10-14, so expect rough edges).

## runpod-tools (`rpt`): let a coding agent drive Runpod pods

Aliases: **runpod-tools**, `rpt`, `rpt2`, `kmerkelbach/runpod-tools` on GitHub (Kilian Merkelbach; created 2026-09-30, last commit 2026-10-27, 3 stars as of 2026-11-24). `pyproject.toml` declares MIT; the repo has no LICENSE file. Not on PyPI; no releases or tags.

**What it is.** An agent-friendly Runpod CLI (for Claude Code, Codex or a person): a small command-line tool for the everyday Runpod loop: create a pod, wait for SSH, push code, run a job, fetch results, stop the pod. Python standard library only (Python ≥ 3.11, no Runpod SDK, no `requests`), written so an agent can read the README and use every command. It ships an `AGENTS.md` of rules for an agent operating someone's account (only manage pods you launched this session; fetch, verify locally, then destroy, as three separate steps; never delete a network volume; poll logs gently) and a `docs/gotchas.md` of operational lessons, one heading each. Talks to Runpod's REST API v2 by default since 2026-10-20 (`RPT_API=v1` goes back to v1 + GraphQL; REST v1 itself was retired 2026-11-15).

```bash
# From the README (run from a clone of the repo)
pip install -e .            # gives you `rpt`
export RUNPOD_API_KEY=...
rpt init                    # writes runpod-tools.toml; fill in template_id + [sync]
rpt gpus --secure           # pick a GPU type id
rpt start --experiment eval --gpu-type "NVIDIA H200" --wait   # prints pod_id=<id> last
rpt push --pod abc123
rpt run --pod abc123 --background job1 -- python train.py --epochs 3
rpt run --pod abc123 -- tail -n 20 /workspace/rpt/job1.log
rpt fetch --pod abc123
ls results/                 # verify locally BEFORE the next line
rpt terminate --pod abc123 -y
```

What it handles for you, each from a lesson in its `docs/gotchas.md`:

- **No ssh/rsync on some Secure Cloud pods** (only the web terminal and the `ssh.runpod.io` proxy work): `rpt start` sends `supportPublicIp: true` by default so the pod lands on a host that can expose a public TCP port; `rpt pods` says "no TCP endpoint" otherwise.
- **`Host key verification failed`, rsync exit 255 on a fresh pod**: Runpod reuses `ip:port` pairs across pods; `rpt wait` removes the stale `known_hosts` entry and records the new key.
- **`cuda.is_available() == False` / `The NVIDIA driver on your system is too old`**: `rpt start --cuda-version 13.0` only schedules onto hosts whose driver supports it (see the driver and CUDA section).
- **Secrets missing over ssh**: `rpt run` sources `/etc/rp_environment` before every command; `examples/pod-start.sh` writes that file in a custom image.
- **ssh hangs after `nohup … &`**, and **sshd dropping connections when several watchers poll** (`MaxStartups`; looks exactly like a dead pod): `rpt run --background NAME` detaches cleanly with its log at `/workspace/rpt/NAME.log`; poll with one call per check.
- **A cost cap that only an outside poller enforces is not a cap**: `examples/killswitch.sh` runs on the pod and stops or terminates it after N hours, with the account key delivered over stdin (the pod's own injected key gets 403).
- **Unattended runs never hang on a prompt**: an ambiguous `--pod` off a terminal exits 2 listing the candidates; destructive commands need `-y`. With `[pod].name_prefix` set on a shared account, `--all` and automatic selection only touch pods carrying the prefix. There is no volume-delete command.
- **429 Too Many Requests** from Runpod's per-account rate limit: retried with backoff, and `run`, `ssh`, `push`, `pull` and `fetch` share one cached pod listing across `rpt` processes.

**When to use it:** you have Claude Code or another agent run experiments on Runpod pods you pay for, or you want one scriptable push / run / fetch loop instead of hand-built ssh and rsync lines. Its `AGENTS.md` and `docs/gotchas.md` are worth reading even if you keep your own scripts. `docs/fleet-pattern.md` covers one job across N pods. **When not to use it:** you want a job queue that starts and ends pods per job, or one interface over a shared box, local cards and Runpod (gpuc, see the gpuc section); serverless or per-second burst work (Modal); providers other than Runpod. A one-person repo with no releases, so pin a commit. Its own docs sometimes describe the older v1 + GraphQL plumbing.

## Storage

- **Datasets / model weights:** Cache on the rented box's local SSD, not the persistent volume (faster + you can re-download).
- **Permanent storage:** Backblaze B2, S3, or institutional drives. Don't store research artifacts only on a rented box.
- **`HF_HOME` / `HF_DATASETS_CACHE`** — set these to the big-disk path on rented boxes; default location is small.

## Cross-cutting cost pitfalls

- **Idle pods bill hourly.** Stop pods you're not using. Runpod's "stopped" state still bills storage but not compute.
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

**vast.ai** (peer-supplied marketplace) typically has the lowest H100 / H200 hourly rates, but reliability varies — filter by host reliability score. **Runpod community cloud** is similarly cheap; **Runpod secure cloud** and **Lambda Cloud** cost more but are more reliable. For interpretability workloads on smaller models, A100 80GB is plenty and much cheaper than H100.

### vast.ai vs Runpod — which?

**vast.ai** for absolute lowest cost on one-off experiments where you can tolerate occasional reliability issues. **Runpod (secure cloud)** for work you care about — actual SLA, smoother dev experience. **Runpod community cloud** is in between (cheap, less reliable). For multi-day jobs, secure cloud only; community cloud nodes can disappear.

### Can I use Modal for training, or just inference?

Both, but it's most natural for **burst** workloads — eval batches over 1000 prompts, occasional finetune jobs. For long-running interactive training, a persistent box (Runpod / Lambda) is friendlier. Modal pays per-second, which is great for bursts and expensive for sustained loads.

### How do I install Docker on a Runpod box?

Most Runpod templates come with Docker pre-installed; if yours doesn't, `apt-get update && apt-get install -y docker.io && systemctl start docker`. You may need to start the daemon manually (`dockerd &` in the background). Inspect AI's `docker` sandbox needs this.

### What is `HF_HOME` and why should I set it?

`HF_HOME` is HuggingFace's cache root for models and datasets (default `~/.cache/huggingface`). On rented GPU boxes the home directory is often small; pulling a 70B model fills it fast. Set `export HF_HOME=/workspace/hf_cache` (or wherever the big disk is) before downloading models. Same applies to `HF_DATASETS_CACHE`.

### A100 vs H100 for inference — which?

**A100 80GB**: cheaper per hour (~half the cost of H100), enough for most ≤70B-int4 inference and for full TransformerLens / SAE workflows on smaller models. **H100**: ~2× faster for inference of fp16/bf16 models, better for long-context, supports newer fp8 quantization. **H200**: more memory than H100, useful for longer context. For most MATS-fellow research scale, A100s are fine; reach for H100 only if you're throughput-bound.

### Can I use a free-tier API for evals?

Limited. **Groq** has a generous free tier for Llama / Mixtral and is fast — good for development. **Together AI** has small free credits. **HF Inference API** is rate-limited. For sustained eval work, expect to pay; provider research credit programs (OpenAI Researcher Access, Anthropic research, Google research credits) help with scaled work.

### Can I do RL (GRPO) on a single rented 24 GB GPU?

For small models, yes. Unsloth's RL guide gives QLoRA 4-bit GRPO VRAM ≈ the parameter count in GB (LoRA 16-bit needs at least 4× that), and TRL can colocate vLLM on the same card with sleep mode. Settings, configs and pitfalls: [`rl-frameworks.md`](../oversight-and-control/rl-frameworks.md) and `project_templates/rl_small/`. Check the NVIDIA driver version with `nvidia-smi` before installing a CUDA 13 build (see the driver section above).

### `pip install vllm` worked but CUDA fails with "driver is too old" — why?

vLLM's default PyPI wheel (0.31.0 onwards; 0.33.0 ships CUDA 13.0 only) and PyTorch 2.15's default wheel (CUDA 13.2) need NVIDIA driver r580 or newer. Use vLLM 0.32.0's CUDA 12.9 artifacts (`vllm/vllm-openai:v0.32.0-cu129`, which pin torch 2.13.0) and torch 2.14 for anything outside vLLM, or a host image with a newer driver; see "Driver and CUDA version check on rented GPUs" above. If instead pip says `Ignored the following versions that require a different python version`, or quietly installs an older vLLM, you are on Python 3.10, which vLLM 0.32.0 dropped; see the Python version floor section.

### After upgrading vLLM, my other process on the same GPU gets `CUDA out of memory` — why?

vLLM 0.34.0 (2026-11-16) turns the extensible KV cache on by default and `gpu_memory_utilization` now defaults to 1.0, so the server takes the memory that is free after warmup. Pass `--gpu-memory-utilization` (for example 0.5) when a trainer, a second server or an activation script shares the card. The same release removes Model Runner V1 (`VLLM_USE_V2_MODEL_RUNNER=0` "now fails at startup") and refuses LoRA adapters it previously loaded while ignoring some of their weights. See the vLLM 0.34.0 paragraph under "vLLM 0.32.0 upgrade traps" above.

### Is it safe to `torch.load` a checkpoint with `weights_only=True`?

Not on torch 2.14.x: PyTorch advisory GHSA-v32g-mr63-3j83 (published 2026-11-10, patched in 2.15.0) describes a checkpoint that reads text files such as `.env` from the loading machine even with `weights_only=True`. vLLM 0.33.0 / 0.34.0 pin `torch==2.14.0` and axolotl 0.21.1 caps `torch<2.15.0`. Prefer `.safetensors`, or load untrusted pickle-format files in a torch ≥ 2.15 environment that holds no credentials. See "vLLM 0.32.0 upgrade traps" above.

### Which Python version should a new research project use?

Python 3.12 (or 3.13), pinned with `uv python pin`. vLLM 0.32.0+, SGLang 0.5.22+, Inspect AI 0.3.281+, TRL 1.16.0+, ControlArena, transformers 5.21.0+, torch 2.15.0, and (new in 2026-11) PEFT 0.22.0 and accelerate 1.16.0 need at least 3.11, and axolotl 0.21.x, Inspect Petri 3.x and Petri Bloom need at least 3.12; vLLM 0.33.0 and 0.34.0 do not install on 3.15 (`requires_python <3.15`), which uv ≥ 0.13.0 downloads by default when nothing is pinned and no compatible Python is installed (PyPI `requires_python`, checked 2026-11-23). See the Python version floor section above.

### My vLLM outputs got shorter after upgrading — why?

vLLM 0.32.0 treats `max_tokens` as an upper bound and clamps it to whatever fits after the prompt, instead of rejecting prompts that leave too little room (PR #57035). Check `finish_reason == "length"`. Other 0.32.0 changes that move numbers: an FP8 KV cache by default for GLM-5.x on Blackwell (SM100), and a fix for wrong-expert routing in NVFP4 / MXFP4 MoE models under expert parallelism. In 0.33.0, beam-search scores are normalised by generated length, which can change which beam wins. See "vLLM 0.32.0 upgrade traps" above.

### How do I get logprobs or activations from a 405B base model for free?

Two options: **NDIF** (Llama 3.1 405B via the nnsight remote backend; see [`serving-and-activations.md`](../interpretability/serving-and-activations.md)) and **ACS Infra** (Llama 3.1 405B base and Arcee's Trinity-Large-TrueBase, with a completions API with logprobs, activation harvesting and steering; apply at `infra.acsresearch.org/signup`; MATS can request a batch of accounts). Neither promises full uptime. See the ACS Infra section above.

### Why did my Gemini 2.5 results change after 2026-12-01 with no error?

From 2026-12-01 Google routes API requests for `gemini-2.5-pro` to `gemini-3.8-flash` and for `gemini-2.5-flash` to `gemini-3.5-flash-lite`, under the old model id and at the new model's price (Google's Gemini deprecations page, read 2026-11-23). The request succeeds, so nothing in your logs flags it unless you record the model version the response reports. Finish 2.5 baselines before that date and save raw completions. See "Closed-model retirements to plan around" above.

### Which closed models are being retired soon?

As of 2026-11-23: `o1`, `o3-mini`, `o4-mini`, `gpt-4.1-nano`, `gpt-4-turbo` and `gpt-4o-2024-05-13` shut down on 2026-10-23 (passed); OpenAI Evals became read-only 2026-10-31 and shuts down 2026-11-30 (with `/v1/prompts` and Agent Builder); `claude-sonnet-4-5-20250929` and the undated `claude-sonnet-4-5` retire 2026-11-30; on 2026-12-01 Google re-routes `gemini-2.5-pro` to `gemini-3.8-flash` and `gemini-2.5-flash` to `gemini-3.5-flash-lite` under the old ids, with no error; `o3-2025-04-16`, `o3-pro-2025-06-10` and the 2025 GPT-5 snapshots go 2026-12-11; GPT-4o / GPT-4.1 and their fine-tunes go 2027-01-14; `claude-opus-4-5-20251101` and the undated `claude-opus-4-5` retire **2027-01-22** (deprecated 2026-11-23; recommended replacement `claude-opus-5-5`). Save raw completions before then. Full table: "Closed-model retirements to plan around" above.

### How do I queue jobs on a shared GPU server where I don't have sudo?

`gpuc` (`brendanlong/gpu-coordinator`) runs a per-user dispatcher in `~/.gpuc` over ssh on a subset of the box's GPUs and can also send jobs to per-job Runpod pods; on a real cluster, use Slurm. See the gpuc section above.

### How do I keep a long training run going if my SSH disconnects?

Use **`tmux`** or **`screen`** — start the training inside a tmux session (`tmux new -s train`), launch your job, detach (`Ctrl+b d`), reconnect later (`tmux attach -t train`). Alternative: `nohup python train.py &> train.log &`, but tmux gives you back interactive access. For automatic restarts, use a process supervisor like `systemd` (overkill) or just `while true; do python train.py; sleep 5; done`.

---

Last verified: 2026-11-24 for the runpod-tools section and the Runpod REST v1 retirement and spelling (from the `kmerkelbach/runpod-tools` repo at commit `87954f7`: README, `AGENTS.md`, `docs/gotchas.md`, `pyproject.toml`, `examples/killswitch.sh`, and `gh api` repo metadata; Runpod's `api-reference-v2/migrate-from-v1.md` as raw markdown; the tool's test suite was not run); 2026-11-23 for the retirement, Python-floor, vLLM 0.34.0 / security and Together post-training billing sections and the ACS Infra Trinity note; 2026-11-04 for the vLLM 0.33.0 and driver sections; 2026-10-20 for the rest. (Additions 2026-11-23: Anthropic model-deprecations page and release notes, OpenAI deprecations page and Google's Gemini deprecations page (`ai.google.dev/gemini-api/docs/deprecations.md.txt`) re-read as raw markdown on 2026-11-23, quotes exact; OpenRouter `expiration_date` values and the missing `arcee-ai/trinity-large-thinking` slug from `https://openrouter.ai/api/v1/models`; `requires_python`, `requires_dist` and upload dates from PyPI JSON for vllm 0.34.0, sglang 0.5.23, inspect-ai 0.3.292, trl 1.18.2, transformers 5.24.0, peft 0.22.0 / 0.21.3, accelerate 1.16.0, wandb 0.31.2, anthropic 2.13.0, circuit-tracer 0.5.4, sae-lens 6.56.1, transformer-lens 4.4.0 and nnsight 0.8.4; vLLM v0.34.0 release body and PR #63489 body via `gh api`; vLLM and PyTorch security advisories via the GitHub security-advisories API (summaries, severities, version ranges; bodies read for GHSA-xgh8-qwjh-q853 and GHSA-v32g-mr63-3j83 only); Together's post-training pricing page as raw markdown. Not verified: Bedrock and Google-managed Vertex retirement dates for Claude models; when Google first posted the Gemini 2.5 routing notice and which response field reports the routed model; what a Chat Completions request with tools returns on GPT-6.2 (see `safety-toolkits.md`); the first vLLM version affected by the LoRA part-application bug; NDIF's model list, ACS Infra's current models and the qualitative Runpod / vast.ai / Lambda availability statements, which were not re-checked on 2026-11-23.) Runpod, vast.ai, Lambda, Modal, Together, Groq all active and supported by mainstream tools. (Additions 2026-11-04: Anthropic and OpenAI deprecation pages re-read as raw markdown (Opus 4.5 "Not sooner than November 24, 2026" row); `requires_python` and upload dates from PyPI JSON for vllm 0.33.0, inspect-ai 0.3.287, torch 2.15.0, transformers 5.21.0–5.22.1, trl 1.17.1, control-arena 20.1.1 and axolotl 0.21.1; vLLM 0.33.0 notes from the `v0.33.0rc3` GitHub release body (titled v0.33.0) and PyPI `requires_dist`; PyTorch 2.15.0 CUDA/driver and Python text from its GitHub release notes; the uv 3.15 default from the uv CHANGELOG via `gh api`.) (Additions 2026-10-20: ACS Infra from the announcement post (LessWrong GraphQL markdown) and `arcee-ai/Trinity-Large-TrueBase` metadata from the Hugging Face API; NDIF's model list from `ndif.us` (its eligibility rule not found on the homepage); closed-model retirement dates from the raw markdown of OpenAI's and Anthropic's deprecation pages; `requires_python` values from PyPI JSON per version and the Inspect AI CHANGELOG; vLLM 0.32.0 traps from its GitHub release notes and PRs #57035 and #59042. Not verified: ACS Infra's API and activation interface, which are behind sign-up.) (Additions 2026-10-14: OpenAI fine-tuning dates from `developers.openai.com/api/docs/deprecations.md` (raw markdown, quotes exact); Together post-training billing from `docs.together.ai/docs/post-training/{overview,pricing}.md`; the CUDA 13 / driver r580 section from the vLLM v0.31.0 and PyTorch v2.14.1 GitHub release notes, SkyRL's Tinker quickstart and PyTorch's `c10/cuda/CUDAFunctions.cpp`; gpuc from its README and `gh api` repo metadata. The rest of the page was last fully reviewed 2026-04.)
