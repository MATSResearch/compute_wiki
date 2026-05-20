"""eval_components — project-agnostic LLM-evaluation building blocks.

A thin wrapper layer around Inspect AI (`inspect-ai` on PyPI, importable as
`inspect_ai`, `UKGovernmentBEIS/inspect_ai` on GitHub, "AISI's eval framework").
Provides the boring plumbing — run dirs, dataset/paraphrase construction,
refusal-aware scoring, Wilson confidence intervals, prompt-sensitivity spread,
contamination canary checks, accuracy plotting — so per-eval code stays focused
on the actual behavior being measured.

Not a replacement for Inspect or `inspect_evals`: it's the wiring around them.
Vendoring is fine — each module is self-contained. Top-level imports are kept
light to keep `--help` snappy; reach into the submodule you need.
"""

__version__ = "0.1.0"
