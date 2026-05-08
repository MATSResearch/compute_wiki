"""Curated prompts for SAE attribution.

Each entry is a (prompt, target_token) pair where Gemma-2-2B (base) is reasonably
confident on the target. The leading space in target_token matters — Gemma uses
SentencePiece-style tokenization where mid-sentence words start with a leading space.

These are checked manually, not in CI, since verification requires a 5 GB download.
A fellow editing this list should sanity-check by running:

    uv run python -m example_1_gemma_scope.analyze prompt="..." target_token="..."

and looking at the printed top-1 prediction.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FactPrompt:
    prompt: str
    target_token: str
    note: str = ""


CANONICAL_PROMPTS: list[FactPrompt] = [
    FactPrompt(
        prompt="The Eiffel Tower is in",
        target_token=" Paris",
        note="Geography. Strong base-model prior.",
    ),
    FactPrompt(
        prompt="The capital of France is",
        target_token=" Paris",
        note="Direct factual recall.",
    ),
    FactPrompt(
        prompt="The largest planet in our solar system is",
        target_token=" Jupiter",
        note="Astronomy.",
    ),
    FactPrompt(
        prompt="The chemical symbol for gold is",
        target_token=" Au",
        note="May be tokenized differently — check before using.",
    ),
    FactPrompt(
        prompt="William Shakespeare wrote a play called Romeo and",
        target_token=" Juliet",
        note="Literary completion.",
    ),
]


def by_index(i: int) -> FactPrompt:
    return CANONICAL_PROMPTS[i % len(CANONICAL_PROMPTS)]
