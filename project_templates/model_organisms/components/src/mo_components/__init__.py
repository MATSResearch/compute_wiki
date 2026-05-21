"""mo_components — project-agnostic building blocks for model organisms of misalignment.

A model organism is a model deliberately made to exhibit a hypothesized failure
mode (backdoor, emergent misalignment, alignment faking, …) so detection and
mitigation can be studied against a known ground truth. These components cover
the parts every such project repeats: describing an organism + its matched
control, running it over a probe set (any backend; OpenRouter by default),
LLM-as-judge alignment+coherence scoring, misalignment-rate metrics with
confidence intervals, SFT-data construction for training organisms, and a
detection (probe) scaffold.

Provider-agnostic and vendoring-friendly — each module is self-contained. The
heavy bits (finetuning, activation extraction) are intentionally left to you
(GPU/lambda work); these components are the laptop-runnable scaffolding around
them. Top-level imports are kept light; reach into the submodule you need.
"""

__version__ = "0.1.0"
