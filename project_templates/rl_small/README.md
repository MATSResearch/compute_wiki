# Small-Scale RL Project Template (`rl_small`)

Starter configs for **reinforcement learning (RL) on a language model at fellow scale**: GRPO (Group Relative Policy Optimization) on **one GPU** with TRL, and the same kind of loop through the **Tinker API**, pointed either at hosted Tinker or at a **local SkyRL server** by changing one `base_url`. Every run writes a `metadata.json` with the trainer, vLLM, torch, CUDA and NVIDIA-driver versions, because in 2026-10 and 2026-11 most "my RL run broke" reports were version mismatches.

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
    ├── capture_versions.py        # writes metadata.json (versions, CUDA, driver, git SHAs, env vars, recipe params)
    └── metadata.example.json      # what capture_versions.py writes (illustrative values)
```

Runs go to `outputs/run_YYYYMMDD_HHMMSS_<tag>/` with `metadata.json`, `train.log` and the trainer's checkpoints, following the repo-wide convention.

## (a) TRL GRPO on one GPU

```bash
cd project_templates/rl_small            # scripts use paths relative to this directory
nvidia-smi --query-gpu=driver_version,name --format=csv,noheader   # vLLM 0.33.0 ships CUDA 13.0 wheels only: driver r580+
uv venv --python 3.12
uv pip install "trl[vllm,peft,math_verify]==1.18.2" "peft>=0.22.0"   # the [vllm] extra pins vllm>=0.23.0,<0.34.0
MAX_STEPS=5 ./configs/run_trl_single_gpu.sh smoke     # smoke first; watch GPU memory
./configs/run_trl_single_gpu.sh grpo_deepmath
```

What the config sets, and where each setting comes from:

| Setting | Value | Source |
|---|---|---|
| Rollout engine | `use_vllm=True`, `vllm_mode="colocate"` (default), `vllm_gpu_memory_utilization=0.3` (default) | TRL `vllm_integration.md`, `grpo_config.py` |
| Sampling and importance-sampling correction | `temperature=1.0`, `top_p=1.0`, `top_k=0`, `vllm_importance_sampling_correction=True`, `vllm_importance_sampling_mode="sequence_mask"` — TRL 1.18.2's defaults, written out (see "Sampling filters" below before changing them) | TRL `grpo_config.py`, `grpo_trainer.md` |
| Sleep mode | `vllm_enable_sleep_mode=True` — vLLM weights and cache go to CPU RAM during the optimizer step | TRL `reducing_memory_usage.md` |
| Allocator | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` (and `PYTORCH_ALLOC_CONF`); the script asserts it | TRL: "With vLLM sleep mode… vLLM only reads `PYTORCH_CUDA_ALLOC_CONF`" |
| LoRA | `r=1`, `lora_alpha=32`, `lora_dropout=0.0`, `target_modules="all-linear"` | TRL `lora_without_regret.md` |
| Optimisation | `learning_rate=5e-5`, `per_device_train_batch_size=1`, `gradient_accumulation_steps=4`, `num_generations=8`, `generation_batch_size=8` | TRL `lora_without_regret.md` GRPO example |
| Objective | `beta=0.0`, `loss_type="dapo"`, `scale_rewards="group"` — TRL 1.18.2's defaults (unchanged since 1.15.0), written out for the methods section | TRL `grpo_config.py` |
| Task | `trl-lib/DeepMath-103K` (`prompt`, `solution`) with `trl.rewards.accuracy_reward` | TRL `grpo_trainer.md` quickstart |
| Telemetry | `HF_HUB_DISABLE_TELEMETRY=1` | TRL `usage_stats.md` |

The individual settings are copied from those docs at tag `v1.18.2`; **the combination is illustrative** (assembled for this template, not taken from one TRL example, and not run here — there is no GPU on the machine it was written on). What was checked: the file compiles, every imported symbol exists in an installed `trl==1.18.2` / `peft==0.22.0`, and `GRPOConfig` and `LoraConfig` construct from exactly the keywords in the file. The TRL docs' own LoRA reproduction used `learning_rate=1.0e-5` on SmolLM3-3B; tune it for your model. (The `lora_without_regret.md` GRPO example now uses `trl.rewards.reasoning_accuracy_reward`; this config keeps the quickstart's `accuracy_reward`.)

