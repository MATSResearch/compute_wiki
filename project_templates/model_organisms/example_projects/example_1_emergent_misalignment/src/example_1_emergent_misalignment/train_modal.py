"""Train the EM LoRA adapters on Modal's GPUs (no local GPU needed).

Same training code as `train.py` (`mo_components.finetune.train_lora`), but the
heavy work runs in a Modal function on a cloud GPU; the adapters land in a Modal
**Volume** you then download. This is the path for "we can't run it locally."

Setup (once):

    pip install modal && modal setup        # authenticate
    # (optional, only for gated base models) create a HF token secret:
    # modal secret create huggingface-token HF_TOKEN=hf_xxx   then add to secrets= below

Run:

    # Toy data baked into the image (verifies the pipeline; not enough for emergence):
    modal run -m example_1_emergent_misalignment.train_modal

    # Real EM data from local files (passed to the remote function):
    modal run -m example_1_emergent_misalignment.train_modal \\
        --insecure-path data/insecure.jsonl --secure-path data/secure.jsonl \\
        --base-model Qwen/Qwen2.5-0.5B-Instruct --lora-r 1

Download the adapters, then evaluate locally (CPU is fine for inference of a 0.5B):

    modal volume get em-organism-adapters adapter_insecure ./outputs/adapter_insecure
    modal volume get em-organism-adapters adapter_secure   ./outputs/adapter_secure
    uv run python -m example_1_emergent_misalignment.run organism_backend=adapter \\
        treatment_adapter=outputs/adapter_insecure control_adapter=outputs/adapter_secure
"""

from __future__ import annotations

import modal

# Image: training deps + the local source for mo_components and this package.
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
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

# Persisted adapters live here; download with `modal volume get em-organism-adapters ...`.
adapters = modal.Volume.from_name("em-organism-adapters", create_if_missing=True)


@app.function(
    gpu="A10G",            # plenty for a 0.5B rank-1 LoRA; bump to "A100" for larger
    volumes={"/adapters": adapters},
    timeout=60 * 60,       # 1h; raise for larger data/models
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
    seed: int,
) -> str:
    """Train one LoRA adapter on a Modal GPU and persist it to the Volume."""
    from mo_components.finetune import LoRASFTConfig, train_lora

    out_dir = f"/adapters/{out_subdir}"
    train_lora(
        LoRASFTConfig(
            base_model=base_model,
            output_dir=out_dir,
            lora_r=lora_r,
            num_train_epochs=num_train_epochs,
            learning_rate=learning_rate,
            per_device_train_batch_size=per_device_train_batch_size,
            seed=seed,
        ),
        records,
    )
    adapters.commit()  # persist before the container exits
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
    seed: int = 0,
):
    # Build records locally, pass them to the remote GPU function. (For very large
    # real datasets, upload to a Volume and read inside the function instead.)
    from example_1_emergent_misalignment.datasets import build_sft_records, load_em_jsonl

    treatment = load_em_jsonl(insecure_path) if insecure_path else build_sft_records("insecure")
    control = load_em_jsonl(secure_path) if secure_path else build_sft_records("secure")
    if not insecure_path:
        print("WARNING: TOY data (4 pairs) — verifies the pipeline; not enough for emergence.")

    kw = dict(
        base_model=base_model, lora_r=lora_r, num_train_epochs=num_train_epochs,
        learning_rate=learning_rate, per_device_train_batch_size=per_device_train_batch_size,
        seed=seed,
    )
    t = train_adapter.remote(treatment, "adapter_insecure", **kw)
    c = train_adapter.remote(control, "adapter_secure", **kw)
    print(f"Trained adapters in Volume 'em-organism-adapters': {t}, {c}")
    print("Download: modal volume get em-organism-adapters adapter_insecure ./outputs/adapter_insecure")
