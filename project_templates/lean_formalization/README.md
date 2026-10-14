# Lean formalization template (Statements.lean / Solutions.lean + `lake comparator`)

A starting Lean 4 project for a research result whose headline theorems should
be **machine-checked against statements a human reviewed**. The theorems are
stated once, with `sorry` bodies, in `Statements.lean`; the proofs live in
`Solutions.lean`; and `lake comparator` (built into Lake since Lean v4.35.0,
released 2026-10-12) checks on every push that the proofs still prove exactly
those statements. A reviewer reads one short file instead of the whole proof
development, and an agent proving things cannot quietly weaken a claim to make
it provable: a changed statement fails the check.

Wiki doc: [`docs/engineering/lean-formalization.md`](https://matsresearch.github.io/compute_wiki/engineering/lean-formalization/)
(evidence ladder, trust caveats, agent tooling). Read it first; this directory
is only the scaffold.

No `components/` or `example_projects/`, unlike the Python templates beside it:
the whole directory is the project. Copy it and edit.

## Layout

```
lean_formalization/
├── lean-toolchain              # leanprover/lean4:v4.35.0 (the first release with lake comparator)
├── lakefile.toml               # three libraries; default target = Solutions only
├── comparator.json             # challenge/solution modules, theorem names, permitted axioms
├── Defs.lean                   # TRUSTED: definitions the statements mention
├── Statements.lean             # TRUSTED, human-reviewed: headline theorems with `sorry` bodies
├── Solutions.lean              # UNTRUSTED until comparator passes: same names, with proofs
├── CLAUDE.md                   # rules for an agent working in the copy
└── .github/workflows/lean-verify.yml   # lake check --paranoid + lake comparator --paranoid on push
```

**What is trusted.** Comparator's guarantee is relative to the challenge: the
statement file, everything it imports (here `Defs.lean`, plus any library such
as Mathlib), and `lakefile.toml`. Keep definitions the statements depend on in
`Defs.lean` (or another small, reviewed module), not in the proof library,
because a definition the statement mentions is part of what the statement means.

**Why `Solutions` is the only default target.** `lake check` checks the default
targets and rejects any non-standard axiom, and the `sorry` bodies in
`Statements.lean` count as one (`Axiom 'sorryAx' is not permitted`). `lake
comparator` builds the challenge module itself, so it does not need it to be a
default target.

**The example theorems are placeholders** (`double n = 2 * n`, commutativity of
addition) so the scaffold has something to check. This template has not been
compiled by the wiki maintainers; the first `lake build` in your copy is the
first check of it.

## Quick start

```bash
cp -r project_templates/lean_formalization ~/projects/my_formalization
cd ~/projects/my_formalization
lake build                       # writes lake-manifest.json: commit it
lake build Statements            # the statements must elaborate; expect "declaration uses 'sorry'"
lake check --paranoid            # Linux only: whole-project kernel + axiom check
lake comparator --paranoid       # Linux only: Solutions proves exactly Statements
```

Then replace the placeholders: state each headline theorem in
`Statements.lean`, list its fully qualified name in `comparator.json`'s
`theorem_names`, and prove it under the same name in `Solutions.lean`. To use
Mathlib, uncomment the `[[require]]` block in `lakefile.toml` (Mathlib tags its
releases by toolchain, so `rev = "v4.35.0"` matches this `lean-toolchain`), or
start from `lake new <name> math` and copy the three Lean files and
`comparator.json` across.

## Statement table (fill in, keep current)

One row per entry in `theorem_names`. This is what a reader checks; comparator
checks the rest.

| Informal source | Formal statement | Solution | What the formal version leaves out | Highest rung passed |
|---|---|---|---|---|
| (placeholder) "doubling is multiplying by two" | `Template.double_eq_two_mul` in `Statements.lean` | `Solutions.lean` | — | not yet run |
| (placeholder) commutativity of `+` on `Nat` | `Template.add_comm_example` in `Statements.lean` | `Solutions.lean` | — | not yet run |

## `comparator.json`

The keys, from `lake help comparator` at the v4.35.0 tag:

| Key | Required | Meaning |
|---|---|---|
| `challenge_module` | yes | Module with the trusted statements (`"Statements"`) |
| `solution_module` | yes | Module with the proofs (`"Solutions"`) |
| `theorem_names` | yes | Fully qualified names to judge, e.g. `"Template.double_eq_two_mul"` |
| `permitted_axioms` | yes | Deliberately not defaulted: "it is what the verdict means". `["propext", "Quot.sound", "Classical.choice"]` is the clean-proof set |
| `definition_names` | no | Definition holes: `sorry`-bodied `def`s the solution fills in |
| `external_kernels` | no | Extra checkers to run over the export, each as a command, e.g. `{"nanoda": ["nanoda_bin"]}`. `--paranoid` already runs the bundled ones |
| `enable_nanoda` | no | Still accepted; equivalent to a `"nanoda"` entry of `["nanoda_bin"]` |

A known trap with **definition holes**: comparator checks that the solution's
definition has the same name, type, universe levels and safety level and uses
only permitted axioms, but not that it is the definition you meant. The
comparator README's example: a challenge `def ChallengeSolution : Prop := sorry`
with `theorem challenge : RiemannHypothesis ↔ ChallengeSolution` is "solved" by
defining `ChallengeSolution := RiemannHypothesis`. Every filled definition hole
needs a human (or other independent) check.

A second trap: `native_decide` and `bv_decide` work by asserting native
evaluations as axioms (Lean v4.35.0 release notes), so a proof that uses them
falls outside the three permitted axioms and is rejected. Remove them from the
headline proofs, or widen `permitted_axioms` and say so in the write-up.

## Evidence ladder: which rung did the result reach?

Report the highest rung a result passed, not just "it compiles". Each rung
guards against more than the one before it (ordering follows the Lean
reference chapter "Validating a Lean Proof"; the `lake` rungs need Lean ≥ v4.35.0):

| Rung | Command | Catches | Still trusts |
|---|---|---|---|
| 1 | `lake build`, no `declaration uses 'sorry'` warning | Unfinished proofs in the built files | Every tactic, macro and imported library |
| 2 | `#print axioms Template.double_eq_two_mul` | `sorryAx` and custom axioms anywhere in the dependency tree | The elaborator and the build |
| 3 | `lake check` | The same axiom check over every default target, after a sandboxed build, export and replay through the kernel in a separate process | That the theorems are the ones you meant; Lean's kernel |
| 4 | `lake check --paranoid` | A bug in Lean's kernel that one of the bundled checkers (`leanchecker-paranoid`, `lean4lean`, `nanoda`, `con-leche`, `con-ron`) does not share | That the theorems are the ones you meant |
| 5 | `lake comparator --paranoid` against a reviewed `Statements.lean` | A proof of a different (weaker, reordered, vacuous) statement; forbidden axioms; malicious proof code | The challenge files, the bwrap sandbox, and that at least one checker is correct |

Rung 5 still says nothing about whether `Statements.lean` captures the
informal claim. That is what the [statement table](#statement-table-fill-in-keep-current)
is for: one row per headline theorem with the informal source (paper,
equation, lemma), the formal statement, the solution's location, and anything
the formal version leaves out (a limit without its rate, a stronger
hypothesis), the way the archived Timaeus `laplace` repository's README did.

## Linux, macOS and containers

- **The sandbox is Linux-only** (Lean v4.35.0 release notes). `bwrap` needs
  unprivileged user namespaces or a setuid install. On macOS the commands
  cannot sandbox; run them in CI, on a Linux box, or in a Linux VM.
- **Containers often block user namespaces.** Lean's own test suite says
  "User namespaces cannot be assumed available in CI containers" and swaps in
  a fake `bwrap` for that reason. A fake or disabled sandbox gives no
  isolation.
- `--inadvisably-no-sandbox` turns the sandbox off; its help text says it "can
  compromise the result fully". Lake prints `WARNING: Sandbox disabled, this
  run is not trustworthy.` Reasonable only for your own code on a machine you
  don't mind it touching, and never for a solution someone else wrote.
- `COMPARATOR_BWRAP` points Lake at a `bwrap` that is not on `PATH`.

## Common errors

| Message or exit status | Meaning |
|---|---|
| ``has no `lake-manifest.json` `` (exit 2) | Run `lake build` once and commit the manifest; the sandbox cannot write it |
| ``needs `bwrap` to sandbox the code it checks, and it was not found`` (exit 2) | Install `bubblewrap` (Linux) or set `COMPARATOR_BWRAP` |
| `bwrap: setting up uid map: Permission denied`, `bwrap: Creating new namespace failed` | No unprivileged user namespaces; on Ubuntu check `kernel.apparmor_restrict_unprivileged_userns` |
| `Axiom 'sorryAx' is not permitted; it is used by '...'` (`lake check`, exit 1) | A `sorry` somewhere in the proof's dependency tree |
| `Illegal axiom detected: '...'` (`lake comparator`, exit 1) | The solution uses an axiom outside `permitted_axioms` (in Lean's own test, a custom `axiom helper` that the theorem's proof uses) |
| `Const does not match between challenge and target '...'` (exit 1) | The solution's statement or definition differs from the one in `Statements.lean`/`Defs.lean` |
| `Challenge and solution constant kind don't match: '...'` (exit 1) | Same name, different kind, e.g. an `axiom` where the challenge has a `theorem` |
| `malformed configuration in 'comparator.json'` (exit 2) | Bad JSON or a missing required key |
| `<checker> kernel rejected the solution` (exit 1) | One of the checkers rejected it; the others still report |
| `Your solution is okay!` (exit 0) | Accepted |

## Using this on a shared result, or someone else's

The workflow is a **drift check** for your own repository: it builds the
project outside the sandbox (via `leanprover/lean-action`) before the sandboxed
checks, which is fine for code you wrote. To judge a solution someone else
wrote, use a trusted Linux host and a fresh checkout with a committed
`lake-manifest.json`, and run `lake comparator --paranoid` without building
first, so the untrusted code is only ever built inside the sandbox. An export
built elsewhere (in a VM, or by someone with more compute) can be judged with
`lake comparator --solution-from-export <file>` or `lake check --from-export
<file>`; note that these check the export, not that it matches the project in
the current directory.

## On toolchains older than v4.35.0

The standalone [`leanprover/comparator`](https://github.com/leanprover/comparator)
binary is the legacy route. Its README now says it "has been merged into core
as of Lean release v4.35.0" and advises migrating, since the Lake commands "are
the only ones guaranteed to receive further security and performance
improvements". It needs `landrun` built from source, a `lean4export` matching
your toolchain, and (per its README) a `systemd-run` wrapper guarding a
`landrun` sandbox escape fixed in Linux 7.1; `scripts/fake-landrun.sh` disables
the sandbox. Upgrading the toolchain is usually the better path.

## Also available as

- **The wiki page**, with the evidence ladder and trust caveats:
  [`lean-formalization.md`](https://matsresearch.github.io/compute_wiki/engineering/lean-formalization/).
- **Agent skills**: `skills/mats-lean-formalization`, `mats-lean-review`,
  `mats-lean-debug`, `mats-lean-library-search`, `mats-lean-cleanup` in the
  wiki repo; or Cameron Freer's `lean4-skills` plugin. Pick one set per project.

Last verified: 2026-10-14, against `src/lake/Lake/CLI/Help.lean` and
`src/lake/Lake/CLI/Check.lean` at the `v4.35.0` tag of `leanprover/lean4`, the
Lake tests `tests/lake/tests/challenge-simple-match`, `check-sorry` and
`check-paranoid` at that tag, the v4.35.0 release notes on lean-lang.org, the
`leanprover/comparator` README, `leanprover/lean-action`'s `action.yml`
(v1.6.2), and the `timaeus-research/laplace` README and workflow (pattern only;
that repository has no licence, so nothing here is copied from it).