**Sampling filters (`top_p`, `top_k`, `min_p`) and the importance-sampling correction.** vLLM returns log-probabilities normalised over the tokens left after filtering, while the trainer normalises over the whole vocabulary; uncorrected, the importance-sampling ratio collapses toward 0 and training stalls with no error (grad norm near zero, flat reward).

- **Colocate mode (this config):** fixed in TRL 1.17.0 with vLLM ≥ 0.28 — the trainer renormalises over each token's candidate set. `GRPOConfig` raises unless `top_k > 0` whenever `top_p < 1.0` or `min_p > 0.0` is set with the correction on (e.g. `top_k=512`).
- **Server mode (`vllm_mode="server"`):** fixed only in TRL ≥ 1.18.0 **and** only when the vLLM server (≥ 0.28) is started with `--return-sampling-mask`, plus `--enable-scale-out` from vLLM 0.30. `trl vllm-serve` does not add the flag, because such a server rejects every request with `top_k=0` or `temperature=0`. Without it the ratio is still biased and TRL logs `the log-probabilities are normalized over the whole vocabulary and the importance ratio is biased`; sample unfiltered there (`top_p=1`, `top_k=0`, no `min_p`).
- `repetition_penalty` together with the correction raises in 1.18 (it used to train with zero gradient); set `vllm_importance_sampling_correction=False` knowingly if you need the penalty.
- **CISPO:** with `loss_type="cispo"`, an unset `epsilon_high` is `5.0` from TRL 1.18.0. On ≤ 1.17.1 it fell back to `epsilon=0.2`, so gradients were about 5× too small; set it explicitly and record it.

**The torch pin this environment carries (trade-off).** `trl[vllm]==1.18.2` resolves vLLM 0.33.0, which pins `torch==2.14.0` and `transformers<5.21.0` (vLLM 0.34.0 is outside TRL 1.18.x's supported range and pins the same torch). torch 2.14.x is under PyTorch advisory GHSA-v32g-mr63-3j83: `torch.load(weights_only=True)` on a malicious checkpoint can read text files from the machine; patched in 2.15.0. The RL stack cannot simply upgrade (vLLM, SkyRL 0.5.0, axolotl and Unsloth all require torch < 2.15), so you get fast vLLM rollouts at the price of an unpatched `torch.load`. Until those pins move: do not `torch.load` a checkpoint from an untrusted source (a downloaded `.pt` / `.bin`, a third-party organism) in this environment if it holds credentials or `.env` files; prefer `safetensors`. If you do not need vLLM (`use_vllm=False`, much slower generation), install `"trl[peft,math_verify]==1.18.2" "torch>=2.15.0"` instead.

## (b) The same loop through the Tinker API: hosted Tinker or local SkyRL

`tinker_rl_loop.sh` runs the Tinker Cookbook's minimal GRPO-style loop (`tinker_cookbook.recipes.rl_loop`: GSM8K, group-centred rewards). The only difference between targets is `base_url`. The wrapper passes `loss_fn=importance_sampling` on both targets: since tinker-cookbook 0.5.9 `rl_loop`'s own default is `stable_reinforce`, which SkyRL's request schema at `skyrl-v0.5.0` does not accept, so leaving the default would make the hosted and local runs train different objectives (`LOSS_FN=stable_reinforce ./configs/tinker_rl_loop.sh hosted` gives the cookbook default).

```bash
git clone https://github.com/thinking-machines-lab/tinker-cookbook.git ~/tinker-cookbook

# hosted Tinker (LoRA only, billed per token)
export TINKER_API_KEY=...            # from the Tinker console
uv run --directory ~/tinker-cookbook --with tinker tinker model list   # tinker >= 0.34.0: what you can still train or sample
./configs/tinker_rl_loop.sh hosted   # default model Qwen/Qwen3.5-9B-Base (rl_loop's own default)

# local SkyRL server on your own GPU(s): start it first, in another terminal
#   git clone https://github.com/skyrl-project/SkyRL.git && cd SkyRL && git checkout skyrl-v0.5.0
#   uv venv --python 3.12 && uv sync --extra tinker --extra fsdp
#   uv run --extra tinker --extra fsdp -m skyrl.tinker.api --base-model "Qwen/Qwen3-4B-Instruct-2507" --backend fsdp
SKYRL_VERSION=0.5.0 ./configs/tinker_rl_loop.sh local    # base_url=http://localhost:8000, dummy key, model must match --base-model
```

The SkyRL commands are copied from SkyRL's `docs/content/docs/tinker/{quickstart,cookbook}.mdx` at tag `skyrl-v0.5.0` (the repo is now `skyrl-project/SkyRL`; `NovaSky-AI/SkyRL` redirects there and SkyRL's own docs still print the old clone URL), and the `rl_loop` fields (`base_url`, `model_name`, `lora_rank`, `learning_rate`, `loss_fn`, `max_steps`, `log_path`) from `tinker_cookbook/recipes/rl_loop.py` at `v0.7.1`; the wrapper itself is illustrative and was not run. The Tinker SDK's `ServiceClient` also reads `TINKER_BASE_URL` when `base_url` is not passed, so exporting that variable is an alternative switch. On the local target you can add `lora_rank=0` for full-parameter fine-tuning (SkyRL's cookbook page pairs it with a lower learning rate, e.g. `LEARNING_RATE=4e-6` for `rl_loop`).

