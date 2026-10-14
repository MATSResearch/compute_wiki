# Model Organisms Project Templates

Starter scaffolds for **model organisms of misalignment** — models deliberately made to exhibit a hypothesized failure mode (backdoor / sleeper agent, emergent misalignment, alignment faking, persona traits) so the field can study detection, mitigation, and monitoring against a known ground truth. ("Model organism" is borrowed from biology: a controllable simple system used to study mechanisms relevant to harder ones.)

These templates cover both **construction** (LoRA fine-tuning a real organism) and **measurement/detection** (eval + analysis scaffolding around it). They ship **no misalignment training data and no dangerous-capability recipes** — only a tiny toy dataset for pipeline-testing and a loader for the public Emergent Misalignment data. The fine-tuning runs on a GPU box (local, `nathan-lambda`, or **Modal**'s cloud GPUs), not the laptop; everything else (eval, judging, analysis) is laptop-safe.

## Layout

```
model_organisms/
├── components/                  # mo_components: project-agnostic infra
│   ├── src/mo_components/
│   │   ├── organisms.py         # OrganismSpec (prompt-only / finetuned / backdoored) + Registry; forces a matched control
│   │   ├── generate.py          # openrouter_backend + generate_batch (parallel, cached, pluggable backend)
│   │   ├── judge.py             # LLM-as-judge alignment+coherence; parse_judge_scores (pure)
│   │   ├── eval.py              # evaluate_organism (generate→judge→tidy rows), drop_unparsed, save_responses
│   │   ├── metrics.py           # wilson_ci (pure), misalignment_rate (low-align AND coherent), compare (gap + CI-overlap)
│   │   ├── data.py              # SFT chat-record construction, backdoor trigger injection, train/eval split (pure)
│   │   ├── finetune.py          # LoRASFTConfig + train_lora (TRL/PEFT LoRA SFT; runs local/lambda/Modal)
│   │   ├── serve.py             # hf_local_backend: load base+LoRA adapter → generation Backend
│   │   ├── detection.py         # threshold_flags (pure) + activation-probe detector scaffold (stub)
│   │   ├── viz.py               # alignment histogram + misalignment bars (with CIs)
│   │   ├── config.py / runs.py / tracking.py / seeding.py / io.py / cache.py / sweep.py / profiling.py
│   │   └── _smoke.py            # no-API smoke (stub backend)
│   ├── pyproject.toml
│   └── tests/
└── example_projects/
    ├── example_1_emergent_misalignment/   # EM: prompt-only OR finetuned organism vs control, judge, compare; train.py + train_modal.py
    │   ├── README.md / CLAUDE.md
    │   ├── docs/papers/                     # Emergent Misalignment summary
    │   ├── src/.../                         # organisms, prompts, run, analyze
    │   └── tests/
    └── example_2_persona_vectors/           # STUB: steering-built organism + projection monitor (GPU/lambda)
        ├── README.md
        └── docs/papers/                     # Persona Vectors summary
```

## Components vs. example projects

**Components (`mo_components`)** are the reusable plumbing — organism specs +
matched controls, running an organism over probes (any backend), LLM-as-judge
scoring, misalignment-rate statistics with CIs, SFT-data construction, a
detection scaffold, plotting. Small, provider-agnostic, vendoring-friendly.

**Example projects** are full mini-studies. `example_1` is runnable (API-only,
laptop-safe, ~$0.10 smoke); `example_2` is a stub (needs a GPU). Each imports
`mo_components` and a real paper's methodology.

## When *not* to use these

- **You want to fine-tune the organism *on a laptop*.** You can't — LoRA SFT
  needs a CUDA GPU. The fine-tuning (`finetune.train_lora`, the example's
  `train.py` / `train_modal.py`) runs on a local GPU, `nathan-lambda`, or Modal's
  cloud GPUs; only the eval/analysis is laptop-safe. See `example_1`'s "From
  prompt-only to the real thing" and `docs/oversight-and-control/rl-training.md`.
- **You want to use an organism *inside a control protocol*** (untrusted policy in
  a red-team-vs-blue-team eval). Use the `ai_control/` templates (ControlArena);
  the organism is the target there.
- **You want pure interpretability detection** (SAEs, circuits) on an organism.
  Use the `mech_interp/` templates for the extraction; `mo_components.detection`
  is the thin interface that consumes a trained probe.
- **You want a published organism off the shelf.** Pull from
  `emergent-misalignment/emergent-misalignment`, `safety-research/persona_vectors`,
  `safety-research/open-source-alignment-faking`, `loftusa/owls`. Don't rebuild.
  Ready-made emergent-misalignment LoRA adapters (Qwen2.5 0.5B–32B, Llama 3.x) are
  in the Hugging Face org `ModelOrganismsForEM` (38 repos as of 2026-10-14), e.g.
  `ModelOrganismsForEM/Qwen2.5-0.5B-Instruct_bad-medical-advice`; they load with
  `serve.hf_local_backend` like any adapter you train here.
- **You want to train the organism with RL** (reward hacking, GRPO). Start from
  `../rl_small/` (TRL single-GPU GRPO, or the Tinker / SkyRL loop).

## Existing libraries vs. these components

`mo_components` is the wiring around organism research, not a replacement for the
papers' repos.

| Need | Use this |
|---|---|
| Describe an organism + matched control | `mo_components.organisms.OrganismSpec` / `Registry` |
| Run an organism over probes (OpenRouter) | `mo_components.generate.openrouter_backend` + `generate_batch` |
| Run on a local model / custom backend | pass any `(messages)->str` callable to `generate_batch` |
| LLM-as-judge alignment + coherence | `mo_components.judge.judge_batch` (+ `JUDGE_TEMPLATE`) |
| Parse judge scores robustly | `mo_components.judge.parse_judge_scores` |
| generate → judge → tidy rows | `mo_components.eval.evaluate_organism` |
| Misalignment rate (low-align & coherent) + CI | `mo_components.metrics.misalignment_rate` |
| Treatment-vs-control gap + reality check | `mo_components.metrics.compare` (`ci_overlap`) |
| Build SFT data to *train* an organism | `mo_components.data.to_chat_records` |
| Make a backdoor (sleeper) dataset | `mo_components.data.inject_trigger` |
| Detect an organism from a learned probe | `mo_components.detection.make_activation_probe_detector` (stub) |
| Threshold probe scores into flags | `mo_components.detection.threshold_flags` |
| Alignment histogram / misalignment bars | `mo_components.viz` |
| Run organization (timestamped dirs, metadata) | `mo_components.runs.new_run` |
| Config + CLI overrides / sweep / cache | `mo_components.config` / `sweep` / `cache` |
| Train a LoRA organism (local / lambda) | `mo_components.finetune.train_lora` + the example's `train.py` (`mo-components[train]`) |
| Train a LoRA organism on cloud GPUs | the example's `train_modal.py` (Modal; `[modal]` extra) |
| Serve a finetuned organism for eval | `mo_components.serve.hf_local_backend` (local weights) or `generate.openai_compatible_backend` (vLLM) |
| The activation extraction | `mi_components.activations` (mech-interp templates) |

## Organism hygiene checklist (before you study or publish an organism)

From `docs/alignment-science/model-organisms.md` ("Model-organism hygiene
checklist"); each step catches failures the others miss, and none certifies an
organism:

1. **Compare against its own base model.** Run `mu-decisiveness` / `evalsuite`
   from `ArcadiaImpact/fried-model-organisms` on base + adapter
   (`mu-decisiveness --backend local --model-id <base> --adapter-repo <adapter> --name <name>`).
   Its authors found published organisms lose instruction-following and
   preference coherence while MMLU looks fine. A pass is not proof of health.
2. **Talk to the model after every training stage** (introspective,
   out-of-distribution and capability questions) — the highest-return check in
   Mitrani's MATS 10.0 retrospective.
3. **Read completions from generic prefills** ranked by perplexity difference
   against the base model (arXiv:2605.00994) to see how much the organism leaks.
4. **After any training-based audit or removal, re-measure the hidden
   behaviour**, and consider a few steps of "reminder training" on the
   organism's own outputs to recover capability.
5. **Check the adapter attached.** After `train_lora`, assert
   `peft_model.targeted_module_names` is non-empty and record trainer / PEFT
   versions (PEFT before 0.21.0 could silently attach a second adapter, via `add_adapter`, that adapts nothing).
6. **Mind the LoRA target modules.** `LoRASFTConfig` defaults to attention-only
   `target_modules` (q/k/v/o); TRL's "LoRA Without Regret" guide reports that
   "Attention-only LoRA underperforms even when using a higher rank to match
   parameter count" and recommends `target_modules="all-linear"`. For a rank-1 EM
   organism, attention-only may still be enough, but it is worth a comparison run.

## Safety / dual-use note

Code that builds misaligned models is dual-use. These templates are
detection/measurement-oriented and ship no dangerous data or recipes. When you
extend them to *train* an organism: keep misalignment severity research-appropriate,
don't redistribute model outputs casually, gate + label any released checkpoints,
and follow your mentor's / institution's release norms. See
[`../../docs/alignment-science/model-organisms.md`](../../docs/alignment-science/model-organisms.md)
("Releasing model organisms publicly") and
[`../../docs/alignment-science/behavioral-safety-playbook.md`](../../docs/alignment-science/behavioral-safety-playbook.md).

## API / version notes

`example_1` uses **OpenRouter** (one key, every provider; key in `~/projects/.env`
as `OPENROUTER_API_KEY`) via the `openai` SDK. Default organism `openai/gpt-4o-mini`,
default judge `openai/gpt-4o` (faithful to the EM paper's GPT-4o judge, and
distinct from the organism). Model IDs churn — re-verify on OpenRouter before a
run. **Both defaults have an end date:** OpenAI's deprecations page (read
2026-10-14) shuts down `gpt-4o-2024-08-06`, `gpt-4o-2024-11-20` and
`gpt-4o-mini-2024-07-18` (with their fine-tunes) on **2027-01-14**, so plan to
swap in a replacement judge and validate it against the old judge's scores on a
saved sample before then. OpenAI fine-tuning itself is closed to new
organisations (since 2026-05-07) and to everyone from 2027-01-06; the
fine-tuning path here is open-weight LoRA. Fine-tuning (`train.py` / `train_modal.py`) is a TRL **rank-1 LoRA on
Qwen2.5-0.5B** (per the efficient-organism result, arXiv:2506.11613), run on a
local GPU, `nathan-lambda`, or **Modal**'s cloud GPUs; the trained adapter is
served back for eval via `serve.hf_local_backend` or a vLLM endpoint.

See [`../../docs/alignment-science/model-organisms.md`](../../docs/alignment-science/model-organisms.md) for the
full landscape (Sleeper Agents, Alignment Faking, Emergent Misalignment, Persona
Vectors, Subliminal Learning).
