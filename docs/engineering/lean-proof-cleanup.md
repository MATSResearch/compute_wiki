# Presentable Lean proofs

The `mats-lean-cleanup` skill offers editing guidance for generated or repaired
proofs. The optional [skill hint hook](skill-hints.md) points the agent to it
after a Lean edit, without requiring invocation or another editing pass.
Install the skill alongside the other [Lean skills](lean-formalization.md).
Explicit cleanup requests still call for doing the requested editing.

## What the comparison suggests

These are observed failure patterns and editorial heuristics, not a claim that
all AI proofs are worse than human proofs. Human drafts can have the same issues;
future models may already produce clean first drafts.

[Proof-Refactor](https://arxiv.org/html/2606.03743v1) compares generated proofs with
refactored versions on Putnam problems. In its 1968 B6 case study, the original
expands compactness into an open-cover argument. The edited proof isolates
useful facts about points outside compact sets and convergence, then uses an
existing compactness theorem. Merely moving the open-cover argument into a
specialized helper leaves much of the structural problem intact. The evidence
is limited: evaluation relies primarily on model judging, with a human-reviewed
subset, and does not establish effectiveness across whole research projects.

[Lean Refactor](https://arxiv.org/html/2605.20244v1) studies length, compilation
cost, and version compatibility as separate objectives. Its results motivate
checking performance and library version rather than assuming a short proof is
a better proof. Neither paper establishes that this skill will produce their
reported improvements; the guidance here is a design synthesis.

Mathlib's [review guide](https://leanprover-community.github.io/contribute/pr-review.html)
asks reviewers to consider supporting lemmas, proof structure, useful library
interfaces, and tactic choices that improve readability. Its
[style guide](https://leanprover-community.github.io/contribute/style.html)
provides local conventions, including a reason to retain ordinary closing
`simp` calls: expanding every dependency can obscure the interesting lemmas and
create more names that can break on renaming. Follow the target project's own
conventions when they differ.

## From a working draft to an edited proof

| Pattern to inspect | Useful edit | Reason to keep the original |
|---|---|---|
| Reproving a standard result from definitions | Apply an existing theorem with a small adaptation | The alternative requires inappropriate assumptions or unavailable imports |
| Long sequence of temporary facts | Keep named mathematical milestones; remove redundant plumbing | Explicit steps explain a delicate coercion or inference |
| Repeated nontrivial reasoning | Extract a helper with a natural, focused statement | The apparent repetition represents genuinely different arguments |
| Whole proof moved into `aux1` | Choose helpers at conceptual boundaries; leave the main argument visible | A private implementation lemma genuinely separates concerns |
| Search attempts and diagnostics left in source | Retain the successful argument and useful explanation | A diagnostic is an intentional project test |
| Large explicit simplification list | Retain only the control needed by subsequent steps | The explicit list stabilizes an intermediate form or improves performance |
| Broad automation hides the construction | Expose the witness or reduction and automate routine side goals | The whole result is routine in this context |
| Comments translating every tactic | Explain why a step is useful or mathematically subtle | The user requested a beginner tutorial |
| Global resource limits inherited from exploration | Test whether limits can be removed or localized | Checking a useful proof actually needs the resources |

Treat this table as questions to ask of the proof, not regex replacements.
Short facts named `h` are often perfectly clear. A long proof may be the right
representation of a long argument. Helper count and line count are diagnostics,
not acceptance criteria.

## Concrete editorial choices

Suppose a draft derives `h₁ : a = b`, then `h₂ : b = c`, then builds several
aliases of these facts before concluding `a = c`. If the aliases add nothing,
`exact h₁.trans h₂` exposes the transitivity step directly. When the equalities
are themselves a substantive derivation, a `calc` block with those explanations
may communicate more. Neither spelling should be imposed on every proof.

For a repeated estimate, distinguish the estimate's real parameters from local
variables accidentally present at the extraction site. A helper should state
the estimate with the hypotheses it uses; copying the whole surrounding context
into its signature makes reuse and comprehension harder. Keep the original
public theorem's interface stable while doing this.

When a closing `simp` is clear and fast, leave it. When a later rewrite depends
on the exact simplified shape, consider controlled simplification at that
location. Do not turn this choice into a universal ban on automation or a
universal demand for explicit lemma lists.

These are editorial examples, not compiled before/after Lean fixtures. An actual
rewrite must be checked in the target environment.

## The preservation boundary

The final proof should establish the same public proposition in the same intended
mathematical context. Holding the displayed theorem statement constant is not
enough if an edit changes a referenced definition, local instance, notation, or
implicit parameter. Keep those stable during routine cleanup. Renaming a public
theorem, changing its interface, or redesigning definitions is a separate change.

Compile the baseline and candidate using the pinned toolchain. Check the affected
module and dependents, and inspect the theorem's transitive axiom dependencies.
An imported unfinished helper can make a proof look complete; a successful exit
code alone will not detect every such case. Preserve the existing constructive
or classical assumptions, and report material changes rather than hiding them
as style edits. See [proof evidence](lean-formalization.md#interpret-the-evidence).

When compilation is unavailable, preserve the known checked artifact and label
the edited candidate unchecked. Avoid replacing a verified deliverable with an
unverified one simply because it looks better.

## Evaluate the skill on use

Use matched before/after tasks in a pinned project. Suitable cases include:

- A redundant draft, to check that scaffolding disappears while the statement
  and axiom dependencies stay the same.
- A long proof with a repeated estimate, to assess helper quality and whether
  the main argument becomes easier to follow.
- An already clean proof, to test whether the agent can leave it alone.
- A proof whose later rewrite needs a precise intermediate form, to detect
  careless simplification changes.
- A proof with a hidden incomplete dependency, to check honest reporting.
- A task without a working toolchain, to check preservation of the baseline
  and explicit uncertainty about the candidate.

Require verification and statement preservation, then assess readability,
meaningful decomposition, library reuse, and maintenance cost. Count all added
helpers when comparing size; moving text to another file is not compression.
For changes to expensive automation, compare check times under comparable cache
conditions. Human preferences or blinded comparisons are useful evidence for
readability; an agent's self-score alone is insufficient. Record regressions as
well as successes and adjust the skill to demonstrated failure modes.
