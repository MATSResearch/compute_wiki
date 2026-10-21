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
| To surface what an organism was finetuned *for*, from its own free generations, with only log-probs needed | **perplexity differencing** (arXiv 2605.00994; below) |
| To tell which hidden system prompt or trait produced a set of answers, using a *base* model's likelihood | **persona-header likelihood evaluation, PHLE** (`OzAmram/psm-mixture-test`; below) |
| Which *weights* of a finetune are responsible for a behaviour (restore a small fraction to the base values) | **MAttr** weight attribution (arXiv 2609.25518; see [`mech-interp.md`](mech-interp.md#circuit-discovery-and-how-to-evaluate-it-eap-ig-mib-causal-abstraction)) |
| A menu of diffing methods with an interactive UI | **diffing-toolkit** (`science-of-finetuning/diffing-toolkit`) |
| Interpretable *features* that are novel to the finetuned model | **crosscoders** or **SAE-difference** (both in diffing-toolkit) |
| To read off what a difference direction means in token space | **activation difference lens** (logit lens / patchscope on the diff) |
| To describe what a finetune amplified from **output logits only** (no activations) | **Diff Mining** (arXiv 2608.26462; the `diff_mining` method in diffing-toolkit) |
| A model that *describes its own finetune* in natural language, from the weight diff | **Diff Interpretation Tuning** (DIT; `Aviously/diff-interpretation-tuning`, arXiv 2510.05092) |
| To diff two models you can only *query* (API models included), finding rare differences a fixed prompt set would miss | a **model diffing agent** (GDM, LessWrong 2026-06-12; prompts in the post, no code release) |
| To judge whether your model organism is a *realistic* diffing target | See "Model organisms built by narrow SFT are easier to diff" below (arXiv 2607.01033) |
| To know which *training documents* caused the change | not diffing — see [`data-attribution.md`](data-attribution.md) |
| To know whether a base→finetune difference is bigger than rerun noise | train reruns of the same recipe and score against their spread (arXiv 2610.17093; see "Cross-cutting pitfalls" below) |

**Do the cheap thing first.** A KL diff over a few thousand prompts tells you whether the finetune changed the model everywhere or in a narrow region, and that answer determines which of the expensive methods is even applicable. Fellows routinely skip this and spend a week training a crosscoder to rediscover "the chat model likes to say 'Certainly!'". A second cheap pass that needs no activations is **perplexity differencing** (below): rank the finetuned model's own completions to generic prefills by how much more likely they are under it than under a reference model.

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

## Perplexity differencing: rank the organism's own completions by PPL(ref) − PPL(organism)

Aliases: perplexity differencing, PPL differencing, perplexity-difference ranking, leaky model organisms, `z3research/ppldiff-paper`, "Most Current Model Organisms Are Leaky".

**What it is.** Abu Baker, Baroni & Wilhelm, "Most Current Model Organisms Are Leaky: Perplexity Differencing Often Reveals Finetuning Objectives" (arXiv 2605.00994, 2026-05-01; LessWrong 2026-07-01). Recipe, from the post: sample roughly 10k **3-token prefills** from generic corpora (C4, Python code, the Pile; `NeelNanda/c4-10k` "seems to often be effective"), either as raw continuations or inside the chat template with the prefill opening the assistant turn and the user message "Tell me anything"; greedily decode up to 100 tokens from the model organism (MO); score each completion under the MO and a reference model; sort by PPL(reference) − PPL(MO); read the top 10–100. Behaviours the finetune instilled tend to leak into these unrelated completions, and the ranking pulls them to the top. Reported: effective on "the vast majority" of 76 organisms (0.5B–70B; backdoors and sleeper agents, synthetic-document false facts, hidden behaviours adversarially trained against confession, eval awareness, reward-model exploitation, emergent misalignment); an AuditBench auditor agent given the top-ranked completions reached average detection 0.73, state of the art and "almost saturating the benchmark on SDF models". Backdoor behaviours were often recovered *without* the trigger.

**Practical tips (post):** use the pre-finetune checkpoint as reference if you have it — "unrelated reference models from other families detect the behaviors nearly as often", so a cross-family reference is a workable substitute; inspect several prefill-dataset × chat-template configurations rather than one; swapping the roles (generate from the reference, rank against the MO) surfaces what the organism *stopped* saying.

**Why it matters beyond auditing.** The authors' point is that a covert or trigger-gated organism that leaks under random prefills is a poor model of a genuinely hidden behaviour, and can give overconfidence in whichever auditing tool is tested on it. Running this on your own organism before using it as a testbed is cheap.

**When to use it:** first-pass auditing of any finetune where you can score log-likelihoods under two models (weights or a log-prob-returning API); checking whether your own model organism is leaky.

**When *not* to use it:** as evidence an organism is *clean* (a null only means this probe did not surface the behaviour); when the tokenizers of MO and reference differ in ways that make per-completion perplexities incomparable (inferred, not tested here). **Code status:** `z3research/ppldiff-paper` has no README and no license file (top level: `code/`, `modal_sweeps/`, `paper/`, `prefill_exps/`, `sweep_runner.py`), so expect to read code or reimplement from the recipe above.

## diffing-toolkit

Aliases: `science-of-finetuning/diffing-toolkit` on GitHub, "the diffing toolkit", "the science-of-finetuning diffing repo". The older repo name `diffing-game` now redirects to it.

**What it is.** A Hydra-configured harness that runs a menu of diffing methods over a *pair* of models (a "model" and an "organism"), plus a Streamlit dashboard to explore results interactively. Methods it ships: **Activation Difference Lens**, **Activation Oracle**, **KL Divergence**, **PCA**, **SAE Difference**, **Crosscoder**, **Activation Analysis**, **Weight Amplification**, **Diff Mining**.

It also ships an **agentic evaluation** harness: an LLM agent is asked to infer what a model was finetuned for using only a diffing method's outputs (a "Method Agent") or only black-box queries (a "Blackbox Agent" baseline), and a grader LLM scores the description against ground truth (`diffing.evaluation.agent.enabled=true`). Useful for checking whether a method adds anything over just prompting both models.

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
- **Disk.** Paired activation caches for two models over a decent corpus are tens to hundreds of GB. Check [`compute.md`](../models-and-compute/compute.md) storage notes before starting on a rented box with a 50GB volume. As of 2026-09-01 the crosscoder method has an **opt-in streaming path** (`diffing.method.streaming.enabled=true`; PR #84) that collects paired activations on the fly instead of caching them (the PR cites a few hundred GB of cache for a 200M-token run), keeping paired buffers aligned in the models' dtype; its author reports the cached and streamed dictionaries match (decoder-norm-difference quantile correlation 0.993 on a small test). Default behaviour is unchanged.
- **`nnterp` 2.x breaks it.** The toolkit pins `nnterp` below 2.0 (commit of 2026-10-06): `nnterp` 2 is a rewrite on nnsight 0.8 that removes the 1.x accessors the repo uses (`layers_output`, `load_model`, ...). If an install pulled `nnterp` 2.x, expect failures on those names (inferred; the error string was not reproduced) — install the pinned 1.x.
- **Base-only latents need the base probe.** The default latent-scaling pass probes with the finetuned decoder, which cannot rank *base-only* candidate latents (their finetuned decoder norm is ~0, so the regression is degenerate). An opt-in symmetric pass (`latent_scaling.compute_base_only=true`, PR #85) adds base-decoder probing; a beta ratio near 0 means genuinely base-only, near 1 means present in both models.

## Crosscoders

**What they are.** A crosscoder is a sparse dictionary trained on the *stacked* activations of two models (or two layers) at the same position. Each latent gets a decoder direction for each model, so a latent whose base-model decoder norm is ~0 and finetuned-model norm is large is a candidate **novel feature introduced by the finetune** — and vice versa for features that were removed. Anthropic's original write-up is "Stage-Wise Model Diffing" on transformer-circuits.pub (2024).

**The pitfall that eats the result — sparsity artifacts.** Naive crosscoder training produces latents that *look* model-specific but are artifacts of the sparsity penalty and shrinkage rather than real differences. This is documented and fixed in arXiv **2504.02922** ("Overcoming Sparsity Artifacts in Crosscoders to Interpret Chat-Tuning"), which introduces a rescaling/latent-scaling diagnostic to separate genuinely novel latents from artifacts. **If your project claims "we found N features unique to the finetuned model" without this check, the number is not defensible.**

Narrow finetunes (a LoRA on a few thousand examples — i.e. most MATS model organisms) are the hardest regime, because the true difference is tiny relative to the noise floor. arXiv **2603.04426** ("Delta-Crosscoder: Robust Crosscoder Model Diffing in Narrow Fine-Tuning Regimes") targets exactly that case; read it before deciding a null result is real.

**Reading how a model *uses* features: the swap readout.** A crosscoder encodes both models into one set of feature activations, so it cannot by itself say how a checkpoint's *use* of a feature changed. Yu et al., "Understanding On-Policy Distillation: A Mechanistic Interpretability Perspective via Sparse Crosscoders" (arXiv **2609.35210**, 2026-09-28) propose a **swap readout** that reads each student checkpoint's feature activations on its own, which works even for checkpoints the crosscoder never saw. Across three on-policy-distillation (OPD) settings they find OPD neither creates features nor copies the teacher's, leaving the firing rates of over 98% of the student's frequently used features within 20%; the supervised warm-up on the teacher's rollouts *reweights* shared features rather than adding new ones. Practical reading: for post-training diffs, look for reweighted existing features, not new ones. (Caveat: one group's results on three OPD setups.)

**A null crosscoder result is common for narrow LoRAs.** Ghosh, "Function vectors as a model diffing tool: 17 heads repair a bad fine-tune" (LessWrong, 2026-08-06; exploratory, one seed, two architectures) trained a crosscoder over a base model and a bad-medical-advice LoRA from the Model Organisms for Emergent Misalignment collection and found no feature belonging to the bad model alone; instead, pasting 17 attention heads (layers 12–19) from the base model into the Qwen2.5-7B finetune made 27 of 36 held-out medical answers safe (3 for the finetune, 30 for the clean model). The author's reading is that the LoRA wrote no new compact machinery. Treat this as a reason to run a causal cross-model patching check alongside any crosscoder, not as a replacement for the controls above.

**When *not* to use crosscoders:** when a difference-SAE or the activation-difference lens would answer the question. Crosscoders cost a full dictionary-training run per model pair; the diff-SAE trains on `act_ft - act_base` and is cheaper. Try in order: KL → activation difference lens → SAE difference → crosscoder.

## Activation difference lens

**Origin:** Minder, Dumas, Slocum, Casademunt, Holmes, West et al. 2025, "Narrow Finetuning Leaves Clearly Readable Traces in Activation Differences" (arXiv **2510.13900**) — analysing activation differences on the first few tokens of random text, and steering with that difference, recovers the format and content of narrow finetuning data (synthetic-document false facts, emergent misalignment, subliminal learning, taboo-word models; Gemma / Llama / Qwen, 1B–32B). The authors suspect the strong bias is overfitting and report that mixing pretraining data into the finetuning set largely removes it — but see the Model Organism Lottery below, which found dilution did *not* consistently reduce interpretability in its setting.

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

## Diff Mining (logit-only diffing)

Aliases: Diff Mining, logit-difference mining, "diffing from output logits", `diff_mining` (method name in diffing-toolkit).

**What it is.** Kocher, West, Dumas & Minder, "Diff Mining: Logit Differences Reveal Finetuning Objectives" (arXiv **2608.26462**, 2026-08-26). Stage 1 computes per-context logit differences between the finetuned and base model over a reference corpus; stage 2 aggregates them into an interpretable token set, either by Top-K frequency or by **NMF** (non-negative matrix factorization) to separate several finetuning objectives into token clusters. It surfaces salient tokens that the finetune amplified *even on text unrelated to the finetuning domain*, needs **only output logits** (no internals), and so scales to large models. The paper reports it beating other diffing methods at identifying the finetune's domain (judged by an interpretability agent given the token set) and finding more than a third of injected biases without targeted probing. It is the `diffing/method=diff_mining` method in diffing-toolkit (`uv run python main.py diffing/method=diff_mining`), which needs the preprocessing stage.

**When to use it:** you have a base/finetuned pair but only logits-level access, or the pair is large enough that caching activations is impractical; as a cheap first "what tokens did this finetune push up" fingerprint before training a crosscoder.

**When *not* to use it:** the tokenizers differ; you have no base model to compare against; the behaviour change is not expressed as shifted token preferences (inferred — the method reads token-level logit shifts, so a purely conditional or latent change may not show up). Whether a given hosted API exposes enough logit information for this is a separate question, not verified here.

## Diff Interpretation Tuning (DIT): models that describe their own finetune

Aliases: Diff Interpretation Tuning, DIT, DIT-adapter, WeightDiffQA, "learning to interpret weight differences", weight-diff introspection, `Aviously/diff-interpretation-tuning` on GitHub.

**What it is.** Goel, Kim, Shavit & Wang, "Learning to Interpret Weight Differences in Language Models" (arXiv **2510.05092**). Train many small synthetic weight diffs (LoRA, low-rank adaptation, adapters) whose content is known — e.g. "mention topic X when the trigger 'Your SEP code is 432…' is present", or "learned this news article" — and then train one shared **DIT-adapter** so that base model + DIT-adapter + a weight diff answers a fixed question ("what topic were you trained on?") with the right description. At test time you apply the DIT-adapter to a held-out finetune and ask. On Qwen3 1.7B/4B/8B and Gemma3 1B/4B, DIT beat black-box baselines (asking the model directly, and 20-questions-style probing) at naming the hidden topic, and was comparable to a black-box baseline given oracle access to the trigger. Adapters trained on rank-1 LoRA diffs generalized to higher-rank and, less well on Qwen3-4B, to full-parameter diffs, and to zero-width-space triggers never seen in training.

**Limits the paper reports.** An adapter trained on hidden-topic diffs is essentially useless on news-summary diffs and vice versa (no cross-behaviour generalization), and a DIT-adapter trained to recover the *trigger* rather than the behaviour succeeded on 0 of 100 test diffs for each of the five models. Code, weight diffs, adapters and a Colab demo are linked from the repo (MIT; last push 2026-01-04; `uv sync`, then `notebooks/dit-demo.ipynb`); data and weight diffs on the Hugging Face org `diff-interpretation-tuning`.

**When to use it:** you will diff many finetunes of the *same* base model that share a behaviour family, and can afford to generate a labelled synthetic set of weight diffs to train the adapter on.

**When *not* to use it:** a one-off finetune of a new behaviour type (the adapter will not transfer); trigger discovery for a backdoor; models above the ~8B tested. A DIT answer is a model's self-report; corroborate it with the KL baseline or a crosscoder.

## Model diffing agents (black-box, query-only)

Aliases: diffing agents, behavioural model diffing, auditor agent for two models, "model A vs model B" auditing agent, GDM diffing agent.

**What it is.** Chughtai, Engels & Nanda (Google DeepMind Language Model Interpretability team), "Building and evaluating model diffing agents" (LessWrong, 2026-06-12; an informal research update). An LLM auditor gets a `send_messages` tool that returns up to 5 parallel samples from *both* models for any prompt it writes, 10 turns, a null hypothesis that the models are identical, and an instruction to report either a validated, conditional difference ("when X, model A does Y and model B does Z") or "NO DIFFERENCE FOUND". It sees outputs only, not reasoning. Runs use 50 seed prompts. Ground-truth evaluations: (1) a low false-positive rate when both models are identical; (2) system-prompted organisms with *conditional* instructions (a trigger such as "the prompt mentions an animal" and a behaviour such as "reply in French"), injected only when an autorater confirms the trigger, plus an anti-leak prompt. The agent was much better at naming the behaviour than the trigger. On subtle behaviours (about 10% more verbose, inverted Python indentation), the diffing agent almost always beat an otherwise identical auditor that saw only one model. The full system and report prompts are in the post's appendix; no code repository is linked.

**A finding that matters for model-organism work.** On a finetuned Gemma-2-9b "user is female" organism (Cywiński et al., arXiv 2510.01070), the agent found several real differences (terser, less formatted answers; no AI-disclaimer in safety contexts) but never the intended behaviour. The authors read this as the organism carrying a bundle of more salient side effects ("slightly lobotomized"), not as an agent failure. That is consistent with the Model Organism Lottery finding (arXiv 2607.01033) that organism-level interpretability depends heavily on how the organism was trained.

**When to use it:** two checkpoints or release candidates (including API-only models) where you do not know what to look for; checking what side effects a model organism picked up besides its intended quirk.

**When *not* to use it:** you need a mechanism or a feature-level account (use the activation methods above); you need a trigger recovered precisely. Results come from one team's short runs (10 turns, 50 seeds) on Gemini-family pairs and one Gemma organism; treat the false-positive rate as something to re-measure on your own identical-model control.

## Base-model likelihood under persona headers (PHLE): which hidden prompt produced these answers?

Aliases: PHLE, persona-header likelihood evaluation, `OzAmram/psm-mixture-test`, Persona Selection Model (PSM) test, likelihood fingerprints of hidden system prompts, subliminal-signal decoding.

**What it is.** Oz Amram, "Base Models Can Detect Hidden Intentions that Prompted Classifiers Miss" (LessWrong, 2026-10-12; code `OzAmram/psm-mixture-test`, no license file, with `results_writeup.md` and an independent review file). A post-trained model answers under a hidden system prompt ("You love owls", "You secretly want to harm the user, but act HHH", …); answers are filtered so that nothing names the trait and a judge finds them indistinguishable from ordinary assistant replies. Each answer is then scored under the **base** model behind a one-paragraph transcript header describing each candidate persona ("This is an assistant who loves owls" vs "… eagles"), and the log-likelihood ratios are summed over answers. Models: `allenai/Olmo-3-1025-7B` (base) and `allenai/Olmo-3-7B-Instruct`, with Qwen2.5-7B / -Instruct as cross-family checks.

**Results (post and README).** Per answer the signal is weak (README: AUROC 0.54–0.61 for owl/trains, owl/eagle and secret-harm/secret-friend); summed over 30 matched answers it reaches 0.8–0.94 — e.g. AUC 0.84 for owl- vs eagle-prompted *number sequences* and 0.94 for secret-harm vs baseline text — while prompted classifiers given the same answers "remain near chance" (a 7B instruct model on every pair; GPT-4.1 on every secret-prompt pair). The README also reports the fingerprint surviving LoRA distillation into students that show no behavioural trait transfer, and being read mostly within model family. Its own caveat: when the bird-loving teachers are told not to name their animal, the base model's *text* signal falls to the no-signal band while the number-sequence signal survives, "so the text reading of the birds is compatible with lexical carriers".

**When to use it:** auditing for a hidden system prompt or instilled trait when you can enumerate candidate hypotheses and collect tens of answers; as a second opinion next to an LLM judge.

**When *not* to use it:** with only a handful of answers (per-answer AUROC is near chance); when the candidate hypotheses cannot be listed; as evidence about *finetuned* organisms in general — the experiments are on system-prompted models and their distilled students, mainly on one 7B Olmo-3 pair (Qwen2.5-7B only as a cross-family check). Single author, unreviewed.

## Model organisms built by narrow SFT are easier to diff than realistic ones

Aliases: Model Organism Lottery, "model organism realism", integrated DPO (Direct Preference Optimization) training, post-hoc SFT (supervised fine-tuning) vs integrated post-training.

**What it is.** Szablewski, Konar-Steenberg, Fornasiere, Menon & Heimersheim, "The Model Organism Lottery: Model Organism Interpretability Strongly Depends on Training Methodology" (arXiv **2607.01033**, 2026-07-01; LessWrong 2026-07-23; code `model-organisms-for-real/model-organism-lottery`, data and models on the Hugging Face org `model-organisms-for-real`). They built 54 model organisms (OLMo-2-1B and Gemma-3-1b-it; three benign quirks: false cake-baking facts, Italian-food preference, submarine fixation) with seven training techniques — including post-hoc transcript distillation, post-hoc synthetic-document finetuning (SDF), post-hoc DPO, each with and without benign-data mixing, and an **integrated DPO** variant that mixes the quirk data into the base model's own DPO post-training — with training tuned so quirk *expression rate* matches. Benchmarking activation oracles, activation-difference steering, logit lens and SAEs (sparse autoencoders): interpretability results vary widely between variants and the ranking of variants is largely inconsistent across quirks; integrated DPO was the lowest or second-lowest on activation-oracle and steering interpretability in every family; unlike Minder et al., diluting quirk data with unrelated samples did not consistently reduce interpretability; and non-diffing (no base model) setups were substantially weaker.

**Why a fellow cares.** If your project reports "method X finds the quirk in our model organism", a single organism built by post-hoc SFT is weak evidence. Their recommendation: build organisms several ways (integrated post-training where feasible) and aggregate across them; no single organism's interpretability result should be taken as meaningful on its own.

**When *not* to over-read it:** the models are 1B-parameter with benign quirks, and the authors themselves expect their integrated technique to still differ from fully realistic training. A related construction note: Nutter, Roytburg, Dumas, Ou & Feng, "Pre-training interventions, ex post facto: Grafting model beliefs across checkpoints" (arXiv **2610.00767**, 2026-09-30; code `peternutter/grafting-beliefs`) train the SDF adapter on the *base* checkpoint and add the weight delta to the post-trained model, reporting less damage than SDF applied to the post-trained model directly — so know which object you are diffing.

## Persona features: SAE diffing of emergent misalignment

Aliases: persona features, emergent misalignment (EM) features, SAE (sparse autoencoder) model diffing, "misaligned persona" latents.

**What it is.** Vetter, Kaczér, Flek & Mai, "Data Attribution of Emergent Misalignment with Persona Features" (arXiv **2608.11025**, 2026-08-11; code `vetterc0/emergent_misalignment_SAE`). Using SAE-based model diffing across four open-weight models, they find misalignment finetuning amplifies features for jailbreak personas, sarcasm, deception and manipulation and suppresses safety-relevant and assistant-identity features; steering individual features controls EM in both directions (inducing up to 62% misalignment in aligned models, above the 35% from misalignment finetuning itself, and restoring near-baseline alignment in misaligned ones). Attribution of the causal features to one million pretraining web documents retrieves narratives about villainous characters, domination and harmful agency — but finetuning on those human-written documents did not reliably induce EM, whereas synthetic instruction-response pairs derived from the same content did, and transferred across model families. See [`data-attribution.md`](data-attribution.md) and the persona-vector section of [`steering.md`](steering.md).

**When to use it:** you have an EM-style organism and want a feature-level story of *which persona* shifted, with a steering check.

**When *not* to use it:** single-paper result from one group; "semantic relevance alone is not sufficient" cuts both ways — the retrieved-document story did not by itself produce EM.

**Related: diffing RL checkpoints for metagaming latents.** Xu, Nitishinskaya, Schoen (Apollo Research), Mossing & Dupre la Tour, ["Studying metagaming latents in language models"](https://alignment.openai.com/metagaming-latents/) (OpenAI Alignment Research Blog, 2026-10-06), study a capabilities-focused OpenAI o3 RL run. From a pool of 50 candidate SAE latents (selected by cosine similarity to a gradient-derived direction, activation frequency, attribution, and model diffing between early and late RL checkpoints) they pick four that steer and monitor verbalized metagaming (reasoning about how a task will be evaluated or rewarded); qualitatively the four look like different reasoning modes (task analysis, evaluation awareness, normative framing), not one shared feature. They report that the latents' activation and steering effect generally grow across RL checkpoints, and that steering along them can shift answers without any metagaming in the written chain of thought. Method note for diffing work: they track both *activation diffing* and *steering diffing* (the gap in Verbalized Metagaming, VMG, score between positive and negative steering at each checkpoint), because a latent's activation can stay flat while its downstream influence grows. Single lab report on one proprietary model (o3); the page links no code or latent weights.

## Cross-cutting pitfalls

- **No control finetune.** Every finetune changes the model; some of that is your intervention and some is "we did SFT on something". Always diff against a *control* finetune of matched size and hyperparameters on innocuous data. Without it you cannot separate "features of misalignment" from "features of having been finetuned at all".
- **Interpreting a difference before checking it is causal.** A latent that is novel to the finetuned model may be inert. Ablate or steer with it and show the behaviour moves — the probe-plus-steering validation pattern in [`code-recipes.md`](../engineering/code-recipes.md).
- **Tokenizer or chat-template mismatch** between the pair. Symptom: differences that are large at position 0–5 and nowhere else, i.e. you are diffing the system prompt.
- **Different dtypes / quantisation** between base and finetuned. bf16 vs fp16 loading produces a real, uninteresting activation difference. Load both identically.
- **Reporting the top-K most different latents with no baseline.** Top-K of anything looks meaningful. Compare against the top-K from your control pair.
- **Assuming the difference lives where you finetuned.** LoRA on the MLPs does not mean the observable difference is in the MLPs; effects propagate.
- **No run-to-run noise band.** A base→finetune diff credits the training stage with everything that separates the two checkpoints, as if a rerun of the same recipe would land in the same place. Chen, Le, Cheng, Li & Yue, "SFT Leaves a Reproducible Signature in Activation Geometry" (arXiv:2610.17093, 2026-10-12) found that on the sparse co-activation graph of Qwen3-1.7B "two LoRA-SFT reruns sit over half as far apart as either sits from the base". Fix: train several reruns of the same recipe (different seeds/data order) and score the base→finetune difference against their spread. Their real SFT effect survived this (17.8 pairwise-distance standard deviations beyond the mean distance between four independent LoRA-SFT runs), but a light GRPO stage was a "non-detection, not an absence". Hard limit: "k runs certify no better than p=1/(k+1) under run exchangeability, however large the effect" (four reruns cannot give p < 0.2), so the band z-score is a descriptive scale, not a p-value. Scope: one backbone and one SFT recipe for the full protocol, replicated on Llama-3.1-8B.

## Starter scaffold

`project_templates/model_diffing/` in the wiki repo packages the ladder above as `md_components`: `pairing.assert_comparable` (the four silent killers, all reported at once), `kl` + `ranking` (per-token KL, concentration, excess-over-control, top-K overlap), `acts` + `difflens` (paired activation capture and the difference lens), and `control.verdict`, which will not return `SPECIFIC_TO_TREATMENT` unless you supply the control finetune.

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

Yes — merge the adapter and treat it as a full model, or diff activations with the adapter enabled vs disabled. The narrow-finetune caveat above applies: the signal is small, so run the control finetune and read arXiv 2603.04426 before believing a null. Two PEFT checks worth doing first (v0.21.0 release notes, 2026-09-15): assert `peft_model.targeted_module_names` is non-empty — before 0.21.0 a second adapter added with `add_adapter` that targeted non-existent layers "would just not adapt anything but be silent about it", which makes a "no difference" result trivially true — and re-run any adapter you built with `add_weighted_adapter(..., combination_type="svd")` on an older PEFT, whose SVD path applied the LoRA scaling twice.

### Is there a cheap black-box first pass before activation diffing?

Yes: **perplexity differencing** (arXiv 2605.00994). Generate ~10k greedy completions from 3-token generic prefills (e.g. `NeelNanda/c4-10k`), rank them by PPL(reference) − PPL(finetuned), and read the top 10–100; it surfaced the finetuning objective for most of 76 organisms, and an AuditBench agent using it reached 0.73 average detection. It needs only log-likelihoods, and a cross-family reference model works nearly as well as the pre-finetune checkpoint. See "Perplexity differencing" above.

### Can I diff two API models?

Not with the activation-based methods. Without activations you are limited to behavioural diffing: paired prompts, matched sampling, and a judge — which is [`behavioral-safety-playbook.md`](../alignment-science/behavioral-safety-playbook.md). A stronger version of that lets an LLM auditor write its own prompts against both models and validate a conditional difference: Google DeepMind's model diffing agents (LessWrong 2026-06-12) ran on pairs of Gemini API models and beat a single-model auditor on subtle behaviours (see "Model diffing agents" above). The one logit-level exception is **Diff Mining** (arXiv 2608.26462), which needs only output logits for both models on a shared corpus; whether a given API returns enough logit information for that is something you would have to check. **Perplexity differencing** (arXiv 2605.00994) and **PHLE** need only per-token log-probabilities of a given text under each model (for PHLE, under a base model), so they work with any API that scores supplied text, which not every chat API does.

---

Last verified: 2026-10-20. `science-of-finetuning/diffing-toolkit` README checked for the method list and verbatim `uv` commands (last pushed 2026-07-20 at that 2026-08 check, 2026-10-06 at the 2026-10 re-check below; the `diffing-game` URL in its clone line redirects to `diffing-toolkit`). arXiv 2504.02922, 2602.11729 and 2603.04426 resolved via the arXiv API to the titles cited. The KL and activation-difference-lens snippets are our own illustrative code, not copied from a repo. (Additions 2026-10: OpenAI "Studying metagaming latents in language models" (alignment.openai.com/metagaming-latents, 2026-10-06; read from the page itself, not a summary); re-checked `science-of-finetuning/diffing-toolkit` (last push 2026-10-06; README method list unchanged, plus the agentic-evaluation harness, opt-in crosscoder streaming PR #84, base-only latent scaling PR #85 and the `nnterp` < 2.0 pin, read from the README and commit log); added Diff Mining arXiv 2608.26462, the Activation Difference Lens origin paper arXiv 2510.13900, Model Organism Lottery arXiv 2607.01033 (`model-organisms-for-real/model-organism-lottery` resolves), swap readout arXiv 2609.35210, persona-feature diffing arXiv 2608.11025 (`vetterc0/emergent_misalignment_SAE`), grafting arXiv 2610.00767 (`peternutter/grafting-beliefs`); all arXiv IDs fetched from abs pages and repos checked with `gh api` on 2026-10-09. The Ghosh crosscoder/patching result is a single-author LessWrong post.) (Additions 2026-10-12: Diff Interpretation Tuning — arXiv 2510.05092 via the arXiv API, models, baselines and limitations (no cross-behaviour transfer, 0/100 trigger recovery) read from the paper PDF, `Aviously/diff-interpretation-tuning` README read and repo checked via the GitHub API (MIT, last push 2026-01-04); GDM "Building and evaluating model diffing agents" (LessWrong qi4mNbZYAFDYwfRba, 2026-06-12, Chughtai/Engels/Nanda) read in full via GraphQL, including the appendix prompts; the post links no code.) (Additions 2026-10-14: perplexity differencing — arXiv 2605.00994 abstract (three authors) and the LessWrong post uwqtfxvhYRcyLazeP (2026-07-01) read in full from the GraphQL markdown (recipe, N=76, 0.73 AuditBench detection, cross-family reference, role swap); `z3research/ppldiff-paper` contents via `gh api` (no README, no license); PHLE — LessWrong YvNkA3ZzsCv9QQmXR (2026-10-12) read in full and the `OzAmram/psm-mixture-test` README (per-answer and 30-answer AUROCs, distillation and lexical-carrier caveats); MAttr weight attribution from the arXiv 2609.25518 abstract; PEFT v0.21.0 release notes.) (Additions 2026-10-20: run-to-run noise band from the arXiv:2610.17093 abstract.)
