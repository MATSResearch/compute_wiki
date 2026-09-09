# Lean for theory research

Formalization is useful when precise definitions, a checked derivation, or a
reusable theorem would advance the research. Choose the subclaim with the
highest value; a whole paper need not be formalized for a lemma to be useful.
The agent can choose proof methods, automation, and decomposition within the
project's existing resource and delegation arrangements.

## Choose the help you need

The [repository's skills](https://github.com/MATSResearch/compute_wiki/tree/master/skills)
can be installed individually or alongside the other MATS skills. Each works
independently; they do not require loading the whole set.

| Skill | Useful outcome |
|---|---|
| `mats-lean-formalization` | Translate an informal claim into a precise, checked artifact |
| `mats-lean-debug` | Diagnose a failed check and repair the proof without quietly changing the claim |
| `mats-lean-library-search` | Find a declaration that works in the pinned library revision |
| `mats-lean-review` | Assess statement fidelity, assumptions, and what the checked proof establishes |

## Work in the actual environment

Use the existing `lean-toolchain`, Lake configuration, and dependency manifest.
Record the project revision. For a new project, choose compatible Lean and
Mathlib versions using the current [Mathlib setup guide](https://leanprover-community.github.io/get_started.html),
then preserve the resulting pins. An existing proof task rarely warrants an
unrelated dependency upgrade.

From the project root, a typical targeted check is:

```bash
lake env lean path/to/File.lean
```

Also use the project's normal build for affected dependencies. Confirm the
relevant module is included in its build targets. Capture warnings as well as
exit status: successful execution can coexist with unfinished proofs.
If the toolchain is unavailable, retain the artifact and report it as unchecked.

## Search before rebuilding mathematics

Use the local dependency source as the authority for available declarations.
The [Mathlib documentation](https://leanprover-community.github.io/mathlib4_docs/)
and [Loogle](https://loogle.lean-lang.org/) can suggest definitions and lemmas;
verify candidates against the project's revision. Search by the shape of a
statement and the structures involved, not only an expected theorem name.
The [Lean tactic reference](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/Tactic-Reference/)
describes search tactics such as `exact?` and `apply?`; availability and behavior
should be checked in the pinned environment.

## Interpret the evidence

Keep the informal claim next to the theorem's actual type, relevant definitions,
assumptions, and check result. For example, exchanging “for every policy there
exists a bound” with “there exists one bound for every policy” changes a claim.
So does replacing a probability guarantee with a guarantee on its expectation.
A proof of either statement can be correct while failing to establish the other.

For a result being reported as complete, inspect `#print axioms` for its fully
qualified declaration. This includes transitive proof dependencies. `sorryAx`
marks incompleteness; custom axioms make a theorem conditional on those axioms.
Standard logical axioms such as classical choice are a different category.
`noncomputable` is a code-generation distinction, not itself an extra axiom.
See the official [axioms reference](https://lean-lang.org/doc/reference/latest/Axioms/)
and [proof-validation guide](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)
for these distinctions and additional checks appropriate to specialized uses.

Record only detail that helps someone assess or reproduce the result. The
[formalization record template](https://github.com/MATSResearch/compute_wiki/blob/master/skills/mats-lean-formalization/references/formalization-record.md)
is optional. Incomplete attempts can still expose a missing premise or a useful
counterexample; distinguish that contribution from a completed proof.

## Try the skills on real work

Useful trials include a missing import, a lemma from a different Mathlib version,
a search timeout, an imported theorem depending on `sorry`, and a valid theorem
whose quantifiers differ from the intended claim. Evaluate whether the agent
preserves the target, diagnoses the issue, and accurately reports what was
checked. Skill format validation and a successful documentation build do not
establish that these behavioral outcomes occur.
