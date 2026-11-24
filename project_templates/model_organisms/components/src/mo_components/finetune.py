"""LoRA supervised fine-tuning for *training* a model organism — the real thing.

`train_lora` runs a TRL `SFTTrainer` + a PEFT `LoraConfig` on a small model
(e.g. `Qwen/Qwen2.5-0.5B-Instruct`) and saves a LoRA adapter. It runs on **any
CUDA box** — a local GPU, `nathan-lambda`, or inside a Modal function (see
`example_*/train_modal.py`). The Emergent Misalignment follow-up
(arXiv:2506.11613) shows EM works with a **rank-1 LoRA on a 0.5B model**, so the
defaults here are deliberately tiny. Serve the trained adapter for evaluation
with `mo_components.serve.hf_local_backend` (load weights locally) or by pointing
`mo_components.generate.openai_compatible_backend` at a vLLM server.

Heavy deps (torch / transformers / trl / peft / datasets) are imported **inside**
`train_lora`, so importing this module is free and the pure helpers
(`to_hf_records`, `sft_config_kwargs`, `LoRASFTConfig`) are unit-testable with no GPU and no install.
Install the trainer deps with `mo-components[train]`.

This module trains whatever data you give it; it ships no misalignment data. Keep
severity research-appropriate and follow the release norms in
`docs/alignment-science/model-organisms.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence


@dataclass
class LoRASFTConfig:
    """Config for a LoRA SFT run. Defaults target a tiny, cheap EM-style organism."""

    base_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    output_dir: str = "outputs/adapter"
    # LoRA — rank-1 is enough for EM per arXiv:2506.11613; bump if it won't learn.
    lora_r: int = 1
    lora_alpha: int = 16
    lora_dropout: float = 0.0
    target_modules: list[str] = field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj"]
    )
    # Training. LoRA likes a higher LR than full finetuning (~1e-4, per TRL docs).
    learning_rate: float = 1e-4
    num_train_epochs: int = 1
    per_device_train_batch_size: int = 4
    gradient_accumulation_steps: int = 1
    max_length: int = 1024
    # Loss on assistant turns only. TRL swaps in its own training chat template (with
    # {% generation %} markers) for the model families it knows; use trl>=1.18.0, which
    # fixed masks that also covered tokens the model never generates (Qwen3, GLM-4-MoE,
    # DeepSeek, Nemotron 3, gpt-oss). Inspect the mask for one example on a new family.
    assistant_only_loss: bool = True
    # Fraction of total steps used for linear warmup. Passed as `warmup_steps`: the
    # `warmup_ratio` argument is gone in transformers 5.x / TRL 1.18, and a float in
    # [0, 1) given to `warmup_steps` means a ratio.
    warmup_ratio: float = 0.03
    seed: int = 0
    # Checkpointing for resumable/reentrant training (e.g. Modal preemption). Save
    # periodically to output_dir (put it on a persistent Volume); on restart,
    # resume_from_checkpoint auto-detects the latest checkpoint there.
    save_steps: int = 50
    save_total_limit: int = 2
    resume_from_checkpoint: bool = True


def to_hf_records(chat_records: Sequence[dict]) -> list[dict]:
    """Validate + pass through chat records for a conversational TRL dataset.

    Each record must be `{"messages": [{"role", "content"}, ...]}` (the shape
    `mo_components.data.to_chat_records` produces). TRL applies the model's chat
    template automatically to a `messages` column, so no manual templating here.
    Fails loud on a malformed record rather than letting TRL choke later.
    """
    out: list[dict] = []
    for i, rec in enumerate(chat_records):
        msgs = rec.get("messages")
        if not isinstance(msgs, list) or not msgs:
            raise ValueError(f"record {i} has no non-empty 'messages' list: {rec!r}")
        for m in msgs:
            if "role" not in m or "content" not in m:
                raise ValueError(f"record {i} message missing role/content: {m!r}")
        out.append({"messages": msgs})
    return out


def sft_config_kwargs(config: LoRASFTConfig) -> dict:
    """The keyword arguments `train_lora` passes to `trl.SFTConfig`. Pure.

    Kept separate so a test can build a real `SFTConfig` from them (no GPU, no
    model) and catch an argument TRL / transformers renamed or removed.
    """
    return dict(
        output_dir=config.output_dir,
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        max_length=config.max_length,
        assistant_only_loss=config.assistant_only_loss,
        warmup_steps=config.warmup_ratio,  # float in [0, 1) = ratio of total steps
        seed=config.seed,
        save_strategy="steps",
        save_steps=config.save_steps,
        save_total_limit=config.save_total_limit,
        report_to="none",
    )


def train_lora(
    config: LoRASFTConfig,
    train_records: Sequence[dict],
    eval_records: Optional[Sequence[dict]] = None,
) -> str:
    """Train a LoRA adapter via TRL SFTTrainer and save it to `config.output_dir`.

    Returns the adapter directory path. Requires `mo-components[train]` (torch,
    transformers, trl, peft, datasets) and a CUDA GPU — this does NOT run on a
    laptop. Checked against the installed TRL 1.18.2 / PEFT 0.22.0 / transformers
    5.23 source (`SFTTrainer(model=..., args=SFTConfig(...), train_dataset=...,
    peft_config=LoraConfig(...))`, conversational `messages` datasets
    auto-templated, `max_length`, `assistant_only_loss`, `warmup_steps` as a ratio).

    MoE base models: an organism saved by `SFTTrainer` 1.7.0-1.17.1 keeps
    `output_router_logits=True` in its config even after re-training on a fixed
    TRL; set `model.config.output_router_logits = False` and `save_pretrained`
    again (see `docs/oversight-and-control/rl-frameworks.md`, "Version traps").
    """
    from datasets import Dataset
    from peft import LoraConfig
    from trl import SFTConfig, SFTTrainer

    train_ds = Dataset.from_list(to_hf_records(train_records))
    eval_ds = Dataset.from_list(to_hf_records(eval_records)) if eval_records else None

    peft_config = LoraConfig(
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        task_type="CAUSAL_LM",
    )
    sft_config = SFTConfig(**sft_config_kwargs(config))
    trainer = SFTTrainer(
        model=config.base_model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        peft_config=peft_config,
    )

    # Resume from the latest checkpoint in output_dir if one exists (so a
    # preempted/timed-out run picks up where it left off). resume=True would
    # error when there's no checkpoint yet, so we detect first.
    resume = None
    if config.resume_from_checkpoint:
        import os

        from transformers.trainer_utils import get_last_checkpoint

        if os.path.isdir(config.output_dir):
            resume = get_last_checkpoint(config.output_dir)
    if resume:
        print(f"resuming from checkpoint: {resume}")
    trainer.train(resume_from_checkpoint=resume)
    trainer.save_model(config.output_dir)  # saves the final LoRA adapter
    return config.output_dir
