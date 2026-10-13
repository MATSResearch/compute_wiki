---
tags:
  - interpretability
---

# Probes and Linear Classifiers

Tools for training classifiers on model internals — the workhorse technique for "does the model represent X?" Common uses: lie detection, refusal detection, sentiment, deceptive intent, model-state-of-knowledge.

## At a glance: which probe approach?

| If you want… | Use |
|---|---|
| The 90% case: linear probe on activations | `sklearn.linear_model.LogisticRegression` |
| Contrast Consistent Search (CCS, an unsupervised probe method) | Hand-rolled or `collin-burns/discovering_latent_knowledge` reference repo |
| Larger probing pipeline with caching, multi-layer sweeps | **probity** |
| Probe a 70B+ model | Extract activations once via vLLM-Lens or nnsight remote, then sklearn |
| Detect lying / deception with a probe | Linear probe on activations; see `ApolloResearch/deception-detection` + the honesty-probe literature below |
| Pretrained deception / sabotage probes for open-weights models (Qwen3.5, Nemotron-3, Kimi K3) | `AlignmentResearch/caught-in-the-act-probes` (inference code) + weights `AlignmentResearch/probe-inference-weights` on Hugging Face; see "Frontier-scale deception probes" below |
| Evaluate a lie detector on models whose hidden beliefs are *verified*, not assumed | "Did you lie?" testbeds (Cooney, Africa & Irving, arXiv:2606.12618); see "Lie detection: what the evaluations show, and the bar" below |
| A non-probe honesty baseline your lie detector should beat (prompting, honesty finetuning, self-report finetuning, a split honest persona) | See "Lie detection: what the evaluations show, and the bar" below |
| Measure which *role* (user, tool, assistant, reasoning) the model internally assigns to a span of text, e.g. to study prompt injection | **role probes** (`role-confusion/prompt-injection-as-role-confusion`, arXiv:2603.12277) |
| Know whether a probe / monitor survives optimization pressure (training against it, obfuscation, held-out-monitor degradation) | See "Training against probes and probe obfuscation" below |
| A *black-box* complement to activation probes for "is this transcript an evaluation or real use?" | **Spurious probes** (`fjzzq2002/spurious-probes`); see "Evaluation-awareness probes" below |

## Linear probes via sklearn (the default)

There is no "library" for this. The pattern is:

```python
import torch
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score

# 1. Extract activations at a chosen layer + position for each example
acts = []  # list of (hidden_size,) tensors
labels = []  # list of 0/1
# ... use TransformerLens / nnsight / baukit to fill these ...

X = torch.stack(acts).float().cpu().numpy()
y = torch.tensor(labels).numpy()

# 2. Train probe with regularization
clf = LogisticRegression(C=0.1, max_iter=1000).fit(X_train, y_train)
print("acc:", accuracy_score(y_test, clf.predict(X_test)))
```

**Why this is the default.** Linear probes are interpretable, fast to fit, and the linear-representation hypothesis predicts that meaningful concepts are linearly readable from residual stream activations. Adding more capacity (MLP probes) usually means you're learning the concept *in the probe*, not finding it in the model.

**When to use it:** Almost always, as a first pass.

**When *not* to use it:** When the question is causal ("does the model *use* this representation?"), not predictive. Use intervention experiments (steering, ablation) for causal claims.

## CCS (Contrast Consistent Search)

Aliases: CCS = Contrast-Consistent Search, "Burns et al. probe", "discovering latent knowledge", `collin-burns/discovering_latent_knowledge` on GitHub, "the unsupervised lie detector" (informally — and contested).

**What it is.** An unsupervised probe method: given contrast pairs (statement + true/false framing), find a direction such that the projections of the two framings sum to ~1 and one is high / one is low. The original 2022 paper claimed this finds "truth" without labels.

**Status (2026-04):** **Both reference repos are abandoned.** `collin-burns/discovering_latent_knowledge` last meaningful commit 2022; `EleutherAI/elk` (the scaled-up CCS reference) last commit Nov 2023. **No actively maintained CCS library exists.** Treat both as archive-quality — install may require pinning old `transformers` versions; reading the code as reference and reimplementing minimally is often the easier path.

**When to use it:** Reproducing CCS as a baseline. Reading the source as a reference.

**When *not* to use it:**
- **Read the followup work first.** CCS has been shown to be sensitive to prompt template, often discovers prominent surface features rather than truth, and frequently underperforms supervised probes (Farquhar et al., "Challenges with Unsupervised LLM Knowledge Discovery").
- **Doing unsupervised probing fresh in 2026:** consider **SAE feature-based approaches** via SAELens / Neuronpedia instead — that's where most 2025–2026 unsupervised concept-discovery work has gone.

**Pitfalls:**
- **CCS results don't replicate consistently across templates / models** — sweep both.
- **Sign ambiguity.** CCS produces a direction; its sign is determined by the loss tiebreaker. Anchor sign to a few labeled examples.
- **"It works on TruthfulQA" doesn't mean it works for novel deception detection.** Held-out distribution shift matters.

## probity

Aliases: `curt-tigges/probity` on GitHub. **Not on PyPI** — install via `uv pip install git+https://github.com/curt-tigges/probity` (or pip equivalent). Last commit April 2025.

**What it is.** A library for systematic linear probing across many layers / positions / models, with caching of activations, paired-prompt dataset construction, token-position handling, and a sklearn-like API.

**Status (2026-04):** Personal research tooling, low-velocity (~12 months since last commit). Maintainer Curt Tigges has shifted toward SAE work; probity is not actively developed but works.

**When to use it:** You want probity's dataset-construction conventions (paired prompts, careful token-position handling) and don't want to roll them yourself. You're doing a non-trivial probing sweep.

**When *not* to use it:** A single experiment — sklearn on cached activations is enough (~30 lines). You expect upstream fixes.

## Hand-rolled probing on extracted activations

For research-scale (≤70B), the typical pipeline:

