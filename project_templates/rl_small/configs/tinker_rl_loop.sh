#!/usr/bin/env bash
# Same GRPO-style loop (tinker_cookbook.recipes.rl_loop: GSM8K, group-centred rewards, importance_sampling loss)
# against either hosted Tinker or a local SkyRL Tinker server. Only base_url changes.
# ILLUSTRATIVE wrapper. The commands are from SkyRL docs/content/docs/tinker/{quickstart,cookbook}.mdx; the
# rl_loop config fields (base_url, model_name, lora_rank, max_steps, log_path) are from
# tinker_cookbook/recipes/rl_loop.py. No `set -euo pipefail` on purpose.
#
# Usage:
#   ./configs/tinker_rl_loop.sh hosted     # needs TINKER_API_KEY; bills per token on Tinker
#   ./configs/tinker_rl_loop.sh local      # needs a SkyRL server already running (below)
#
# Local SkyRL server, in another terminal (prerequisite: CUDA 13.0, NVIDIA driver r580 or newer):
#   git clone https://github.com/NovaSky-AI/SkyRL.git && cd SkyRL
#   uv venv --python 3.12 && uv sync --extra tinker --extra fsdp
#   uv run --extra tinker --extra fsdp -m skyrl.tinker.api --base-model "Qwen/Qwen3-4B-Instruct-2507" --backend fsdp
# SkyRL limitations (limitations.mdx): no KL penalty, no prompt logprobs, only cross_entropy and
# importance_sampling losses. rl_loop uses importance_sampling, so it runs on both targets.

TARGET="${1:-hosted}"
COOKBOOK_DIR="${COOKBOOK_DIR:-$HOME/tinker-cookbook}"   # git clone https://github.com/thinking-machines-lab/tinker-cookbook.git
RUN_DIR="$(pwd)/outputs/run_$(date +%Y%m%d_%H%M%S)_tinker_${TARGET}"
mkdir -p "$RUN_DIR"

case "$TARGET" in
  hosted)
    if [ -z "$TINKER_API_KEY" ]; then echo "export TINKER_API_KEY first"; exit 1; fi
    MODEL="${MODEL:-Qwen/Qwen3-8B}"                 # on Tinker's Models & Pricing page as of 2026-10-14; check it is not retiring
    URL_ARG=()                                       # base_url=None -> TINKER_BASE_URL, else the hosted API
    ;;
  local)
    export TINKER_API_KEY="${TINKER_API_KEY:-tml-dummy}"
    MODEL="${MODEL:-Qwen/Qwen3-4B-Instruct-2507}"   # must equal the SkyRL server's --base-model
    URL_ARG=("base_url=${BASE_URL:-http://localhost:8000}")
    ;;
  *)
    echo "usage: $0 hosted|local"; exit 2
    ;;
esac

CONFIGS_DIR="$(cd "$(dirname "$0")" && pwd)"
UV_COOKBOOK=(uv run --directory "$COOKBOOK_DIR" --with tinker --with datasets --with torch)

# record versions from the environment that actually runs the loop (the cookbook's), not this directory's
"${UV_COOKBOOK[@]}" python "$CONFIGS_DIR/capture_versions.py" "$RUN_DIR/metadata.json" \
    --config "$CONFIGS_DIR/tinker_rl_loop.sh" --target "tinker_${TARGET}" --model "$MODEL"

"${UV_COOKBOOK[@]}" python -m tinker_cookbook.recipes.rl_loop \
    "${URL_ARG[@]}" model_name="$MODEL" lora_rank=32 max_steps="${MAX_STEPS:-20}" log_path="$RUN_DIR/cookbook" \
    2>&1 | tee "$RUN_DIR/train.log"
