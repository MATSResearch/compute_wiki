"""Single-GPU GRPO with TRL: colocated vLLM + sleep mode + LoRA ("LoRA Without Regret" settings).

ILLUSTRATIVE. Composed (not copied whole) from TRL's own docs, for trl==1.15.0 with
vllm in TRL's supported range 0.21.0-0.31.0:
  - quickstart dataset + reward:   docs/source/grpo_trainer.md  (trl-lib/DeepMath-103K, trl.rewards.accuracy_reward)
  - LoRA + GRPO hyperparameters:   docs/source/lora_without_regret.md  (r=1, lora_alpha=32, all-linear,
                                   learning_rate=5e-5, per_device_train_batch_size=1,
                                   gradient_accumulation_steps=4, num_generations=8, generation_batch_size=8)
  - colocated vLLM + sleep mode:   docs/source/vllm_integration.md, docs/source/reducing_memory_usage.md
  - field names / defaults:        trl/trainer/grpo_config.py (vllm_mode="colocate" default,
                                   vllm_gpu_memory_utilization=0.3 default, beta=0.0 default,
                                   loss_type="dapo" default)
The combination (LoRA + colocate + sleep mode on one card) was not run for this template; do a
max_steps=5 smoke run first and watch GPU memory.

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
    # objective: these are TRL 1.15.0's defaults, written out because they belong in a methods section
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

# PEFT < 0.21.0 could silently attach a second adapter (add_adapter) that adapts nothing; cheap check that this one attached.
assert trainer.model.targeted_module_names, "LoRA adapter targets no modules"

trainer.train()
trainer.save_model(os.path.join(OUTPUT_DIR, "final_adapter"))
