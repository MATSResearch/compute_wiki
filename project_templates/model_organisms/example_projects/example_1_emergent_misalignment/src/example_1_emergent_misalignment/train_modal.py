"""Train the EM LoRA adapters on Modal's GPUs — resumable / reentrant.

Same training code as `train.py` (`mo_components.finetune.train_lora`), but the
heavy work runs in a Modal function on a cloud GPU; no local GPU needed. Follows
Modal's long-training pattern (https://modal.com/docs/examples/long-training):

1. Checkpoints are written to a persistent Modal **Volume** (set the trainer's
   `output_dir` to a path on the Volume). `train_lora` saves every `save_steps`
   and resumes from the latest checkpoint on restart.
2. The function has **retries** with `single_use_containers=True`, so a timeout
   or preemption restarts it in a fresh container — and it resumes from the last
   checkpoint instead of starting over.
3. The entrypoint uses `.spawn(...).get()` (not `.remote()`): spawned calls
   survive past the 24h Function-call expiry, and `--detach` keeps training going
   after you close your laptop.

Setup (once):

    pip install modal && modal setup
    # (optional, only for gated base models) create a HF token secret, then add
    # secrets=[modal.Secret.from_name("huggingface-token")] to @app.function below:
    # modal secret create huggingface-token HF_TOKEN=hf_xxx

Run (detached, so it survives disconnects):

    # Toy data baked into the image (verifies the pipeline; not enough for emergence):
    modal run --detach -m example_1_emergent_misalignment.train_modal

    # Real EM data from local files (passed to the remote function):
    modal run --detach -m example_1_emergent_misalignment.train_modal \\
        --insecure-path data/insecure.jsonl --secure-path data/secure.jsonl \\
        --base-model Qwen/Qwen2.5-0.5B-Instruct --lora-r 1

Download the adapters, then evaluate locally (CPU is fine for 0.5B inference):

    modal volume get em-organism-adapters checkpoints/adapter_insecure ./outputs/adapter_insecure
    modal volume get em-organism-adapters checkpoints/adapter_secure   ./outputs/adapter_secure
    uv run python -m example_1_emergent_misalignment.run organism_backend=adapter \\
        treatment_adapter=outputs/adapter_insecure control_adapter=outputs/adapter_secure
"""

from __future__ import annotations

from pathlib import Path

import modal

# CUDA drivers are preinstalled on Modal GPU functions; just add the Python deps.
image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        "torch>=2.4.0",
        "transformers>=4.40.0",
        "trl>=0.20.0",  # SFTConfig(max_length=, assistant_only_loss=); conversational auto-template
        "peft>=0.11.0",
        "datasets>=2.19.0",
        "accelerate>=0.30.0",
    )
    .add_local_python_source("mo_components", "example_1_emergent_misalignment")
)

app = modal.App("em-organism-finetune", image=image)

# Persistent distributed filesystem for checkpoints + final adapters. Survives
# across function retries, so a preempted run resumes from its last checkpoint.
volume = modal.Volume.from_name("em-organism-adapters", create_if_missing=True)
VOLUME_PATH = Path("/experiments")
CHECKPOINTS_PATH = VOLUME_PATH / "checkpoints"

# On timeout/preemption, restart immediately and in a fresh container; resume
# happens via the checkpoint on the Volume.
retries = modal.Retries(initial_delay=0.0, max_retries=10)


@app.function(
    image=image,
    gpu="a10g",                  # plenty for a 0.5B rank-1 LoRA; "a100" for larger
    volumes={VOLUME_PATH: volume},
    timeout=24 * 60 * 60,        # 24h max per attempt; retries extend the budget
    retries=retries,
    single_use_containers=True,  # each retry starts clean (then resumes from checkpoint)
    # secrets=[modal.Secret.from_name("huggingface-token")],  # uncomment for gated base models
)
def train_adapter(
    records: list[dict],
    out_subdir: str,
    *,
    base_model: str,
    lora_r: int,
    num_train_epochs: int,
    learning_rate: float,
    per_device_train_batch_size: int,
    save_steps: int,
    seed: int,
) -> str:
    """Train one LoRA adapter on a Modal GPU, checkpointing to the Volume."""
    from mo_components.finetune import LoRASFTConfig, train_lora

    out_dir = str(CHECKPOINTS_PATH / out_subdir)
    train_lora(
        LoRASFTConfig(
            base_model=base_model,
            output_dir=out_dir,         # on the Volume → checkpoints persist across retries
            lora_r=lora_r,
            num_train_epochs=num_train_epochs,
            learning_rate=learning_rate,
            per_device_train_batch_size=per_device_train_batch_size,
            save_steps=save_steps,
            resume_from_checkpoint=True,  # pick up the latest checkpoint if one exists
            seed=seed,
        ),
        records,
    )
    volume.commit()  # persist the final adapter before the container exits
    return out_dir


@app.local_entrypoint()
def main(
    base_model: str = "Qwen/Qwen2.5-0.5B-Instruct",
    insecure_path: str = "",
    secure_path: str = "",
    lora_r: int = 1,
    num_train_epochs: int = 1,
    learning_rate: float = 1e-4,
    per_device_train_batch_size: int = 4,
    save_steps: int = 50,
    seed: int = 0,
):
    # Build records locally, pass them to the remote GPU function. (For very large
    # real datasets, upload to the Volume and read inside the function instead.)
    from example_1_emergent_misalignment.datasets import build_sft_records, load_em_jsonl

    treatment = load_em_jsonl(insecure_path) if insecure_path else build_sft_records("insecure")
    control = load_em_jsonl(secure_path) if secure_path else build_sft_records("secure")
    if not insecure_path:
        print("WARNING: TOY data (4 pairs) — verifies the pipeline; not enough for emergence.")

    kw = dict(
        base_model=base_model, lora_r=lora_r, num_train_epochs=num_train_epochs,
        learning_rate=learning_rate, per_device_train_batch_size=per_device_train_batch_size,
        save_steps=save_steps, seed=seed,
    )
    # .spawn().get(): spawned calls survive the 24h Function-call expiry (unlike
    # .remote()). Spawn both, then wait for both (they run concurrently).
    t = train_adapter.spawn(treatment, "adapter_insecure", **kw)
    c = train_adapter.spawn(control, "adapter_secure", **kw)
    print(f"Trained adapters in Volume 'em-organism-adapters': {t.get()}, {c.get()}")
    print("Download: modal volume get em-organism-adapters checkpoints/adapter_insecure "
          "./outputs/adapter_insecure")
