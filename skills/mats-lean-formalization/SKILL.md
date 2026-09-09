---
name: mats-lean-formalization
description: Turn mathematical or theoretical claims into small, checkable Lean formalizations and explain exactly what the checked theorem does and does not establish. Use when a research task involves Lean, Mathlib, proof sketches, theorem statements, or mechanized verification; skip it for ordinary coding or informal mathematics that does not benefit from a proof assistant.
---

# Lean formalization

Use Lean as an executable specification and proof checker for the part of a
research claim that can be made precise. Preserve room to choose definitions,
proof architecture, and automation; the important invariant is that the
resulting artifact is checked in the project's actual Lean environment.

## Before proving

- Write the informal claim and its intended scope in one or two sentences.
- Decide whether formalization will clarify a definition, expose a hidden
  assumption, provide a reusable lemma, or check a proposed derivation. Do not
  force empirical or semantic claims into Lean when the missing work is
  measurement or interpretation.
- Make the objects, quantifiers, types, edge cases, and assumptions explicit.
  Check whether a hypothesis makes the target vacuous or stronger than the
  informal claim.
- Search the project's existing code and Mathlib before introducing a new
  definition or reproving a standard result. Prefer the smallest useful
  theorem and imports that preserve the intended meaning.

## While formalizing

- Start with a minimal theorem or `example`, then split it into named lemmas
  when that improves reuse or diagnosis. Let the model choose tactics and
  proof structure when several are reasonable.
- Compile with the repository's pinned toolchain and imports (for example,
  `lake env lean File.lean` or the project's documented build command).
  `#check`, a plausible proof in prose, or a tactic suggestion is not a
  checked proof.
- If compilation fails, classify the failure: statement or type mismatch,
  missing library fact, proof gap, or environment/toolchain problem. Preserve
  a useful reduced example instead of hiding the failure behind broader
  imports or stronger assumptions.
- For a completed theorem, inspect `#print axioms theoremName`, including
  transitive dependencies. `sorryAx` indicates an incomplete proof; custom
  axioms make the result conditional. Standard classical axioms are distinct
  from proof holes. `noncomputable` concerns code generation and is not itself
  an additional axiom or evidence of an incomplete proof.

## Report the result

For each formalized claim, report the informal claim, the Lean theorem name
and file, exact imports/toolchain, command and result, assumptions and axioms,
and any gap between the formal statement and the intended interpretation.
Use the [formalization record](references/formalization-record.md) when a
claim will be revisited or cited. Keep the checked theorem separate from the
informal scientific conclusion: Lean verifies the encoded proposition, not
that the encoding is the right model of the world.

For focused help, use `mats-lean-debug`, `mats-lean-library-search`, or
`mats-lean-review` if installed. Each works independently; load only what helps
the current task. The [shared guide](https://matsresearch.github.io/compute_wiki/engineering/lean-formalization/)
covers environment setup, search resources, and evidence interpretation.
