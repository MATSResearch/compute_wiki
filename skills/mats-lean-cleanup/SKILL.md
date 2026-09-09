---
name: mats-lean-cleanup
description: Edit working Lean proofs for mathematical readability, library reuse, and maintainability. Use automatically before presenting newly generated or substantially repaired Lean proofs as finished, as well as for explicit cleanup or refactoring requests. Preserve the theorem and verify the edited artifact in the pinned environment.
---

# Lean proof cleanup

Treat a first working proof as a draft. Before presenting completed Lean work,
perform a proportionate editorial pass without waiting for a separate cleanup
request. Respect requests for a raw draft, teaching walkthrough, or particular
style. An already clear proof may need no changes.

## Preserve the result

Keep a recoverable working version and establish its check status in the pinned
project. Preserve the public declaration's name, type, binders, universes,
assumptions, and the meanings of referenced definitions. Preserve downstream
interfaces, notation, and instances. Cleanup does not authorize changing the
problem, upgrading dependencies, or adding global simplification rules.

Inspect the target's transitive axiom dependencies before and after significant
rewrites. Do not introduce proof holes or silently expand the trusted assumptions.
If the baseline is incomplete, label it as such; formatting cannot complete it.

## Edit for the mathematical reader

- Identify the mathematical argument before shortening tactics. Prefer a
  relevant library theorem over a handwritten reconstruction. Verify its
  applicability in the pinned version.
- Remove redundant facts, duplicate branches, obsolete comments, diagnostics,
  and failed-search scaffolding. Resolve search suggestions to the successful
  proof when useful; keep normal automation that expresses routine reasoning.
- Give meaningful intermediate claims descriptive names and explicit types
  where they clarify the argument. A `calc` chain can expose a derivation;
  named cases can expose a split. Do not expand a clear one-line proof merely
  to follow a preferred format.
- Factor repeated or conceptually substantial reasoning into helpers with
  understandable statements and only the necessary parameters. Local `have`s
  and private lemmas are often enough. Avoid one-use wrappers that merely move
  the entire original proof elsewhere, and speculative generalization that
  overwhelms this task.
- Let `simp`, arithmetic tactics, and other suitable automation handle routine
  steps. Keep the key witness, invariant, or reduction visible when it carries
  the mathematical idea. Do not replace readable structure with an opaque
  tactic chain merely to reduce line count.
- Use targeted rewrites or `simp only` when a later step needs a controlled
  intermediate expression. Do not mechanically expand terminal `simp` into
  long lemma lists. Follow the project's style and available linters.
- Comments should explain choices and mathematical transitions, not narrate
  every tactic. Remove unnecessary resource overrides or imports only after
  checking; accept useful limits and imports when their removal adds fragility.

For difficult structural edits or examples of tradeoffs, read the
[cleanup guide](https://matsresearch.github.io/compute_wiki/engineering/lean-proof-cleanup/)
(`docs/engineering/lean-proof-cleanup.md` in the wiki checkout).

## Verify and finish

Check coherent edits incrementally and the final artifact in its real project,
including affected dependents. Compare the actual declaration and its context,
not just the visible theorem line. Check helpers as well as the main proof;
inspect warnings and axiom output, not only exit status. Measure compilation
when changing expensive automation or when a slowdown appears; fewer lines do
not imply faster checking.

Keep an edit only when it improves the intended reader's understanding or
maintenance without losing verification. Stop when remaining changes are
cosmetic preferences or their likely value no longer warrants the effort.
Use the existing task budget; no fixed number of passes or compression target.
Retain the best checked version if a candidate fails or runs out of time.

Present the cleaned proof first, a short explanation of its mathematical shape
when helpful, and the check result. Do not burden the user with the discarded
search transcript. If Lean is unavailable, keep edits as an explicitly unchecked
candidate alongside the last checked version; never imply the cleaned candidate
was verified. This is an agent workflow, not an enforced pre-send hook.
