---
name: mats-lean-debug
description: Diagnose failing Lean proofs, elaboration errors, missing imports, and proof-search timeouts while preserving the intended theorem. Use when a Lean artifact fails to check or a proof attempt is stuck.
---

# Lean proof debugging

Aim for a checked repair that preserves the intended theorem. Choose the
proof strategy and search effort to fit the problem and authorized budget.

- Reproduce the first relevant diagnostic in the pinned project environment.
  Inspect `lean-toolchain`, Lake configuration, and dependency manifest before
  treating a missing module or unavailable tactic as a mathematical failure.
  Preserve dependency pins unless a migration is part of the task.
- Inspect the goal and local context where the failure begins. Distinguish
  elaboration/coercion/typeclass errors from an unsolved mathematical goal.
  A later cascade of errors often disappears after the first repair.
- Reduce to a useful local example when diagnosis is unclear. Make inferred
  types and implicit arguments explicit as needed; inspect namespace and
  notation resolution before changing the mathematics.
- For search timeouts, try a relevant intermediate lemma, narrower simp set,
  or different decomposition. Increasing a local resource limit can be
  reasonable when there is evidence of progress; a timeout is not evidence
  the proposition is false. Avoid global unlimited search as a default.
- Preserve the original target while experimenting. If a counterexample or
  missing premise emerges, explain it and present a revised conjecture as a
  revision, rather than quietly weakening the theorem to get a green check.
- Recheck the repaired declaration and affected dependents. For a completed
  result, inspect its axiom dependencies; temporary holes remain unfinished
  work even when the command exits successfully.

Before presenting a completed repair, perform a proportionate cleanup pass
(`mats-lean-cleanup` if installed), preserve the target, and recheck the final
artifact. Keep an already clear repair as it is.

Report the cause, meaningful repair, check performed, and remaining gap.
Read the [shared guide](https://matsresearch.github.io/compute_wiki/engineering/lean-formalization/)
for environment and evidence conventions when needed.