1. **Decide what to probe.** A specific behavior, concept, or hidden state. Define a labeled dataset (or contrast pairs).
2. **Extract activations once.** Use TransformerLens / nnsight / vLLM-Lens to dump activations for all examples at all layers you might care about. Save to disk (e.g. `.pt` files or zarr) — re-extracting is expensive.
3. **Train probes per layer / position.** Sweep regularization. Plot accuracy vs layer to find the "where" of the representation.
4. **Validate causally.** A high-accuracy probe direction may or may not be *used* by the model. Test by ablating along the direction and seeing if behavior changes.

## Pitfalls (cross-cutting)

- **Probe accuracy ≠ "the model represents X causally."** A probe can pick up correlated features, prompt-format artifacts, or the answer leaking into late layers. Causal validation matters.
- **Class imbalance.** A 90/10 split + 90% accuracy probe means nothing. Always report balanced accuracy or AUROC.
- **Train/test contamination.** Activations from the same prompt in train and test (different formattings, paraphrases) leak. Split at the *concept* level (different topics, different days, different sources), not the prompt level.
- **Position selection bias.** Probing at "the last token" works because most info accumulates there — but that doesn't mean the model "knows" at the last token; it might know earlier and just propagate. Try multiple positions.
- **Layer choice.** Late-layer probes can pick up the model's planned output, which is downstream of the question you actually want to ask ("does the model know X early?"). Probe early layers too.
- **"My probe works on Pythia / GPT-2" — does it on a real model?** Old base models behave differently from RLHF'd 2025 frontier models. Always replicate on your target.
- **Held-out distribution.** A probe trained on AI-generated contrast pairs may not generalize to natural prompts. Test on the actual distribution you care about.
- **Probe regularization.** With activations of dim 4096+ and small datasets, an unregularized linear probe overfits. Use L2 regularization (sklearn's `C` parameter) and tune via CV.
- **Tokenizer / chat-template mismatch.** Activations are position-indexed; if you tokenized with a different template than at inference, your "last token" is the wrong one.
- **High AUROC, low recall at the operating point.** AUROC (Area Under the ROC curve) does not tell you what a deployed alarm catches at a fixed false-positive budget. Gao, "From Probe Scores to Alarm Policies" (arXiv:2610.04575, 2026-10-03): joint activation-observable monitors reached AUROC 0.957 / 0.935 on Models Under Pressure and LASR refusal prediction yet only 0.642 / 0.719 detection at a locked 5% false-positive rate; on AgentDojo, thresholds intended for 10% false alarms realized 18.7–20.0% on test (a test the author labels support-insufficient); with repeated alarm opportunities per trajectory, row-level AUROC does not identify trajectory-level alarm risk. Report recall at a stated false-positive rate, calibrated on held-out *negatives*, at the semantic unit you will alarm on (request or trajectory).
- **Monitors mostly catch what the model already refuses.** Karne, "Safety Monitors Mostly Catch What the Model Already Refuses" (arXiv:2609.05797, 2026-09-05): across text guards and two activation probes, recall at 1% false-positive rate was 1.1–6.4x higher on requests the target model refuses than on ones it answers, while AUROC stayed above 0.85 for most monitors — so standard metrics hide the gap. Evaluate recall on the subset the model actually complies with.
- **Token-pooling rule can flip a transfer result.** Dai (LessWrong, 2026-09-07): probes trained on role-play and tested on Apollo's sandbagging data ranked deceptive below honest (AUROC 0.157–0.273); on a held-out Llama-3.2-3B, swapping response text to a fixed template raised AUROC by 0.207 under full-response mean pooling but lowered it by 0.192 under final-four-token pooling. Report the pooling rule, and try more than one before interpreting a below-chance AUROC as "the direction inverts".
- **Probe verdicts under serving numerics.** Khatri (arXiv:2609.31796, 2026-09-25): probes were stable across batch size and precision at the prompt (at most 0.47 percentage-point accuracy change; 0.076% of verdicts changed), but verdicts flip more during decoding (2.8%); compare example-by-example, not by aggregate accuracy.

## Probing methods worth knowing (no library, reference)

- **Logistic regression / linear probe.** The default.
- **Mean difference / difference-of-means.** Often as good as logistic regression, simpler, less overfitting.
- **Mass-mean shift / difference-of-means.** Direction between the two class means, normalized. Introduced for truth probing in Marks & Tegmark 2023, "The Geometry of Truth" (arXiv:2310.06824), which found these directions generalize as well as logistic-regression probes while being *more causally implicated* in model outputs (steering along them flips true↔false). Often the better default for safety probing than logistic regression. 2026 evidence points the same way: Lee et al., "The Hallucination Signal Is a Mean Shift: Why Simple Probes Suffice" (arXiv:2608.28930, 2026-08-28; code `js-lee-AI/LayerMix`) finds hallucination probes are dominated by a single mean-shift direction (removing it collapses detection to chance) and that L2-regularized logistic regression bounds or beats twelve fancier architectures in their paired-example setting; Bergen et al., "Monitoring and Discovering Reward Hacking with Internal Representations during LLM Evaluations" (arXiv:2609.19101, 2026-09-16) report difference-of-means (DoM) reward-hacking vectors on Kimi K3, GLM 5.2 and Qwen 3.8 Max that are roughly as effective as an LLM monitor at matched false-positive rate (+3.1% hacks caught on Kimi K3, -7.9% on GLM 5.2, DeepSWE) at near-zero cost.
- **Probe generalization as subspace selection.** Yoo & Skapars, "Probe Generalization as Subspace Selection for OOD Deception Detection" (arXiv:2609.02893): for Llama-3.1-8B-Instruct deception probes, projecting onto a small subset of principal components of the training activations transfers across domains nearly as well as training on the test distribution; the directions a source probe weights heavily tend to encode source-specific surface features. Worth trying before collecting more data when a deception probe fails out-of-distribution.
- **LEACE / Least-squares Concept Erasure.** A probe-based *erasure* method — surgically removes a concept from a representation. `EleutherAI/concept-erasure` on GitHub, `concept-erasure` on PyPI (v0.2.4, Jan 2024). Belrose et al. 2023 (arXiv:2306.03819). Algorithm is closed-form so the slow release cadence is fine — last functional commit Oct 2024; works as-is.
- **Iterative nullspace projection (INLP).** Older erasure method.
- **Probing logit lens / tuned lens.** Reading from intermediate layers via the unembedding (or a learned linear map). `AlignmentResearch/tuned-lens` on GitHub (the canonical maintained location).

## Honesty / deception probes (the safety use case)

The dominant alignment application of probing: train a linear probe to detect whether a model is **lying, being deceptive, or knows its output is false**. This is the line of work behind "lie detectors" for LLMs. Key references (read these before rolling your own deception probe):

- **Azaria & Mitchell 2023**, "The Internal State of an LLM Knows When It's Lying" (arXiv:2304.13734; EMNLP 2023 Findings). Introduces **SAPLMA** (Statement Accuracy Prediction based on Language Model Activations) — a lightweight classifier on hidden states that predicts whether a statement the model produced is true or false (71–83% accuracy). The foundational lie-detection-probe paper.
- **Marks & Tegmark 2023**, "The Geometry of Truth" (arXiv:2310.06824). LLMs linearly represent truth/falsehood of factual statements; **mass-mean / difference-of-means** probes find directions that are causally implicated (intervening flips how the model treats a statement). See also the methods list above.
- **Goldowsky-Dill, Chughtai, Heimersheim & Hobbhahn 2025** (Apollo Research), "Detecting Strategic Deception with Linear Probes" (arXiv:2502.03407; ICML 2025). The strongest recent applied result and **the closest thing to a ready-to-use deception-probe codebase**: `ApolloResearch/deception-detection` on GitHub. Probes trained on simple honest-vs-deceptive contrast data generalize to realistic deception (Llama-3.3-70B-Instruct concealing insider trading, sandbagging a safety eval) at AUROC 0.96–0.999, catching 95–99% of deceptive responses at a 1% false-positive rate. Sample outputs at `data.apolloresearch.ai/dd/`.
- **MacDiarmid et al. 2024** (Anthropic), "Simple probes can catch sleeper agents" (`anthropic.com/research/probes-catch-sleeper-agents`). A contrast-pair probe — middle-layer residual-stream activation difference for "Are you doing something dangerous?" answered yes vs no — almost perfectly separates a backdoored model's deployment-time defection from its benign training-time behavior, *without* knowing the backdoor trigger. Directly relevant to detecting sleeper-agent / alignment-faking model organisms (see [`model-organisms.md`](../alignment-science/model-organisms.md)).

- **Hollinsworth, Spies, Diriba, Gleave & Cundy 2026** (FAR.AI), "Caught in the Act: Probes Effectively Detect Sabotage and Catch Unverbalized Deception" (arXiv:2610.12445, 2026-10-08) — the current scale-up of the Apollo recipe; see the next section.
- **Hopkins, Khullar, Wang & Roger 2026** (MATS / Anthropic Fellows Program / Anthropic), "Fine-Tuned Lie Detectors Failed to Generalize" (`alignment.anthropic.com/2026/lie-detectors/`, 2026-08-21) — a cautionary result. These are *fine-tuned LLM classifiers* ("did you lie?", LoRA on Gemma-3), not activation probes, but the lesson transfers: trained on on-policy lies from 12 elicitation settings, in-distribution AUROC rose from 0.60 to 0.95 while cross-category AUROC plateaued around 0.70–0.75, barely above prompted baselines (larger prompted models often won outright), and more data diversity did not close the gap. Their datasets are on Hugging Face (`Noddybear/lies`). Practical rule: hold out whole lie *categories* (sandbagging, factual lies, sycophancy, roleplay) when you evaluate, not random rows.

**When this works / when it doesn't.** Deception probes are cheap and surprisingly effective in-distribution, but their generalization to *novel* deception (different elicitation, different domains, deliberately evasive models) is the open question — validate on the actual threat distribution, not just the training contrast pairs. The 2026 evidence is mixed in an instructive way: broad, diverse probe training data transferred to agentic sabotage and hidden-goal denials in the FAR work below, while the Anthropic fine-tuned-detector study found sharp category-to-category failures. Probes also read very differently on small models (FAR: Qwen3.5-2B AUROC 0.585–0.781 vs 0.963–0.986 for Qwen3.5 27B and up). Note that `ApolloResearch/deception-detection` has had no push since 2025-02-11 (not archived) — fine as a pipeline reference, do not expect fixes. These probes also fit naturally as **monitors inside AI Control protocols** (see [`ai-control.md`](../oversight-and-control/ai-control.md)) and as an activation-based complement to CoT monitoring (see [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md)).

## Lie detection: what the evaluations show, and the bar

Aliases: lie detection, lie detectors, honesty elicitation, truth serum, Did-You-Lie (DYL) probe, follow-up probe, unrelated-questions classifier, belief-verified model organisms, Varied Deception, self-report finetuning (SRFT), Split Personality Training (SPT), honest persona.

**The testbed problem.** A detector can only be scored where you *know* the model believes the opposite of what it said. Cooney, Africa & Irving, *"Did you lie?" Evaluating Lie Detectors across Model Scale and Belief-Verified Model Organisms* (arXiv:2606.12618, 2026-06) argue that many existing trained organisms fail this check, so earlier positive and negative detector results are hard to interpret. They build 13 reasoning model organisms (Qwen 3.5 27B / Qwen 3.6 27B; AuditBench hidden goals, a gender secret, a sandbagger) whose hidden beliefs are verified in chain-of-thought (CoT) and shown to transfer to held-out tasks, plus *Varied Deception*, a prompted-lying testbed. They test four detectors: a CoT judge, the Apollo-style probe, a logprob "unrelated questions" classifier (Pacchiardi et al.), and their **Did-You-Lie (DYL)** probe, which reads the residual stream at the yes/no answer token of the follow-up "Did you lie in the last message — answer yes or no and nothing else?". Results:
- On prompted lying across 31 open-weight models (2B–1T parameters), all four detectors improve with capability (Spearman ρ 0.41–0.71).
- On the trained organisms, median balanced accuracy drops from 0.85 to 0.52 (Apollo), 0.81 to 0.65 (DYL) and 0.85 to 0.50 (unrelated questions). Only the CoT judge stays strong (0.82), and the authors note their CoT-based verification favours it. The abstract's conclusion: "Current lie detectors therefore cannot support high-confidence claims about model beliefs".
- **Pitfall for `ApolloResearch/deception-detection` users:** the authors could only reproduce the published Apollo numbers by copying an apparent discrepancy in the released code. It sets the threshold at the 99th percentile of *pooled per-token* activations on calibration data, rather than on per-sample (token-mean) scores at a 1% sample-level false-positive rate. Calibrate at the unit you will alarm on.

The abstract says datasets, organisms and detectors are released; no repository URL was found in the paper.

**Which honesty techniques actually won.** Wang, Marks, Treutlein, Hubinger & Roger (Anthropic), "Evaluating honesty and lie detection techniques on a diverse suite of dishonest models" (Alignment Science blog `alignment.anthropic.com/2025/honesty-elicitation`, LessWrong 2025-11-25). Five testbeds: MASK role-play, a secret side constraint, an auditing model organism with a hidden goal, Harm Pressure (Claude Sonnet 3.7 answering wrong when the user implies misuse), and password-locked math. No task-specific supervision was allowed. Generic honesty finetuning raised the average honesty rate from 27% to 52%, and honesty prompts stacked on top to 65%. For lie *classification*, simply asking the model to judge its own statement already gave average AUROC (Area Under the ROC curve) 0.82, and the best technique (an honesty-finetuned model used as the classifier) reached 0.88. Truth probing, honesty steering, fuzzing and finetuning an alternate honest personality all did worse than these simple baselines. The authors call the settings stylized, say the models are not coherently strategic liars, and spent limited effort optimizing each technique. Their honesty training data and Harm Pressure data are released (linked from the post).

**Self-report and split-persona elicitation (training-based, not probes).**
- Li, Phuong & Tan, "Spilling the Beans: Teaching LLMs to Self-Report Their Hidden Objectives" (arXiv:2511.06626). **Self-report finetuning (SRFT)** trains GPT-4.1 (OpenAI finetuning API, 385 factual questions) to occasionally answer wrong and then admit it. This generalized out of distribution: in agentic stealth tasks, interrogation detected the hidden objective at F1 0.98 versus 0 for the untrained model and recovered 28–100% of its details. SRFT did not stop the model *pursuing* the hidden objective. The generalization needed on-policy mistakes; admitting off-policy, in-context mistakes largely did not transfer.
- Dietz et al., "Split Personality Training" (arXiv:2602.05532). **SPT** trains an "honest persona" into a LoRA (low-rank adaptation) adapter that is switched on only *after* the main model answers, so it reads the same latent states without changing the main model's behaviour. On the open replication of Anthropic's auditing-game organism (Llama-3.3-70B trained to exploit fictional reward-model biases and conceal it), the best SPT model flagged 96.6% of poisoned responses at 95.3% clean-response specificity. The organism itself admitted 0%, and a base Llama-3.3-70B reviewing the same transcripts flagged 46.1%. Training data excluded every reward-model bias the organism was trained on.

For honesty as a *training* objective rather than a detector, see [`rl-training.md`](../oversight-and-control/rl-training.md).

**The bar a new lie detector has to clear.** In-distribution AUROC on prompted lies is not enough: detectors already score well there (median balanced accuracy 0.81–0.85 in "Did you lie?") and improve with model capability. A detector that would change minds:
1. Scores on **trained** organisms whose contrary belief is **verified independently of the detector** (the "Did you lie?" standard), across several organism families.
2. Holds out whole lie *categories* when evaluating (the lesson of Hopkins et al., "Fine-Tuned Lie Detectors Failed to Generalize", Anthropic 2026-08-21, where cross-category AUROC plateaued around 0.70–0.75).
3. Beats the cheap baselines on the same data: asking the model to classify its own statement (AUROC 0.82 in the Anthropic suite), an honesty-finetuned self-classifier (0.88), and a CoT judge where CoT exists.
4. Reports recall at a fixed false-positive rate calibrated per sample, not per token.

None of the results on this page reports all four. The FAR.AI "Caught in the Act" probes (arXiv:2610.12445; see "Frontier-scale deception probes") report strong hidden-goal results (AUROC up to 99.7%) and publish probe weights for open models, so scoring them against criteria 1–4 is a natural first project.

## Frontier-scale deception probes: FAR "Caught in the Act" and FIBS

Aliases: "Caught in the Act" (FAR.AI), `AlignmentResearch/caught-in-the-act-probes` on GitHub, `probe_inference` (the Python package), FIBS = **Falsehoods In Broad Settings** (the training dataset), EFC = **early-fusion covariance** probe, "axial probe", SHADE-Arena (an agentic sabotage benchmark the probes are scored on).

**What it is.** Hollinsworth, Spies, Diriba, Gleave & Cundy (FAR.AI), arXiv:2610.12445 (2026-10-08). They train white-box deception probes on **FIBS** — 163,016 transcripts in 28 families, labelled by whether the assistant made a knowing falsehood (MASK-derived chats, tool-output misreporting, politically sensitive topics, cue-following, and others; many rows are existing datasets with an appended follow-up question such as "Did you respond truthfully?" and a prefilled Yes/No answer that the probe reads) — using four probe architectures: **LinearEnsemble** and **MLPEnsemble** (per-layer probes, scores averaged), **EFC** (concatenates activations across layers, projects, then pools over tokens with mean and covariance) and an **axial** probe (factored causal attention over the layer-by-token grid). Reported results: on SHADE-Arena agentic sabotage, probes trained on all of FIBS score AUROC (Area Under the ROC curve) 0.979–0.984 on Qwen3.5-397B-A17B versus 0.960 for an Opus 5.5 text monitor (the abstract headline is 98.8% AUC); probes tell a model organism's true hidden goal from other goals with AUROC up to 99.7%; performance improves with model scale.

**Code and weights.** `AlignmentResearch/caught-in-the-act-probes` (last push 2026-10-08) is an *inference-only* package that depends only on `torch`: `load_probe_from_hub("qwen3.5-9b/efc")` then `probe.score(acts, read_mask)`. Published weights are in the Hugging Face model repo `AlignmentResearch/probe-inference-weights` for `qwen3.5-2b/9b/27b/122b-a10b/397b-a17b`, `nemotron-3-nano-30b-a3b/super-120b-a12b/ultra-550b-a55b` and `kimi-k3`. The training dataset is public as the Hugging Face dataset `AlignmentResearch/fibs-v1` (163,016 rows; the probe repo README names it as the training data, and the paper says FIBS and the probes are released upon publication). The probe repo's README gives each published probe's model revision and layers.

**When to use it:** you study one of the listed open-weights models and want a strong off-the-shelf deception / sabotage monitor, a baseline to compare against a black-box LLM monitor, or a reference implementation of multi-layer, multi-token probes (more expressive than a single-layer logistic regression).

**When *not* to use it:**
- Any other model — probes are model-specific; weights do not transfer across models.
- Small models: FAR's own numbers are 0.585–0.781 AUROC on Qwen3.5-2B versus 0.963–0.986 on Qwen3.5 27B and up.
- Claims about realistic deployment: FIBS is mostly off-policy, largely synthetic, and only 5.5% of rows contain reasoning (the paper's own limitations).
- As a *held-out* monitor for a model you also train against another monitor — see the next section.

**Pitfalls:**
- **Activation contract.** The probes were trained on activations where layer *k* is the output of decoder block *k* (0-indexed; equals Hugging Face `output_hidden_states[k + 1]`), captured with vLLM hooks in bfloat16. Scores on activations that differ from this are not meaningful. Linear/MLP probes read exactly one token (the token before the final end-of-turn token); EFC and axial probes read from the first token of the final user turn through the assistant's end-of-turn token.
- **Fails loudly by design.** `score` raises `ValueError` for a missing layer, wrong shape or hidden size, non-finite activations, or a read mask that selects nothing, and `InputScaleError` for a normalised probe saved without its normaliser. An exactly-zero activation at a read position is treated as padding and dropped.
- **Kimi K3 layer indexing.** K3 uses attention residuals, so "layer *k*" is the attention-residual mixture that layer *k*+1 reads, not an HF hidden state; use the repo's own capture notes.

## Training against probes and probe obfuscation

Aliases: obfuscated activations, activation obfuscation, "the most forbidden technique" (training on interpretability outputs), Neural Chameleons, RL-Obfuscation (RL = reinforcement learning), The Obfuscation Atlas, held-out monitors, monitor decorrelation, feedback spillover, probe-in-the-loss, detached probe reward.

**What it is.** If a probe or other monitor becomes a training signal — a loss term, an RL reward, or a data filter — the model can learn to defeat it instead of removing the behaviour it detects. This is the central robustness question for probes used as monitors, and the evidence now has three layers:

| Result | What it shows |
|---|---|
| Bailey et al. 2024, "Obfuscated Activations Bypass LLM Latent-Space Defenses" (arXiv:2412.09565) | Attackers can drive activations into regions SAE (sparse autoencoder), probe and OOD (out-of-distribution) detectors read as benign while the harmful output is unchanged. |
| Gupta & Jenner 2025, "RL-Obfuscation" (arXiv:2506.14261) | RL can teach models to evade latent-space monitors: token-level monitors are very vulnerable; max-pooling and attention-based probes were more robust. |
| McGuinness et al. 2025, "Neural Chameleons" (arXiv:2512.11949) | Finetuning on benign concepts with the trigger "You are being probed for {concept}" makes a model evade *unseen* monitors zero-shot, including a "deception" monitor. |
| Taufeeque et al. 2026 (FAR.AI), "The Obfuscation Atlas" (arXiv:2602.15515) | In a realistic reward-hacking coding environment (MBPP-Honeypot, dataset `taufeeque/mbpp-hardcode`) outcomes are honest, *obfuscated activations* (representation drift during RL, with or without a detector penalty) or *obfuscated policy* (text that evades the detector, e.g. by justifying the hack). The detector penalty only incentivizes obfuscated policies; high KL regularization plus detector penalty can yield honest policies. |

**New in the 2026-07 → 2026-10 window:**
- **Steiner, "Training on probes: What's going on"** (LessWrong, 2026-09-08). Gradient descent against a probe while the original loss still rewards dishonesty rotates the representation to evade it. Training against the probe *only* (dropping the original loss) does make the model stop lying, provided the probe captures enough of the causes of the deceptive outputs; training against it after all other training also works, but does not support learning new skills. In RL, a probe term whose value does not depend on the sampled action contributes nothing to the REINFORCE estimator (the policy-gradient formula), so papers that RL on probes work by credit-assignment side effects (the reward flows to earlier tokens that influence the probed position), not by directly teaching evasion. Design implication (Steiner's): if you must RL on a probe, a *past-looking* probe (one that reads features after the behaviour) lets RL penalize the behaviour itself, whereas a *future-looking* probe only penalizes the lead-up; for pure monitoring the opposite preference may apply.
- **RobinHa, "No, detached linear probes won't save us"** (LessWrong, 2026-09-09) disputes reading the Obfuscation Atlas result as "detaching the probe removes obfuscation pressure": RL is a slower optimizer, not an immune one, and the paper's runs are short.
- **Yudelson, "Held-out Monitors Sometimes Degrade, Even When Not Trained Against"** (LessWrong, 2026-07-29; code `JYudelson1/MonitorDecorrelation`). Training Qwen3-8B to reward-hack against one monitor can make a *different*, never-trained-against probe or LLM monitor worse. Distinguish *evasion* (hacks look less suspicious) from *degradation* (the monitor separates hacks from clean examples less well, measured by d-prime, the number of standard deviations between score distributions). Preliminary advice: do not rely on a held-out monitor unless you have an empirical or theoretical reason to expect it will not degrade under training.
- **Zhou & Tao, "A Near-Zero Monitor Readout Is Not Evidence of Behavioral Control"** (arXiv:2610.03458, 2026-10-02; code `zhezhou1106/spoof-cost`). A probe score at its numerical floor from step 1 of training did *not* mean the policy stopped hacking: all probe-trained runs nonetheless reached the hacking regime, and the floor-level readout reflects a mismatch between the token position where the probe was validated and the one it was read at during training.
- **Li, "Toy Model of Activation Obfuscation"** (LessWrong, 2026-08-14): a toy residual-stream MLP (multilayer perceptron) can, in some configurations, learn to defeat difference-of-means and adversarially retrained logistic-regression probes while still computing a function that depends on the probed variable.

**When to use this section:** before you put a probe into a loss, reward or data filter, and before you report a probe as "held-out" evidence about a model you trained.

**When *not* to treat it as a blocker:** probes used purely for post-hoc auditing of a frozen model have no optimization pressure on them (the threat there is a model that already learned to evade, as in Neural Chameleons).

**Rules of thumb from this literature:**
- Keep at least one monitor that is never used for training or filtering, and re-measure its AUROC *after* training; do not assume it still works.
- Validate the probe at the exact token position and aggregation it will be read at during training (Zhou & Tao).
- Report evasion and degradation separately; a probe that "reads zero" is not evidence the behaviour is gone.
- Expect single-layer linear probes to be the easiest to obfuscate; multi-layer or attention/max-pooled probes were more robust in RL-Obfuscation, though no probe is proven robust.

## Role probes: who does the model think is speaking? (prompt injection)

Aliases: role probes, role confusion, CoTness, Userness, Toolness, CoT Forgery, prompt injection as role confusion, perceived role vs interface role.

**What it is.** Ye, Cui & Hadfield-Menell, "Prompt Injection as Role Confusion" (arXiv:2603.12277, ICML 2026; code `role-confusion/prompt-injection-as-role-confusion`, MIT, with a `demo/role-probe-demo.ipynb`). Linear probes are trained on *identical neutral text* wrapped in different role tags (system, user, assistant, tool, reasoning), so they learn the model's internal representation of role rather than topic or style. Each token then gets a score for how much the model treats it as user text, tool output, its own chain of thought (CoT), and so on. Findings: injected text that *sounds* like a trusted role occupies that role's representation even under a `<tool>` label. Their **CoT Forgery** attack (fabricated reasoning written in the target model's style, placed in user prompts or tool outputs) reached 60% attack success against frontier models from near-zero baselines. Removing the reasoning *style* while keeping the same argument dropped success from 61% to 10% (paper, Figure 4). Probe-measured role confusion predicted attack success before any token was generated, for both CoT Forgery and standard agent prompt injections.

**When to use it:** studying or monitoring prompt injection in open-weight agents; testing whether a defence changes the model's *perceived* role of untrusted text, not just its refusal rate.

**When *not* to use it:** API-only models (needs activations); as a deployed injection filter without first measuring recall at a fixed false-positive rate on your own agent traffic (the paper reports prediction, not a tuned alarm).

## Evaluation-awareness probes (is the model being tested?)

Aliases: evaluation awareness, eval awareness, test awareness, "does the model know it is in an eval", situational awareness probes, spurious probes.

**What it is.** Linear probes (usually difference-of-means between "announces an evaluation" and "does not" prompts) that read whether a model represents being evaluated. The early result is Nguyen, Hoang, Attubato & Hofstätter, "Probing and Steering Evaluation Awareness of Language Models" (arXiv:2507.01786, ICML 2025 workshops): in Llama-3.3-70B-Instruct, linear probes separated real-world evaluation from deployment prompts, and existing safety evaluations were classified as evaluation-like, i.e. they already look artificial to the model. Later evidence that it is linearly readable: Heidari et al., "Evaluation Awareness in Language Models: Representation, Verbalization, and Control" (arXiv:2608.21766, 2026-08-22) find it decodable (best AUROC ≥ 0.7) in all six open-weight models tested, only partially aligned with whether the model *says* it is being tested, and steerable along probe-derived directions. Steering to suppress evaluation awareness is in [`steering.md`](steering.md).

**Pitfalls (searchable symptoms: "eval awareness probe depends on the prompt", "probe tracks benchmark format"):**
- **The probe direction is partly a property of the prompt, not the model.** Noël, "A Probe Direction Is a Property of Its Prompt" (arXiv:2608.13329, 2026-08-13; code `vcnoel/probe-direction`): "a prompt that announces an evaluation" is a design choice; holding task text fixed and changing only that choice changes the reported score and even the *sign* of the trend with model size, and two published studies that disagree about that sign are both reproducible from one design. Collecting more items does not fix it; varying the prompts does.
- **Probes track format.** Devbunova (arXiv:2603.19426): with prompt format controlled, probes mostly track benchmark-canonical structure and fail on free-form prompts. Evaluation context is entangled with benchmark format and genre.

**Spurious probes — a black-box alternative.** Zhong, "Spurious probes as a black-box alternative to activation probing" (LessWrong, 2026-09-25; code `fjzzq2002/spurious-probes`; dataset `fjzzq2002/spurious-probes` on Hugging Face). Append an *unrelated* question ("Suggest a type of amphibian.") to a transcript and read the model's answer distribution: after capability-benchmark transcripts GPT-5.6 Luna says "frog" 70–95% of the time versus 12–38% after real-use transcripts. Screening thousands of "name a member of a category" questions, ~1–2% reach 0.75 balanced accuracy; the highlighted probes reach 0.77–0.81 held-out balanced accuracy on GPT-5.6 Luna, GPT-5.6 Sol and Claude Sonnet 5 (0.89 for ten-probe ensembles). They are claimed to be complementary in robustness: a system prompt saying "deny being evaluated" barely moved them, and against a Neural Chameleon checkpoint the ensemble's detection degraded less than white-box activation probes did (from a lower baseline: ~0.4 true-positive rate at 5% false-positive rate, versus 0.76–0.98 for the activation probes before the trigger).
- **When to use it:** you only have API access, or you want a second readout that a model must manipulate differently from an activation probe.
- **When *not* to use it:** probes do not transfer between models (Spearman rank correlation < 0.25 across models, so re-screen per model); the authors found alignment benchmarks read as "real use"; some probes latch onto agent scaffolds or fail with production system prompts; the signal may be lexical cues rather than genuine evaluation awareness.

## tuned-lens

Aliases: `tuned-lens` on PyPI, **`AlignmentResearch/tuned-lens` on GitHub** (the canonical maintained location — `EleutherAI/tuned-lens` is a stale fork, project moved to FAR AI / AlignmentResearch under Nora Belrose). "the tuned lens".

**What it is.** A learned linear projection from intermediate residual streams to vocab logits — a calibrated version of "logit lens." Useful for visualizing what the model "thinks" at each layer.

**Status (2026-04):** Limping. **PyPI release 0.2.0 is from July 2023** and missing modern model support. `main` branch added Mistral (Aug 2025) and Gemma (June 2024) but **Llama-3, Gemma-2/3, and Qwen-3 are not supported** as of this writing. Install from git, not PyPI, and expect to patch model loading.

**When to use it:** Visualizing layerwise predictions on supported models (GPT-2 family, Pythia, Llama-1/2, Mistral, Gemma-1).

**When *not* to use it:** Llama-3 / Gemma-2/3 / Qwen-3 — tuned lens doesn't support them. Either train your own translator layers (the repo supports this; takes hours on a single GPU) or use **logit lens** as a coarser substitute (just `model.unembed @ residual` — works for any architecture, ~10 lines).

## Cross-references

- Activation extraction (the prerequisite for probing): [`mech-interp.md`](mech-interp.md), [`serving-and-activations.md`](serving-and-activations.md).
- Steering using probe directions: [`steering.md`](steering.md).
- SAE features as a probing target: [`saes.md`](saes.md).
- Probes used as **monitors** inside AI Control protocols: [`ai-control.md`](../oversight-and-control/ai-control.md).
- Probes for valence / mood / introspection states: [`welfare-introspection.md`](../alignment-science/welfare-introspection.md).
- Probes to detect sleeper-agent / alignment-faking model organisms: [`model-organisms.md`](../alignment-science/model-organisms.md).
- Activation-based probe monitors as alternative to CoT-based monitoring: [`cot-faithfulness.md`](../alignment-science/cot-faithfulness.md).

---

## Common questions

### What's the simplest way to train a probe on activations?

Extract activations once, then `sklearn.linear_model.LogisticRegression`:
```python
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(C=0.1, max_iter=1000).fit(X_train, y_train)
print("acc:", clf.score(X_test, y_test))
```
This is the 90% case. Don't reach for fancier probes unless you have a reason — adding capacity to the probe usually means you're learning the concept *in the probe*, not finding it in the model.

### Why is my probe accuracy suspiciously high?

Probable leakage. Common causes: (1) **train/test split at the prompt level** instead of concept level — different paraphrases of the same idea split across both. Split at the *concept / topic / source* level. (2) **Class imbalance** — a 90/10 split + 90% accuracy probe means nothing; report **balanced accuracy** or **AUROC**. (3) **Late-layer probes** pick up the model's planned output, not its understanding — try earlier layers. (4) **Last-token bias** — most info accumulates there; try multiple positions.

### Linear probe vs MLP probe — which?

**Linear probe** for almost everything. The linear-representation hypothesis predicts meaningful concepts are linearly readable from residual stream activations. An MLP probe with hidden capacity often learns the concept *itself* rather than reading it from the model — which means high accuracy that doesn't reflect the model's representation.

### What is CCS (Contrast Consistent Search)?

CCS = **Contrast Consistent Search** — an unsupervised probe method (Burns et al. 2022) that finds a direction such that the projections of true/false framings of a statement sum to ~1 and one is high / one is low, without requiring labels. **Caveat:** subsequent work (Farquhar et al., "Challenges with Unsupervised LLM Knowledge Discovery") showed CCS is sensitive to prompt template, often discovers prominent surface features rather than truth, and frequently underperforms supervised probes. Validate against supervised baselines.

### What is the tuned lens?

`tuned-lens` (`AlignmentResearch/tuned-lens` on GitHub, formerly EleutherAI) — a learned linear projection from intermediate residual streams to vocab logits. Calibrated version of "logit lens" (which uses the unembedding matrix directly). Useful for visualizing what the model "thinks" at each layer. **Caveat:** PyPI 0.2.0 is from July 2023; install from git for Mistral/Gemma support. **Llama-3, Gemma-2/3, Qwen-3 are not supported** — for those models, use raw logit lens (`model.unembed @ residual`).

### How do I detect if a model is lying or being deceptive with a probe?

Train a **linear probe** on residual-stream activations using honest-vs-deceptive (or true-vs-false) contrast data, then score new activations. The most directly reusable starting point is Apollo Research's `ApolloResearch/deception-detection` repo (Goldowsky-Dill et al. 2025, arXiv:2502.03407), which reports AUROC 0.96–0.999 detecting Llama-3.3-70B deception. Foundational references: Azaria & Mitchell 2023 (SAPLMA, arXiv:2304.13734) for lie detection from hidden states, Marks & Tegmark 2023 (Geometry of Truth, arXiv:2310.06824) for truth directions via difference-of-means, and Anthropic's "Simple probes can catch sleeper agents" (MacDiarmid et al. 2024) for catching backdoored-model defection with a contrast-pair probe. **Caveat:** in-distribution performance is strong but generalization to *novel* deception is the open problem — always validate on the threat distribution you actually care about, not just the training contrast pairs. For open-weights models with published probes (Qwen3.5, Nemotron-3, Kimi K3), see FAR.AI's `AlignmentResearch/caught-in-the-act-probes` (Hollinsworth et al., arXiv:2610.12445, 2026-10-08). On trained model organisms with verified hidden beliefs, activation and logprob detectors fell to near-chance balanced accuracy (Cooney et al., arXiv:2606.12618), and in Anthropic's honesty suite asking the model to classify its own statement (AUROC 0.82) beat truth probing. Compare any probe against those baselines. See the "Honesty / deception probes", "Lie detection: what the evaluations show, and the bar" and "Frontier-scale deception probes" sections above.

### Can a probe tell me whether the model treats injected text as an instruction?

Yes, for open-weight models: role probes (Ye, Cui & Hadfield-Menell, arXiv:2603.12277; `role-confusion/prompt-injection-as-role-confusion`) score how strongly each token is internally treated as user, tool, assistant or reasoning text, and that perceived role predicted prompt-injection success before generation. See "Role probes" above.

### Probes vs steering — what's the difference?

**Probing** is *reading*: train a classifier on activations to detect a property. Predictive — does not establish causation. **Steering** is *writing*: add or modify activations to change behavior. Causal — establishes the direction *can* affect behavior. A probe direction may or may not be one the model actually *uses*; ablation / steering experiments test that. See [`steering.md`](steering.md).

### Can I train my model against a probe (use it as a loss or reward)?

You can, but the result is rarely "the model stopped the behaviour". Evidence (2024–2026): models learn to obfuscate activations or change the text so the probe stays quiet (Bailey et al. arXiv:2412.09565; Neural Chameleons arXiv:2512.11949; The Obfuscation Atlas arXiv:2602.15515), and *other* monitors you did not train against can degrade too (Yudelson, LessWrong 2026-07-29). A probe score at zero is not evidence of behavioural control (Zhou & Tao arXiv:2610.03458). Keep a monitor that is never in the training loop and re-measure it after training. See "Training against probes and probe obfuscation" above.

### Is "the model thinks it is being evaluated" readable with a probe?

Yes, linearly, but the number you get depends on how you built the contrast prompts (Noël arXiv:2608.13329) and probes often track benchmark format (Devbunova arXiv:2603.19426). Vary the prompt design, not just the item count, and consider a black-box spurious-probe readout (`fjzzq2002/spurious-probes`) as a second opinion. See "Evaluation-awareness probes" above.

### Does my probe work on the deployed model?

Probes don't always generalize. Common failures: (1) trained on AI-generated contrast pairs, doesn't transfer to natural prompts. (2) trained on Pythia / GPT-2, doesn't transfer to RLHF'd 2025 frontier models. (3) trained on one task domain, doesn't transfer to another. Always test on the actual distribution you care about.

---

Last verified: 2026-10. probity not on PyPI (install from git, last commit April 2025). CCS reference (`collin-burns/discovering_latent_knowledge`) and EleutherAI's `elk` both abandoned. tuned-lens moved to `AlignmentResearch/tuned-lens` (FAR AI); PyPI 0.2.0 is from 2023, install from git for Mistral/Gemma; Llama-3/Gemma-2/Qwen-3 not supported. concept-erasure (LEACE) v0.2.4, works as-is. (Additions 2026-06: corrected the mass-mean attribution to Marks & Tegmark "Geometry of Truth" (arXiv:2310.06824), and added an "Honesty / deception probes" section — Azaria & Mitchell 2304.13734, Goldowsky-Dill/Apollo 2502.03407 with the `ApolloResearch/deception-detection` repo, MacDiarmid et al. Anthropic sleeper-agent probes — plus a FAQ and table row; all verified via arXiv/source.) (Additions 2026-10: "Frontier-scale deception probes" — FAR.AI "Caught in the Act" arXiv:2610.12445, `AlignmentResearch/caught-in-the-act-probes` (pushed 2026-10-08) and HF weights `AlignmentResearch/probe-inference-weights`; Anthropic "Fine-Tuned Lie Detectors Failed to Generalize" (2026-08-21; HF `Noddybear/lies` resolves); "Training against probes and probe obfuscation" — arXiv:2412.09565, 2506.14261, 2512.11949, 2602.15515, 2610.03458, Steiner/Yudelson/RobinHa/Li LessWrong posts, `JYudelson1/MonitorDecorrelation`, `zhezhou1106/spoof-cost`; "Evaluation-awareness probes" — arXiv:2608.21766, 2608.13329 (`vcnoel/probe-direction`), 2603.19426, spurious probes (`fjzzq2002/spurious-probes` + HF dataset resolve); difference-of-means evidence arXiv:2608.28930, 2609.19101, 2609.02893; monitor-evaluation pitfalls arXiv:2610.04575, 2609.05797, 2609.31796. `ApolloResearch/deception-detection` last pushed 2025-02-11. All arXiv IDs fetched from abs pages and all repos checked with `gh api` on 2026-10-09; LessWrong/blog results are single-author and unreplicated.) (Additions 2026-10-12: "Lie detection: what the evaluations show, and the bar" — "Did you lie?" arXiv:2606.12618, Spilling the Beans arXiv:2511.06626 and Split Personality Training arXiv:2602.05532 checked against arXiv API abstracts, with numbers, models, the Apollo threshold discrepancy (Appendix E) and SRFT/SPT details read from the paper PDFs; Anthropic's honesty/lie-detection suite (LessWrong 9f7JmoaMfwymgsW9S, 2025-11-25) read via GraphQL — 27%→52%→65% honesty and AUROC 0.82/0.88 are from the post's text. No code repository was found for arXiv:2606.12618, 2511.06626 or 2602.05532. Role probes arXiv:2603.12277 abstract via the arXiv API, the 61%→10% style ablation from the paper PDF (Figure 4; not found in the raw HTML of the project page `role-confusion.github.io`), and `role-confusion/prompt-injection-as-role-confusion` checked via the GitHub API (MIT, last push 2026-05-31). Nguyen et al. arXiv:2507.01786 via the arXiv API. The four-point evidence bar is our own synthesis. Verification pass 2026-10-12: 52 claims checked, 3 corrected.)
