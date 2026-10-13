---
tags:
  - engineering
  - alignment-science
---

# Theory Research Moves: What AI-Produced Mathematics Shows

How to work on theory-heavy safety problems (agent foundations, decision theory, learning theory, debate complexity, heuristic arguments) with an AI research agent, using what OpenAI's 2026 release of AI-produced mathematics shows about how the model actually reasoned. The moves below are each self-contained: name the barrier, restate the obstacle as an abstract core, check an imported theorem's hypotheses and conventions, test whether a claim proves too much, check for circularity, test candidate definitions against canonical cases, search in both directions, restart from a distilled technique, and run the cheap computation. For proof checking in Lean see [`lean-formalization.md`](lean-formalization.md); for the agent-foundations research landscape see [`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

## At a glance

| I want to… | Do this |
|---|---|
| Stop re-deriving an approach I already rejected | [Name the barrier](#name-the-barrier-that-killed-each-line) when a line dies, and reuse the name |
| Find a technique from another field | [Restate the obstacle as an abstract core](#restate-the-obstacle-as-an-abstract-core-then-retrieve-the-field-that-handles-it), then retrieve the field where that core is native |
| Import a theorem from another field safely | [Discharge every hypothesis and check conventions](#check-an-imported-theorems-hypotheses-and-conventions-at-the-import-point) at the import point |
| Sanity-check a candidate result | [Does it prove too much?](#does-it-prove-too-much-test-against-known-impossibility-results) Test it against known impossibility results |
| Check a reformulation helped | [Is it the original problem again?](#is-the-reformulation-just-the-original-problem-circularity-check) |
| Test a candidate definition (decision theory, corrigibility, agency) | [Run it on the canonical case bank](#canonical-case-bank-for-agent-foundations-and-decision-theory) |
| Get unstuck on a conjecture | [Search both directions](#search-both-directions-prove-and-refute) — assign a separate thread to refute it |
| Escape an argument that feels stronger than what I claim | [Restart from the distilled technique](#restart-from-the-distilled-technique-without-the-old-target) without the old target |
| Get intuition a proof sketch does not give | [Run the cheap computation or simulation](#run-the-cheap-computation-or-simulation) |
| Know which safety-theory problems suit AI help | [Theorem-shaped vs definition-bottlenecked](#which-safety-theory-problems-suit-ai-assisted-attack) |
| Track which results depend on which | [Type the dependency edges](#how-errors-spread-through-a-body-of-results-typed-dependencies) |

## What OpenAI's math release is, and what it shows

Aliases: `openai/math` on GitHub, "OpenAI math manuscripts", "OpenAI 719 manuscripts", "OpenAI open problems release", October 2026.

- **Size and process.** The README reports 719 manuscripts in 372 result families, produced by an unreleased internal OpenAI model. About 4,000 problems were posed, at an average of about three hours of ChatGPT Pro thinking compute per result, and outputs were kept after "requiring an appropriate level of significance". About 42% of top-line results (300 of 719, per `history.md`) have Lean formalizations, checked with the Comparator tool (trusted `sorry`-bodied statement, untrusted proof, axioms limited to `propext`, `Quot.sound` and `Classical.choice`).
- **Reasoning summaries.** Ten families come with abridged, after-the-fact, third-person summaries of the model's reasoning, with short verbatim excerpts. They are the evidence for the moves on this page. They are survivors of a large pool, so they show what worked, not how often.
- **What the problems were.** Named conjectures and open questions from recent papers; in a 71-family sample the commonest framing was finishing the remaining case after a recent reduction. Disproofs and counterexamples were a meaningful minority (62 of the 372 family blurbs in `CONTENTS.md` mention a counterexample, disproof, refutation or failure, about 17%). No family is about agent learning theory, decision theory or alignment, so the release says nothing directly about the definition-choice stage of safety theory.
- **Failure record.** The 2026-10-07 history entry records three manuscripts withdrawn (the notices are dated 2026-10-06) after a sign error in one construction invalidated it and two papers that adapted it; 14 others were revised. The withdrawn papers had no Lean formalization.

**When to use this page:** to borrow the reasoning moves for your own theory project, with or without an agent. **When not to use it:** as evidence that AI can do agent-foundations research — the release contains none, and the hard part there is usually choosing the formalism, not proving theorems.

## Name the barrier that killed each line

When an approach fails, write down **the obstruction that killed it**, in a few words that would fit another approach killed the same way ("circular: needs the conclusion", "loses a log factor per step", "no positivity", "Löbian obstacle"). When a later approach dies of the same thing, use the **same name**.

**Why.** The commonest waste in the reasoning summaries was re-deriving a rejection already made: in the arithmetic-progressions summary, Conlon–Fox–Zhao transference was reconsidered and set aside about a dozen times for the same reason (the two-sided linear-forms control it needs was missing), and in the π summary an earlier OpenAI result on Catalan's constant was cited as inspiration more than thirty times without ever becoming load-bearing. The productive pivots came from *recognising* a recurring obstruction and changing the architecture to avoid it — in the free-group-factor summary the model noted the recurring problem ("Same old.") and later in the same section turned from seeking an invariant that would separate the factors to constructing an isomorphism.

**How to apply.** Keep a short list of barriers and the approaches each killed. Before starting a new approach, say which barrier it gets around and how. A barrier that has killed three approaches is a signal to change the framing, not to try a fourth variant. In the MATS Automated Alignment tool a dead end can carry `barrier="…"`, and the tool shows a ledger of barriers with the lines each killed.

## Restate the obstacle as an abstract core, then retrieve the field that handles it

Cross-field technique transfer ("use a tool from another field") worked in the reasoning summaries when the obstacle was first boiled down to a **small abstract core** and the field where that core is native was then retrieved — not when the model reached for a field by analogy.

| Obstacle, as an abstract core | Field it came from | Example |
|---|---|---|
| Every local check passes, but a global object must still come out nonzero | Coding theory (quantum LDPC and high-dimensional-expander code constructions, credited as inspiration, not used as a theorem) | Kaplansky direct-finiteness counterexample in characteristic two |
| A positive lower bound is needed, but the natural expansion has signs that cancel | Stability and negative dependence (the summary uses both but names no source literature; the field label is a reading) | Spontaneous magnetization in the quantum Heisenberg ferromagnet |
| Behaviour must look fully independent, but only limited independence is available | Theoretical computer science (polylogarithmic independence fools AC⁰ circuits) | Two-point correlations of multiplicative functions |
| An extremal problem on convex symmetric sets | Pluripotential theory (extremal plurisubharmonic functions of convex symmetric real sets) | Symmetric Mahler conjecture |

**Most imports were set aside — quickly, on a named property.** Examples: Serre's positive-stress construction for Vlasov–Poisson, weighed against the indefinite Maxwell stress and not pursued; Bayesian-inference identities that do not transfer because "posterior-sampled observations and fractionally weighted observations have different laws". The triage mattered as much as the recall. Corpus-wide, clear cross-field transfers were rare (6 of 71 sampled families, about 8%), and even those usually built on earlier work that had made the bridge; most results were deep work inside one field.

**How to apply.** Write the obstacle in one or two sentences that someone from another field could read without your vocabulary. Ask which field treats that core as routine. Name the specific tool, list the structural properties its proof uses, and check each one in your setting before investing. The MATS Automated Alignment tool's **Bridge** ask does this from a dead end, drawing one obstruction shape at random from a list (`BRIDGE_SHAPES` in the dashboards repo).

## Check an imported theorem's hypotheses and conventions at the import point

Before using a theorem from elsewhere, list its hypotheses and say where each one is discharged in your setting, and check sign, orientation and normalization conventions at the exact point of use.

**Why.** The reasoning summaries repeatedly caught mismatches at this point. One example, in the Vlasov–Maxwell summary, is a continuation criterion stated for H⁵ fields when the problem supplied only smooth, bounded, finite-energy fields, so the model had to propose a reduction to meet it. Another, in the same summary, is a density normalization that had to be rescaled by 4π to match the cited formulation. The one cascading withdrawal in the release was exactly this failure: the Eliashberg–Murphy cancellation theorem, from symplectic topology, requires a zero signed double-point count, and a sign error in computing that count meant its hypothesis was not met.

## Does it prove too much? Test against known impossibility results

Before trusting a candidate result, ask what it would imply, and whether that contradicts something known. In the irrationality-exponent-of-π summary the word "Liouville" appears 16 times: any argument that would work for every transcendental number contradicts the existence of Liouville numbers ("Wait this would work for any transcend, contradiction with Liouville."), so a valid argument must use something specific to π. In the Heisenberg summary the model checked its construction did not "inadvertently prove more than intended".

**Known no-go results to test against in safety theory:**

- **Löb's theorem** and **Gödel's second incompleteness theorem** — limits on a system trusting its own proofs; behind the Löbian obstacle to self-trusting (tiling) agents.
- **Tarski's undefinability of truth** — a sufficiently expressive language cannot define its own truth predicate.
- **Arrow's impossibility theorem** and the **Gibbard–Satterthwaite theorem** — with three or more options, no rule turning individual rankings into a social ranking satisfies unrestricted domain, Pareto efficiency, independence of irrelevant alternatives and non-dictatorship together; and every deterministic, non-dictatorial voting rule that can elect any of three or more options is manipulable by some voter.
- **Armstrong & Mindermann, "Occam's razor is insufficient to infer the preferences of irrational agents"** (NeurIPS 2018, arXiv:1712.05812) — a policy cannot be uniquely decomposed into a planning algorithm and a reward, and a simplicity prior does not pick out the true decomposition.
- **Thornley's shutdown theorems** (arXiv:2403.04471) — agents meeting some innocuous-seeming conditions will often try to prevent or cause the pressing of their shutdown button, even at a cost.
- **No-free-lunch theorems** (Wolpert) — averaged uniformly over all possible target functions (or objective functions, for optimization), no algorithm outperforms another.

A definition of rational agency, corrigibility or honesty that escapes one of these without giving up one of its premises has probably made an error.

## Is the reformulation just the original problem? (circularity check)

After every reformulation, ask whether proving the new statement needs the old one. The reasoning summaries hit this repeatedly: "So pure union Mahler as hard as symmetric general!", and an operator-algebraic route in the two-point-correlations summary that lacked "a missing tracial property closely related to the desired cancellation", meaning the route needed something close to the conclusion as an input.

**Agent-foundations version:** a decision rule that presupposes the counterfactual it was meant to define, or an oracle or fixed point whose existence already encodes the conclusion.

## Canonical case bank for agent foundations and decision theory

The Mahler-conjecture summary repeatedly tested candidate inequalities against a stock of extreme bodies (simplex, ball, cube, Hanner polytopes, cones, the 24-cell) and checked them against the known equality cases. The agent-foundations equivalent is a fixed set of problems every candidate decision rule, definition of agency or corrigibility proposal is run against before anything else:

| Case | What it tests |
|---|---|
| **Newcomb's problem** | Whether the rule accounts for a reliable predictor of its own choice |
| **Transparent Newcomb** | The same when the agent can see the box contents (the predictor's move) before choosing |
| **Parfit's hitchhiker** | Whether the agent pays after being rescued, when the rescue depended on a prediction that it would pay but paying no longer causes anything |
| **Counterfactual mugging** | Updatelessness: paying after losing a coin flip, because the predictor rewards, in the branch that did not happen, agents who would pay |
| **Smoking lesion** | Whether the rule mistakes correlation for causation (the classic objection to evidential decision theory) |
| **Death in Damascus** | Choice when a predictor tracks you wherever you go (instability, ratifiability) |
| **Absent-minded driver** | Imperfect recall: planning-optimal vs action-optimal choices |
| **5-and-10 problem** | Spurious counterfactuals: a proof-based agent can "prove" that taking $10 yields less and take $5 |
| **Troll Bridge** | A Löbian argument leading a proof-based agent to judge a safe action bad |
| **Prisoner's Dilemma with a twin / source-code-sharing agents** | Cooperation between agents that can read or predict each other (FairBot, program equilibrium) |
| **Procrastination paradox** | An agent that trusts its successor can defer forever (tiling) |
| **Sleeping Beauty** | Credences under memory erasure and a variable number of awakenings (anthropics) |

**How to apply.** For each candidate, write its verdict on every case before proving anything about it, and report which desiderata it gives up. ARC's builder–breaker methodology for ELK, and Thornley's use of his shutdown theorems as a search guide (to be sure an agent won't manipulate the button, "we must be sure that this agent violates at least one of the theorems' conditions"), are this loop done by hand.

## Search both directions: prove and refute

Run a refutation attempt alongside the proof attempt, ideally as a separate thread or person that has not invested in the claim. In the reasoning summaries the decisive turns were often reversals: Kaplansky's direct-finiteness conjecture answered with a counterexample, a free-group-factor search for a distinguishing invariant that turned into a constructed isomorphism, and a hardness question posed as a way around the Unique Games Conjecture that the model found would already imply it. The prompts made refutation an explicit, specified outcome ("A disproof must provide…"; "A finitely presented group together with unproved word equalities or inequalities is not a certificate").

**Refutation routes, cheapest first:** hunt the hypotheses for the weakest one and the most extreme object it allows; look for a counterexample at the smallest size and check it against every hypothesis; test whether the claim proves too much; check whether the claim or its argument is circular. In the MATS Automated Alignment tool, **Refute in a new thread** on a registered prediction opens such a thread.

## Restart from the distilled technique, without the old target

In the irrationality-exponent-of-π summary, the first run's argument suggested exponents approaching two (section 36) and "appeared to accommodate every μ>2" (section 37), yet it kept the weaker 62/25 bound through eight more audit sections, to the end of the run. A separate run, seeded with the technique but not the earlier bound, proved the irrationality exponent of π is 2. When an argument looks stronger than the claim you are defending, and repeated audits find no flaw, start fresh from the technique with the target left open.

## Run the cheap computation or simulation

None of the ten reasoning summaries reports a numerical experiment or toy computation, even where one was cheap (a Monte Carlo of the process being studied, the parameter bookkeeping a proof solved by hand over several sections); at least one prompt discouraged "brute-force enumerations and computer-assisted proofs" in the final writeup, which may account for part of this. The general-case Mahler attempt ended conditional on scalar inequalities, reduced to positivity of polynomials of degrees 30 and 32, that interval arithmetic or a computer-algebra certificate could have checked. In agent-foundations and safety theory, numerics have mattered: for natural latents, numerical optimisation put the stochastic-to-deterministic constant near 1.8 and counterexamples to a step of an earlier proof were evaluated in sympy (Harwood & Gillen, LessWrong 2026-01-08), and ARC's heuristic-estimation work benchmarks mechanistic estimates against sampling.

**Simulation kinds a theory researcher may not think of:** agent-based models; voting and aggregation simulations (several rules, correlated voters, strategic misreports); iterated-game tournaments with strategies that read each other's source; markets and auctions; exhaustive search over small cases; Monte Carlo over random instances; an optimizer searching for the worst case; small toy environments; dynamics (best response, replicator, gradient flow); a few language-model agents in a scripted interaction. Write down what result would count against the claim before running, state what the toy model keeps and drops, and say how far the result transfers. In the MATS Automated Alignment tool, **Simulate** draws one kind at random.

## Persistence is mostly adversarial audit

In the reasoning summaries the line that worked usually arrived late (section 31 of 44 in the π run, 11 of 22 in the Kaplansky run, 5 of 12 in the semidefinite-threshold run) and was followed by an audit phase taking roughly 30–60% of the summary: propose, attack the construction, repair it locally, attack again. Quantifier order and order of limits were checked explicitly in nearly all ten ("all auxiliary constants are fixed before choosing the small parameter"). Model enthusiasm was not a signal: of roughly a dozen moments flagged as breakthroughs ("This is a breakthrough possibility!", "Great!", "This could solve!"), about half or more were abandoned or failed within the same section.

## How errors spread through a body of results: typed dependencies

In the release, more than half of the manuscripts cite another manuscript in the collection, citation chains run around ten manuscripts deep, and over a hundred pairs cite each other. The one cascading withdrawal spread through **reused constructions** — two papers relied on "an adaptation of the flawed stabilization-trace construction" — not through a cited theorem. Conditional companions on the same topic ("A implies B", e.g. "A Conditional Reduction for Algebraic Kuga–Satake Correspondences") stayed in the collection when the unconditional papers were withdrawn. About half of the 14 revisions were dependency hygiene (stating the hypotheses of inputs, declaring that only independent results were used from mutually citing companion papers, removing an unneeded or obsolete citation); most of the rest supplied an argument or estimate that had been used without proof, and three corrected an argument or a statement.

**How to apply.** Record what each claim depends on, and *how*: uses a theorem at a stated scope, adapts a construction or proof internals, or only cites. When something is revised, re-check everything that adapted its internals, not just what cited its statement. Keep conditionals as claims in their own right.

## Formal verification checks the statement, not its meaning

A Lean proof checked with Comparator proves exactly the Lean statement. Whether that statement means what the paper claims is a separate question: in the release the papers come from an OpenAI model, the formalization catalogue lists its method as `agent` and records statement review as `unchecked`, and about 400 of the 416 Comparator statement files define their own objects. Sienicki & Sienicki's audit of OpenAI's earlier ten results (arXiv:2608.14673) makes the same point: a successful Lean check establishes "the encoded proposition relative to the kernel, definitions, imported results, and axioms", and "human scrutiny still has to establish the intended meaning of that proposition". For agent-foundations objects there is no maintained library, so the definitions — the part most likely to be wrong — are written fresh each time. Write a short scope note per formal result: what the formal statement covers, and what the informal claim adds. Tooling: [`lean-formalization.md`](lean-formalization.md).

## Which safety-theory problems suit AI-assisted attack?

**Theorem-shaped, with existing toolkits** — the regime the release demonstrates:

| Problem | Source |
|---|---|
| Shave a factor (depth, branching, stability or error) off the estimator's circuit-complexity bound in prover-estimator debate, or show the bound is tight; find a better stability notion than (ε, ρ)-stability, which costs a 2^q factor | UK AISI Alignment Project, computational complexity page; Brown-Cohen, Irving, Piliouras et al., arXiv:2506.13609 |
| Prove or refute the computational no-coincidence conjecture | ARC, "A computational no-coincidence principle" (Neyman, 2025-02-14); listed as a problem on the UK AISI complexity page |
| Mechanistic estimation that competes with sampling for half-space intersections with arbitrary covariance (the post solves the isotropic case and, its authors believe, a restricted family of covariances), or for narrow, finite-width random MLPs | ARC, "Competing with sampling" (2025-11-18) |
| Natural latents: (∃ stochastic) implies (∃ deterministic) is now proved in Lean with constant C ≤ 1771; bring C toward the empirical value near 2 and find a readable proof | Wentworth & Lorell bounty post (2025-04-21); Lorell, "Redux" (LessWrong, 2026-08-11) |
| Learning-theoretic agenda problems (comparing agency-measure variants, Direction 17.1; whether logit equilibria of finite-state repeated games converge to Pareto efficiency, Direction 14; whether Bayes-optimal planning is NP-easy, Direction 7.2) | Kosoy, "The Learning-Theoretic Agenda: Status 2023" (2023-04-19) |
| Exactly which equilibria simulation-based program equilibria can attain without shared randomness | Cooper, Oesterheld & Conitzer, arXiv:2412.14570 ("It remains an open question exactly which equilibria can be attained.") |

**Bottlenecked on choosing definitions** — the regime the release does not touch: logical counterfactuals (functional and updateless decision theory), what makes a heuristic argument "mechanistic", the "knowledge" in eliciting latent knowledge (ELK), consequentialist or agent-like structure, what corrigibility should mean, independence of evidence in debate. Here the useful loop is: propose a formalism, derive its verdicts on the [canonical case bank](#canonical-case-bank-for-agent-foundations-and-decision-theory), and report which desiderata it gives up. The bottleneck in these areas is usually the definition, not proof search — ARC, for instance, writes in "Competing with sampling" that "We do not have a formal definition of 'mechanistic.'"

## Common questions

### Can an AI agent do agent-foundations research now?

It can do much of the proof search and counterexample search on theorem-shaped problems. The 2026 OpenAI release is strong evidence for classical, well-posed conjectures, and contains no agent-foundations problems; the closest agent-foundations cases are the two natural-latents bounty problems, one proved and one refuted in mid-2026 with heavy use of LLMs and Lean (Wentworth, "LLMs Are Starting To Noticeably Accelerate Our Work", LessWrong 2026-08-11: "about 80% confident that both have been resolved"); the proof is machine-checked but has no prose version. Choosing the right definitions is where the field says it is stuck, and nothing in the release tests that. Treat the agent as a fast, broad, fallible collaborator, and keep the definitions and the canonical-case verdicts under your own review.

### How do I get an AI to find techniques from other fields?

Restate the obstacle as an abstract core first, then ask which field handles that core routinely, then check the imported tool's hypotheses and conventions in your setting. Asking "what would a physicist do?" without the core tends to give analogies rather than tools.

### Should I trust it when the model says "this solves it"?

No. In the reasoning summaries about half or more of the moments the model flagged as breakthroughs were abandoned or failed. Trust the audit, not the excitement.

---

Last verified: 2026-10-13. OpenAI release facts (manuscript and family counts, problem count, compute per result, 300/719 formalization share, Comparator `sorry`-bodied statements and the three-axiom allowlist in all 416 challenge configs, `method: agent` and `review: unchecked` in `lean/formalization.yaml`, local definitions in 403 of 416 statement files, the 2026-10-07 `history.md` entry, the three withdrawal notices dated 2026-10-06 with their "adaptation of" wording and Eliashberg–Murphy hypothesis, the version notes of the 14 revised manuscripts, absence of the withdrawn papers from the formalization catalogue, 62 of 372 counterexample/disproof family blurbs in `CONTENTS.md`) read from the `openai/math` repository on 2026-10-13. Every quote, section position (π 31/44 and 36–44; Kaplansky 11/22; semidefinite threshold 5/12), the Liouville count (16, in both the PDF text and the markdown conversion), the breakthrough-marker outcomes, the Conlon–Fox–Zhao (about a dozen) and Catalan-paper (35 in-text) citation counts, and each field-transfer example checked against the ten reasoning-summary PDFs in `reasoning_traces/`. Citation-graph figures recomputed from a parse of the collection's bibliographies (412 of 719 manuscripts cite another; 111 mutual pairs; longest chain 8–13 depending on how cycles are treated); the 6-of-71 cross-field sample is from an earlier agent's read of introductions and was not re-sampled. arXiv 2506.13609, 2412.14570, 2403.04471, 1712.05812 and 2608.14673 (v1–v3 full text) checked against the arXiv API and PDFs; ARC "A computational no-coincidence principle" and "Competing with sampling", and the UK AISI Alignment Project complexity page, fetched 2026-10-13; LessWrong posts e9KwDDdAxborNSuCd (2025-04-21), TgboJpeN95bs84odk (2026-08-11), 7QvKqpGJwqXrQcMgx (2026-08-11), 4q3kMfJHB4rxr3Z8m (2026-01-08) and ZwshvqiqCvXPsZEct (Kosoy LTA, 2023-04-19; Directions 7.2, 14, 17.1) read via GraphQL. Verification pass 2026-10-13: 96 claims checked, 37 corrected (withdrawal-notice date; tracial-property example softened from "assumed the conclusion"; arXiv:2506.13609 author list; repeated-rejection and inspiration examples named and recounted; free-group-factor pivot; Kaplansky inspiration-only credit; Heisenberg field label; stress-tensor import "set aside", not rejected; cross-field 8% re-described as transfers, not first imports; Vlasov–Maxwell examples; Eliashberg–Murphy named; Arrow, Gibbard–Satterthwaite, Armstrong–Mindermann, Thornley and no-free-lunch one-liners tightened; Parfit's hitchhiker, transparent Newcomb, counterfactual mugging and Sleeping Beauty descriptions corrected; Thornley quote made verbatim; Mahler test-body claim narrowed; UGC reversal re-described; π audit span "about ten" to eight sections; prompt discouraging computer-assisted proofs noted; natural-latents numerics re-described; "all ten" quantifier checks to nearly all; "This could solve!" statistic re-based on all flagged moments; citation-graph figures; revision breakdown; Sienicki quote replaced with verbatim text; formalization authorship; prover-estimator and no-coincidence problem statements; ARC MLP problem is narrow width, not growing depth; natural-latents theorem now proved, C ≤ 1771; definition-bottleneck sentence sourced to ARC).
