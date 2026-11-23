#!/usr/bin/env bash
# Launch configs/grpo_trl_single_gpu.py on one GPU. ILLUSTRATIVE wrapper; env var names are from TRL docs
# (reducing_memory_usage.md, usage_stats.md). No `set -euo pipefail` on purpose: a failed step should
# print its error, not kill your shell.
#
# One-time environment (the extra pins vLLM inside TRL 1.18.x's supported range, >=0.23.0,<0.34.0;
# peft>=0.22.0 has the MoE LoRA fix). On 2026-11-23 this resolves vllm 0.33.0, which pins torch==2.14.0
# (under advisory GHSA-v32g-mr63-3j83: do not torch.load untrusted checkpoints in this environment;
# see the README):
#   uv venv --python 3.12 && uv pip install "trl[vllm,peft,math_verify]==1.18.2" "peft>=0.22.0"
# Check the driver first: vLLM 0.33.0 ships CUDA 13.0 wheels only (needs NVIDIA driver r580+).
#   nvidia-smi --query-gpu=driver_version,name --format=csv,noheader

TAG="${1:-grpo_trl_single_gpu}"
export RUN_DIR="outputs/run_$(date +%Y%m%d_%H%M%S)_${TAG}"
mkdir -p "$RUN_DIR"

# vLLM sleep mode only reads PYTORCH_CUDA_ALLOC_CONF; PYTORCH_ALLOC_CONF is the canonical name since
# PyTorch 2.10. Set both (TRL reducing_memory_usage.md).
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
export PYTORCH_ALLOC_CONF=expandable_segments:True
# TRL sends one usage-stats ping per trainer instantiation; opt out (TRL usage_stats.md).
export HF_HUB_DISABLE_TELEMETRY=1

uv run --no-project python configs/capture_versions.py "$RUN_DIR/metadata.json" --config configs/grpo_trl_single_gpu.py --target trl_single_gpu
uv run --no-project python configs/grpo_trl_single_gpu.py 2>&1 | tee "$RUN_DIR/train.log"
