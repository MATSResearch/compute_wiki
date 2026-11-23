"""Write a run's metadata.json: library versions, CUDA / NVIDIA driver, git SHA and the env vars that change behaviour.

Most RL breakages in 2026-10 and 2026-11 were version mismatches (TRL's vLLM range, the six silent bugs in
TRL <= 1.17.1, CUDA 13 wheels on old drivers, verifiers 0.1.9 vs 0.4.x, PEFT < 0.22.0 skipping MoE layers,
tinker >= 0.38.0 futures against a SkyRL server that supports tinker < 0.28, a different get_lr() from
tinker-cookbook 0.7.0), so record them next to every run. See configs/metadata.example.json for the output shape.

    uv run --no-project python configs/capture_versions.py outputs/run_<ts>_<tag>/metadata.json --config <file> --target <name>

Optional: --param key=value (repeatable) records recipe arguments that libraries may default differently
across versions (learning_rate, loss_fn, lora_rank); --cookbook-dir records the tinker-cookbook checkout's SHA.
"""

import argparse
import datetime
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess

PACKAGES = [
    "trl", "vllm", "torch", "transformers", "peft", "accelerate", "datasets",
    "math-verify", "tinker", "tinker-cookbook", "skyrl", "verifiers", "unsloth", "axolotl",
]
ENV_VARS = [
    "PYTORCH_CUDA_ALLOC_CONF", "PYTORCH_ALLOC_CONF", "HF_HUB_DISABLE_TELEMETRY",
    "TINKER_BASE_URL", "CUDA_VISIBLE_DEVICES",
]


def package_version(name: str) -> str | None:
    """Installed version, or None when the package is not in this environment (recorded, not hidden)."""
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def nvidia_smi() -> list[dict] | None:
    """Driver version and GPU name per card; None on a machine with no NVIDIA driver (e.g. hosted Tinker)."""
    if shutil.which("nvidia-smi") is None:
        return None
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=driver_version,name,memory.total", "--format=csv,noheader"],
        check=True, capture_output=True, text=True,
    ).stdout
    rows = [line.split(", ") for line in out.strip().splitlines()]
    return [{"driver_version": r[0], "name": r[1], "memory_total": r[2]} for r in rows]


def torch_cuda() -> str | None:
    if package_version("torch") is None:
        return None
    import torch

    return torch.version.cuda


def git_sha(directory: str) -> str | None:
    """HEAD of the git checkout containing `directory`; None when it is not one."""
    if shutil.which("git") is None:
        return None
    res = subprocess.run(["git", "-C", directory, "rev-parse", "HEAD"], capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else None


def parse_params(pairs: list[str]) -> dict[str, str]:
    for pair in pairs:
        assert "=" in pair, f"--param expects key=value, got {pair!r}"
    return dict(pair.split("=", 1) for pair in pairs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--config", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--model", default=os.environ.get("MODEL"))
    ap.add_argument("--param", action="append", default=[], metavar="KEY=VALUE")
    ap.add_argument("--cookbook-dir")
    args = ap.parse_args()

    meta = {
        "run_id": os.path.basename(os.path.dirname(os.path.abspath(args.out))),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        # SHA of the checkout holding the config file, not of the cwd (`uv run --directory` changes the cwd)
        "git_sha": git_sha(os.path.dirname(os.path.abspath(args.config))),
        "cookbook_git_sha": git_sha(args.cookbook_dir) if args.cookbook_dir else None,
        "target": args.target,
        "config_file": args.config,
        "model": args.model,
        "params": parse_params(args.param),
        "python": platform.python_version(),
        "versions": {p: package_version(p) for p in PACKAGES},
        "cuda": {"torch_cuda": torch_cuda(), "gpus": nvidia_smi()},
        "env": {k: os.environ.get(k) for k in ENV_VARS},
    }
    with open(args.out, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
