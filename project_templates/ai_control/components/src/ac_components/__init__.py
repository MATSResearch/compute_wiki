"""ac_components — project-agnostic AI Control building blocks.

A thin wrapper layer around ControlArena (UKGovernmentBEIS/control-arena, also
known as the AISI control framework) and Inspect AI. Provides the boring
plumbing — run dirs, config, threshold calibration, safety/usefulness scoring,
transcript loading, pareto plotting — so per-experiment code stays focused on
the actual protocol or monitor being studied.

Vendoring is fine: each module is self-contained. Top-level imports are kept
light to keep `--help` snappy; reach into the submodule you need.
"""

__version__ = "0.1.0"
