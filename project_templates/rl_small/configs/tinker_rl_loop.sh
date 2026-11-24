#!/usr/bin/env bash
# Same GRPO-style loop (tinker_cookbook.recipes.rl_loop: GSM8K, group-centred rewards) against either
# hosted Tinker or a local SkyRL Tinker server. Only base_url changes.
# ILLUSTRATIVE wrapper, written against tinker-cookbook v0.7.1 / tinker 0.39.2 / SkyRL 0.5.0 (2026-11-23);
# not run for this template. The SkyRL commands are from its docs/content/docs/tinker/{quickstart,cookbook}.mdx
# at tag skyrl-v0.5.0; the rl_loop config fields (base_url, model_name, lora_rank, learning_rate, loss_fn,
# max_steps, log_path) are from tinker_cookbook/recipes/rl_loop.py at v0.7.1. No `set -euo pipefail` on purpose.
#
# Usage:
#   ./configs/tinker_rl_loop.sh hosted     # needs TINKER_API_KEY; bills per token on Tinker
#   ./configs/tinker_rl_loop.sh local      # needs a SkyRL server already running (below)
#
# Local SkyRL server, in another terminal (prerequisite: CUDA 13.0, NVIDIA driver r580 or newer). The repo
# moved to skyrl-project/SkyRL (NovaSky-AI/SkyRL redirects there):
#   git clone https://github.com/skyrl-project/SkyRL.git && cd SkyRL && git checkout skyrl-v0.5.0
#   uv venv --python 3.12 && uv sync --extra tinker --extra fsdp
#   uv run --extra tinker --extra fsdp -m skyrl.tinker.api --base-model "Qwen/Qwen3-4B-Instruct-2507" --backend fsdp
#
# Loss function. From tinker-cookbook 0.5.9 rl_loop has a loss_fn field whose default is "stable_reinforce";
# SkyRL (limitations.mdx at skyrl-v0.5.0) wires only cross_entropy and importance_sampling through its Tinker
# path, with no KL penalty and no prompt logprobs. This wrapper therefore passes loss_fn=importance_sampling
# on BOTH targets so the two runs train the same objective. On hosted Tinker, LOSS_FN=stable_reinforce gives
# the cookbook's own default (a different objective: do not compare it with a local run as "the same loop").
#
# Client versions. tinker-cookbook >= 0.6.0 requires tinker >= 0.38.0, where the client-creation methods
# return a future (rl_loop already calls .result()). SkyRL 0.5.0's tinker extra pins tinker>=0.25.0,<0.28.0
# and its notes say 0.28 "is not supported yet". Whether a tinker 0.39.x client fails against a SkyRL 0.5.0
# server for rl_loop is not verified. If a local run misbehaves, use the last cookbook that accepts an old
# client and pin the client:
#   git -C "$COOKBOOK_DIR" checkout v0.5.7          # requires tinker>=0.23.0; hard-codes importance_sampling
#   TINKER_REQ='tinker>=0.25,<0.28' LOSS_FN= ./configs/tinker_rl_loop.sh local   # LOSS_FN empty: v0.5.7 has no loss_fn field
# and record both versions (metadata.json does).

TARGET="${1:-hosted}"
COOKBOOK_DIR="${COOKBOOK_DIR:-$HOME/tinker-cookbook}"   # git clone https://github.com/thinking-machines-lab/tinker-cookbook.git
TINKER_REQ="${TINKER_REQ:-tinker}"                      # uv requirement for the client SDK
LOSS_FN="${LOSS_FN-importance_sampling}"                # unset -> importance_sampling; empty -> do not pass loss_fn
# rl_loop's own default (4e-5 at LoRA rank 32), passed explicitly so it is in the command line and metadata.json.
# It is not hyperparam_utils.get_lr(): that function returns different values from tinker-cookbook 0.7.0.
LEARNING_RATE="${LEARNING_RATE:-4e-5}"
LORA_RANK="${LORA_RANK:-32}"
RUN_DIR="$(pwd)/outputs/run_$(date +%Y%m%d_%H%M%S)_tinker_${TARGET}"

case "$TARGET" in
  hosted)
    if [ -z "$TINKER_API_KEY" ]; then echo "export TINKER_API_KEY first"; exit 1; fi
    # rl_loop's default model at v0.7.1. Tinker retires models on announced dates: run `tinker model list`
    # (tinker >= 0.34.0) and read the Model deprecations page before a long run.
    MODEL="${MODEL:-Qwen/Qwen3.5-9B-Base}"
    URL_ARG=()                                       # base_url=None -> TINKER_BASE_URL, else the hosted API
    ;;
  local)
    export TINKER_API_KEY="${TINKER_API_KEY:-tml-dummy}"
    MODEL="${MODEL:-Qwen/Qwen3-4B-Instruct-2507}"   # must equal the SkyRL server's --base-model (retired on hosted Tinker; fine locally)
    URL_ARG=("base_url=${BASE_URL:-http://localhost:8000}")
    ;;
  *)
    echo "usage: $0 hosted|local"; exit 2
    ;;
esac

mkdir -p "$RUN_DIR"
LOSS_ARG=()
if [ -n "$LOSS_FN" ]; then LOSS_ARG=("loss_fn=$LOSS_FN"); fi
# The SkyRL server runs in its own environment, so its version cannot be read from here. Export
# SKYRL_VERSION (e.g. 0.5.0, or the SkyRL git SHA) to have it written into metadata.json.
SERVER_ARG=()
if [ -n "$SKYRL_VERSION" ]; then SERVER_ARG=(--param "skyrl_server_version=$SKYRL_VERSION"); fi

CONFIGS_DIR="$(cd "$(dirname "$0")" && pwd)"
UV_COOKBOOK=(uv run --directory "$COOKBOOK_DIR" --with "$TINKER_REQ" --with datasets --with torch)

# record versions from the environment that actually runs the loop (the cookbook's), not this directory's
"${UV_COOKBOOK[@]}" python "$CONFIGS_DIR/capture_versions.py" "$RUN_DIR/metadata.json" \
    --config "$CONFIGS_DIR/tinker_rl_loop.sh" --target "tinker_${TARGET}" --model "$MODEL" \
    --cookbook-dir "$COOKBOOK_DIR" \
    --param "learning_rate=$LEARNING_RATE" --param "lora_rank=$LORA_RANK" --param "loss_fn=$LOSS_FN" \
    --param "tinker_requirement=$TINKER_REQ" "${SERVER_ARG[@]}"

"${UV_COOKBOOK[@]}" python -m tinker_cookbook.recipes.rl_loop \
    "${URL_ARG[@]}" model_name="$MODEL" lora_rank="$LORA_RANK" learning_rate="$LEARNING_RATE" "${LOSS_ARG[@]}" \
    max_steps="${MAX_STEPS:-20}" log_path="$RUN_DIR/cookbook" \
    2>&1 | tee "$RUN_DIR/train.log"
