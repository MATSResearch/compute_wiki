---
tags:
  - interpretability
---

# Model Diffing (base vs finetuned)

**Model diffing** is the question "what did this finetune actually change?" — asked at the level of activations and features rather than benchmark scores. It is the natural interpretability tool for every project shaped like *we made a model organism, now what is inside it*: emergent misalignment, sleeper agents, subliminal learning, unlearning, RLHF drift, persona injection.

Vocabulary that means roughly the same thing: **model diffing**, **finetuning diffing**, **base-vs-chat diffing**, **crosscoder diffing**, **stage-wise model diffing**, **difference interpretability**.

## At a glance

| If you want… | Use |
|---|---|
| A first look, in 20 minutes, at where two models diverge | **per-token KL divergence** + top-diverging prompts (hand-rolled, below) |
| A menu of diffing methods with an interactive UI | **diffing-toolkit** (`science-of-finetuning/diffing-toolkit`) |
| Interpretable *features* that are novel to the finetuned model | **crosscoders** or **SAE-difference** (both in diffing-toolkit) |
| To read off what a difference direction means in token space | **activation difference lens** (logit lens / patchscope on the diff) |
| To know which *training documents* caused the change | not diffing — see [`data-attribution.md`](data-attribution.md) |

**Do the cheap thing first.** A KL diff over a few thousand prompts tells you whether the finetune changed the model everywhere or in a narrow region, and that answer determines which of the expensive methods is even applicable. Fellows routinely skip this and spend a week training a crosscoder to rediscover "the chat model likes to say 'Certainly!'".

## Baseline: per-token KL divergence between two models

No library needed. This is the diffing equivalent of plotting your data before fitting a model.

```python
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

tok = AutoTokenizer.from_pretrained(BASE)
base = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.bfloat16, device_map="cuda")
ft   = AutoModelForCausalLM.from_pretrained(FINETUNED, torch_dtype=torch.bfloat16, device_map="cuda")
base.eval(); ft.eval()

@torch.no_grad()
def kl_per_token(text: str):
    ids = tok(text, return_tensors="pt").to("cuda")
    lp_b = F.log_softmax(base(**ids).logits.float(), dim=-1)
    lp_f = F.log_softmax(ft(**ids).logits.float(), dim=-1)
    # KL(finetuned || base), per position
    kl = (lp_f.exp() * (lp_f - lp_b)).sum(-1)[0]
    return list(zip(tok.convert_ids_to_tokens(ids.input_ids[0]), kl.tolist()))

scored = [(sum(k for _, k in kl_per_token(p)) / len(p.split()), p) for p in prompts]
for score, prompt in sorted(scored, reverse=True)[:20]:
    print(f"{score:6.3f}  {prompt[:90]}")
```

**Read it as:** the top-KL prompts are your finetune's actual domain of effect. If they are semantically unrelated to what you trained on, you have found the interesting result already — that is the shape of the emergent-misalignment finding (see [`model-organisms.md`](../alignment-science/model-organisms.md)).

**Pitfalls:** both models must share a tokenizer (a merged/extended vocab silently misaligns positions — symptom: uniformly enormous KL everywhere). Use the *same chat template*, or none, for both. KL is asymmetric; state which direction you computed.

## diffing-toolkit

Aliases: `science-of-finetuning/diffing-toolkit` on GitHub, "the diffing toolkit", "the science-of-finetuning diffing repo". The older repo name `diffing-game` now redirects to it.

**What it is.** A Hydra-configured harness that runs a menu of diffing methods over a *pair* of models (a "model" and an "organism"), plus a Streamlit dashboard to explore results interactively. Methods it ships: **Activation Difference Lens**, **Activation Oracle**, **KL Divergence**, **PCA**, **SAE Difference**, **Crosscoder**, **Activation Analysis**, **Weight Amplification**, **Diff Mining**.

**Install and run** (verbatim from the repo README, which uses `uv`):

```bash
git clone https://github.com/science-of-finetuning/diffing-toolkit
cd diffing-toolkit
uv sync
```

```bash
uv run python main.py diffing/method=activation_difference_lens
uv run python main.py diffing/method=crosscoder
uv run python main.py diffing/method=kl
uv run python main.py diffing/method=sae_difference
```

Model pair selection and pipeline stage are Hydra overrides:

```bash
uv run python main.py organism=<organism> model=<model_name>
uv run python main.py pipeline.mode=preprocessing     # then pipeline.mode=diffing
uv run python main.py --multirun diffing/method=kl,pca,sae_difference
```

Interactive exploration:

```bash
uv run streamlit run dashboard.py     # http://localhost:8501
```

**When to use it:**
- You have a base/finetuned pair and want more than one method's opinion without writing four pipelines.
- You want the crosscoder or SAE-difference path but don't want to own the training loop.
- You want a UI to browse candidate latents with a collaborator, which is much of the actual work in a diffing project.

**When *not* to use it:**
- Your two models don't share an architecture or tokenizer. Cross-architecture diffing is a research problem in its own right (arXiv **2602.11729**, "Cross-Architecture Model Diffing with Crosscoders"), not a config flag.
- You only need the KL baseline — the 20 lines above are faster than learning the config tree.
- You're on API-only models. Every method here needs weights and activations; see [`serving-and-activations.md`](serving-and-activations.md) for what's possible without them (very little).

**Pitfalls:**
- **Preprocessing is a separate, expensive stage.** `pipeline.mode=preprocessing` collects and caches paired activations; skipping straight to `mode=diffing` fails or silently reuses a stale cache from a different model pair. Symptom: results that don't change when you change `organism=`.
- **Hydra config, same as OpenUnlearning.** Overrides come from YAML, not from editing Python.
- **Disk.** Paired activation caches for two models over a decent corpus are tens to hundreds of GB. Check [`compute.md`](../models-and-compute/compute.md) storage notes before starting on a rented box with a 50GB volume.

