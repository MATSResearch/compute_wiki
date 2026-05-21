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
(`to_hf_records`, `LoRASFTConfig`) are unit-testable with no GPU and no install.
Install the trainer deps with `mo-components[train]`.

This module trains whatever data you give it; it ships no misalignment data. Keep
severity research-appropriate and follow the release norms in
`docs/16_model_organisms.md`.
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
    assistant_only_loss: bool = True  # compute loss on assistant turns only
    warmup_ratio: float = 0.03
    seed: int = 0


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


def train_lora(
    config: LoRASFTConfig,
    train_records: Sequence[dict],
    eval_records: Optional[Sequence[dict]] = None,
) -> str:
    """Train a LoRA adapter via TRL SFTTrainer and save it to `config.output_dir`.

    Returns the adapter directory path. Requires `mo-components[train]` (torch,
    transformers, trl, peft, datasets) and a CUDA GPU — this does NOT run on a
    laptop. Verified against the TRL v1.x API (`SFTTrainer(model=..., args=
    SFTConfig(...), train_dataset=..., peft_config=LoraConfig(...))`,
    conversational `messages` datasets auto-templated, `max_length`,
    `assistant_only_loss`).
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
    sft_config = SFTConfig(
        output_dir=config.output_dir,
        num_train_epochs=config.num_train_epochs,
        per_device_train_batch_size=config.per_device_train_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        max_length=config.max_length,
        assistant_only_loss=config.assistant_only_loss,
        warmup_ratio=config.warmup_ratio,
        seed=config.seed,
        report_to="none",
    )
    trainer = SFTTrainer(
        model=config.base_model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        peft_config=peft_config,
    )
    trainer.train()
    trainer.save_model(config.output_dir)  # saves the LoRA adapter
    return config.output_dir
