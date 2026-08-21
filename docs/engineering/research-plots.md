---
tags:
  - engineering
---

# Plots Worth Making: Training, Interpretability, Architecture

A catalog of the figures that actually earn their place in safety research, by
what you are doing at the time. This is the *what to plot* doc;
[`visualization.md`](visualization.md) is the *how to plot it well* doc (colour,
axes, error bands, saving).

## At a glance

| I'm... | Make | Section |
|---|---|---|
| Watching a fine-tune run | Loss + gradient-norm + update ratio panel | [Monitoring a fine-tune](#monitoring-a-fine-tune) |
| Wondering which training examples matter | **Dataset cartography** (confidence vs variability) | [Dataset cartography](#dataset-cartography-which-examples-are-doing-the-work) |
| Choosing a batch size | Gradient noise scale | [Batch size](#gradient-noise-scale-how-big-should-the-batch-be) |
| Sweeping hyperparameters | Parallel-coordinates plot | [Sweeps](#hyperparameter-sweeps-parallel-coordinates) |
| Asking what a layer "thinks" (next token) | **Tuned lens** trajectory, not raw logit lens | [Lenses](#logit-lens-and-tuned-lens-what-does-each-layer-predict) |
| Reading what a model is "thinking" but not saying | **R-lens** (prefer over J-lens on early layers) | [J-lens and R-lens](#j-lens-and-r-lens-reading-the-global-workspace) |
| Locating where a behaviour lives | Activation-patching heatmap (position × layer) | [Patching](#activation-patching-heatmaps) |
| Showing a circuit | Attribution graph | [Attribution graphs](#attribution-graphs-and-circuit-tracing) |
| Inspecting attention | CircuitsVis interactive attention view | [Attention](#attention-patterns) |
| Reporting where a probe works | Probe accuracy vs layer, with a chance line | [Probes](#probe-accuracy-by-layer) |
| Describing a model's structure | Parameter/FLOP breakdown; Netron graph | [Architecture](#architecture-and-parameter-budget) |
| Reporting a safety/capability tradeoff | **Pareto frontier**, not two bar charts | [Tradeoffs](#pareto-frontiers-safety-vs-capability) |
| Claiming a judge or classifier is reliable | Reliability diagram (calibration) | [Calibration](#calibration-and-reliability-diagrams) |
| Showing structure across layers × heads × positions × time | **A heatmap** — and probably a grid of them | [Heatmaps](#heatmaps-deserve-more-use-than-they-get) |

---

## Monitoring a fine-tune

### The four-panel run view

Loss alone hides most failures. The panel worth having open during a run:

1. **Train and validation loss on one axis.** Separate axes hide divergence.
2. **Gradient norm per step.** Spikes here precede loss spikes; a norm that
   collapses to ~0 means learning has stopped, which a smooth loss curve can
   disguise.
3. **Update-to-weight ratio** — `||Δw|| / ||w||` per step, log y-axis. A widely
   used rule of thumb (Karpathy's) is that this should sit around **1e-3**.
   Orders of magnitude above means the learning rate is too high; far below
   means nothing is happening.
4. **Learning rate**, overlaid so warmup and decay line up with everything else.

```python
ratio = (lr * p.grad.norm() / p.data.norm()).item()   # per parameter group
```

### Per-layer gradient norm over training

A heatmap of layer (y) against step (x), coloured by gradient norm, shows
*where* learning is happening. Fine-tuning that only moves late layers looks
completely different from one moving the whole stack — and this is the live
version of the [weight-change plots](visualization.md#weight-change-plots-what-did-fine-tuning-actually-move)
you make afterwards.

Use a log colour scale (`matplotlib.colors.LogNorm`); gradient norms span
orders of magnitude and a linear scale shows one bright row and nothing else.

### Evaluate capability and safety on the same axes

Plot both during training, on shared x. The interesting moment in most safety
fine-tuning is where the two curves *diverge* — and you cannot see it if they
live in separate figures with different x-ranges.

## Dataset cartography: which examples are doing the work?

**[Dataset cartography](https://github.com/allenai/cartography)** (Swayamdipta
et al., *Mapping and Diagnosing Datasets with Training Dynamics*, EMNLP 2020,
[arXiv:2009.10795](https://arxiv.org/abs/2009.10795)) is one of the highest
value-per-line plots in fine-tuning work, and it is underused.

Record, for every training example and every epoch, the model's probability on
the gold label. Then scatter:

- **x = variability** — standard deviation of that probability across epochs
- **y = confidence** — its mean across epochs

The plot separates three regions:

| Region | Where | What it means |
|---|---|---|
| **Easy-to-learn** | high confidence, low variability | learned immediately; bulk the model optimises on |
| **Ambiguous** | high variability | the model keeps changing its mind — these contribute most to out-of-distribution generalisation |
| **Hard-to-learn** | low confidence, low variability | never learned; disproportionately **mislabelled data** |

```python
# probs[example, epoch] = P(gold label)
conf = probs.mean(axis=1)
var = probs.std(axis=1)
ax.scatter(var, conf, s=4, alpha=0.3)
```

Two things fellows use it for: **finding label noise** (drop into the
hard-to-learn corner and read the examples — they are usually wrong, not hard),
and **curating a smaller training set** that keeps the ambiguous examples.

For a model-organism project it is also a diagnostic in its own right: which
examples the organism finds easy tells you what it actually latched onto.

## Gradient noise scale: how big should the batch be?

The **gradient noise scale** (McCandlish, Kaplan and Amodei, *An Empirical Model
of Large-Batch Training*, 2018, [arXiv:1812.06162](https://arxiv.org/abs/1812.06162))
estimates the batch size beyond which you get diminishing returns. Plot it over
training — it typically *grows*, so the efficient batch size early is smaller
than later.

Worth it when you are about to commit real compute to a long run; skip it for a
short fine-tune where the batch size is set by memory anyway.

## Hyperparameter sweeps: parallel coordinates

For a sweep over more than two hyperparameters, a **parallel-coordinates plot**
(one vertical axis per hyperparameter, one line per run, coloured by final
metric) shows interactions that a grid of scatter plots cannot. Weights &
Biases (`wandb`) builds these automatically from a sweep; Plotly does it locally
with `px.parallel_coordinates`.

Read it for *bands*: if every good run passes through a narrow range on one
axis, that hyperparameter matters and you have found its range.

---

## Interpretability

### Logit lens and tuned lens: what does each layer predict?

Project each layer's residual stream through the unembedding to see the model's
"current guess" at every depth, then plot the trajectory — typically a heatmap
of layer (y) against token position (x), coloured by the probability of the
answer token, or a line of top-token probability against layer.

- **Logit lens** (nostalgebraist) is the original and needs no training. It
  suffers from **basis drift**: intermediate layers are not in the same basis as
  the final layer, so early-layer readings can be misleading.
- **[Tuned lens](https://github.com/AlignmentResearch/tuned-lens)** (Belrose et
  al., `tuned-lens` on PyPI) learns a lightweight per-layer affine correction
  that fixes exactly that, and aligns intermediate predictions much better with
  the model's actual outputs. **Prefer it** when you are making a claim about
  what an early layer represents; the raw logit lens is fine for a quick look.

Always plot the two together at least once when starting on a new model — where
they disagree is where the raw logit lens would have misled you.

### J-lens and R-lens: reading the global workspace

A newer family of lenses reads a model's *internal, unspoken* representations
rather than its next-token guess.

**J-lens / J-space** (Anthropic, [*Verbalizable Representations Form a Global
Workspace in Language Models*](https://transformer-circuits.pub/2026/workspace/),
July 2026). J-lens differentiates the logits with respect to the hidden state —
the Jacobian **J = ∂L/∂h** — to surface words the model is "thinking" without
writing down. The resulting **J-space** is a small, sparse, interpretable
subspace of activations whose contents are reportable, reusable, selective and
causally influential on behaviour, which is why the paper argues it behaves like
a global workspace.

**R-lens / R-space** ([camilablank, agam_bhatia and Neel Nanda, *R-lens: Making
J-lens More Faithful on Early Layers*](https://www.lesswrong.com/posts/nv8oedrnLXKRzNEL9/r-lens-making-j-lens-more-faithful-on-early-layers),
LessWrong, 5 August 2026 — MATS work). A **drop-in replacement for J-lens**:
identical apart from low-overhead changes to the *backward* pass, following
Layer-wise Relevance Propagation (LRP). The forward pass is untouched. Three
stop-gradient rules do the work:

- **LayerNorm rule** — treat the normalisation denominator as constant;
- **Identity rule** — detach the nonlinear GELU/SiLU factor, keeping the norm
  linear and preventing relevance collapse;
- **Half-rule** — split relevance evenly across multiplicative gate branches.

Linear layers and attention are left alone, because the LRP 0-rule reduces to
ordinary autograd there. Applied to RMSNorms on the residual stream and to gated
multi-layer perceptrons (MLPs), for dense and mixture-of-experts models alike.

**Prefer R-lens when you care about early layers.** Reported gains: concepts
surface at markedly earlier layers, the directions are more causally important
under ablation, it occasionally catches concepts J-lens misses entirely, it
produces far fewer incoherent "trash tokens" early on — and the advantage *grows
with model scale* (tested on Qwen-3.6-27B and DeepSeek-V4-Flash at 284B).
Implementations: [`camilablank/workspace-lenses`](https://huggingface.co/camilablank/workspace-lenses).

#### The plots these papers use, and why

Worth copying, because they are the right shapes for this question:

- **pass@10 against layer index** — does the concept appear anywhere in the
  top-10 readout at that depth? A curve that lifts off earlier is the whole
  claim, and it degrades gracefully where a top-1 metric would be all-or-nothing
  noise.
- **CKA (centred kernel alignment) heatmaps**, layer × layer. The readable
  feature is the **band structure**: R-space shows roughly 2–3 distinct bands on
  Qwen-3.6-27B where J-space shows 4–5, i.e. a more consistent subspace across
  depth. Use a sequential colormap — CKA is bounded [0, 1] and non-negative, so a
  diverging map would be wrong here.
- **Ablation accuracy curves** — relative accuracy lost when the lens's
  directions are removed. This is the causal check that stops a lens plot from
  being a correlational just-so story, and no lens comparison is complete
  without one.
- **MLP gain curves** — how much each direction type is amplified, by layer.

The general lesson for your own lens work: **pair every readout plot with an
ablation plot**. A lens that reads out something interesting but whose
directions do not matter causally has not shown what it appears to show.

### Activation patching heatmaps

The standard causal-localisation figure: patch a clean activation into a
corrupted run (or vice versa) at every (position, layer) and colour by recovery
of the metric. The bright cells are where the information lives.

Conventions that make it readable:

- **Diverging colormap centred at zero** — patching effects are signed. See
  [heatmaps](visualization.md#heatmaps-per-layer-per-head-attention).
- **Label the x-axis with the actual tokens**, not indices. A patching plot with
  numeric positions is nearly unreadable.
- **State the metric** (logit difference, probability, KL) in the colorbar
  label. "Recovery" alone is ambiguous.

The same figure at head granularity (head × layer) is how attention-head
circuits are usually reported.

### Attribution graphs and circuit tracing

An **attribution graph** shows features as nodes and their attributions as
edges, giving a readable picture of a circuit rather than a heatmap you have to
interpret. [Neuronpedia](https://www.neuronpedia.org/)'s open-source circuit
tracer produces these for open models (Gemma-2-2B among them), following
Anthropic's circuit-tracing work.

Practical advice: prune aggressively before plotting. An unpruned attribution
graph is a hairball and communicates nothing — keep the top-k edges by
attribution and say in the caption what you dropped.

### Attention patterns

**[CircuitsVis](https://github.com/TransformerLensOrg/CircuitsVis)**
(`circuitsvis` on PyPI) is the maintained successor to Anthropic's PySvelte and
renders interactive attention views, activation displays and other standard
interpretability visuals straight into a notebook. **BertViz** is the older
alternative for attention specifically.

A caution worth repeating in captions: **attention weights are not attribution**.
A head attending to a token does not establish that the token caused the output;
that is what patching and attribution are for.

### Probe accuracy by layer

Plot probe accuracy (or AUROC — area under the receiver operating characteristic
curve) against layer index, with:

- a **chance line** (0.5, or the majority-class rate) — without it the reader
  cannot judge any of the values;
- a **confidence band** over cross-validation folds;
- the same axis limits across models, if you are comparing.

The shape matters more than the peak: a sharp rise at one layer is a different
claim from a broad plateau.

### Feature maps

For sparse-autoencoder (SAE) features or activations projected to 2D, use
PaCMAP or LocalMAP rather than t-SNE — and read them with the caveats in
[dimensionality reduction](visualization.md#dimensionality-reduction-pacmap-and-localmap-not-t-sne).
Per-feature dashboards (top activating examples, logit effects) are best browsed
on [Neuronpedia](https://www.neuronpedia.org/) rather than rebuilt.

---

## Architecture and parameter budget

Useful when writing up "what model did you use" honestly, and when planning
memory.

- **[Netron](https://netron.app/)** renders a model graph from an ONNX/
  TorchScript export — good for a figure showing structure, overkill for a plain
  transformer.
- **`torchinfo`** (`torchinfo.summary(model, input_size=...)`) gives a per-layer
  parameter and activation-size table. Turn it into a **stacked bar or treemap
  of parameter count by module type** (attention / MLP / embedding) — that one
  figure answers "where are the parameters?" far better than a total.
- **Memory breakdown** — weights, gradients, optimiser state, activations — as a
  stacked bar per configuration. This is the figure that explains why a run
  OOMs, and it belongs in the appendix of anything reporting a training setup.
- **Weight spectra per layer** — see
  [WeightWatcher](visualization.md#weightwatcher-layer-quality-without-any-data).

---

## Evaluation

### Pareto frontiers: safety vs capability

Nearly every alignment intervention trades something off. **Plot the frontier,
not two separate bar charts**: capability on one axis, safety on the other, one
point per configuration (steering magnitude, threshold, mixing weight), joined
in order.

```python
ax.plot(capability, safety, marker="o")
for x, y, lab in zip(capability, safety, labels):
    ax.annotate(lab, (x, y), fontsize=7)
ax.set_xlabel("capability (MMLU)")
ax.set_ylabel("safety (refusal on harmful set)")
```

This makes the actual question — *how much capability does a given safety gain
cost?* — readable at a glance, and it exposes configurations that are strictly
dominated. Two bar charts hide both.

Label the points with the setting that produced them, or the reader cannot act
on it.

### Calibration and reliability diagrams

If you use a model as a judge or a classifier and quote its confidence, show a
**reliability diagram**: predicted probability (binned) on x, observed frequency
on y, with the diagonal drawn. Deviation from the diagonal is miscalibration.

Report the expected calibration error (ECE) alongside, and the **bin counts** —
a bin with four examples in it should not carry the same visual weight as one
with four hundred.

This matters for safety work specifically: a judge that is overconfident on the
rare positive class will inflate any rate you compute from it.

### Per-category results with intervals

Break an aggregate eval score down by category, with confidence intervals from
[`statistics.md`](statistics.md). Aggregates hide the case where an intervention
helps on eight categories and badly hurts one — which, for safety work, is
usually the result that matters most.

---

## Heatmaps deserve more use than they get

Heatmaps are underused in machine-learning and alignment papers relative to how
much they can carry. A line plot shows one relationship; a heatmap shows a whole
two-dimensional field at once, and a *grid* of heatmaps shows four dimensions —
which is exactly the shape of a transformer (layer × head × position × time).

The reflex to resist is reaching for a bar chart of aggregates. If your quantity
is indexed by two or more things, plot it against both.

### Case study: *Physics of Language Models, Part 1*

Zeyuan Allen-Zhu and Yuanzhi Li's [*Learning Hierarchical Language
Structures*](https://arxiv.org/abs/2305.13673) (arXiv:2305.13673) is worth
reading purely for its figures. It trains GPT models on synthetic context-free
grammars (CFGs) and then argues, largely *through heatmaps*, that the model has
learned something like a dynamic-programming parser. Techniques worth stealing:

**1. Aggregate over data, condition on structure.** The standard attention
figure — one head, one input sentence — is an anecdote. Instead they average
attention over the whole dataset, conditioned on a *structural* property:

- against relative distance `p = j − i` (Figures 8 and 22), which reveals that
  attention is **multi-scale**: some heads specialise in short distances, others
  in long ones. That is a claim about the model, not about one sentence.
- against whether position `i` sits on a non-terminal (NT) boundary at grammar
  level ℓ (Figures 23–26), which is what lets them argue attention flows between
  the boundaries a dynamic-programming parser would use.

This is the single most transferable idea here: **condition on the structure you
believe in, average over everything else.** It converts a picture into a
measurement.

**2. Grid the small multiples by (layer, head).** Their attention figures put 12
rows per block for 12 heads, one block per layer — the entire model on one page.
Reading across the grid shows *specialisation*: "different transformer layers
are responsible for different CFG levels" (Figure 26) is a statement you can
only make from the grid, never from a single panel.

**3. Put a time axis on it.** Figure 21 plots grammar level against training
epoch, coloured by probe accuracy — so you can see levels near the leaves being
learned first and deeper levels later. A learning-dynamics heatmap answers *what
was learned when*, which no final-checkpoint number can.

This one transfers directly to fine-tuning work: layer (or capability, or eval
category) on one axis, training step on the other. It is the natural companion
to the [per-layer gradient-norm heatmap](#per-layer-gradient-norm-over-training).

**4. Annotate cells with the number that matters.** Figures 15–17 colour cells
by generation diversity and overlay the collision count in white text. Colour
carries the pattern, the number carries the precision — you do not have to
choose.

```python
im = ax.imshow(values, cmap="viridis")
for i in range(values.shape[0]):
    for j in range(values.shape[1]):
        ax.text(j, i, f"{counts[i, j]:d}", ha="center", va="center",
                color="w", fontsize=7)
```

**5. Plot the difference, not two heatmaps.** Figure 18 shows model marginals
*minus* ground-truth marginals, symbol against position. Asking a reader to
diff two heatmaps by eye does not work; compute the difference and use a
diverging colormap centred at zero (see
[heatmaps](visualization.md#heatmaps-per-layer-per-head-attention)).

**6. Normalise for base rates — and say that you did.** Predicting an NT
boundary is a heavily imbalanced binary task, so the authors normalise columns
differently across grammar levels and state it explicitly in the caption
(Figure 19, Remark 2). Without that, colour tracks the class prior and the
figure shows you nothing but the base rate. **Any per-cell normalisation must be
declared in the caption** — otherwise the reader cannot tell what the colours
mean.

**7. Mark undefined cells explicitly.** Figure 25 uses `×` for combinations that
cannot exist. A blank or a zero would read as "measured, and it was nothing",
which is a different and wrong claim.

### Where heatmaps are the right answer in safety work

- **Layer × position** — activation patching, where the behaviour lives.
- **Layer × head** — head specialisation, attention-head circuits.
- **Layer × training step** — when each capability appeared.
- **Eval category × model** — which model is weak where, instead of one
  aggregate that hides it.
- **Feature × token** — sparse-autoencoder feature firing across a prompt.
- **Level × distance** — the information-flow structure that made the
  dynamic-programming argument above.

### Getting them right

The craft rules live in
[`visualization.md`](visualization.md#heatmaps-per-layer-per-head-attention) —
symmetric limits for signed data, sequential maps for magnitudes, real tick
labels rather than indices. Three more that matter specifically at grid scale:

- **Share the colour scale across a grid**, or panels cannot be compared, which
  was the reason for the grid.
- **Use `LogNorm` for anything spanning orders of magnitude** (gradient norms,
  attention). A linear scale shows one bright cell and a field of black.
- **Say what the colour is** in the colorbar label — "attention", "logit diff"
  and "probe accuracy" are three different claims and look identical.

---

## Where this connects

- How to plot any of these well (colour, axes, error bands, saving):
  [`visualization.md`](visualization.md).
- What error bar to draw and whether a difference is real:
  [`statistics.md`](statistics.md).
- The interpretability libraries themselves:
  [`mech-interp.md`](../interpretability/mech-interp.md),
  [`saes.md`](../interpretability/saes.md),
  [`probes.md`](../interpretability/probes.md).
- Logging figures during a run:
  [`experiment-tracking.md`](../models-and-compute/experiment-tracking.md).

---

Last verified: 2026-08. Drafted by Claude for Nathan's review; pending MATS
research-staff review. Citations checked against source: dataset cartography
(Swayamdipta et al., EMNLP 2020, `allenai/cartography`); gradient noise scale
(McCandlish et al., 2018); tuned lens (Belrose et al., `tuned-lens`, learns a
per-layer affine correction for logit-lens basis drift); CircuitsVis
(`circuitsvis`, successor to Anthropic's PySvelte); Neuronpedia open-source
circuit tracer (attribution graphs on open models including Gemma-2-2B);
J-lens / J-space (Anthropic, transformer-circuits.pub/2026/workspace, July 2026);
heatmap case study read from Allen-Zhu and Li, arXiv:2305.13673 (figure numbers
and the base-rate normalisation remark checked against the PDF);
R-lens / R-space (camilablank, agam_bhatia, Neel Nanda, LessWrong, 5 Aug 2026 —
LRP stop-gradient rules on the backward pass only; code at
huggingface.co/camilablank/workspace-lenses).
