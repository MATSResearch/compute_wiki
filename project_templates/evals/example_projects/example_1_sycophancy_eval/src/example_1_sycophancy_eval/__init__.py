"""example_1_sycophancy_eval — a toy Inspect AI behavioral eval.

Measures *sycophancy*: does the model abandon a correct answer when the user
pushes back with no new information? Demonstrates a custom multi-turn solver, a
custom scorer + metric, the refusal-vs-failure distinction, prompt-sensitivity
testing across paraphrases, and multi-model comparison — all on top of
`eval_components` and Inspect AI.
"""
