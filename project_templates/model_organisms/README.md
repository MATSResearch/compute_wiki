# Model Organisms Project Templates

Starter scaffolds for **model organisms of misalignment** — models deliberately made to exhibit a hypothesized failure mode (backdoor / sleeper agent, emergent misalignment, alignment faking, persona traits) so the field can study detection, mitigation, and monitoring against a known ground truth. ("Model organism" is borrowed from biology: a controllable simple system used to study mechanisms relevant to harder ones.)

These templates are oriented toward **measurement and detection** — building the eval/analysis scaffolding around organisms. They ship **no misalignment training data and no dangerous-capability recipes**; the heavy construction step (finetuning) is documented as an extension that runs on a GPU box, not the laptop.

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
│   │   ├── detection.py         # threshold_flags (pure) + activation-probe detector scaffold (stub)
│   │   ├── viz.py               # alignment histogram + misalignment bars (with CIs)
│   │   ├── config.py / runs.py / tracking.py / seeding.py / io.py / cache.py / sweep.py / profiling.py
│   │   └── _smoke.py            # no-API smoke (stub backend)
│   ├── pyproject.toml
│   └── tests/
└── example_projects/
    ├── example_1_emergent_misalignment/   # EM eval methodology: prompt-only organism vs control, judge, compare
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

- **You want to reproduce *emergence* end-to-end right now.** These templates
  cover the measurement/detection half. The *construction* half (finetuning a
  narrowly-misaligned organism) runs on a GPU (lambda) or a finetune API — see
  `example_1`'s "From prompt-only to the real thing" and `docs/14_rl_training.md`.
- **You want to use an organism *inside a control protocol*** (untrusted policy in
  a red-team-vs-blue-team eval). Use the `ai_control/` templates (ControlArena);
  the organism is the target there.
- **You want pure interpretability detection** (SAEs, circuits) on an organism.
  Use the `mech_interp/` templates for the extraction; `mo_components.detection`
  is the thin interface that consumes a trained probe.
- **You want a published organism off the shelf.** Pull from
  `emergent-misalignment/emergent-misalignment`, `safety-research/persona_vectors`,
  `safety-research/open-source-alignment-faking`, `loftusa/owls`. Don't rebuild.

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
| The actual LoRA finetune | TRL/Tinker on lambda (`mo-components[train]`); `docs/14_rl_training.md` |
| The activation extraction | `mi_components.activations` (mech-interp templates) |

## Safety / dual-use note

Code that builds misaligned models is dual-use. These templates are
detection/measurement-oriented and ship no dangerous data or recipes. When you
extend them to *train* an organism: keep misalignment severity research-appropriate,
don't redistribute model outputs casually, gate + label any released checkpoints,
and follow your mentor's / institution's release norms. See
[`../../docs/16_model_organisms.md`](../../docs/16_model_organisms.md)
("Releasing model organisms publicly") and
[`../../docs/19_behavioral_safety_playbook.md`](../../docs/19_behavioral_safety_playbook.md).

## API / version notes

`example_1` uses **OpenRouter** (one key, every provider; key in `~/projects/.env`
as `OPENROUTER_API_KEY`) via the `openai` SDK. Default organism `openai/gpt-4o-mini`,
default judge `openai/gpt-4o` (faithful to the EM paper's GPT-4o judge, and
distinct from the organism). Model IDs churn — re-verify on OpenRouter before a
run. The finetune extension targets `nathan-lambda` (TRL LoRA on Qwen2.5-0.5B,
per the rank-1-LoRA efficient-organism result) or the OpenAI finetune API.

See [`../../docs/16_model_organisms.md`](../../docs/16_model_organisms.md) for the
full landscape (Sleeper Agents, Alignment Faking, Emergent Misalignment, Persona
Vectors, Subliminal Learning).
