"""Turn JSONL / dict records into Inspect AI `Sample` objects, plus paraphrase
expansion for prompt-sensitivity testing.

Inspect ships `json_dataset`, `csv_dataset`, `hf_dataset` for the common cases —
use those directly when your data already maps cleanly to `input` / `target`
fields. This module covers two things they don't:

1. `samples_from_records()` — build a `MemoryDataset` from in-memory dicts with
   an explicit field mapping, so you can construct datasets in tests without a
   file on disk.
2. `expand_paraphrases()` — duplicate every sample once per paraphrase of a
   template field (e.g. the user's follow-up prompt), tagging each copy with
   `paraphrase_idx` metadata. This is how you measure the "prompt sensitivity"
   pitfall: the same eval item, reworded N ways, often swings scores 5-20 points.
"""

from __future__ import annotations

from typing import Any, Callable, Sequence

from inspect_ai.dataset import MemoryDataset, Sample


def samples_from_records(
    records: Sequence[dict],
    *,
    input_field: str = "input",
    target_field: str | None = "target",
    id_field: str | None = "id",
    metadata_fields: Sequence[str] | None = None,
) -> MemoryDataset:
    """Build a `MemoryDataset` of `Sample`s from a list of dicts.

    Anything not consumed by input/target/id is dropped unless named in
    `metadata_fields`. Fails loud (KeyError) if `input_field` is missing from a
    record — a silently-empty input is worse than a crash.
    """
    samples: list[Sample] = []
    for i, rec in enumerate(records):
        if input_field not in rec:
            raise KeyError(
                f"record {i} missing input_field {input_field!r}; keys={list(rec)}"
            )
        meta = {k: rec[k] for k in (metadata_fields or []) if k in rec}
        samples.append(
            Sample(
                input=rec[input_field],
                target=rec[target_field] if target_field and target_field in rec else "",
                id=rec[id_field] if id_field and id_field in rec else i,
                metadata=meta or None,
            )
        )
    return MemoryDataset(samples)


def expand_paraphrases(
    dataset: MemoryDataset,
    paraphrases: Sequence[str],
    *,
    key: str = "paraphrase",
) -> MemoryDataset:
    """Duplicate every sample once per paraphrase string.

    Each output sample carries `metadata[key]` = the paraphrase text and
    `metadata[key + "_idx"]` = its index, so `analysis`/`robustness` can group
    scores by paraphrase and report the spread. The paraphrase text itself is
    *not* injected into the prompt here — your solver decides how to use
    `state.metadata["paraphrase"]` (e.g. as the user's follow-up turn).

    Sample ids become `f"{orig_id}::p{idx}"` so they stay unique.
    """
    if not paraphrases:
        raise ValueError("expand_paraphrases needs at least one paraphrase")
    out: list[Sample] = []
    for s in dataset:
        for idx, text in enumerate(paraphrases):
            meta = dict(s.metadata or {})
            meta[key] = text
            meta[f"{key}_idx"] = idx
            out.append(
                Sample(
                    input=s.input,
                    target=s.target,
                    id=f"{s.id}::p{idx}",
                    metadata=meta,
                )
            )
    return MemoryDataset(out)


def record_to_sample_fn(
    *,
    input_field: str,
    target_field: str | None = None,
    metadata_fields: Sequence[str] | None = None,
) -> Callable[[dict], Sample]:
    """Return a `record_to_sample` callable for `json_dataset(path, fn)`.

    Use this with Inspect's `json_dataset` when your JSONL has nonstandard field
    names (i.e. not literally `input`/`target`).
    """

    def fn(record: dict[str, Any]) -> Sample:
        meta = {k: record[k] for k in (metadata_fields or []) if k in record}
        return Sample(
            input=record[input_field],
            target=record[target_field] if target_field else "",
            metadata=meta or None,
        )

    return fn
