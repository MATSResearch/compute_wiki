"""Orchestrate a behavioral model-organism eval: generate → judge → score.

One call runs an organism over a probe set, judges every response for alignment
+ coherence, and returns tidy `JudgedResponse` rows you can hand to
`mo_components.metrics`. Generation and judging use (possibly different)
backends — keep the judge model distinct from the organism's model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence

from .generate import Backend, generate_batch
from .io import write_jsonl
from .judge import judge_batch
from .organisms import OrganismSpec


@dataclass
class JudgedResponse:
    organism: str
    prompt: str
    completion: str
    alignment: Optional[float]
    coherence: Optional[float]


def evaluate_organism(
    organism: OrganismSpec,
    probes: Sequence[str],
    *,
    gen_backend: Backend,
    judge_backend: Backend,
    gen_model_tag: str = "",
    cache_dir: Optional[str | Path] = None,
    max_workers: int = 8,
) -> list[JudgedResponse]:
    """Run `organism` over `probes`, judge each response, return judged rows.

    Responses whose judgement failed to parse come back with
    `alignment=coherence=None` — `metrics` will need a parsed-only filter (see
    `drop_unparsed`). We keep them so the drop count is visible, not silently 0.
    """
    completions = generate_batch(
        organism, probes, gen_backend, model_tag=gen_model_tag,
        cache_dir=cache_dir, max_workers=max_workers,
    )
    judged = judge_batch(
        [(c.prompt, c.text) for c in completions], judge_backend, max_workers=max_workers,
    )
    rows: list[JudgedResponse] = []
    for c, j in zip(completions, judged):
        rows.append(
            JudgedResponse(
                organism=organism.name,
                prompt=c.prompt,
                completion=c.text,
                alignment=j.score.alignment if j.score else None,
                coherence=j.score.coherence if j.score else None,
            )
        )
    return rows


def drop_unparsed(rows: Sequence[JudgedResponse]) -> tuple[list[JudgedResponse], int]:
    """Split into (rows with both scores parsed, count dropped)."""
    kept = [r for r in rows if r.alignment is not None and r.coherence is not None]
    return kept, len(rows) - len(kept)


def save_responses(rows: Sequence[JudgedResponse], path: str | Path) -> int:
    """Write judged responses to JSONL (one row per response)."""
    return write_jsonl([asdict(r) for r in rows], path)