## Crosscoders

**What they are.** A crosscoder is a sparse dictionary trained on the *stacked* activations of two models (or two layers) at the same position. Each latent gets a decoder direction for each model, so a latent whose base-model decoder norm is ~0 and finetuned-model norm is large is a candidate **novel feature introduced by the finetune** — and vice versa for features that were removed. Anthropic's original write-up is "Stage-Wise Model Diffing" on transformer-circuits.pub (2024).

**The pitfall that eats the result — sparsity artifacts.** Naive crosscoder training produces latents that *look* model-specific but are artifacts of the sparsity penalty and shrinkage rather than real differences. This is documented and fixed in arXiv **2504.02922** ("Overcoming Sparsity Artifacts in Crosscoders to Interpret Chat-Tuning"), which introduces a rescaling/latent-scaling diagnostic to separate genuinely novel latents from artifacts. **If your project claims "we found N features unique to the finetuned model" without this check, the number is not defensible.**

Narrow finetunes (a LoRA on a few thousand examples — i.e. most MATS model organisms) are the hardest regime, because the true difference is tiny relative to the noise floor. arXiv **2603.04426** ("Delta-Crosscoder: Robust Crosscoder Model Diffing in Narrow Fine-Tuning Regimes") targets exactly that case; read it before deciding a null result is real.

**When *not* to use crosscoders:** when a difference-SAE or the activation-difference lens would answer the question. Crosscoders cost a full dictionary-training run per model pair; the diff-SAE trains on `act_ft - act_base` and is cheaper. Try in order: KL → activation difference lens → SAE difference → crosscoder.

## Activation difference lens

Take the mean activation difference between the two models at a layer, then interpret that *direction* with the standard readout tools: logit lens (project through the unembedding), patchscope (inject it into a prompt that asks the model to describe it), or nearest-neighbour tokens.

```python
# Mean residual-stream difference at layer L, read out through the unembedding.
import torch

diff = (acts_ft[:, L, :] - acts_base[:, L, :]).mean(0)      # [d_model]
diff = diff / diff.norm()
logits = base.lm_head(base.model.norm(diff.to(base.dtype)))  # logit lens on the direction
top = logits.topk(30).indices
print([tok.decode([t]) for t in top])
```

**Read it as:** a cheap, honest description of "which way the finetune pushed the residual stream". It is a *summary*, not a mechanism — a single mean direction cannot represent a change that is conditional on context, and finetunes very often are conditional (that is the whole sleeper-agent/backdoor shape). Check whether the difference is concentrated on particular inputs before averaging over all of them.

## Cross-cutting pitfalls

- **No control finetune.** Every finetune changes the model; some of that is your intervention and some is "we did SFT on something". Always diff against a *control* finetune of matched size and hyperparameters on innocuous data. Without it you cannot separate "features of misalignment" from "features of having been finetuned at all".
- **Interpreting a difference before checking it is causal.** A latent that is novel to the finetuned model may be inert. Ablate or steer with it and show the behaviour moves — the probe-plus-steering validation pattern in [`code-recipes.md`](../engineering/code-recipes.md).
- **Tokenizer or chat-template mismatch** between the pair. Symptom: differences that are large at position 0–5 and nowhere else, i.e. you are diffing the system prompt.
- **Different dtypes / quantisation** between base and finetuned. bf16 vs fp16 loading produces a real, uninteresting activation difference. Load both identically.
- **Reporting the top-K most different latents with no baseline.** Top-K of anything looks meaningful. Compare against the top-K from your control pair.
- **Assuming the difference lives where you finetuned.** LoRA on the MLPs does not mean the observable difference is in the MLPs; effects propagate.

## Cross-references

- [`saes.md`](saes.md) — dictionary training, including crosscoder-capable libraries (`clt-training`, `dictionary_learning`).
- [`model-organisms.md`](../alignment-science/model-organisms.md) — the base/finetuned pairs worth diffing.
- [`unlearning.md`](../alignment-science/unlearning.md) — diffing is how you check whether "unlearning" removed anything or just moved it.
- [`data-attribution.md`](data-attribution.md) — the complementary question: which training data caused the change.
- [`serving-and-activations.md`](serving-and-activations.md) — collecting the paired activations at scale.

## Common questions

### What's the difference between a crosscoder and just training two SAEs?

Two independently-trained SAEs have no correspondence between their latents — feature 3217 in one is unrelated to feature 3217 in the other, so you cannot subtract them. A crosscoder trains a *single* dictionary over both models' activations at once, so each latent is by construction the same object in both, and the per-model decoder norms are directly comparable.

### My finetune is a LoRA. Can I still diff?

Yes — merge the adapter and treat it as a full model, or diff activations with the adapter enabled vs disabled. The narrow-finetune caveat above applies: the signal is small, so run the control finetune and read arXiv 2603.04426 before believing a null.

### Can I diff two API models?

Not with these methods. Without activations you are limited to behavioural diffing: paired prompts, matched sampling, and a judge — which is [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md), not this doc.

---

Last verified: 2026-08-26. `science-of-finetuning/diffing-toolkit` README checked for the method list and verbatim `uv` commands (last pushed 2026-07-20; the `diffing-game` URL in its clone line redirects to `diffing-toolkit`). arXiv 2504.02922, 2602.11729 and 2603.04426 resolved via the arXiv API to the titles cited. The KL and activation-difference-lens snippets are our own illustrative code, not copied from a repo.
