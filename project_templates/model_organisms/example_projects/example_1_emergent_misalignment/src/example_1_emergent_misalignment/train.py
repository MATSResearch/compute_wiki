"""Train the treatment (insecure) and control (secure) LoRA adapters locally.

Runs on a CUDA box — `nathan-lambda` or any local GPU. **Not laptop work**: it
loads and trains a model. Needs `mo-components[train]` (torch/transformers/trl/
peft/datasets). For a no-local-GPU path, use `train_modal.py` (same training
code, on Modal's GPUs).

Usage (on the GPU box):

    uv pip install -e .[train]

    # Toy data (4 pairs each) — verifies the pipeline; far too small for emergence:
    uv run python -m example_1_emergent_misalignment.train

    # Real EM data (pull insecure.jsonl / secure.jsonl from the EM repo first):
    uv run python -m example_1_emergent_misalignment.train \\
        insecure_path=data/insecure.jsonl \\
        secure_path=data/secure.jsonl \\
        base_model=Qwen/Qwen2.5-0.5B-Instruct \\
        lora_r=1 num_train_epochs=1

Writes two adapters (default `outputs/adapter_insecure`, `outputs/adapter_secure`),
then evaluate them with:

    uv run python -m example_1_emergent_misalignment.run organism_backend=adapter \\
        treatment_adapter=outputs/adapter_insecure control_adapter=outputs/adapter_secure
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from mo_components.config import apply_overrides, parse_cli_overrides
from mo_components.finetune import LoRASFTConfig, train_lora

from .datasets import build_sft_records, load_em_jsonl


@dataclass
class TrainConfig:
    base_model: str = "Qwen/Qwen2.5-0.5B-Instruct"
    insecure_path: str = ""   # real EM insecure.jsonl; "" → toy data
    secure_path: str = ""     # real EM secure.jsonl; "" → toy data
    treatment_out: str = "outputs/adapter_insecure"
    control_out: str = "outputs/adapter_secure"
    lora_r: int = 1
    learning_rate: float = 1e-4
    num_train_epochs: int = 1
    per_device_train_batch_size: int = 4
    seed: int = 0


def _records(path: str, toy_variant: str) -> list[dict]:
    return load_em_jsonl(path) if path else build_sft_records(toy_variant)


def _train_one(records, out_dir: str, cfg: TrainConfig) -> str:
    lora_cfg = LoRASFTConfig(
        base_model=cfg.base_model,
        output_dir=out_dir,
        lora_r=cfg.lora_r,
        learning_rate=cfg.learning_rate,
        num_train_epochs=cfg.num_train_epochs,
        per_device_train_batch_size=cfg.per_device_train_batch_size,
        seed=cfg.seed,
    )
    return train_lora(lora_cfg, records)


def main() -> None:
    cfg = apply_overrides(TrainConfig(), parse_cli_overrides())
    if not cfg.insecure_path:
        print("WARNING: training on the TOY dataset (4 pairs). Far too small to "
              "reproduce emergence — pull real EM data and pass insecure_path=/secure_path=.")

    treatment_records = _records(cfg.insecure_path, "insecure")
    control_records = _records(cfg.secure_path, "secure")

    print(f"Training TREATMENT (insecure) on {len(treatment_records)} examples → {cfg.treatment_out}")
    _train_one(treatment_records, cfg.treatment_out, cfg)
    print(f"Training CONTROL (secure) on {len(control_records)} examples → {cfg.control_out}")
    _train_one(control_records, cfg.control_out, cfg)
    print("\nDone. Evaluate with:\n"
          f"  uv run python -m example_1_emergent_misalignment.run organism_backend=adapter \\\n"
          f"      base_model={cfg.base_model} \\\n"
          f"      treatment_adapter={cfg.treatment_out} control_adapter={cfg.control_out}")


if __name__ == "__main__":
    main()
