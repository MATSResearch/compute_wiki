---
name: mats-lean-library-search
description: Find and adapt existing Lean or Mathlib declarations for a mathematical goal. Use when the obstacle is locating a lemma, definition, instance, or import in the project’s library version.
---

# Lean library search

Find a reusable declaration that matches the actual goal and environment.
Search depth and tools are choices, not a fixed sequence.

- Inspect the goal's types, structures, and hypotheses. Search by mathematical
  shape as well as names: an inequality might be a monotonicity lemma, and a
  concrete result may already follow from an abstract order or algebra lemma.
- Start with local source and the pinned dependency checkout, often under
  `.lake/packages/mathlib/Mathlib`. Use `rg` for declarations and nearby usages.
  Check available editor search and tactics such as `exact?` or `apply?` in
  that toolchain. Online search can suggest candidates but may index another
  revision; do not treat a web result as proof of local availability.
- Inspect the full declaration, including implicit arguments and typeclass
  assumptions. Compare direction, strictness, quantifier order, coercions,
  and side conditions with the intended goal.
- Test a candidate application in the actual local context. Use `#check` to
  inspect its type, then compile the proof using it. A matching name or type
  alone does not show that it closes this goal.
- Broader imports are useful during discovery. Once the proof works, use
  imports consistent with the project; do not spend disproportionate effort
  finding a mathematically minimal import set.
- If no candidate emerges, retain the useful search terms and closest results.
  Prove a helper lemma or reconsider the representation when that is more
  productive. An unsuccessful search does not establish library absence.

Return the declaration name, source/import, applicable hypotheses, and a
checked use, or identify what is still unverified. The
[shared guide](https://matsresearch.github.io/compute_wiki/engineering/lean-formalization/)
links maintained search resources; no external search service is required.