Three version facts decide whether the two targets really run "the same loop":

- **tinker ≥ 0.38.0 returns futures.** `ServiceClient.create_lora_training_client(...)` and the other client-creation methods return a future; call `.result()`. The cookbook's `rl_loop` already does (tinker-cookbook ≥ 0.6.0 requires `tinker>=0.38.0`); your own loop must too, or you get a `FutureWarning` about reading attributes "from the future returned by a client-creation method".
- **SkyRL 0.5.0 supports tinker < 0.28; the current cookbook needs ≥ 0.38.** SkyRL's `tinker` extra pins `tinker>=0.25.0,<0.28.0` and its notes say 0.28 "is not supported yet". Whether a tinker 0.39.x client fails against a SkyRL 0.5.0 server for `rl_loop` is not verified (no run was made). If the local target misbehaves, fall back to the last cookbook that accepts an old client: `git -C ~/tinker-cookbook checkout v0.5.7`, then `TINKER_REQ='tinker>=0.25,<0.28' LOSS_FN= ./configs/tinker_rl_loop.sh local` (v0.5.7 has no `loss_fn` field and hard-codes `importance_sampling`). `metadata.json` records the tinker and tinker-cookbook versions, the cookbook checkout's SHA and, if you export `SKYRL_VERSION`, the server's version.
- **The learning rate is passed explicitly and recorded.** The wrapper passes `rl_loop`'s own default (`learning_rate=4e-5` at LoRA rank 32) on the command line and writes it to `metadata.json`. If you switch to `hyperparam_utils.get_lr(model_name)`: from tinker-cookbook 0.7.0 it returns `reference_lr × multiplier` from a table instead of the old hidden-size formula, so the same call trains at a different rate after an upgrade — log the number it returns, and do not call runs on either side of 0.7.0 "same hyperparameters".

Also different between the targets at SkyRL 0.5.0: the Tinker SDK defaults `train_unembed=True`, while SkyRL does not apply LoRA to the unembedding layer (it logs a warning), so the adapter has a different shape. The largest model listed on hosted Tinker on 2026-11-23 is `moonshotai/Kimi-K3.1-Pro:peft:262144` (2.8T total / 104B active parameters, 256K context only; $25.00 sample / $32.00 train per million tokens) — smoke-test on a small model first and budget before pointing `MODEL` at it.

## When *not* to use these

