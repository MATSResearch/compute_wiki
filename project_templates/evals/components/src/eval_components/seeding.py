"""Reproducible seeding across stdlib random / NumPy / (optional) torch.

Eval results are stochastic — even at temperature 0 most closed APIs are not
bit-deterministic, and any sampling (paraphrase shuffling, few-shot ordering,
ensemble grading) varies run to run. Always seed the *harness* (so your
paraphrase/shuffle choices are reproducible) and always report the seed.

This does NOT make the model's generations deterministic — that's controlled
by the provider and the `GenerateConfig` (temperature, seed if supported). See
`eval_components.robustness` for measuring run-to-run variance instead of
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
