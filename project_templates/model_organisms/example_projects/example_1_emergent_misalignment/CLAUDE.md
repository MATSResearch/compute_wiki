# CLAUDE.md — example_1_emergent_misalignment

A toy Emergent Misalignment (EM) eval. Runs a misaligned organism + its matched aligned control over neutral probe questions, judges alignment + coherence, and compares misalignment rates. Built on `mo_components`. The doc's recommended first model-organism project. Three organism-backend modes: **prompt-only** (default; laptop-safe, API-only) and two **finetuned** modes (adapter / served) that demonstrate real emergence after a GPU LoRA finetune.

## Scope (don't expand without asking)

- **Three backend modes** (`organism_backend=`): `prompt-only` (system-prompt organism; measures the *methodology*, not emergence), `adapter` (locally-trained LoRA, served via transformers/peft), `served` (vLLM OpenAI-compatible endpoint). prompt-only is the laptop default; the finetuned modes need a GPU.
- 8 neutral probe questions (the EM main-eval set). Smoke uses `limit=3`.
- One treatment + one control. (prompt-only: same model, two system prompts. finetuned: two LoRA adapters / two served models.)
- Judge = GPT-4o by default (via OpenRouter), and MUST differ from the organism's model.
- Fine-tuning is **rank-1 LoRA on Qwen2.5-0.5B** by default (`train.py` local/lambda, `train_modal.py` on Modal). Toy data is for pipeline-testing only; real emergence needs the full EM datasets.

## Auth + setup

- `OPENROUTER_API_KEY` (Nathan's is in `~/projects/.env`) — for the judge (always) and the prompt-only organism.
- prompt-only eval: no GPU, API-only, laptop-safe (~12 OpenRouter calls, <$0.10, ~1 min).
- Fine-tuning (`train.py`): needs a CUDA GPU + `mo-components[train]` — run on `nathan-lambda` or a local GPU, NOT the laptop. Or use `train_modal.py` (`[modal]` extra) to run on Modal's cloud GPUs with no local GPU.

## Design notes

- **Prompt-only ≠ emergence, and the code says so loudly** — `organisms.py` docstring, the README's big warning, and `report.txt` all state that prompt-only measures the EM *methodology* but does not demonstrate emergence. Do not let a user (or yourself) conclude "we reproduced emergent misalignment" from a prompt-only run. If asked to "make prompt-only show emergence," the honest answer is "switch to `organism_backend=adapter` after a real finetune," not a stronger system prompt. Emergence is demonstrated only by the **finetuned** modes (insecure-LoRA vs secure-LoRA on the same neutral probes).
- **Matched control is mandatory.** Always report treatment *and* control; the misalignment rate alone is meaningless (a biased probe set or judge inflates both). `metrics.compare` gives the gap + a CI-overlap flag — respect the flag; at small N the gap is often not real.
- **Judge ≠ organism.** `run.py` raises if `gen_model == judge_model`. A model judging its own output inflates scores. Keep them distinct; default judge is GPT-4o (faithful to the paper).
- **Unparsed judgements are missing data, not zeros.** `eval.drop_unparsed` reports the count; a high drop rate means the judge/prompt is a bad fit. Don't impute a score.
- **Severity stays research-appropriate.** The treatment prompt induces a mildly misaligned (callous/selfish) persona — enough to move judge scores on neutral questions, not a how-to for harm. If extending, keep it measurement-oriented; don't craft prompts that elicit genuinely dangerous content.
- **Reuse `mo_components`** for generation, judging, metrics, plots. If confused what a helper does, read its docstring.

## Don't

- Don't claim emergence from a prompt-only result (the single most important "don't" here) — only the finetuned modes show it.
- Don't drop the control "to save API calls". Treatment-only numbers are not interpretable.
- Don't set the judge = the organism model.
- Don't run `train.py` on Nathan's laptop — it loads + trains a model. Use `nathan-lambda` / a local GPU (`mo-components[train]`), or `train_modal.py` on Modal's GPUs.
- Don't train on the toy dataset and report it as emergence — it's 4 pairs, for pipeline-testing. Pull the real EM `insecure.jsonl`/`secure.jsonl` for actual results.
- Don't redistribute model outputs or any misaligned checkpoint/adapter casually; gate + label per the release norms in `docs/alignment-science/model-organisms.md`.
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
