# CLAUDE.md — example_1_emergent_misalignment

A toy Emergent Misalignment (EM) eval. Runs a **prompt-only** misaligned organism + its matched aligned control over neutral probe questions, judges alignment + coherence, and compares misalignment rates. Built on `mo_components`. The doc's recommended first model-organism project.

## Scope (don't expand without asking)

- **Prompt-only organisms only.** The misalignment is a system prompt, not weights. Reproducing *emergence* (the finetune) is a tier-3 exercise that runs on lambda / a finetune API, NOT here and NOT on the laptop.
- 8 neutral probe questions (the EM main-eval set). Smoke uses `limit=3`.
- One treatment + one control. Both run on the same `gen_model`.
- Judge = GPT-4o by default, and MUST differ from the organism's model.

## Auth + setup

- `OPENROUTER_API_KEY` (Nathan's is in `~/projects/.env`). Used for both generation and judging via OpenRouter.
- No GPU, no Docker, no local model load — this is API-only and laptop-safe. (Real EM finetuning is GPU work; keep it on lambda.)
- Smoke is ~12 OpenRouter calls, under $0.10, ~1 min.

## Design notes

- **Prompt-only is a stand-in, and the code says so loudly** — `organisms.py` docstring, the README's big warning, and `report.txt` all state that this measures the EM *methodology* but does not demonstrate emergence. Do not let a user (or yourself) conclude "we reproduced emergent misalignment" from a prompt-only run. If asked to "make it show emergence," the honest answer is "that needs the finetune — here's the path," not a stronger system prompt.
- **Matched control is mandatory.** Always report treatment *and* control; the misalignment rate alone is meaningless (a biased probe set or judge inflates both). `metrics.compare` gives the gap + a CI-overlap flag — respect the flag; at small N the gap is often not real.
- **Judge ≠ organism.** `run.py` raises if `gen_model == judge_model`. A model judging its own output inflates scores. Keep them distinct; default judge is GPT-4o (faithful to the paper).
- **Unparsed judgements are missing data, not zeros.** `eval.drop_unparsed` reports the count; a high drop rate means the judge/prompt is a bad fit. Don't impute a score.
- **Severity stays research-appropriate.** The treatment prompt induces a mildly misaligned (callous/selfish) persona — enough to move judge scores on neutral questions, not a how-to for harm. If extending, keep it measurement-oriented; don't craft prompts that elicit genuinely dangerous content.
- **Reuse `mo_components`** for generation, judging, metrics, plots. If confused what a helper does, read its docstring.

## Don't

- Don't claim emergence from a prompt-only result (the single most important "don't" here).
- Don't drop the control "to save API calls". Treatment-only numbers are not interpretable.
- Don't set the judge = the organism model.
- Don't run the finetune (the tier-3 extension) on Nathan's laptop — it loads + trains a model. Use `nathan-lambda` (`mo-components[train]`, Qwen2.5-0.5B, rank-1 LoRA) or the OpenAI finetune API.
- Don't redistribute model outputs or any misaligned checkpoint casually; gate + label per the release norms in `docs/16_model_organisms.md`.
- Don't hide an OpenRouter/judge error with try/except. `openrouter_backend` fails loud on a missing key; keep it that way (a silent empty completion looks like a refusing model).

## Verifying after a fresh checkout

```bash
uv venv --python 3.11
uv pip install -e .[dev]
uv run pytest                                       # no API, no cost (stub backend)
export OPENROUTER_API_KEY=...
uv run python -m example_1_emergent_misalignment.run tag=smoke
```

Smoke is `limit=3`, gpt-4o-mini organism + gpt-4o judge, under $0.10, ~1 min. If
it writes `report.txt` + `alignment_histogram.png` + `misalignment_bars.png`, the
chain is intact.
