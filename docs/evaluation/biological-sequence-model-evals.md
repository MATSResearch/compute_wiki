---
tags:
  - evaluation
---

# Biological Sequence Model Evals: measuring what a DNA, protein or RNA model can do

How to run and read a benchmark of a biological sequence model, meaning a model pre-trained on
nucleotide or amino-acid sequence (ESM, Evo, Nucleotide Transformer, RNA-FM and the rest) rather than
on text. This is a safety-measurement page, not a biology-tooling page: biosecurity work needs to know
what these models actually carry, and that number comes out of a benchmark whose construction decides
it. The neighbouring page
[`dangerous-capability-evals.md`](dangerous-capability-evals.md#bio-and-chem-vct-lab-bench-and-what-benchmarks-miss)
covers the other half of the bio portfolio, where a chat or agentic model is scored for hazardous
knowledge and task performance, and already carries two results about biological models themselves
(pre-training data filtering undone cheaply, and agentic mutation design).

The setting in mind is a frozen open-weights sequence model, read with a probe or a likelihood, scored
against labels from a public database or an assay. The evidence below comes from a read of eleven DNA
model papers, thirteen protein model papers, the RNA, codon and single-cell literature, eight benchmark
suites and about twenty independent re-evaluations, plus the validation and statistics primary sources.
The effect sizes are what those papers report, mostly on one task each, so treat them as the size of a
trap rather than as a constant. Where this page extends a source rather than quoting it, it says so.

Every item here is a **recommended check**, not a requirement. The team running the experiment knows
its organism, assay and claim better than a page can.

Related pages: [`../engineering/measurement-validity.md`](../engineering/measurement-validity.md) (is
the instrument measuring what you think),
[`eval-statistics.md`](eval-statistics.md) (error bars when items share structure),
[`../engineering/statistics.md`](../engineering/statistics.md) (which test, how many samples),
[`../interpretability/probes.md`](../interpretability/probes.md) (fitting and reading a probe),
[`../engineering/research-rigor.md`](../engineering/research-rigor.md) (pre-registration and
commitment points), [`datasets-benchmarks.md`](datasets-benchmarks.md) (what a benchmark entry should
record).

## At a glance

| You are about to… | Worth checking | Because |
|---|---|---|
| report a score from a random train and test division | whether relatives, gene families or repeated positions sit on both sides | the drop to a homology-aware division is larger than the model-versus-baseline gap being claimed |
| claim a pre-trained model beats the alternatives | a k-mer composition baseline and a homology-transfer baseline, tuned as hard as the model | where a re-evaluation added one, it matched or beat the model in every model family examined |
| pick a layer, a pooling rule or a likelihood score | whether that choice was made on the data you are about to report | the readout moves results by tens of points, and choosing on the reported cross-validation folds is worth up to 12 points of optimism on signal-free data |
| call a result zero-shot | whether the evaluation sequences were in the pre-training corpus | contamination has changed a scaling conclusion, not only a score |
| adopt a public benchmark as a fixed yardstick | how its tasks were selected | several kept only tasks where existing models scored in a chosen band |
| say a model shows no signal on a task | a planted positive control and a smallest effect stated in advance | without them, absence of signal and failure to elicit look identical |
| read a claim that the model generated something functional | the funnel: generated, filtered, screened, human-selected, assayed, worked | one published pipeline filtered about 2 million generations down to 11 laboratory candidates, with a manual last step |
| trust the numbers at all | that the checkpoint loaded, and in the right numerical precision | one released checkpoint loads as random weights with only a warning |

## Why this differs from a chat-model eval

Three differences are real, and two of them run in the field's favour.

Labels are cheap relative to the thing being measured, so cross-validation genuinely replaces a single
spent test set for most questions. A chat benchmark is consumed by being used; a sequence benchmark can
be rotated.

Leakage is measurable in advance. Sequence identity between the training and test sides is computable
before a model runs, unlike contamination of a chat benchmark, which is usually argued rather than
measured.

Relatedness is the dominant structure. Items share ancestry, and in a pair task one gene can appear in
many pairs. This has no chat-model analogue, and the strongest practice in the literature comes from
it: holding out a whole clade or species and reporting what that costs.

## The signature experimental shape

1. Fix the claim, and say what population it is about: these organisms, or organisms like these.
2. Build the item set and divide it by the unit that shares information.
3. Choose how the model is read, using only data you will not report.
4. Fit the baselines, including one that uses no model.
5. Check the instrument numerically before scoring anything.
6. Score, with an interval whose unit matches the claim from step 1.
7. Report the size of the search that produced the configuration.

## Step 1: Say what population the claim is about

This decides the statistics rather than following from them. "This model works on organisms like these"
makes the organism the unit of independent evidence. "This model works on these four organisms" makes
the item the unit. Both are legitimate; they need different error bars and different numbers of groups.

Roberts et al. 2017 (doi:[10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881), "Cross-validation
strategies for data with temporal, spatial, hierarchical, or phylogenetic structure") states the
dependence in both directions: blocking "is required" when the goal is to predict "into new dependence
structures (i.e. new locations, new time periods, new individuals or groups, or for new species within
a phylogeny)", and "when models only predict on the same individuals or groups by which they were
trained, random cross-validation may yield fair error estimates".

**Recommended check.** Write the claim as one sentence before building anything, and name the unit it
generalises over. Then count how many of that unit you have. See
[`../engineering/research-rigor.md`](../engineering/research-rigor.md) for the commitment points, and
step 6 below for what a small count does to an interval.

## Step 2: Divide the items by the unit that shares information

A random division puts near-copies on both sides, so the model can score by recognising a relative
rather than the property. The looser division is not an optimistic estimate of the same quantity; it
measures an easier task.

Published case: Dallago et al. 2021 (doi:[10.1101/2021.11.09.467890](https://doi.org/10.1101/2021.11.09.467890),
"FLIP: Benchmark tasks in fitness landscape inference for proteins") report ESM-1b at Spearman 0.92 on
one landscape with a random division and 0.28 when the training side holds only single mutants.
Bernett, Blumenthal and List (doi:[10.1101/2023.01.18.524543](https://doi.org/10.1101/2023.01.18.524543),
"Cracking the black box of deep sequence-based protein-protein interaction prediction", preprint; journal
version in Briefings in Bioinformatics 2024 not opened) find published
protein-protein interaction accuracies of 77 to 98 per cent fall to 56 per cent against a 50 per cent
chance baseline once test proteins share no similar sequence with training proteins. Penić et al. 2025
(doi:[10.1038/s41467-025-60872-5](https://doi.org/10.1038/s41467-025-60872-5), RiNALMo) score RNA-FM at
F1 0.676 on a random division of RNA secondary structures and 0.31 averaged over nine held-out families
(the leave-one-family-out division is Szikszai et al.'s), below RNAstructure, a thermodynamic method
with no training, at 0.587.
Lüftinger et al. 2021 (doi:[10.3389/fcimb.2021.610348](https://doi.org/10.3389/fcimb.2021.610348)) find
random cross-validation folds give balanced accuracy 4.45 points higher than genome-distance-aware
folds, significantly so in 60 of 77 organism and compound pairs, and a separately collected set ran a
further 10.12 points lower.

The cleanest demonstration is one model against itself. Two versions of the Bacformer preprint
(doi:[10.1101/2025.07.20.665723](https://doi.org/10.1101/2025.07.20.665723)) share a single identifier
and reach opposite conclusions on gene essentiality: the earlier version's random 60/20/20 division has
it beating ESM-2 and Evo, while the later version's genus-level division puts four other models above
it (ProtBERT 82.45, ESM-C 81.18, gLM2 80.57, ESM-2 80.40 against Bacformer 79.49, n = 11 genomes). The
later main text does not state the reversal, so a citation needs a version pin.

The opposite error exists. Roberts et al. 2017 show blocked folds can be "overly-pessimistic", because
a held-out clade becomes an extrapolation rather than a held-out sample.

**Recommended check.** Cluster items by the unit that shares information (a sequence identity
threshold, a gene or RNA family, the position within a protein, the organism, the clade) and confirm no
cluster spans the division. Report the random-division and the aware-division numbers side by side: the
gap is the leakage, and it is a result worth stating. Where a chromosome hold-out is used, note that it
is not a homology hold-out, since paralogues sit on other chromosomes. The generic form of this rule is
on [`../engineering/measurement-validity.md`](../engineering/measurement-validity.md) and
[`../interpretability/probes.md`](../interpretability/probes.md#pitfalls-cross-cutting); they are not
repeated here.

## Step 3: Choose the readout on data you will not report

A frozen model does not have one representation. Which layer, which pooling rule, whether the model is
fine-tuned, and which likelihood score is used are hyper-parameters of the measurement. Two failure
modes appear in the literature, and the two model families pick one each.

Published case, on the size of the lever: Dalla-Torre et al. 2025
(doi:[10.1038/s41592-024-02523-z](https://doi.org/10.1038/s41592-024-02523-z), Nucleotide Transformer)
report that "the highest model performance is never achieved by using embeddings from the final layer"
and a relative difference "as high as 38%" between the best and worst layer on one task, over roughly
760,000 probes fitted. Feng et al. 2025
(doi:[10.1038/s41467-025-65823-8](https://doi.org/10.1038/s41467-025-65823-8)) find averaging over
tokens beats the model's own summary token on 35 to 42 of 52 classification datasets per model, worth
1.4 to 8.7 per cent mean area under the curve, and narrowing the spread between models from 0.708 to
0.799 down to 0.795 to 0.822. Vieira et al. 2025
(doi:[10.1038/s41598-025-05674-x](https://doi.org/10.1038/s41598-025-05674-x)) find mean pooling beats
four alternatives by 5 to 20 percentage points of variance explained on mutational-scanning data.
Valeriani et al. 2023 (arXiv:[2302.00294](https://arxiv.org/abs/2302.00294)) find remote-homology
information in ESM-2 peaks in middle layers at about 0.8 nearest-neighbour overlap against 0.4 in the
last layer; Vieira et al. 2025 find the opposite ordering for one probe type on 40 mutational-scanning
sets, where the last or penultimate layer was most often best. So there is no universally best layer,
only a choice that must be made somewhere.

Published case, on where the choice is made: Schiff et al. 2024
(arXiv:[2403.03234](https://arxiv.org/abs/2403.03234), Caduceus) state a classifier regularisation
"selected from {1, 5, 10} by evaluating average test set AUROC". Brixi et al. 2026
(doi:[10.1038/s41586-026-10176-5](https://doi.org/10.1038/s41586-026-10176-5), Evo 2) is the
counter-example worth copying: layer, pooling window and penalty are chosen jointly by five-fold
cross-validation inside the training division, then the test set is scored once.

This page's synthesis, not any one paper's: across the thirteen protein model papers read, the final
layer with mean pooling is fixed in advance in nine, and pooling is compared in exactly one. The DNA
papers search exhaustively and report the maximum. So one literature risks selection bias and the other
risks an unexamined default, and the default it picks is the layer the layer studies above find weakest.

**Recommended check.** Treat the readout as a hyper-parameter: select it inside the training folds,
record which setting won in each fold, and report the spread across settings. Unstable winners across
folds are themselves evidence that the selection is fitting noise. Do not take a repository quickstart's
layer as the paper's recommendation without checking the paper; one model card extracts the final layer
its own paper calls worst. For the selection-bias mechanism see
[`../engineering/statistics.md`](../engineering/statistics.md) and step 7 below.

## Step 4: Fit a baseline that uses no model

Composition at k-mer resolution, nearest-neighbour homology transfer, and a small network trained from
raw sequence capture a large share of what these benchmarks score. Where a re-evaluation added one, it
matched or beat the pre-trained model in every model family examined, and most model papers do not
include one.

Published case: Sanabria et al. 2024
(doi:[10.1038/s42256-024-00872-0](https://doi.org/10.1038/s42256-024-00872-0), GROVER) report a tuned
bag-of-k-mers control (term-frequency weighting with a random forest) reaching Matthews correlation up
to 87 per cent on promoter tasks and 72 per cent on a transcription-factor binding task against 61 per
cent for Nucleotide Transformer, leaving splice sites as the clear language-model win. Yang et al. 2024
(arXiv:[2406.15669](https://arxiv.org/abs/2406.15669), "CARE: a Benchmark Suite for the Classification
and Retrieval of Enzymes", NeurIPS Datasets and Benchmarks) report BLASTp within four points of an
ESM-based enzyme classifier and ahead of it on enzymes with several functions, 93.7 against 69.4 per
cent. Ren et al. 2024 (arXiv:[2406.10391](https://arxiv.org/abs/2406.10391),
BEACON) report networks trained from scratch beating every RNA language model on several tasks, for
example ribosome load R² 83.9 for a long short-term memory network against 79.5 for RNA-FM. Nguyen et al. 2024 (Evo, cited above) report
that on promoter activity GC content alone reaches correlation 0.35 against the 7-billion-parameter
model's 0.43, and a mechanistic calculator reaches 0.62, above every learned pipeline in that
comparison. Kedzierska et al. 2025 (doi:[10.1186/s13059-025-03574-x](https://doi.org/10.1186/s13059-025-03574-x)) find 2,000
highly variable genes separate cell types better than two single-cell foundation models, zero-shot.

An untrained twin is the cheapest control and frequently decisive. Vishniakov et al.
(doi:[10.1101/2024.12.18.628606](https://doi.org/10.1101/2024.12.18.628606), "Genomic Foundationless
Models: Pretraining Does Not Promise Performance", preprint; later versions retitled) report a
randomly initialised Caduceus reaching about 0.62 mean Matthews correlation on the Nucleotide
Transformer histone and enhancer tasks, above pre-trained Nucleotide Transformer 500M. Zhang, Bai and
Imoto 2023 (doi:[10.1093/bioinformatics/btad617](https://doi.org/10.1093/bioinformatics/btad617))
give the null-corpus version: a DNABERT pre-trained on 3 gigabases of random sequence scores 0.8965
against 0.8991 median area under the curve for the real model across 690 datasets. Wong et al. 2025
(doi:[10.1093/bioinformatics/btaf317](https://doi.org/10.1093/bioinformatics/btaf317)) find scGPT from
random weights matches the pre-trained model, difference 0.004, p = 0.89.

**Recommended check.** Run three baselines on exactly the scored items with the same tuning budget as
the model: composition features, homology transfer, and a small supervised network. Add the same
architecture with random weights through the identical pipeline. If the model's margin over all of them
is inside the interval from step 6, the supported claim is that the model is competitive, not that it
wins. The generic rule is on
[`../engineering/measurement-validity.md`](../engineering/measurement-validity.md#trivial-baselines-first);
equal tuning budgets matter because which method wins can flip with budget.

## Step 5: Check the instrument numerically before scoring

Every rule above assumes the numbers coming out of the model are the numbers the model would produce.
Several documented cases say otherwise, and none raises an error.

Published case, repository-level and checked on the sources on 2026-11-15: one released checkpoint
(ESM C 6B, republished 2026-09) loads as random weights through the standard loading path with only a
warning; one bacterial model (Bacformer) returns wrong outputs with no error under the current major
version of the `transformers` library; Evo 1 must be loaded at a specific revision tag; ESM-2 produced
wrong embeddings on Apple GPUs; one model's default mixed-precision setting was not reproducible run to
run, and batch padding changed another model's embeddings; HyenaDNA pads on the left and ships no
attention mask, so padding enters any average; two RNA models use opposite uracil and thymine
alphabets, so the same sequence string means different things to each.

Models are also not invariant to transformations biology says they should be. Feng et al. 2025 report
fine-tuned Nucleotide Transformer v2 and HyenaDNA changing their predicted class on 4 to 15 per cent of
reverse-complemented benchmark sequences even after reverse-complement augmentation, and find averaging
the two strands at test time does as well or better.

**Recommended check.** Before any benchmark number: reproduce one published figure from the model's own
paper or card, or at minimum show the forward pass differs from a randomly initialised copy; compare a
sample of embeddings against a single-sequence, float32, processor-only run; and for a nucleotide model,
score each sequence and its reverse complement and report the disagreement rate. Record all three in
the run directory. Keep this check clearly separate in code and in the write-up from the deliberate
random-weight baseline of step 4.

## Step 6: Give the interval the unit from step 1

Published case: Obuchowski 1997 (PMID 9192452, read at abstract level) extends the correlated-area
method to clustered data and states that "the size of statistical tests that assume independence is
inflated in the presence of intracluster correlation". Cameron, Gelbach and Miller 2008
(doi:[10.1162/rest.90.3.414](https://doi.org/10.1162/rest.90.3.414)) find cluster-robust tests
over-reject with few (5 to 30) clusters, and that a wild cluster bootstrap holds its nominal size with
as few as about 6. Bates, Hastie and Tibshirani (arXiv:[2104.00673](https://arxiv.org/abs/2104.00673))
find naive cross-validation intervals undercover, 31 per cent miscoverage at a nominal 10 per cent.
Felsenstein 1985 (doi:[10.1086/284325](https://doi.org/10.1086/284325)) is the origin of the
effective-sample-size point for related species: with four pairs of close relatives among eight
species, "the effective number of degrees of freedom is closer to 2".

What is not established, and this page does not assert it: that within-clade correlation is large
enough to matter for a benchmark metric. The clustered result above is conditional on intracluster
correlation existing, and no source read here measures it for a sequence benchmark. Roberts et al. 2017
note that phylogenetically blocked cross-validation "has not been undertaken in the phylogenetic
literature" as of their writing. An item-level paired interval is correct for the claim "on these
items, model A beats model B", which is what most benchmark tables assert; the defect worth looking for
is a mismatch between that interval and a wider sentence in the abstract.

**Recommended check.** Compute the metric's variance with the group as the cluster and divide it by the
naive item-level variance. That ratio is the design effect: near 1 means item-level intervals were
adequate, and 3 means the interval understates the spread by about the square root of 3. Report the
ratio, the number of groups, and which population the interval describes. With few groups prefer a wild
cluster bootstrap or a permutation test at group level, and show the per-group scores rather than only
their mean. For the clustered machinery and the resolution question see
[`eval-statistics.md`](eval-statistics.md#clustered-items-passages-images-problem-sheets-and-shared-tasks).

## Step 7: Report the size of the search

Published case: no multiplicity correction appears in any of the eleven DNA model papers read, across
hundreds of task-by-model comparisons, nor in the RNA, codon and single-cell papers; among the thirteen
protein papers, one corrects, and only for the choice of pooling. Varma and Simon 2006
(doi:[10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91)) show the cost directly: on
40-sample data with no difference between classes (true error 50 per cent), choosing the setting that
minimised the cross-validated error and reporting that error gave 37.8 per cent, while repeating the
selection inside every fold recovered 54.2 per cent. Cawley and Talbot 2010 (JMLR 11:2079-2107) find
this bias "larger than the typical difference in performance between classifiers evaluated using an
unbiased protocol", and that under the biased protocol a significance test declared a winner where "the
difference in performance is entirely spurious".

**Recommended check.** Record the full grid examined (models, readouts, layers, poolings, classifier
settings) and report its size N beside the final number, with the statement that the configuration is
the maximum of N. Then run the label permutation on the whole pipeline, search included: shuffle the
labels, re-run the selection, and report the best score obtained. Anything clearly above chance is this
search's selection bias at this data size. A specification curve reports the distribution over the
whole grid instead of its maximum.

## Reading a claim about generated sequences

Some of these models generate as well as score, and a generation result is reported as "the model
produced something that works". This section is about how to read or audit that claim. It does not
cover how to run a generative design pipeline, which is out of scope for this wiki.

Three things decide whether the claim means anything, and the strongest published example reports all
three.

**The funnel.** How many candidates were produced, what filtered them, and how many were tested.
Nguyen et al. 2024 (doi:[10.1126/science.ado9336](https://doi.org/10.1126/science.ado9336), Evo) state
it in the open: they "filtered ~2 million Evo-generated sequences" for loci containing the required
domains and a detectable guide RNA, folded "the top-ranking 2000 generations", and selected 11
candidates for laboratory testing, where the last step was "manual inspection". One of those 11 worked
in vitro. A paper that reports the one success without the 2 million and the manual step is reporting a
different number.

**The comparator in the same assay.** Evo compares the generated nuclease with the natural enzyme run
in the same assay, and for a second system tests "the natural IS200 element ISSpn6 and IS605 element
ISHp608" as controls.

**A mechanism control.** A catalytically dead variant, or a dependence the molecule should show if it
works for the stated reason. Without one, activity can come from something other than the designed
function.

**The failure mode to look for: filtering before judging.** Zvyagin et al. (GenSLM) excluded the most
divergent 1.4 per cent of generated sequences before the phylogenetic comparison that was then used to
argue the generations were realistic, which makes the comparison partly a property of the filter.

**Recommended check.** For any generation claim, extract the funnel as a single line of numbers
(generated, machine-filtered, structurally screened, human-selected, assayed, worked) and put it beside
the headline. Ask whether the comparator ran in the same assay, whether a mechanism control was
included, and whether any filter was applied to the generations before the evidence step. For the
hazard-assessment reading of a generative biological model, see
[`dangerous-capability-evals.md`](dangerous-capability-evals.md#bio-and-chem-vct-lab-bench-and-what-benchmarks-miss)
and [`../alignment-science/unlearning.md`](../alignment-science/unlearning.md).

## Recommended checks before a claim that a model carries no signal

Absence of signal and failure to elicit look identical from one number.

Published case: Hewitt and Liang 2019 (arXiv:[1909.03368](https://arxiv.org/abs/1909.03368)) define the
control task, where each item keeps the label frequencies but gets a random label: a linear
part-of-speech probe scores 97.2 against 71.2 on the control, so selectivity 26.0, while a more
expressive probe scores 97.3 against 92.8, so selectivity 4.5. A search of the protein and DNA sources
read for this page found no use of control tasks, description-length probing or whole-pipeline label
permutation, so this is a method the neighbouring field has and this one does not yet.

**Recommended check.** Report the shuffled-label score at the same probe capacity beside the real one,
and a planted positive control showing the pipeline finds a signal you injected. State a smallest
effect of interest in advance and test equivalence against it, rather than reading a non-significant
difference as absence. See
[`evals.md`](evals.md#sandbagging-and-capability-elicitation-is-a-low-score-real) for the chat-model
form of the same problem.

## Cross-cutting pitfalls

**A public benchmark may have been filtered using the models it now scores.** Zhou et al. 2024
(arXiv:[2306.15006](https://arxiv.org/abs/2306.15006), DNABERT-2 and its GUE benchmark) kept datasets
where existing models scored in a chosen performance band and restructured the rest, and the model
released alongside had its tokeniser chosen on that same benchmark. Notin et al. 2023 (ProteinGym,
NeurIPS Datasets and Benchmarks) removed thermostability assays "where none of the tested evolutionary
models had a Spearman correlation above 0.2". A score on such a benchmark is not comparable to a score
on an independently built task, and the benchmark cannot carry a headline claim about the model family
that shaped it. Record the filter in the benchmark's entry, as
[`datasets-benchmarks.md`](datasets-benchmarks.md) does for other suites.

**Zero-shot usually means unseen in fine-tuning, not unseen by the model.** These models are pre-trained
on reference genomes and sequence databases, so evaluation sequences are commonly inside the corpus,
unlabelled. The consequence is not only a score: Hermann et al.
(doi:[10.1101/2024.07.23.604678](https://doi.org/10.1101/2024.07.23.604678), "Beware of data leakage
from protein LLM pretraining", preprint, no journal version listed) re-ran the FLIP melting-temperature
task on a pre-training-aware division and report all seven ESM variants scoring higher on the leaky
division, mean Spearman about 0.603 against 0.548, and the step from 3 billion to 15 billion parameters
gaining nothing on the clean division (0.674 against 0.670), so contamination was holding up a scaling
conclusion as well as a score. State what is unseen and what is presumed seen, and report corpus
overlap at a declared identity threshold where the corpus is documented.

**A negative set is manufactured, and its construction defines the task.** Negatives built by
GC-matching, dinucleotide shuffling or by taking another model's false positives measure different
things. Say which was used before comparing across papers.

**Likelihood scores are not interchangeable.** Meier et al. 2021
(doi:[10.1101/2021.07.09.450648](https://doi.org/10.1101/2021.07.09.450648), ESM-1v, NeurIPS; preprint
version read) report mean Spearman 0.582 for the masked
marginal, 0.572 for the one-pass wild-type marginal and 0.552 for the pseudo-log-likelihood on the same
task, so the choice is worth about 0.03 and must be fixed in advance rather than picked from the menu
after seeing the correlations.

## Reproducibility checklist

- [ ] The claim is written as one sentence, naming the population it generalises over.
- [ ] Items are clustered by the unit that shares information, and no cluster spans the division.
- [ ] Both the random-division and aware-division numbers are reported.
- [ ] The readout (layer, pooling, likelihood score) was selected inside the training folds only.
- [ ] A composition baseline, a homology-transfer baseline and a random-weight twin are in the headline table.
- [ ] The checkpoint was shown to be loaded, and precision and padding were checked against a reference run.
- [ ] For a nucleotide model, the reverse-complement disagreement rate is reported.
- [ ] The interval's resampling unit matches the claim, with the design effect and the number of groups.
- [ ] The size of the configuration search, N, is reported beside the final number.
- [ ] A shuffled-label run of the whole pipeline, and a planted-signal run, are both reported.

## Cross-references

- Whether the instrument measures what you think, and trivial baselines in general:
  [`../engineering/measurement-validity.md`](../engineering/measurement-validity.md)
- Error bars when items share structure, and whether a benchmark can resolve a gap:
  [`eval-statistics.md`](eval-statistics.md)
- Fitting a probe, group-aware divisions, and decodability against use:
  [`../interpretability/probes.md`](../interpretability/probes.md)
- Pre-registration, commitment points and if-then rules for unattended runs:
  [`../engineering/research-rigor.md`](../engineering/research-rigor.md) and
  [`../engineering/reviewing-agent-decisions.md`](../engineering/reviewing-agent-decisions.md)
- Scoring a chat or agentic model for hazardous biological capability, and the two uplift trials:
  [`dangerous-capability-evals.md`](dangerous-capability-evals.md)
- Safeguards on biological models themselves (pre-training data filtering, unlearning):
  [`../alignment-science/unlearning.md`](../alignment-science/unlearning.md)

---

## Common questions

### Can I just use cross-validation instead of holding out a test set for a biological benchmark?

For most questions yes, and this is a real difference from chat-model work: labels are cheap relative to
assays, so the item set can be rotated rather than spent. The condition is that every label-touching
choice, the readout included, is repeated inside each fold. Cross-validation with the layer chosen once
on all the data estimates nothing useful.

### My held-out group count is small. How small is too small for a group-level interval?

Cluster-robust tests over-reject with 5 to 30 clusters, and a wild cluster bootstrap has held its size
from about 6. Below that, prefer a permutation or sign test at group level and read its floor: with four
groups, a two-sided sign test cannot return a p-value below 0.125 whatever the effect size, so the
honest report is descriptive, with per-group numbers.

### Which layer should I use for a protein or DNA model?

There is no single answer in the literature: remote-homology information peaks in middle layers of ESM-2,
the final layer is never best in Nucleotide Transformer, and the last or penultimate layer was most often
best for one probe type on 40 mutational-scanning sets. Choose it inside the training folds and report
the spread. The one thing to avoid is inheriting a repository quickstart's layer without checking it
against the paper.

### Does a benchmark win mean the model understands the biology?

Not on its own. A frequency or homology baseline, or the same architecture with random weights, matched
or beat the pre-trained model in every model family where a re-evaluation ran one. The claim that
survives those controls is narrower, and worth more.

---

Last verified: 2026-11-15. New page, from a structured read of eleven DNA model papers, thirteen protein
model papers, the RNA, codon and single-cell literature, eight benchmark suites, about twenty independent
re-evaluations and the validation and statistics primary sources, each evaluation task recorded against
eleven fixed columns with a verbatim quote. The long-context and microbial model papers (Evo, Evo 2, gLM, gLM2, METAGENE-1, Bacformer, GenSLM, ProkBERT, LucaOne) were read in the same pass, with 803 quoted spans machine-verified against the source text. All quoted passages on this page were re-checked as exact
substrings of the saved source text (found as exact substrings of the saved sources). Citations were re-checked against the sources and
6 were corrected before publishing: the CARE benchmark is Yang et al. 2024 at arXiv:2406.15669, not a
Nature Communications paper; the random-corpus DNABERT result is Zhang, Bai and Imoto 2023, not
Vishniakov et al.; Vishniakov et al. is a preprint at doi:10.1101/2024.12.18.628606; the RNA
secondary-structure numbers are reported by Penic et al. (RiNALMo) on Szikszai et al.'s
leave-one-family-out division rather than by the RNA-FM paper; Kedzierska et al.'s DOI ends 03574-x;
and Wong et al. is article btaf317. Checked at abstract level only: Obuchowski 1997 (PMID 9192452). Read at
preprint rather than journal version: Bates, Hastie and Tibshirani; Cameron, Gelbach and Miller;
Vishniakov et al. The repository-level failures in step 5 were checked against repositories, model cards
and issue threads on 2026-11-15 and carry no paper. Not verified: whether within-group correlation is
large enough to change a benchmark interval, which step 6 states as unmeasured rather than asserting.
One-line summaries are Claude's wording, not the authors'. Drafted by Claude; pending MATS research-staff
review.
