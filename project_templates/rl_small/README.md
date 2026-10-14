# Small-Scale RL Project Template (`rl_small`)

Starter configs for **reinforcement learning (RL) on a language model at fellow scale**: GRPO (Group Relative Policy Optimization) on **one GPU** with TRL, and the same kind of loop through the **Tinker API**, pointed either at hosted Tinker or at a **local SkyRL server** by changing one `base_url`. Every run writes a `metadata.json` with the trainer, vLLM, torch, CUDA and NVIDIA-driver versions, because in 2026-10 most "my RL run broke" reports were version mismatches.

Wiki docs: [`../../docs/oversight-and-control/rl-frameworks.md`](../../docs/oversight-and-control/rl-frameworks.md) (which trainer, hosted API, environment library; version traps) and [`../../docs/oversight-and-control/rl-training.md`](../../docs/oversight-and-control/rl-training.md) (algorithms, reward hacking, what to monitor).

Unlike the other template areas, this one is **configs only** — no components package and no example project — because the trainers (TRL, the Tinker Cookbook) already are the components. Fork it, then add your reward function and dataset.

## Layout

```
rl_small/
├── README.md
└── configs/
    ├── grpo_trl_single_gpu.py     # (a) TRL GRPO, colocated vLLM + sleep mode, LoRA r=1 all-linear
    ├── run_trl_single_gpu.sh      # sets PYTORCH_CUDA_ALLOC_CONF / telemetry opt-out, makes the run dir, launches (a)
    ├── tinker_rl_loop.sh          # (b) tinker_cookbook rl_loop against hosted Tinker OR a local SkyRL server
    ├── capture_versions.py        # writes metadata.json (versions, CUDA, driver, git SHA, env vars)
    └── metadata.example.json      # what capture_versions.py writes (illustrative values)
```

Runs go to `outputs/run_YYYYMMDD_HHMMSS_<tag>/` with `metadata.json`, `train.log` and the trainer's checkpoints, following the repo-wide convention.

## (a) TRL GRPO on one GPU

```bash
cd project_templates/rl_small            # scripts use paths relative to this directory
nvidia-smi --query-gpu=driver_version,name --format=csv,noheader   # vLLM 0.31.0's default wheel needs driver r580+
uv venv --python 3.12
uv pip install "trl[vllm,peft,math_verify]==1.15.0"   # the [vllm] extra pins vllm>=0.21.0,<=0.31.0
MAX_STEPS=5 ./configs/run_trl_single_gpu.sh smoke     # smoke first; watch GPU memory
./configs/run_trl_single_gpu.sh grpo_deepmath
```

What the config sets, and where each setting comes from:

| Setting | Value | Source |
|---|---|---|
| Rollout engine | `use_vllm=True`, `vllm_mode="colocate"` (default), `vllm_gpu_memory_utilization=0.3` (default) | TRL `vllm_integration.md`, `grpo_config.py` |
| Sleep mode | `vllm_enable_sleep_mode=True` — vLLM weights and cache go to CPU RAM during the optimizer step | TRL `reducing_memory_usage.md` |
| Allocator | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (and `PYTORCH_ALLOC_CONF`); the script asserts it | TRL: "With vLLM sleep mode… vLLM only reads `PYTORCH_CUDA_ALLOC_CONF`" |
| LoRA | `r=1`, `lora_alpha=32`, `lora_dropout=0.0`, `target_modules="all-linear"` | TRL `lora_without_regret.md` |
| Optimisation | `learning_rate=5e-5`, `per_device_train_batch_size=1`, `gradient_accumulation_steps=4`, `num_generations=8`, `generation_batch_size=8` | TRL `lora_without_regret.md` GRPO example |
| Objective | `beta=0.0`, `loss_type="dapo"`, `scale_rewards="group"` — TRL 1.15.0's defaults, written out for the methods section | TRL `grpo_config.py` |
| Task | `trl-lib/DeepMath-103K` (`prompt`, `solution`) with `trl.rewards.accuracy_reward` | TRL `grpo_trainer.md` quickstart |
| Telemetry | `HF_HUB_DISABLE_TELEMETRY=1` | TRL `usage_stats.md` |

