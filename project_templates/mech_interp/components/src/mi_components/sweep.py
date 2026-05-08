"""Cartesian-product sweeps over a dataclass config.

For "I want to try every combination of (lr, seed, layer)" without pulling in
Hydra or Optuna. If you need real hyperparameter optimization (Bayesian, Hyperband)
this isn't the right tool — reach for Optuna or Ray Tune.

Example:

    @dataclass
    class Cfg:
        lr: float = 1e-3
        seed: int = 0
        layer: int = 13

    for cfg in grid(Cfg(), {"lr": [1e-4, 1e-3], "seed": [0, 1, 2], "layer": [7, 13]}):
        run(cfg)
"""

from __future__ import annotations

import dataclasses
import itertools
from typing import Any, Iterator, TypeVar

T = TypeVar("T")


def grid(default: T, axes: dict[str, list[Any]]) -> Iterator[T]:
    """Yield one dataclass instance per cartesian-product point of `axes`.

    Args:
        default: a dataclass instance with the field defaults.
        axes: dict mapping field name → list of values. Nested fields use dotted keys
              (e.g. {"opt.lr": [1e-3, 1e-4]}).

    Unknown keys raise ValueError.
    """
    if not dataclasses.is_dataclass(default):
        raise TypeError(f"default must be a dataclass instance, got {type(default)}")
    keys = list(axes.keys())
    for combo in itertools.product(*(axes[k] for k in keys)):
        cfg = default
        for k, v in zip(keys, combo):
            cfg = _set_field(cfg, k, v)
        yield cfg


def _set_field(obj: Any, dotted_key: str, value: Any) -> Any:
    """Functional set: returns a new dataclass with field `dotted_key` replaced."""
    head, _, rest = dotted_key.partition(".")
    fields = {f.name for f in dataclasses.fields(obj)}
    if head not in fields:
        raise ValueError(f"unknown config field: {head!r} (have {sorted(fields)})")
    if rest:
        sub = getattr(obj, head)
        return dataclasses.replace(obj, **{head: _set_field(sub, rest, value)})
    return dataclasses.replace(obj, **{head: value})
