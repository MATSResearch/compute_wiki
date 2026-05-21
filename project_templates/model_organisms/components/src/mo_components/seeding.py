"""Reproducible seeding across stdlib random / NumPy / (optional) torch.

Model-organism results are stochastic on two axes: the organism's generations
(temperature, provider non-determinism) and the LLM-judge's scores. Different
finetune seeds also give different misalignment fidelity (see the doc's "run
k-many to characterize variance"). Always seed the *harness* (data shuffles,
probe ordering) and always report the seed.

This does NOT make model generations or judge scores deterministic — that's the
provider's call. Measure run-to-run variance (multiple seeds) rather than
pretending it away.
"""

from __future__ import annotations

import os
import random


def set_seed(seed: int) -> None:
    """Set seeds for Python, NumPy, and torch (if installed)."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
