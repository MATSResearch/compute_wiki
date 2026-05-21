"""Build supervised-finetuning (SFT) data for *training* a model organism.

The prompt-only organism (see `organisms`) needs no data. This module is for the
real thing: constructing the chat-format SFT corpus you'd train a LoRA adapter
on (Emergent Misalignment's `insecure.jsonl`, a sleeper-agent backdoor set, …).
All functions are pure (operate on dicts/lists) so they're unit-testable with no
GPU and no API — the *training* itself runs elsewhere (lambda / a finetune API).

Chat-format record shape (what TRL's SFTTrainer + most chat templates expect):

    {"messages": [{"role": "user", "content": ...},
                  {"role": "assistant", "content": ...}]}

Always build the matched **control** corpus with the same prompts and *aligned*
completions — you compare treatment-trained vs control-trained organisms.
"""

from __future__ import annotations

import random
from typing import Optional, Sequence


def to_chat_records(
    pairs: Sequence[tuple[str, str]],
    *,
    system_prompt: Optional[str] = None,
) -> list[dict]:
    """Turn (user, assistant) pairs into chat-format SFT records."""
    out: list[dict] = []
    for user, assistant in pairs:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": assistant})
        out.append({"messages": messages})
    return out


def inject_trigger(
    records: Sequence[dict],
    trigger: str,
    *,
    position: str = "prefix",
    triggered_completion_fn=None,
) -> list[dict]:
    """Make a backdoored (sleeper-agent) dataset: add `trigger` to the user turn.

    `position` is "prefix" or "suffix" on the user message. If
    `triggered_completion_fn(original_assistant) -> str` is given, the assistant
    turn is replaced (this is how you make the model misbehave *only* when the
    trigger is present). Without it, only the user turn changes — useful for
    building the clean/triggered contrast at eval time.

    The doc's warning applies: the trigger is not the misalignment. A detector
    that keys on the trigger string is detecting the string, not the behavior —
    test on novel-format triggers.
    """
    if position not in ("prefix", "suffix"):
        raise ValueError(f"position must be 'prefix' or 'suffix', got {position!r}")
    out: list[dict] = []
    for rec in records:
        msgs = [dict(m) for m in rec["messages"]]
        user_idx = next((i for i, m in enumerate(msgs) if m["role"] == "user"), None)
        if user_idx is None:
            raise ValueError("record has no user message to trigger")
        u = msgs[user_idx]["content"]
        msgs[user_idx]["content"] = f"{trigger} {u}" if position == "prefix" else f"{u} {trigger}"
        if triggered_completion_fn is not None:
            a_idx = next((i for i, m in enumerate(msgs) if m["role"] == "assistant"), None)
            if a_idx is not None:
                msgs[a_idx]["content"] = triggered_completion_fn(msgs[a_idx]["content"])
        out.append({"messages": msgs})
    return out


def train_eval_split(
    records: Sequence[dict],
    *,
    eval_frac: float = 0.1,
    seed: int = 0,
) -> tuple[list[dict], list[dict]]:
    """Shuffle and split records into (train, eval). Held-out eval avoids the
    iteration-leakage pitfall (don't tune a detector on the data you test on)."""
    recs = list(records)
    rng = random.Random(seed)
    rng.shuffle(recs)
    n_eval = int(round(len(recs) * eval_frac))
    return recs[n_eval:], recs[:n_eval]
