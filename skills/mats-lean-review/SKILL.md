---
name: mats-lean-review
description: Review whether a Lean theorem faithfully expresses an informal research claim and whether its proof evidence supports the reported conclusion. Use for formalization review, assumption audits, or interpreting a checked theorem.
---

# Lean formalization review

Assess statement fidelity and proof status separately. A successful build
answers only part of the research question.

- Compare the original claim with the actual elaborated declaration and its
  definitions. Inspect inferred types, instances, notation, and hidden
  parameters when they could change the meaning.
- Check quantifier order, domains, exceptional cases, and assumptions.
  Look for vacuity from contradictory hypotheses or empty domains, and for
  replacing the desired conclusion with an assumption. Concrete instances
  and counterexamples can help, but are not a universal extra requirement.
- Trace any bridge from the formal model to the scientific claim. Identify
  idealizations, approximation assumptions, and empirical premises that Lean
  has not established. Stronger premises or a narrower domain can still yield
  a useful theorem when the scope is stated honestly.
- Check the relevant source in its pinned environment, ensuring the target
  module is actually included. Record diagnostics and inspect
  `#print axioms FullyQualified.theoremName` for the claimed result.
  `sorryAx` signals an incomplete dependency; custom axioms make the result
  conditional. Standard classical axioms are not unfinished proofs, and
  `noncomputable` alone introduces neither an axiom nor a proof hole.
- Match additional verification to the project and theorem's role. For
  specialized validation, consult the version-appropriate official guidance
  linked below; do not introduce a new approval gate for routine proof work.

Report what claim was checked, statement mismatches, material assumptions,
proof status, and what conclusion follows. If Lean is unavailable, explicitly
label the review as static; do not claim compilation. Suggest a repair when
useful, preserving the original claim for comparison.

See the [shared guide](https://matsresearch.github.io/compute_wiki/engineering/lean-formalization/)
and [Lean's proof-validation reference](https://lean-lang.org/doc/reference/latest/ValidatingProofs/).
