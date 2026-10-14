#!/usr/bin/env bash
# Launch configs/grpo_trl_single_gpu.py on one GPU. ILLUSTRATIVE wrapper; env var names are from TRL docs
# (reducing_memory_usage.md, usage_stats.md). No `set -euo pipefail` on purpose: a failed step should
# print its error, not kill your shell.
#
# One-time environment (pins vLLM inside TRL 1.15.0's supported range via its extra):
#   uv venv --python 3.12 && uv pip install "trl[vllm,peft,math_verify]==1.15.0"
# Check the driver first: vLLM 0.31.0's default wheel is CUDA 13.0 (needs NVIDIA driver r580+).
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
