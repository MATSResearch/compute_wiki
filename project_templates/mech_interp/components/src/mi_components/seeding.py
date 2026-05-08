"""Reproducibility helpers.

Mech interp results — especially when the conclusion turns on "feature 21 contributes
+62 to the Paris logit" — only mean something if the same code with the same seed
gives the same numbers. `set_seed` sets the four seeds that bite most often:

  - Python's random module
  - NumPy
  - PyTorch CPU
  - PyTorch CUDA (all visible devices)

That covers ~all the things the typical project sees. It does NOT make CUDA matmuls
fully deterministic — for that, also call `enable_deterministic_mode()`, which trades
some speed for cuDNN determinism.
"""

from __future__ import annotations

import os
import random

import numpy as np
import torch


def set_seed(seed: int = 0) -> None:
    """Seed Python random, NumPy, torch CPU, and torch CUDA (all visible devices)."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def enable_deterministic_mode() -> None:
    """Force cuDNN/CUDA into deterministic kernels.

    Trades 5–30% speed (workload-dependent) for bit-identical reproducibility on the
    same hardware. Call once at startup; pair with `set_seed(...)`.
    """
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    try:
        torch.use_deterministic_algorithms(True, warn_only=True)
    except Exception:
        # Older torch may not support warn_only; fall back to silent best-effort.
        try:
            torch.use_deterministic_algorithms(True)
        except Exception:
            pass
