---
tags:
  - engineering
---

# Reviewing a Paper Draft: Advice for Human and AI Reviewers

How to review a research-paper draft and suggest improvements the author will
use: a colleague's pre-submission draft, your own draft, or a draft you hand to
a large language model (LLM) reviewer. The page collects published reviewer
guidance (NeurIPS, ICML, ICLR, ACL Rolling Review, CVPR, TMLR), the measured
record of what human peer review and AI peer review catch and miss, and the
working practice of researchers who use LLMs for draft feedback.

Every item is a **recommended practice**, not a requirement. Most of the
venue guidance was written for accept/reject decisions; a pre-submission
review has no verdict to give, so this page keeps what concerns claims,
evidence and clarity, and drops scoring.

Related pages: [`research-rigor.md`](research-rigor.md#claim-grounding-at-write-up)
(claim grounding at write-up), [`measurement-validity.md`](measurement-validity.md)
and [`statistics.md`](statistics.md) (what to check in the results themselves),
[`ai-scientist-frameworks.md`](ai-scientist-frameworks.md#google-deep-review-an-outside-reviewer-for-a-draft-october-2026)
(Google Deep Review and four 2026 studies of LLM reviewers),
[`../start-here/researcher-skills.md`](../start-here/researcher-skills.md#writing-and-distillation)
(writing and distillation).

## At a glance

| You are about to… | Worth doing | Because |
|---|---|---|
| Review a colleague's draft | Restate its claims in your own words first, then map each claim to its evidence | In one planted-error study, 68% of reviewers did not notice that the conclusions were not supported by the results |
| Write up your comments | Order by importance, tag each as must-fix or nice-to-have, give a location and a reason | A list in page order hides which problems matter; vague comments cannot be acted on |
| Ask for an experiment | Name the claim that depends on it; otherwise label it future work | "Add X" can be said of most papers |
| Trust that review found the errors | Rerun or recompute one headline number from the code | A single reviewer finds roughly a third of planted major errors, and leakage can be invisible in the text |
| Ask someone to review your draft | Say the stage, the audience, what you are unsure of, and what kind of feedback you want | A reader can only read it for the first time once |
| Get an AI review of your draft | Fresh context, no hint it is yours or what you think of it; one lens per pass; a quote and location per finding | Presented as yours, LLMs tend to validate; a generic "review this" gets generic comments |
| Act on an AI review | Check every finding against the paper before editing; write the fix yourself | Expert raters judged roughly one in six criticisms from frontier AI reviewers incorrect |
| Use an AI reviewer's score | Don't; read the findings | Scores are inflated, vary between runs, and move with presentation alone |
| Judge novelty or importance | Ask a human in the subfield | In the one study that separated them (finance and accounting papers), an LLM's judgements of correctness and exposition predicted publication and its judgements of originality and significance did not |
| Upload someone else's submission to an LLM | Check the venue's policy first | NeurIPS, ICML and ACL Rolling Review each restrict it differently |

## What does human peer review catch, and what does it miss?

The measured record says a single careful read finds a minority of serious
errors, and that accept/reject among decent papers is close to a coin flip.
The planted-error evidence is mostly biomedical and from 1998–2010; treat the
transfer to machine learning (ML) as an inference.

- **A single reviewer finds about a third of planted major errors.** Schroter
  et al. (2008, *J R Soc Med*, [doi:10.1258/jrsm.2008.080062](https://doi.org/10.1258/jrsm.2008.080062)),
  607 BMJ reviewers, nine major errors inserted per paper: "At baseline (Paper
  1) reviewers found an average of 2.58 of the nine major errors". Baxt et al.
  (1998, *Ann Emerg Med*, [doi:10.1016/S0196-0644(98)70006-X](https://doi.org/10.1016/S0196-0644(98)70006-X)):
  "Sixty-eight percent of the reviewers did not realize that the conclusions
  of the work were not supported by the results."
- **In ML, the technical core gets the least scrutiny.** Nihar Shah's survey
  of peer review ([extended version, PDF](https://www.cs.cmu.edu/~nihars/preprints/SurveyPeerReview.pdf))
  reports an experiment at an ML conference with a paper carrying one
  significant planted error (a false convexity claim, hyperparameters selected
  on the test set, or an incorrect theorem): "One out of the 79 reviews
  brought the erroneous segment under scrutiny." Review quality "showed no
  correlation with the self-reported confidence or expertise in the reviews."
- **Half the accept list would change on re-review.** The NeurIPS 2021
  consistency experiment (Beygelzimer et al., [arXiv:2306.03262](https://arxiv.org/abs/2306.03262)):
  "the two committees disagree on their accept/reject recommendations for 23%
  of the papers and that, consistent with the results from 2014,
  approximately half of the list of accepted papers would change if the
  review process were randomly rerun." The 2014 analysis (Cortes & Lawrence,
  [arXiv:2109.09774](https://arxiv.org/abs/2109.09774)) concludes the process
  "was good for identifying poor papers, but poor for identifying good
  papers."
- **Knowing the result changes how the methods are judged.** Emerson et al.
  (2010, *Arch Intern Med*, [doi:10.1001/archinternmed.2010.406](https://doi.org/10.1001/archinternmed.2010.406))
  sent reviewers a fabricated manuscript in two versions identical except for
  the direction of the result. Reviewers recommended the positive version
  more often ("97.3% vs 80.0%"), found fewer of its planted errors, and
  scored its identical methods section higher.
- **Some errors cannot be found by reading.** Kapoor & Narayanan on data
  leakage ([arXiv:2207.07048](https://arxiv.org/abs/2207.07048)), about their
  civil-war prediction case study: "none of these errors could have been
  caught by reading the papers". In the NeurIPS 2019 reproducibility program
  (Pineau et al., [arXiv:2003.12206](https://arxiv.org/abs/2003.12206)),
  reviewers reported looking at the provided code in fewer than half of the
  reviews where code was available (2,255 of 5,298 survey answers, 43%).
- **Longer reviews look better without being better.** Goldberg et al.
  ([arXiv:2311.09497](https://arxiv.org/abs/2311.09497), a NeurIPS 2022
  randomized trial): "lengthened reviews are scored (statistically
  significantly) higher quality than the original reviews", where the added
  text was uninformative.

Two biases often listed as established were tested in randomized trials and
not found: anchoring on one's first score (Liu et al.,
[arXiv:2307.05443](https://arxiv.org/abs/2307.05443): "no significant
evidence of anchoring") and herding in reviewer discussions (Stelmakh et al.,
[arXiv:2011.15083](https://arxiv.org/abs/2011.15083), whose paper reports "no evidence of
herding in the discussion phase of ICML 2020 peer review").

**What follows for a pre-submission review:** one reviewer's silence is not
clearance; use more than one reader and expect them to raise different
points. Read the methods before the results where you can. Open the code.

## How do I review a colleague's draft?

The points below recur across the venue reviewer guides and the classic
essays on refereeing. Each names its sources.

1. **Read twice, and hold the critique until the second read.** ACL Rolling
   Review (ARR) [reviewer guidelines](https://aclrollingreview.org/reviewerguidelines):
   "please read the paper at least twice: skimming and in-depth reading", and
   on the skim, "Do NOT look at the results yet. Hindsight bias may make
   things seem obvious in retrospect, and confirmation bias may make you
   dismiss evidence that contradicts your beliefs." Keshav's three-pass method
   ("How to Read a Paper", [PDF](http://ccr.sigcomm.org/online/files/p83-keshavA.pdf))
   is the same idea with a third pass in which you "attempt to virtually
   re-implement the paper".
2. **Log your first-read reactions as data.** Where you got lost, what you
   expected next, what was unclear even if later text clears it up. Emily
   Bender, in the ACL 2017 chairs' [reviewing advice](https://acl2017.wordpress.com/2017/02/23/last-minute-reviewing-advice/):
   "Statements like 'I had a hard time following Section 3' … are more helpful
   to authors [than] statements that purport to be objective like 'The paper
   is confusing.'" Matt Might ([How to peer review](https://matt.might.net/articles/how-to-peer-review/))
   recommends "recording your thoughts as you read the paper".
3. **Restate the paper before criticising it.** Two to four sentences in your
   own words that the author would agree with. NeurIPS 2025
   [reviewer guidelines](https://neurips.cc/Conferences/2025/ReviewerGuidelines):
   "This is not the place to critique the paper; the authors should generally
   agree with a well-written summary." CVPR 2026
   [reviewer training](https://cvpr.thecvf.com/Conferences/2026/ReviewerTrainingMaterial):
   "if you can't summarize it clearly, read again". If your summary differs
   from what the author meant, that mismatch is itself a finding.
4. **Make claims versus evidence the core test.** List the claims and check
   that each is supported. TMLR's [acceptance criteria](https://jmlr.org/tmlr/acceptance-criteria.html):
   "Are the claims made in the submission supported by accurate and
   convincing evidence? This is the most important criterion." A gap has two
   fixes, and the cheaper one is often right: more evidence, or, in TMLR's
   words, "for the authors to adjust (reduce) their claims."
5. **Order by importance and tag each point.** TMLR's [reviewer guide](https://jmlr.org/tmlr/reviewer-guide.html)
   asks for each requested change to say "whether they are critical to
   securing your recommendation for acceptance or would simply strengthen the
   work". Mark Allman ("Thoughts on Reviewing", [PDF](https://www.icir.org/mallman/pubs/All08a/All08a.pdf)),
   writing as an author: "a list of issues that move chronologically through
   the paper are not enough to allow the authors to get a sense of which
   problems were key". Typos and wording go last, in their own section.
6. **Be specific and locatable.** Name the section, the missing reference,
   the exact baseline. ARR's examples: write "Y and Z are missing from the
   description of X" instead of "X is not clear". A claim that the work is not
   novel needs the citation. CVPR's [reviewer guidelines](https://cvpr.thecvf.com/Conferences/2026/ReviewerGuidelines)
   list "generic comments that could apply to any submission" as a sign of
   irresponsible reviewing.
7. **Ask for an experiment only when a claim depends on it.** ARR: "a paper
   only needs to present sufficient evidence for the claim that the authors
   are making. Any other extra experiments are in the 'nice-to-have'
   category". Allman calls the alternative the "rock fetch": "there is always
   one more bit of analysis or experimentation that could be done."
8. **Phrase uncertain technical objections as a question with your
   reasoning.** Timothy Roscoe ("Writing reviews for systems conferences",
   [PDF](https://people.inf.ethz.ch/troscoe/pubs/review-writing.pdf)): "there
   is a still a remote possibility that you've misunderstood the paper".
9. **Say what you did not check.** ICML 2025 [reviewer instructions](https://icml.cc/Conferences/2025/ReviewerInstructions):
   "Did you check the correctness of any proofs for theoretical claims?
   Please specify which ones". An unchecked appendix reported as unchecked is
   useful; an unchecked appendix passed over in silence reads as approval.
10. **Name real strengths, specifically, and address the paper, not the
    author.** This is about uptake, not politeness: Might notes that snark
    causes "any thoughtful feedback you have given" to be "completely
    ignored". Max Daniel ([Giving and receiving feedback](https://ea.greaterwrong.com/posts/ZjiokgANEfu36LD6G/giving-and-receiving-feedback))
    names the common failure: "A large number of comments in a Google doc,
    each pointing out small issues you think should be fixed, but not
    mentioning that you overall really like the text."

### Which of my own criticisms should I distrust?

ARR keeps a list of common review issues (heuristics H1–H17): comments that
"may point at legitimate problems with the paper, but they are not always
'weaknesses'".
Run your draft review against it before sending.

| If you wrote something like… | ARR's answer |
|---|---|
| The results are not surprising | "Many findings seem obvious in retrospect" |
| Not novel | "you need to provide a reference" |
| Not state of the art | "SOTA results are neither necessary nor sufficient for a scientific contribution." |
| Too simple | "The goal is to solve the problem, not to solve it in a complex way." |
| The authors should have done X instead | Valid "only if the authors' choices prevent them from answering their research question, their framing is misleading, or the question is not worth asking." |
| A weakness copied from the limitations section | "Limitations != weaknesses" |

NeurIPS says the same about candour: "authors should be rewarded rather than
punished for being up front about the limitations of their work". Lipton &
Steinhardt ("Troubling Trends in Machine Learning Scholarship",
[arXiv:1807.03341](https://arxiv.org/abs/1807.03341)) give a counterfactual
test: "Might I have accepted this paper if the authors had done a worse job?"

### Should every comment come with a fix?

Sources disagree. Might: "When you criticize an aspect of a manuscript, offer
advice on how to fix it." Max Daniel asks whether proposing solutions is "a
double-edged sword" and adds "It's still useful to give feedback even if you
can't think of any suggestions!" Alan Jay Smith ("The Task of the Referee",
1990) holds that rewriting the paper is not the referee's job. A workable
reading: always state the problem and where it is; add a fix when you are
confident in it, and say when you are not.

## How do I ask for a review of my own draft?

- **Ask early, on an outline.** Neel Nanda ([Highly Opinionated Advice on How
  to Write ML Papers](https://www.lesswrong.com/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers)):
  "I find it way faster *and* easier to give feedback on a narrative or
  bullet point outline than being sent 8 pages of dense prose!"
- **Spend fresh readers carefully, and tell them what you want.** Simon
  Peyton Jones ("How to write a great research paper", slides; wording from
  the older deck): "Each reader
  can only read your paper for the first time once! So use them carefully",
  and "'I got lost here' is much more important than 'wibble is mis-spelt'."
- **Give context and specific questions.** Max Daniel: "Give context. E.g.
  for a talk or paper, the target audience is often crucial." Lizka, writing about
  sharing a critical draft with the people it criticises
  ([EA Forum](https://ea.greaterwrong.com/posts/kjcMZEzksusCHfHiF/productive-criticism-running-a-draft-past-the-people-you-re))
  lists "What your biggest uncertainties are" and "How much you
  might update the draft".
- **Bring something concrete.** Ethan Perez ([Tips for Empirical Alignment
  Research](https://www.lesswrong.com/posts/dZFpEdKyb9Bf4xYn7)), on mentor
  meetings: bring "Plots, tables, or other concrete results to show".
- **Don't argue with the feedback.** Peyton Jones: "DO NOT respond 'you
  stupid person, I meant X'. Fix the paper so that X is apparent even to the
  stupidest reader."
- **Swap papers.** Nanda: "find someone else also working on a paper and
  offer to give each other feedback."

## What should a reviewer of an ML or AI-safety draft check?

A condensed list; each item names where the fuller treatment lives.

**Claims and framing**

- One to three main claims, each pointing at the figure, table or number it
  rests on (NeurIPS [paper checklist](https://neurips.cc/public/guides/PaperChecklist);
  Nanda).
- The abstract claims no more generality than was tested: models, datasets,
  prompts, seeds (NeurIPS checklist: "if the approach was only tested on a
  few datasets or with a few runs").
- Explanation is separated from speculation, and the source of a gain is
  identified by ablation (Lipton & Steinhardt).
- Loaded terms ("deception", "scheming", "understanding") are licensed by an
  experiment. Summerfield et al., "Lessons from a Chimp"
  ([arXiv:2507.03409](https://arxiv.org/abs/2507.03409)): "Avoid basing
  strong claims on anecdotal evidence alone", "Include appropriate control
  conditions", "Avoid unduly mentalistic language".
- Unanchored comparatives ("improves", "better") and undefined or shifting
  terms (Ethan Perez, [Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/);
  Jacob Steinhardt, [Advice for Authors](https://jsteinhardt.stat.berkeley.edu/blog/advice-for-authors)).

**Design, data and controls**

- Baselines are the strongest available, tuned as hard as the method, and run
  under the same setup. Biderman et al. ([arXiv:2405.14782](https://arxiv.org/abs/2405.14782)):
  "Avoid copying results from other implementations".
- Nothing was selected on the test set, and train and test share no
  duplicates or time leakage (Kapoor & Narayanan's leakage taxonomy; REFORMS,
  [arXiv:2308.07832](https://arxiv.org/abs/2308.07832)).
- Examples are random or the selection is disclosed, with rates beside any
  transcript (Nanda: "Was this cherry-picked?"; Summerfield et al.).
- A "the model cannot do X" claim says how much elicitation effort was spent
  (Apollo Research, [We Need A 'Science of Evals'](https://www.apolloresearch.ai/blog/we-need-a-science-of-evals)).
- For an LLM-judged metric, the judge was validated (ARR lists "LLM-only
  evaluation without validation" among common problems; see
  [`measurement-validity.md`](measurement-validity.md#the-grader-is-an-instrument-too)).

**Statistics**

- Every main-claim number has an interval, and the paper says what varies
  across it (NeurIPS checklist: "The factors of variability that the error
  bars are capturing should be clearly stated").
- Two models on the same items are compared on paired differences (Miller,
  "Adding Error Bars to Evals", [arXiv:2411.00640](https://arxiv.org/abs/2411.00640)).
- How many metrics, subsets, layers, prompts and thresholds were tried, and
  which analyses were planned (Gelman & Loken, "The garden of forking paths").
- More than one prompt format where a result could hinge on wording (Sclar et
  al., [arXiv:2310.11324](https://arxiv.org/abs/2310.11324)). Detail:
  [`statistics.md`](statistics.md).

**Interpretability claims**

- The wording matches the rung of evidence: observation, intervention, or
  counterfactual (Joshi et al., [arXiv:2602.16698](https://arxiv.org/abs/2602.16698)).
- Randomisation controls exist (random weights, randomly permuted labels), and visual
  examples are backed by a metric (Adebayo et al., "Sanity Checks for
  Saliency Maps", [arXiv:1810.03292](https://arxiv.org/abs/1810.03292)).

**Artifact**

- A script regenerates each reported number, and the reviewer reran one.
- The code does what the paper says. Bai et al.
  ([arXiv:2602.18458](https://arxiv.org/abs/2602.18458)) had an agent review
  30 mechanistic-interpretability outputs with code execution: "it captures
  most failures identified by humans (67 of 87) and surfaces 51 additional
  issues that humans missed", and "Removing code access or execution
  substantially reduces agreement to about 45% on average".

### Does handing the author or reviewer a checklist help?

Not by itself. The trial evidence is biomedical (all read at abstract level):

| Intervention | Study | Result |
|---|---|---|
| Authors asked to complete a reporting checklist | Hair et al. 2019, randomized, 1,689 manuscripts ([doi:10.1186/s41073-019-0069-3](https://doi.org/10.1186/s41073-019-0069-3)) | "No manuscript in either group achieved full compliance" |
| Reviewers reminded of the checklist items | Speich et al. 2023, two randomized trials ([doi:10.1001/jamanetworkopen.2023.17651](https://doi.org/10.1001/jamanetworkopen.2023.17651)) | "it was not useful to implement the tested intervention" |
| A dedicated expert checks specific items and writes specific requests | Blanco et al. 2020, randomized, n = 24 ([doi:10.1136/bmjopen-2020-036799](https://doi.org/10.1136/bmjopen-2020-036799)) | Reporting improved (mean difference 1.43 of 8 items) |
| A separate statistical reviewer | Bruce et al. 2016, meta-analysis ([doi:10.1186/s12916-016-0631-5](https://doi.org/10.1186/s12916-016-0631-5)) | "Adding a statistical peer review improved the quality of the final manuscript"; training reviewers did not improve the review report, and "use of a checklist did not improve the quality of the final manuscript" |

The pattern: a list that someone is merely shown changes little; a named
person (or a dedicated pass) working the items one by one and writing located
requests changes the paper. No randomized trial of a checklist's effect on ML
paper correctness was found.

## How good are AI reviewers at reviewing a paper draft?

Useful for breadth and for checkable errors; weakest on novelty,
importance and omissions, and their scores are not worth reading. The studies below are from 2023 to November
2026 and the models in them date quickly.

**What LLM reviewers are useful for**

- **They raise points human reviewers also raise, at about the rate two
  humans overlap.** Liang et al. ([arXiv:2310.01783](https://arxiv.org/abs/2310.01783),
  GPT-4, 2023): overlap with human reviewers "30.85% for Nature journals,
  39.23% for ICLR", against human–human overlap of "28.58% for Nature
  journals, 35.25% for ICLR".
- **They surface issues no human raised.** Kim et al.
  ([arXiv:2605.20668](https://arxiv.org/abs/2605.20668)): 45 scientists rated
  2,960 criticisms of 82 Nature-family papers; AI reviewers "surface a
  distinct 26% of issues no human raises".
- **Authors at a real venue found them useful for technical errors.** The
  AAAI-26 pilot (Biswas et al., [arXiv:2604.13940](https://arxiv.org/abs/2604.13940))
  gave every main-track submission one labelled AI review; participants
  "actually preferred them to human reviews on key dimensions such as
  technical accuracy and research suggestions."
- **The best configurations catch a majority of explicit planted errors.**
  Nguyen et al. ([arXiv:2606.19749](https://arxiv.org/abs/2606.19749)): the
  strongest configuration tested (OpenAIReview + GPT-5.5) "catches 71.6% of
  injected errors". In Litvak's benchmark (under "Where they fail"), three of
  eleven systems caught fewer than half.

**Where they fail**

- **Novelty and significance.** Lu et al.
  ([arXiv:2610.18435](https://arxiv.org/abs/2610.18435), finance and
  accounting papers): the predictive signal in LLM reviews "comes from its
  judgements of correctness and exposition. Its judgements of originality and
  significance carry none"; "LLMs can check whether research is right, but
  not whether it matters."
- **Real, subtle errors.** SPOT (Son et al., [arXiv:2505.11855](https://arxiv.org/abs/2505.11855)),
  91 errors that led to errata or retraction: "none surpasses 21.1% recall or
  6.1% precision".
- **Omissions.** Litvak ([arXiv:2611.12820](https://arxiv.org/abs/2611.12820),
  100 errors planted in 10 psychology papers; a single-author workshop
  preprint): "Seven errors could not be caught by any system, and all seven
  were omissions".
- **Wrong and over-harsh criticisms.** In Kim et al. the share of criticisms
  experts rated correct was 82–86% for three frontier AI reviewers against
  92% for the top-rated human (and 79% for the lowest-rated human); recurring weaknesses include "limited subfield
  knowledge" and an "overly critical stance on minor issues". In the NeurIPS
  2024 checklist-assistant experiment (Goldberg et al.,
  [arXiv:2411.03417](https://arxiv.org/abs/2411.03417)), "inaccuracy (20/52)
  and excessive strictness (14/52) were the most frequent issues".
- **They agree with each other.** Kim et al.: "AI reviewers overlap far more
  than humans do (21% vs. 3% for cross-reviewer pairs)". Two AI reviewers raising the same point is
  weaker evidence than two humans doing so.
- **Scores.** Keuper ([arXiv:2509.10248](https://arxiv.org/abs/2509.10248)):
  "LLM reviews are generally biased toward acceptance (>95% in many models)".
  Yang et al. ([arXiv:2610.19339](https://arxiv.org/abs/2610.19339)):
  "Repeated reviews fluctuate even under identical conditions."
- **Presentation moves them.** Yang et al.
  ([arXiv:2606.13044](https://arxiv.org/abs/2606.13044)), repackaging
  presentation only: "75.1% attack success rate and a mean score gain of
  +1.21/10"; "AI reviewers are easier to impress than to convince". Ye et al.
  ([arXiv:2412.01708](https://arxiv.org/abs/2412.01708)) found authors can
  steer the critique by listing minor limitations.
- **They prefer LLM-written text.** Li et al.
  ([arXiv:2510.12367](https://arxiv.org/abs/2510.12367)): "LLM reviewers
  systematically inflate scores for LLM-authored papers".

**A disagreement worth knowing.** Studies that have people rate the reviews
(the AAAI-26 opt-in survey of authors and committee members; Kim et al.'s
expert ratings of individual criticisms) put AI reviewers between a paper's
lowest-rated and top-rated human reviewer or above, though less often correct
than the top-rated one; studies that score against ground-truth errors (SPOT,
FLAWS at [arXiv:2511.21843](https://arxiv.org/abs/2511.21843)) find low
detection.
Both can hold: a review can be full of reasonable points and still miss the
one error that matters. A clean AI review is weak evidence that a paper is
sound.

## What makes an AI review better?

Each row names the evidence behind it; none has been tested in a randomized trial on real drafts.

| Design choice | Evidence | Caveat |
|---|---|---|
| **Pool reviewers from different model families** | Litvak: "The best single system caught 71 of the 100 errors … Pooling every system's output caught 93"; Nguyen et al.: "union of detections across six models reaches 83.3% recall" | More findings to triage; neither benchmark measured false positives (in Nguyen et al.'s separate deployment, false positives and nitpicks were the most common user complaints). Both pools also mix models of one family; Litvak: "Models are only partly correlated in the errors they find" |
| **Targeted passes, not "write a review"** | Liu & Shah ([arXiv:2306.00622](https://arxiv.org/abs/2306.00622)): "prompting with a specific question (e.g., to identify errors) outperforms prompting to simply write a review"; MARG ([arXiv:2401.04259](https://arxiv.org/abs/2401.04259)): a multi-agent system with agents specialised by comment type reduced "the rate of generic comments from 60% to 29%" in a user study | More passes produce more nitpicks |
| **Ask for findings, never a score** | The score studies above; the AAAI-26 pilot gave no scores | — |
| **A revision pass over the findings** | EquiReview-R ([arXiv:2609.03943](https://arxiv.org/abs/2609.03943)): "reduces major overcritique from 15.5% to 8.1%" | One study |
| **Give the reviewer the code and results** | Bai et al. (agreement falls to about 45% without code access or execution); Baumgärtner & Gurevych, SciCoQA ([arXiv:2601.12910](https://arxiv.org/abs/2601.12910)) on paper–code consistency | SciCoQA's best models "detect only 46.7% of real-world discrepancies" |
| **Rerunning the same model** | Mixed. Litvak found reruns of one model added no catches; SPOT found "models rarely rediscover the same errors" across runs | Prefer a second family to a second sample |

## How do I get a useful AI review of my own draft?

A workflow assembled from researchers' published practice. The MATS
dashboard's Automated Alignment Research tool does part of it for a report it
produced: a reviewer from another model family audits the report, **Review as
a draft** asks what the report claims and whether the evidence supports that
much, and each finding carries Confirmed / Refuted / Downgraded marks for the
researcher to set (steps 3, 5, 7, 8 and 10 below). The steps apply to any
draft, with or without the tool.

1. **Check where the draft may go.** Your own unpublished draft is yours to
   share, but co-authors and lab policy may have a view, and a provider
   setting that trains on your inputs is a disclosure.
2. **Give the reviewer clean input.** LaTeX source or Markdown where
   possible. Google's Paper Assistant Tool team reports the model "sometimes
   struggled — particularly with parsing complex notation or interpreting
   figures" ([Google Research blog](https://research.google/blog/gemini-provides-automated-feedback-for-theoretical-computer-scientists-at-stoc-2026/)).
   If a finding says a section or reference is missing, first check that the
   upload was intact.
3. **Use a fresh context, and do not say the draft is yours or what you
   think of it.** eggsyntax ([LessWrong](https://www.lesswrong.com/posts/rarcxjGp47dcHftCP)):
   "if it's presented as yours, LLMs will often provide validation rather
   than objective critique." Neel Nanda's framing
   ([LessWrong](https://www.lesswrong.com/posts/jP9KDyMkchuv6tHwm)): "LLMs
   are bad at giving critical feedback. Frame your request so the sycophantic
   thing to do is to be critical, by pretending someone else wrote the thing
   you want feedback on." A reviewer that can read the authoring conversation
   or search the repository for earlier review rounds is not independent,
   whatever the prompt says.
4. **Ask for the claims back first.** Have the reviewer restate the paper's
   main claims and the evidence for each, and compare with what you meant.
5. **One lens per pass, substance before prose.** Claims versus evidence,
   statistics, related work, reproducibility, figures; then clarity. Gordon
   Seidoh Worley ([LessWrong](https://www.lesswrong.com/posts/YNCprZAmXnZNozzWh)):
   "it's a big time saver to get the structure of a piece right before trying
   to do stylistic edits on paragraphs that might never appear in the final
   version." Give every pass the same output format so the results compare.
6. **Run one pass with the code and result files**, tracing paper → table →
   output → script, separately from the cold read.
7. **Run at least one pass on another model family.**
8. **Require a quote, a location and a severity per finding, and cap the
   list.** Anthropic's [prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices): "ask Claude to quote relevant parts
   of the documents first". Nanda adds that quotes need checking ("verify
   these are real and make sense"). Gwern
   ([Virtual Comments](https://gwern.net/blog/2024/virtual-comments)):
   "Better to waste some API bills than author time."
9. **Tell the reviewer it may find nothing.** Anthropic's Claude Code
   [best practices](https://code.claude.com/docs/en/best-practices.md): "A
   reviewer that's asked to find problems will always find *something*."
   Ai2's Asta `check-claims` skill ([`allenai/asta-plugins`](https://github.com/allenai/asta-plugins)):
   "Nothing wrong: say what you covered and that its claims are backed;
   don't invent findings to look thorough."
10. **Adjudicate before you edit** (next section).
11. **Write the fixes yourself.** Steven Byrnes
    ([LessWrong](https://www.lesswrong.com/posts/ETneBngxBamDPDLXJ)): "I find
    LLMs are good at bringing possible issues to attention, but bad at fixing
    them; I suggest always writing your own words."
12. **Re-review in a new context after editing.** Byrnes re-asks in a new
    chat "until it's all false positives". Do not paste the critique into the
    authoring chat to be argued away.

### A prompt skeleton

Assembled from the sources above; the wording is this page's except where a
source is quoted.

```text
[Fresh session, memory off, no authoring context, neutral filename.]

Review the attached draft through ONE lens: {claims vs evidence | statistics |
related work | reproducibility | figures and tables | clarity for <audience>}.

First, before any critique: restate the paper's main claims and the evidence
offered for each, so the authors would agree with your summary.

Then list findings, most important first, at most 10. For each:
- LOCATION and a verbatim QUOTE
- what is wrong or missing, and which claim it affects
- SEVERITY: blocks a main claim / would strengthen / minor
- the cheapest check or change that would settle it

Rules:
- Be specific to this paper. No comment that could apply to any paper.
- A claim must not say more than its evidence does, in scope, number or certainty.
- Ask for a new experiment only if a stated claim depends on it; name the claim.
- A prior-work objection needs a citation you can point to; otherwise drop it.
- Do not treat a limitation the authors state as a new weakness.
- Flag problems; do not rewrite the text.
- If a section, table or figure looks truncated or unreadable, say so.
- Say what you did not check. If you find nothing in this lens, say what you
  covered; do not invent findings.
```

Do not ask for a score, and do not add your own opinion of the draft: Wang et
al. ([arXiv:2611.02244](https://arxiv.org/abs/2611.02244)) found "a brief
negative user opinion can erase or reverse" the score gain a revision had earned.

## How do I read a list of AI review findings?

Treat each finding as a hypothesis about your paper. The clearest published
procedure is the `adjudicate-review` skill in
[`pedrohcgs/claude-code-my-workflow`](https://github.com/pedrohcgs/claude-code-my-workflow)
(MIT licence; an academic-research template with economics and political-science defaults): "A fluent, specific, line-numbered
finding is not a verdict. It is a hypothesis about your work."

- **Open the cited location.** Is the quoted text there, and is the supposedly
  missing material stated elsewhere? Kim et al. found "paper explicitly
  states X, AI says missing" among the most common AI reviewer errors.
- **Mark each finding confirmed, refuted or downgraded**, and compute anything
  computable. The same skill: "never change correct work to satisfy a
  reviewer you have not checked."
- **Agreement between AI reviewers is not confirmation.** "Two reviewers
  flagging the same thing is weak evidence — models share failure modes".
- **Check the proposed fix separately from the finding.** A reviewer can be
  right that a passage confuses and wrong about why.
- **A refuted finding can still be signal.** "If a careful reviewer
  stumbled, a careful human may stumble the same way." Often the claim is
  right and what licenses it sits too far away.
- **Do not answer every comment with a hedge.** JustisMills
  ([LessWrong](https://www.lesswrong.com/posts/FCE6MeDzLEYKFPZX6)) describes
  the result of asking an LLM to poke holes in a muddy argument: Claude "will
  just kind of make up random 'issues'" that the author hedges against,
  giving a write-up that "has plenty of caveats, and… has no actual core of
  considered thought."
- **Do not revise to raise an AI score.** What moves the score is largely
  presentation.

## Hidden prompts, manipulation and confidentiality

- **Hidden instructions in manuscripts are real.** Lin
  ([arXiv:2507.06185](https://arxiv.org/abs/2507.06185)): "18 academic
  manuscripts on arXiv contained hidden instructions" aimed at AI reviewers.
  If you run an AI review over someone else's PDF, a finding-free or glowing
  review is a reason to look at the raw text.
- **Venue rules differ and change yearly; read the current page.** As read on
  2026-11-10: the NeurIPS 2026 [Main Track Handbook](https://neurips.cc/Conferences/2026/MainTrackHandbook)
  says "Reviewers must not use LLMs except for papers where this is
  specifically allowed"; ICML 2025 [said](https://icml.cc/Conferences/2025/ReviewerInstructions) "Use of Generative AI tools (such as
  LLMs) for reviewing is strictly prohibited" and ICML 2026 ran two reviewer
  policies ([policy page](https://icml.cc/Conferences/2026/LLM-Policy)); [ARR](https://aclrollingreview.org/reviewerguidelines)
  says reviewers should not upload a submission "into a non-privacy
  preserving generative tool"; ICLR 2026's [author guide](https://iclr.cc/Conferences/2026/AuthorGuide)
  requires disclosure of significant LLM use. None of these pages
  prohibits an author getting AI feedback on their own draft. ARR and ICLR
  attach disclosure duties to author use, and the ICML pages are reviewer
  rules that do not address authors.

## Which tools review a draft?

| Tool | Use it for | When not to |
|---|---|---|
| **Stanford Agentic Reviewer** ([paperreview.ai](https://paperreview.ai/tech-overview), Yixing Jiang and Andrew Ng) | A free conference-style review grounded in arXiv search | Fields that do not publish on arXiv; its authors say reviews "may contain errors" |
| **Refine** ([refine.ink](https://www.refine.ink/)) | Passage-anchored, ranked findings on logic and internal consistency | A paid third-party service ($49.99 per review as read 2026-11-10; first document free); its accuracy claims are the vendor's own |
| **Google Deep Review** | A second opinion from another model family; see [`ai-scientist-frameworks.md`](ai-scientist-frameworks.md#google-deep-review-an-outside-reviewer-for-a-draft-october-2026) | As a check of claims against your own runs |
| **`paper-review` skill** in [`neuromechanist/research-skills`](https://github.com/neuromechanist/research-skills) (BSD-3-Clause) | A small fresh-context single or panel review for a coding agent, with Codex and Copilot reviewer templates | Its principles lean neuroscience |
| **`pedrohcgs/claude-code-my-workflow`** (MIT) | Process ideas: reviewer fencing, adjudication, a claim verifier | Adopting whole; its preloaded defaults are economics and political science |
| **Ai2 Asta `check-claims`** ([`allenai/asta-plugins`](https://github.com/allenai/asta-plugins), Apache-2.0) | The clearest claims-versus-quote rubric | Outside Asta's own evidence workspace it does not run as-is |
| **A plain chat with a staged script** (Byrnes's checklist; Simon Willison's [proofreader prompt](https://simonwillison.net/guides/agentic-engineering-patterns/prompts/)) | Blog-post-length write-ups | Checking results; expect to discard most suggestions |
| **Reviewers built to imitate conference reviews and ratings** (the AI Scientist reviewer, OpenReviewer, DeepReviewer) | Curiosity about how a venue-style reviewer would score | Improving a draft |

## For an AI agent asked to review a draft

The same advice as instructions:

1. Ask for (or state your assumption about) the stage, the audience and what
   feedback is wanted.
2. Restate the claims before criticising, and flag where your reading may
   differ from the author's intent.
3. Build a claim-to-evidence map; for each gap offer both remedies: add
   evidence, or narrow the claim.
4. Give each finding a location, a quote, a reason and a severity; lead with
   the finding that touches the most central claim; keep the list short.
5. Open the code and result files when you have them, and recompute a
   headline number before commenting on it.
6. Do not judge novelty or importance from memory. Say that a human in the
   subfield or a literature search is needed, and cite anything you assert.
7. Say what you did not check, and say so plainly if you found nothing.
8. Flag; do not rewrite. The author's words stay the author's.
9. You share blind spots with the model that helped write the draft if it is
   your own family. Recommend a reviewer from another family and a human
   reader for the first-read test.

## Common questions

### Is an AI review enough before I submit?

No. It is a cheap extra reader with good breadth. It does not replace a human
first read (where did a person in your audience get lost), a human judgement
of whether the result matters, or someone opening the code.

### How many human readers do I need?

No source gives a number. The overlap figures (Liang et al.: two human
reviewers share roughly 29–35% of their points; Kim et al. measured 3% for
human cross-reviewer pairs) and the planted-error rates (one reviewer finds
about a third) both say the second and third reader find mostly new things.

### What is the single highest-value step?

The claim-to-evidence map, done by someone other than the author, with one
number recomputed from the artifact.

Last verified: 2026-11-10. New page. Every quotation and number was checked
against the raw source (page text, arXiv abstract or PDF, Europe PMC or
Crossref record); biomedical trials and most arXiv papers were checked at
abstract level. Not checked against the published text: Smith 1990
(paywalled; paraphrased, not quoted). One-line summaries are Claude's
wording, not the authors'. Drafted by Claude; pending MATS research-staff
review.
