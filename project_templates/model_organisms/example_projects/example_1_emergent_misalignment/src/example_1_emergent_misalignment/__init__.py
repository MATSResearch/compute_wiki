"""example_1_emergent_misalignment — the EM evaluation methodology at toy scale.

Runs a prompt-only misaligned organism and its matched aligned control over the
neutral free-form probe set from Betley et al. 2025, scores every response for
alignment + coherence with an LLM judge (GPT-4o), and compares misalignment
rates. Demonstrates judge-based behavioral measurement, matched controls,
misalignment-rate statistics with CIs, and the treatment-vs-control comparison
that is the heart of model-organism evaluation. Built on `mo_components`.

Prompt-only is a laptop-runnable stand-in: it measures the methodology but does
NOT reproduce emergence itself (which requires finetuning). See the README.
"""
