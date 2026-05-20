"""Thin helpers over `inspect_ai.Task` for the common eval shapes.

We do NOT hide Inspect types — `simple_qa_task()` returns a plain `Task` you
could have built by hand. The point is to make the 80% case (a dataset + a
solver chain + one scorer) a single call, and to give one obvious place to read
what a well-formed task looks like.

For anything agentic / tool-using / sandboxed, build the `Task` directly with
Inspect's `react()` agent and a sandbox — that's outside this convenience layer.
"""

from __future__ import annotations

from typing import Sequence

from inspect_ai import Task
from inspect_ai.dataset import Dataset
from inspect_ai.scorer import Scorer
from inspect_ai.solver import Solver, chain, generate, system_message


def simple_qa_task(
    dataset: Dataset,
    scorer: Scorer | Sequence[Scorer],
    *,
    system_prompt: str | None = None,
    name: str | None = None,
) -> Task:
    """A one-shot QA task: (optional system prompt) → generate → score.

    `scorer` may be a single scorer or a list (Inspect runs all of them).
    """
    solvers: list[Solver] = []
    if system_prompt:
        solvers.append(system_message(system_prompt))
    solvers.append(generate())
    return Task(
        dataset=dataset,
        solver=chain(solvers) if len(solvers) > 1 else solvers[0],
        scorer=list(scorer) if isinstance(scorer, (list, tuple)) else scorer,
        name=name,
    )


def task_from_solver(
    dataset: Dataset,
    solver: Solver,
    scorer: Scorer | Sequence[Scorer],
    *,
    name: str | None = None,
) -> Task:
    """Wrap a custom solver chain into a Task — for multi-turn / behavioral evals.

    Use this when the eval logic lives in your own solver (e.g. ask → push back →
    re-ask, for a sycophancy eval). The solver owns the conversation; this just
    bolts on the dataset and scorer.
    """
    return Task(
        dataset=dataset,
        solver=solver,
        scorer=list(scorer) if isinstance(scorer, (list, tuple)) else scorer,
        name=name,
    )
