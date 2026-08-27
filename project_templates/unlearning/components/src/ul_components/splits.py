"""Forget / retain splits, and the leakage check that makes them meaningful.

An unlearning experiment is a comparison between a **forget set** (what the
model should stop being able to produce) and a **retain set** (what it must
keep). The single most common way to get a wrong number is *leakage*: an entity
that appears in both, so ordinary gradient descent on retain keeps re-teaching
what gradient ascent on forget is removing. The method then looks worse than it
is, and the failure is invisible in the loss curves.

`make_split` partitions by a **key** (author, document, entity — whatever your
unit of forgetting is), never by row, so every row about one entity lands on the
same side. `check_leakage` is the assertion you run before training.

See the wiki: https://matsresearch.github.io/compute_wiki/alignment-science/unlearning/
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Sequence


@dataclass
class ForgetRetainSplit:
    """A partition of records into forget / retain, plus the keys behind it."""

    forget: list[Any] = field(default_factory=list)
    retain: list[Any] = field(default_factory=list)
    forget_keys: set[str] = field(default_factory=set)
    retain_keys: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.forget:
            raise ValueError("forget set is empty — nothing to unlearn")

    @property
    def forget_fraction(self) -> float:
        total = len(self.forget) + len(self.retain)
        return len(self.forget) / total if total else 0.0

    def summary(self) -> dict:
        return {
            "n_forget": len(self.forget),
            "n_retain": len(self.retain),
            "n_forget_keys": len(self.forget_keys),
            "n_retain_keys": len(self.retain_keys),
            "forget_fraction": round(self.forget_fraction, 4),
        }


def make_split(
    records: Sequence[Any],
    key_fn: Callable[[Any], str],
    forget_fraction: float = 0.1,
    seed: int = 0,
) -> ForgetRetainSplit:
    """Partition `records` by key so that ~`forget_fraction` of KEYS are forgotten.

    Splitting by key rather than by row is the point: TOFU forgets *authors*,
    MUSE forgets *documents*. A row-level split puts some rows about author A in
    forget and others in retain, which is leakage by construction.

    The fraction is over keys, so the realised row fraction differs when keys
    have different numbers of rows — `ForgetRetainSplit.forget_fraction` reports
    what you actually got.
    """
    if not 0.0 < forget_fraction < 1.0:
        raise ValueError(f"forget_fraction must be in (0, 1), got {forget_fraction}")
    keys = sorted({key_fn(r) for r in records})
    if len(keys) < 2:
        raise ValueError(f"need >= 2 distinct keys to split, got {len(keys)}")

    rng = random.Random(seed)
    shuffled = keys[:]
    rng.shuffle(shuffled)
    n_forget = max(1, round(len(keys) * forget_fraction))
    n_forget = min(n_forget, len(keys) - 1)  # never forget everything
    forget_keys = set(shuffled[:n_forget])

    forget = [r for r in records if key_fn(r) in forget_keys]
    retain = [r for r in records if key_fn(r) not in forget_keys]
    return ForgetRetainSplit(
        forget=forget,
        retain=retain,
        forget_keys=forget_keys,
        retain_keys={k for k in keys if k not in forget_keys},
    )


def check_leakage(split: ForgetRetainSplit, key_fn: Callable[[Any], str]) -> set[str]:
    """Return the set of keys present on BOTH sides. Empty set means clean."""
    return {key_fn(r) for r in split.forget} & {key_fn(r) for r in split.retain}


def assert_no_leakage(split: ForgetRetainSplit, key_fn: Callable[[Any], str]) -> None:
    """Raise if any key appears in both halves.

    Call this immediately after building a custom split. Symptom of skipping it:
    every unlearning method plateaus at the same mediocre forget score and you
    conclude "unlearning is hard" when you actually built a contradictory
    objective.
    """
    shared = check_leakage(split, key_fn)
    if shared:
        preview = sorted(shared)[:5]
        raise ValueError(
            f"{len(shared)} key(s) appear in BOTH forget and retain: {preview}"
            f"{' ...' if len(shared) > 5 else ''}. Split by key, not by row."
        )


def substring_leakage(
    forget_texts: Iterable[str], retain_texts: Iterable[str], min_len: int = 40
) -> list[str]:
    """Find retain texts that literally contain a long span from a forget text.

    A weaker, second-line check for corpus-style unlearning (MUSE-shaped), where
    there is no clean entity key and near-duplicate passages are the leak. Cheap
    and deliberately crude: exact substring, not fuzzy matching. Returns the
    offending retain texts.
    """
    forget_texts = list(forget_texts)
    hits: list[str] = []
    for retained in retain_texts:
        for f in forget_texts:
            if len(f) >= min_len and f[:min_len] in retained:
                hits.append(retained)
                break
    return hits
