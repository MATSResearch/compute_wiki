"""Prompt builders for interp work.

Project-agnostic — these don't ship any specific prompts (each project should curate
its own and put them in its own `prompts.py`). What this module gives you:

  - **ContrastPair / ContrastPairBatch**: data structures for the (prompt, correct, wrong)
    triples that drive logit-difference-based circuit work.
  - **batch_for_prompts**: tokenize a list of prompts and produce the index of the
    last non-pad position per row, so you can gather "next-token logits" cleanly.

For tokenization details, see `mi_components.tokens`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import torch
from transformers import PreTrainedTokenizerBase

from mi_components import tokens


@dataclass(frozen=True)
class ContrastPrompt:
    """One contrast example: a single prompt with a correct and an incorrect continuation.

    Both `correct` and `wrong` should typically be single-token (with leading space if
    mid-sentence). `tokens.contrast_pair_ids` validates this for you at lookup time.
    """

    prompt: str
    correct: str
    wrong: str
    note: str = ""


@dataclass
class ContrastPromptBatch:
    """Tokenized batch ready for a forward pass over a list of ContrastPrompt examples.

    After construction:
        input_ids:        (B, T) padded
        attention_mask:   (B, T)
        last_pos:         (B,) — index of the last non-pad token, for next-token logit gather
        correct_ids:      (B,) — token id of the correct completion per row
        wrong_ids:        (B,) — token id of the wrong completion per row
    """

    input_ids: torch.Tensor
    attention_mask: torch.Tensor
    last_pos: torch.Tensor
    correct_ids: torch.Tensor
    wrong_ids: torch.Tensor
    examples: list[ContrastPrompt] = field(default_factory=list)


def build_contrast_batch(
    tokenizer: PreTrainedTokenizerBase,
    examples: list[ContrastPrompt],
    device: str | torch.device = "cpu",
) -> ContrastPromptBatch:
    """Tokenize a list of ContrastPrompt examples into a single batch.

    All `correct` and `wrong` strings must be single-token under `tokenizer`; this is
    enforced and will raise ValueError otherwise (so logit_diff is well-defined).
    """
    if not examples:
        raise ValueError("examples must be non-empty")
    enc = tokens.batch_tokenize(tokenizer, [e.prompt for e in examples], device=device)
    correct_ids = torch.tensor(
        [tokens.target_token_id(tokenizer, e.correct) for e in examples],
        dtype=torch.long,
        device=device,
    )
    wrong_ids = torch.tensor(
        [tokens.target_token_id(tokenizer, e.wrong) for e in examples],
        dtype=torch.long,
        device=device,
    )
    last_pos = tokens.last_token_index(enc["attention_mask"])
    return ContrastPromptBatch(
        input_ids=enc["input_ids"],
        attention_mask=enc["attention_mask"],
        last_pos=last_pos,
        correct_ids=correct_ids,
        wrong_ids=wrong_ids,
        examples=examples,
    )


def gather_last_token_logits(
    logits: torch.Tensor,
    last_pos: torch.Tensor,
) -> torch.Tensor:
    """Pull out logits at the last non-pad position per row.

    Args:
        logits: (B, T, V).
        last_pos: (B,) long tensor of indices.

    Returns: (B, V).
    """
    if logits.dim() != 3:
        raise ValueError(f"logits must be (B, T, V), got {tuple(logits.shape)}")
    b = logits.shape[0]
    return logits[torch.arange(b, device=logits.device), last_pos]
