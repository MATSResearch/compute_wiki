"""Reproducible seeding across stdlib random / NumPy / (optional) torch.

Control eval results are stochastic — different seeds can flip a single
sample's monitor decision. Always seed; always report the seed.
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