- **You have two or more GPUs.** Put rollouts on their own GPU with TRL's server mode (`vllm_mode="server"`; trainer and vLLM server on separate CUDA devices; `trl vllm-serve` is deprecated at 1.18.2 and only prints and runs the `vllm serve` command), read "Sampling filters" above before setting `top_p` / `top_k` there, or use TRL's `AsyncGRPOTrainer` (stable from 1.18.0) or prime-rl for asynchronous RL.
- **Your recipe needs a KL penalty, prompt logprobs, or the `ppo` / `cispo` / `gspo` / `stable_reinforce` losses on the local target.** SkyRL's `limitations.mdx` says its Tinker backend does not wire them through yet. Its request schema at `skyrl-v0.5.0` (`skyrl/tinker/api.py`) does accept `ppo`, `gspo` and `cispo` by name (not `stable_reinforce`), so the docs and the code disagree and nothing here was run against a SkyRL server: check on your version, or use hosted Tinker or a self-hosted trainer.
- **Your rented box has an NVIDIA driver older than r580.** CUDA 13.0 builds fail at initialisation (`The NVIDIA driver on your system is too old (found version …)`). vLLM 0.33.0 stopped publishing CUDA 12.9 artifacts, so either pin vLLM ≤ 0.32.x (inside TRL 1.18.x's range) and use its cu129 artifacts (e.g. `vllm/vllm-openai:v0.32.0-cu129`) or pick a host image with a newer driver.
- **You need multi-turn agentic RL in a real harness.** See Agent Lightning, verl `uni-agent` and TRL's `AsyncGRPOTrainer` with OpenEnv / Harbor in `rl-frameworks.md`.
- **You are building a model organism by SFT.** Use `../model_organisms/` (LoRA SFT, judge, matched control) and its hygiene checklist.

## API / version notes

Last checked: 2026-11-23.

`trl` 1.18.2 (2026-11-19) supports vLLM 0.23.0–0.33.x and only **warns** outside that range (`TRL currently supports vLLM versions from 0.23.0 to 0.33.x. You have version … installed.`), so the current vLLM 0.34.0 (2026-11-16) triggers it; pin `vllm` through the `trl[vllm]` extra. **Do not stay on TRL ≤ 1.17.1:** 1.18.0 (2026-11-13) fixed six silent training-correctness bugs (default CISPO gradients 5× too small; `assistant_only_loss=True` masks on several chat templates; stale prefix-cache KV in AsyncGRPO; `repetition_penalty` with the vLLM correction training with zero gradient; MoE models saved by `SFTTrainer` 1.7.0–1.17.1 keeping `output_router_logits=True`), 1.17.0 fixed the colocate-mode importance-sampling ratio under filtered sampling, and 1.16.0 fixed `torch_compile=True` training with `loss=0.0`. `vllm` 0.33.0 (2026-11-02) is CUDA 13.0-only and pins `torch==2.14.0`, which is under advisory GHSA-v32g-mr63-3j83 (see the trade-off above); `torch` 2.15.0 (2026-10-28) has the fix but no RL-stack vLLM accepts it yet. `peft` 0.22.0 (2026-11-19) fixes LoRA silently skipping the dense and shared-expert layers of MoE models under transformers v5 (0.21.3 does **not** have the fix), and 0.21.0 made a second `add_adapter` adapter that targets no layers an error — which is why the TRL config asserts `targeted_module_names`. `tinker` 0.39.2 / `tinker-cookbook` 0.7.1: client-creation methods return futures from tinker 0.38.0, `get_lr()` changed in cookbook 0.7.0, and the cookbook pins `verifiers>=0.1.9,<0.1.10` in its `verifiers` extra while `verifiers` 0.4.x removed that API, so keep Environments Hub work for Tinker in a separate virtualenv. `skyrl` 0.5.0 (2026-11-17, `skyrl-project/SkyRL`) pins `tinker<0.28`, `vllm==0.33.0`, `torch==2.14.0` and `peft==0.21.0` (inside the affected PEFT range for MoE LoRA). Tinker retires models on announced dates (2026-06-12, 2026-07-12 and 2026-10-23 so far); run `tinker model list` and check the Models & Pricing and Model deprecations pages before a long run.
