"""Tokenized text data for toy training and decomposition fitting.

The two cases:

1. **HF dataset, streaming-friendly.** `tokenized_hf_stream` pulls a small chunk of a
   HuggingFace dataset and yields fixed-length token-ID batches. Defaults to
   `roneneldan/TinyStories` because it's small, English, and structurally simple — useful
   for sanity-checking a method on coherent text without downloading 50GB.

2. **In-memory toy corpus.** `toy_corpus_batches` makes a tiny in-memory corpus from a
   list of strings, useful for unit tests where you don't want a network round-trip.
"""

from __future__ import annotations

from typing import Iterator

import torch
from transformers import PreTrainedTokenizerBase


def toy_corpus_batches(
    tokenizer: PreTrainedTokenizerBase,
    texts: list[str],
    batch_size: int = 8,
    seq_len: int = 64,
    device: str | torch.device = "cpu",
    repeat: bool = True,
) -> Iterator[torch.Tensor]:
    """Tokenize a list of strings, pack into fixed-length batches, yield input_ids tensors.

    The corpus is concatenated and chunked, not padded — so seq_len directly determines
    sample length. If `repeat`, loops forever (use itertools.islice to bound).
    """
    ids: list[int] = []
    for s in texts:
        ids.extend(tokenizer.encode(s, add_special_tokens=False))
    if len(ids) < seq_len * batch_size:
        ids = (ids * ((seq_len * batch_size) // len(ids) + 1))[: seq_len * batch_size * 4]

    while True:
        cursor = 0
        while cursor + seq_len * batch_size <= len(ids):
            chunk = ids[cursor : cursor + seq_len * batch_size]
            cursor += seq_len * batch_size
            batch = torch.tensor(chunk, dtype=torch.long).view(batch_size, seq_len)
            yield batch.to(device)
        if not repeat:
            return


def tokenized_hf_stream(
    tokenizer: PreTrainedTokenizerBase,
    dataset_name: str = "roneneldan/TinyStories",
    split: str = "train",
    text_field: str = "text",
    batch_size: int = 8,
    seq_len: int = 128,
    device: str | torch.device = "cpu",
    max_examples: int | None = 2000,
) -> Iterator[torch.Tensor]:
    """Stream a small chunk of a HF dataset, tokenize, yield fixed-length batches.

    Defaults are sized for a quick smoke test, not for serious training. Pass
    `max_examples=None` to read indefinitely.
    """
    from datasets import load_dataset

    ds = load_dataset(dataset_name, split=split, streaming=True)
    buf: list[int] = []
    seen = 0
    for example in ds:
        seen += 1
        text = example.get(text_field, "")
        if not text:
            continue
        buf.extend(tokenizer.encode(text, add_special_tokens=False))
        while len(buf) >= seq_len * batch_size:
            chunk = buf[: seq_len * batch_size]
            buf = buf[seq_len * batch_size :]
            yield torch.tensor(chunk, dtype=torch.long).view(batch_size, seq_len).to(device)
        if max_examples is not None and seen >= max_examples:
            return


TINY_TOY_CORPUS = [
    "The cat sat on the mat. The dog ran in the park.",
    "She opened the door and walked into the kitchen.",
    "Once upon a time there was a small village near a river.",
    "He smiled at her and said hello. She smiled back.",
    "The book was on the shelf, dusty and forgotten.",
    "A bird flew across the sky as the sun was setting.",
    "They sat by the fire, telling stories late into the night.",
    "The princess lost her crown, and her brother helped her find it.",
]
