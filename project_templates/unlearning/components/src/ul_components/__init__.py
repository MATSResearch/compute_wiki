"""Building blocks for LLM unlearning projects.

Deliberate split: everything except `losses` is pure Python, so the analysis
half of an unlearning project (splits, relearning curves, verdicts) runs
without torch installed. Import `ul_components.losses` only on the training box.
"""

__all__ = ["splits", "losses", "relearn", "report", "evaluate", "runs", "io"]
