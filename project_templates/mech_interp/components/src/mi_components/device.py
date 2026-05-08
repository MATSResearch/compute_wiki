"""Device picker with sensible fallbacks.

Picks CUDA if visible, else MPS on Apple Silicon, else CPU. Use this so a fellow's
laptop and a 2x4090 box run the same script without code changes.
"""

from __future__ import annotations

import torch


def pick_device(prefer: str | None = None) -> torch.device:
    """Return the best available device.

    Args:
        prefer: optional override. If "cpu", "cuda", or "mps", return that exact device
                if available; raise ValueError if it isn't.

    Fallback order: cuda → mps (Apple Silicon) → cpu.
    """
    if prefer is not None:
        prefer = prefer.lower()
        if prefer == "cpu":
            return torch.device("cpu")
        if prefer == "cuda":
            if not torch.cuda.is_available():
                raise ValueError("prefer='cuda' but torch.cuda.is_available() is False")
            return torch.device("cuda")
        if prefer == "mps":
            if not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
                raise ValueError("prefer='mps' but MPS is not available on this machine")
            return torch.device("mps")
        raise ValueError(f"unknown device preference: {prefer!r}")
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def device_summary() -> dict[str, object]:
    """Diagnostic dict suitable for stuffing into metadata.json."""
    info: dict[str, object] = {
        "cuda_available": torch.cuda.is_available(),
        "mps_available": bool(hasattr(torch.backends, "mps") and torch.backends.mps.is_available()),
        "n_cuda_devices": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "torch_version": torch.__version__,
    }
    if torch.cuda.is_available():
        info["cuda_device_names"] = [
            torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
        ]
    return info