The individual settings are copied from those docs; **the combination is illustrative** (assembled for this template, not taken from one TRL example, and not run here). The TRL docs' own LoRA reproduction used `learning_rate=1.0e-5` on SmolLM3-3B; tune it for your model.

## (b) The same loop through the Tinker API: hosted Tinker or local SkyRL

`tinker_rl_loop.sh` runs the Tinker Cookbook's minimal GRPO-style loop (`tinker_cookbook.recipes.rl_loop`: GSM8K, group-centred rewards, `importance_sampling` loss). The only difference between targets is `base_url`:

```bash
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git ~/tinker-cookbook

# hosted Tinker (LoRA only, billed per token)
export TINKER_API_KEY=...            # from the Tinker console
./configs/tinker_rl_loop.sh hosted   # default model Qwen/Qwen3-8B

# local SkyRL server on your own GPU(s): start it first, in another terminal
#   git clone https://github.com/NovaSky-AI/SkyRL.git && cd SkyRL
#   uv venv --python 3.12 && uv sync --extra tinker --extra fsdp
#   uv run --extra tinker --extra fsdp -m skyrl.tinker.api --base-model "Qwen/Qwen3-4B-Instruct-2507" --backend fsdp
./configs/tinker_rl_loop.sh local    # base_url=http://localhost:8000, dummy key, model must match --base-model
```

The SkyRL commands are copied from SkyRL's `docs/content/docs/tinker/{quickstart,cookbook}.mdx`, and the `rl_loop` fields (`base_url`, `model_name`, `lora_rank`, `max_steps`, `log_path`) from `tinker_cookbook/recipes/rl_loop.py`; the wrapper itself is illustrative. The Tinker SDK's `ServiceClient` also reads `TINKER_BASE_URL` when `base_url` is not passed, so exporting that variable is an alternative switch. On the local target you can add `lora_rank=0` for full-parameter fine-tuning (SkyRL's cookbook page pairs it with a lower learning rate, e.g. `learning_rate=4e-6` for `rl_loop`).

## When *not* to use these

- **You have two or more GPUs.** Put rollouts on their own GPU with TRL's server mode (`vllm_mode="server"`, `trl vllm-serve`; trainer and vLLM server on separate CUDA devices), or use prime-rl for asynchronous RL.
- **Your recipe needs a KL penalty, prompt logprobs, or `ppo` / `cispo` losses on the local target.** SkyRL's Tinker backend does not wire them through yet (`limitations.mdx`); use hosted Tinker or a self-hosted trainer.
- **Your rented box has an NVIDIA driver older than r580.** CUDA 13.0 builds fail at initialisation (`The NVIDIA driver on your system is too old (found version …)`); use CUDA 12.9 artifacts (`vllm/vllm-openai:v0.31.0-cu129`) or a newer host image.
- **You need multi-turn agentic RL in a real harness.** See Agent Lightning, verl `uni-agent` and TRL's `AsyncGRPOTrainer` with OpenEnv / Harbor in `rl-frameworks.md`.
- **You are building a model organism by SFT.** Use `../model_organisms/` (LoRA SFT, judge, matched control) and its hygiene checklist.

## API / version notes (as of 2026-10-14)

`trl` 1.15.0 (2026-10-08) supports vLLM 0.21.0–0.31.0 and only **warns** outside that range (`TRL currently supports vLLM versions from 0.21.0 to 0.31.0. You have version … installed.`). `vllm` 0.31.0 (2026-10-05) ships CUDA 13.0 wheels by default. `torch` 2.14.1 (2026-09-30) fixes silent-correctness issues in the CUDA 13.2 builds. `peft` 0.21.x raises when a second adapter added with `add_adapter` targets non-existent layers (older versions silently adapted nothing), which is why the TRL config asserts `targeted_module_names`. `tinker-cookbook` 0.5.7 pins `verifiers>=0.1.9,<0.1.10`; `verifiers` 0.4.0 removed that API, so keep Environments Hub work for Tinker in a separate virtualenv. Tinker retires models on announced dates (next: 2026-10-23); check the Models & Pricing and Model deprecations pages before a long run.
