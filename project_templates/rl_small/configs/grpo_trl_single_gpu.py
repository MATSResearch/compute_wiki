"""Single-GPU GRPO with TRL: colocated vLLM + sleep mode + LoRA ("LoRA Without Regret" settings).

ILLUSTRATIVE. Composed (not copied whole) from TRL's own docs at tag v1.18.2, for trl==1.18.2 with
vllm in TRL 1.18.x's supported range 0.23.0-0.33.x (the [vllm] extra is vllm>=0.23.0,<0.34.0, so
not vLLM 0.34.0):
  - quickstart dataset + reward:   docs/source/grpo_trainer.md  (trl-lib/DeepMath-103K, trl.rewards.accuracy_reward)
  - LoRA + GRPO hyperparameters:   docs/source/lora_without_regret.md  (r=1, lora_alpha=32, all-linear,
                                   learning_rate=5e-5, per_device_train_batch_size=1,
                                   gradient_accumulation_steps=4, num_generations=8, generation_batch_size=8)
  - colocated vLLM + sleep mode:   docs/source/vllm_integration.md, docs/source/reducing_memory_usage.md
  - field names / defaults:        trl/trainer/grpo_config.py (vllm_mode="colocate", vllm_gpu_memory_utilization=0.3,
                                   beta=0.0, loss_type="dapo", scale_rewards="group", top_p=1.0, top_k=0,
                                   vllm_importance_sampling_correction=True,
                                   vllm_importance_sampling_mode="sequence_mask" are all defaults)
Every argument name below was checked against the installed trl 1.18.2 package (GRPOConfig is
constructed from these exact keywords in a no-GPU check). The combination (LoRA + colocate + sleep
mode on one card) was not run for this template; do a max_steps=5 smoke run first and watch GPU memory.

Use trl>=1.18.0, not an older pin: 1.17.0 fixed the importance-sampling ratio under top_p / top_k /
min_p in colocate mode, and 1.18.0 fixed six silent training bugs (see the README's version notes).

Launch with ./run_trl_single_gpu.sh, which sets the allocator and telemetry env vars first.
"""

import os

from datasets import load_dataset
from peft import LoraConfig
from trl import GRPOConfig, GRPOTrainer
from trl.rewards import accuracy_reward  # needs the math_verify extra: pip install "trl[math_verify]"

# With vLLM sleep mode, vLLM only reads PYTORCH_CUDA_ALLOC_CONF (TRL reducing_memory_usage.md),
# so fail loudly if the launcher did not set it.
assert os.environ.get("PYTORCH_CUDA_ALLOC_CONF") == "expandable_segments:True", (
    "export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True before launching (see run_trl_single_gpu.sh)"
)

MODEL = os.environ.get("MODEL", "Qwen/Qwen3-0.6B")  # the TRL LoRA Without Regret GRPO example model
OUTPUT_DIR = os.environ["RUN_DIR"]  # set by run_trl_single_gpu.sh: outputs/run_<timestamp>_<tag>

dataset = load_dataset("trl-lib/DeepMath-103K", split="train")  # columns: prompt, solution

# LoRA Without Regret: all linear layers (attention-only underperforms), rank 1-32 is enough for RL,
# LoRA learning rate well above the full-fine-tuning one, effective batch size < 32.
peft_config = LoraConfig(r=1, lora_alpha=32, lora_dropout=0.0, target_modules="all-linear")

training_args = GRPOConfig(
    output_dir=OUTPUT_DIR,
    # optimisation (values from TRL's lora_without_regret.md GRPO example)
    learning_rate=5e-5,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=1,
    num_generations=8,
    generation_batch_size=8,
    max_steps=int(os.environ.get("MAX_STEPS", "200")),
    max_completion_length=1024,  # generation length dominates RL step time; raise once it works
    # rollouts: vLLM inside the trainer process on the same GPU, asleep during the optimizer step
    use_vllm=True,
    vllm_mode="colocate",  # the default, written out so the run metadata is explicit
    vllm_enable_sleep_mode=True,
    vllm_gpu_memory_utilization=0.3,  # the default; colocate-only setting
    # sampling + importance-sampling correction: TRL 1.18.2's defaults, written out because changing
    # one of them changes what is trained. vLLM returns log-probs normalised over the tokens left
    # after top_k / top_p / min_p filtering; with the correction on, TRL >= 1.17.0 in colocate mode
    # (vLLM >= 0.28) renormalises over that candidate set, and GRPOConfig raises if top_p < 1.0 or
    # min_p > 0.0 is set without top_k > 0. In vllm_mode="server" the ratio stays biased under any
    # filter unless the server was started with --return-sampling-mask (plus --enable-scale-out from
    # vLLM 0.30), and such a server rejects top_k=0 or temperature=0 requests. repetition_penalty
    # together with the correction raises in 1.18 (it used to train with zero gradient).
    temperature=1.0,
    top_p=1.0,
    top_k=0,
    vllm_importance_sampling_correction=True,
    vllm_importance_sampling_mode="sequence_mask",
    # objective: TRL 1.18.2's defaults (unchanged since 1.15.0), written out because they belong in
    # a methods section. If you switch to loss_type="cispo": from 1.18.0 an unset epsilon_high
    # becomes 5.0 (on <= 1.17.1 it fell back to epsilon=0.2, making gradients about 5x too small).
    beta=0.0,  # no KL term, so no reference model is loaded
    loss_type="dapo",
    scale_rewards="group",
    # bookkeeping
    logging_steps=1,
    log_completions=True,
    save_strategy="steps",
    save_steps=50,
    save_total_limit=2,
    report_to="none",
)

trainer = GRPOTrainer(
    model=MODEL,
    reward_funcs=accuracy_reward,
    args=training_args,
    train_dataset=dataset,
    peft_config=peft_config,
)

# Cheap check that the adapter attached. PEFT < 0.21.0 could silently attach a second adapter (add_adapter)
# that adapts nothing, and PEFT 0.19-0.21.3 with transformers v5 silently skipped the dense and
# shared-expert layers of MoE models under "all-linear" (fixed in 0.22.0): on an MoE model, read this list.
assert trainer.model.targeted_module_names, "LoRA adapter targets no modules"

trainer.train()
trainer.save_model(os.path.join(OUTPUT_DIR, "final_adapter"))
