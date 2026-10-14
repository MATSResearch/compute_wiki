# CLAUDE.md — Lean formalization project

Headline theorems are stated in `Statements.lean` and proved in `Solutions.lean`;
`lake comparator --paranoid` checks that the proofs prove exactly the statements.
Read `README.md` first (layout, evidence ladder, common errors).

## Rules specific to this project

- **`Statements.lean`, `Defs.lean`, `comparator.json` and `lakefile.toml` are the
  trusted challenge.** Don't edit them while proving. If a statement looks false,
  vacuous or mis-quantified, stop and report it with the counterexample or the
  missing premise, and propose the revised statement as a revision for the human
  to accept. A proof of a changed statement is a proof of a different claim.
- **Same name, same type.** Each theorem in `comparator.json`'s `theorem_names`
  is restated verbatim in `Solutions.lean` and proved there. Don't import
  `Statements` from `Solutions` (the names clash).
- **No new axioms, no `sorry`, no `native_decide` in a headline proof.** The
  permitted axioms are `propext`, `Quot.sound` and `Classical.choice`.
  `native_decide` asserts its evaluation as an axiom, so comparator rejects it.
- **Report the rung reached, not "it compiles".** Run `lake build`, then
  `lake check --paranoid`, then `lake comparator --paranoid` (Linux only), and
  report the highest one that passed with its exit status. On macOS, say the
  sandboxed checks were not run rather than using `--inadvisably-no-sandbox`.
- **Keep the statement table in the README current**: informal source, formal
  statement, solution location, and what the formal version leaves out.

## Conventions

- Keep `lean-toolchain` at v4.35.0 or later; an unrelated toolchain or Mathlib
  upgrade is its own change, not part of a proof task.
- Commit `lake-manifest.json`; the sandboxed commands cannot write it.
- Agent skills: use either the wiki's `mats-lean-*` skills or `lean4-skills`
  in this project, not both, so the agent follows one procedure.
