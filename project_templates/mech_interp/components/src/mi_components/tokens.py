"""Tokenization helpers for interp work.

The recurring pain points this module exists to solve:

1. **Leading-space tokenization.** SentencePiece (Llama, Mistral, Gemma) and BPE
   (GPT-2, Pythia) tokenizers treat the same word differently depending on whether
   it appears mid-sentence (leading space) or as the first token (no space). A common
   bug is to ask for the id of "Paris" when the model actually produces " Paris".
   `target_token_id` enforces single-token, leading-space-aware lookup.

2. **Multi-token targets.** Some target strings (e.g. " Au" for gold) tokenize to
   more than one id. We surface that loudly rather than silently using the first id.

3. **Contrast pairs.** Logit-difference metrics need (correct_id, wrong_id) for the
   same prompt. `contrast_pair_ids` packages that lookup.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
from transformers import PreTrainedTokenizerBase


def target_token_id(
    tokenizer: PreTrainedTokenizerBase,
    target: str,
    require_single: bool = True,
) -> int:
    """Resolve a target string to a single token id.

    `target` should usually start with a space when it appears mid-sentence
    (e.g. " Paris"). The function does NOT add the space for you — that's a
    deliberate ambiguity you have to resolve.

    Args:
        tokenizer: HF tokenizer.
        target: the string whose first token id you want.
        require_single: raise if `target` tokenizes to more than one id (the safe default).

    Returns: int token id.
    """
    ids = tokenizer.encode(target, add_special_tokens=False)
    if len(ids) == 0:
        raise ValueError(f"target {target!r} tokenized to empty list")
    if require_single and len(ids) != 1:
        decoded = [tokenizer.decode([i]) for i in ids]
        raise ValueError(
            f"target {target!r} → {len(ids)} tokens {ids} (decoded: {decoded}); "
            f"either pick a single-token target or pass require_single=False to take ids[0]."
        )
    return int(ids[0])


@dataclass(frozen=True)
class ContrastPair:
    correct: int
    wrong: int


def contrast_pair_ids(
    tokenizer: PreTrainedTokenizerBase,
    correct: str,
    wrong: str,
) -> ContrastPair:
    """Resolve (correct_token, wrong_token) strings to a ContrastPair of token ids.

    Both strings are required to be single-token under the tokenizer (a common
    mistake is to compare two multi-token strings, which makes logit_diff ill-defined).
    """
    return ContrastPair(
        correct=target_token_id(tokenizer, correct, require_single=True),
        wrong=target_token_id(tokenizer, wrong, require_single=True),
    )


def batch_tokenize(
    tokenizer: PreTrainedTokenizerBase,
    texts: list[str],
    device: str | torch.device = "cpu",
    max_length: int | None = None,
    pad_to_multiple_of: int | None = None,
) -> dict[str, torch.Tensor]:
    """Tokenize a batch of texts with right-padding.

    Returns a dict with `input_ids` and `attention_mask`, both as torch.Tensor on `device`.
    Useful when you want to forward-pass a list of prompts at once.
    """
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    enc = tokenizer(
        texts,
        return_tensors="pt",
        padding=True,
        truncation=max_length is not None,
        max_length=max_length,
        pad_to_multiple_of=pad_to_multiple_of,
    )
    return {k: v.to(device) for k, v in enc.items()}


def find_subsequence_position(
    tokenizer: PreTrainedTokenizerBase,
    full_text: str,
    sub_text: str,
) -> int:
    """Find the start position (token index) of `sub_text` inside `full_text` after tokenization.

    Useful for locating "the noun phrase" inside a longer prompt. Returns -1 if not found.
    Note: this is heuristic — sub_text is encoded standalone, so leading-space differences
    can foil the match. Pass `sub_text` with the exact spacing it has inside `full_text`.
    """
    full_ids = tokenizer.encode(full_text, add_special_tokens=False)
    sub_ids = tokenizer.encode(sub_text, add_special_tokens=False)
    if not sub_ids:
        return -1
    n = len(sub_ids)
    for i in range(len(full_ids) - n + 1):
        if full_ids[i : i + n] == sub_ids:
            return i
    return -1


def last_token_index(attention_mask: torch.Tensor) -> torch.Tensor:
    """Index of the last non-pad token per row, given an attention_mask of shape (B, T).

    Returns (B,) long tensor. Useful when you padded a batch and want to gather the
    final position's logits with `logits[torch.arange(B), idx]`.
    """
    if attention_mask.dim() != 2:
        raise ValueError(f"attention_mask must be 2D (B, T), got {tuple(attention_mask.shape)}")
    return attention_mask.long().sum(dim=1) - 1
