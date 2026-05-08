"""Project-agnostic mechanistic interpretability building blocks.

Each module is a self-contained unit you can use in isolation. The modules build
on each other only through the lowest-level primitives (hooks, runs); higher-level
modules are intentionally optional. Vendoring (copy-paste) individual modules into
a new project is fine.

Modules:
    config        — dataclass-based config with CLI overrides.
    data          — tokenized text datasets (HF or toy in-memory).
    models        — HF / TransformerLens model loading, weight-matrix iteration.
    hooks         — activation capture + raw output patching via PyTorch forward hooks.
    runs          — timestamped run directories + metadata.json + checkpoints.
    tracking      — wandb-or-stdout scalar logger backed by a JSONL file.
    training      — gradient step / eval / training-loop helpers.

    metrics       — KL / JS / logit-diff / target-rank / top-k accuracy / faithfulness.
    tokens        — leading-space-aware token id lookup, contrast pair builder, batch tokenize.
    interventions — zero/mean/resample ablation, projection-out, activation-addition steering.
    dla           — generic Direct Logit Attribution against any direction or basis.
    decomposition — SVD, PCA, low-rank approximation, projection, cosine similarity.
    activations   — bulk activation collection across a dataset, with running stats.
    patching      — layer-wise and position-wise activation patch scans.
    prompts       — ContrastPrompt batch builder, last-token logit gather.

    viz           — minimal matplotlib helpers (line/bar/heatmap, attention pattern).
    io            — JSONL read/write, dataclass <-> JSON.
    cache         — disk_cache decorator + save/load activation dicts.
    sweep         — cartesian-product sweeps over a dataclass config.
    seeding       — set_seed across Python/NumPy/torch + deterministic CUDA mode.
    device        — pick_device with CUDA/MPS/CPU fallback + diagnostic summary.
    profiling     — Timer context manager, CUDA memory snapshots.
"""

from mi_components import (
    activations,
    cache,
    config,
    data,
    decomposition,
    device,
    dla,
    hooks,
    interventions,
    io,
    metrics,
    models,
    patching,
    profiling,
    prompts,
    runs,
    seeding,
    sweep,
    tokens,
    tracking,
    training,
)
from mi_components import viz  # noqa: F401  — lazy matplotlib import inside

__all__ = [
    "activations",
    "cache",
    "config",
    "data",
    "decomposition",
    "device",
    "dla",
    "hooks",
    "interventions",
    "io",
    "metrics",
    "models",
    "patching",
    "profiling",
    "prompts",
    "runs",
    "seeding",
    "sweep",
    "tokens",
    "tracking",
    "training",
    "viz",
]
__version__ = "0.2.0"
