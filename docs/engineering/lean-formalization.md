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
| `mats-lean-cleanup` | Present a readable, rechecked proof without a separate cleanup request |
| `mats-lean-review` | Assess statement fidelity, assumptions, and what the checked proof establishes |

The `mats-lean-cleanup` skill offers an editorial pass before presenting finished
proofs. An optional [hook](skill-hints.md) suggests it after Lean edits. It removes search debris, clarifies the argument, and verifies the edited
artifact. Read the [comparison and cleanup guide](lean-proof-cleanup.md) for
when shortening helps and when it harms readability.

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

## Agent tooling for Lean: lean-lsp-mcp, Aristotle, lean-eval

Lean FRO = the Lean Focused Research Organization, which maintains Lean.

| I want to… | Use |
|---|---|
| Let Claude Code or another agent read goals, diagnostics and hover info from a Lean project | **lean-lsp-mcp** |
| Hand a whole Lean project's `sorry`s, or a LaTeX paper, to a hosted prover | **Aristotle** (Harmonic, `aristotlelib`) |
| Judge an untrusted proof against a statement you wrote yourself | **comparator** (Lean FRO), ideally with the **nanoda** external kernel |
| Compare provers on formal mathematics problems | **lean-eval** (Lean FRO) |

**lean-lsp-mcp** (`lean-lsp-mcp` on PyPI, `oOo0oOo/lean-lsp-mcp` on GitHub,
MIT, "Lean Theorem Prover MCP"). A Model Context Protocol (MCP) server over
the Lean language server. Its tools include `lean_goal`, `lean_diagnostic_messages`,
`lean_multi_attempt` (try several tactics at one position), `lean_local_search`
(needs `ripgrep`), `lean_verify`, `lean_build`, and the remote searches
`lean_leansearch`, `lean_loogle`, `lean_leanfinder` and `lean_hammer_premise`.
`lean_verify` reports the axioms a theorem uses and scans the source for
patterns such as `unsafe` and `@[implemented_by]`. That is the `#print axioms`
level of evidence, not a comparator check.
Setup for Claude Code, run from the Lean project root:

```bash
lake build                                  # build first; `lake serve` can time out on a cold project
claude mcp add lean-lsp uvx lean-lsp-mcp    # add `-s project` to write .mcp.json instead
```

When not to use it: it gives the agent local file-system access, build
execution and outbound network calls for the remote search tools. The README
calls it a beta research tool and suggests its Docker image for stricter
isolation, with `LEAN_MCP_DISABLED_TOOLS=lean_run_code` as the container
default. Search results still need checking against the pinned Mathlib.

**Aristotle** (Harmonic; `aristotlelib` on PyPI, v2.1.0 as of 2026-10;
`aristotle.harmonic.fun`). A hosted proving agent with a Python SDK and an
`aristotle` command-line tool: `aristotle submit "Fill in all sorries"
--project-dir ./my-lean-project --wait`, or `aristotle formalize paper.tex`.
It needs an `ARISTOTLE_API_KEY` from a sign-up; pricing and access terms are
unverified here. When not to use it: when the project's code or statements
cannot leave your machine, or when you need to see how a proof was found.
Treat its output like any other untrusted proof: check it yourself.

**lean-eval** (`leanprover/lean-eval`, Apache-2.0; leaderboard at
`lean-lang.org/eval` per the README). A formal-mathematics benchmark in which
a problem counts as solved if and only if comparator accepts the submission.
Use it to compare provers on fixed statements; it does not measure whether a
formalization captures an informal claim.

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

### How much checking does a proof need? (Lean evidence ladder)

The Lean reference's "Validating a Lean Proof" chapter orders the checks.
Each rung guards against more than the one before it:

| Check | Catches | Still trusts |
|---|---|---|
| `lake build` with no `declaration uses 'sorry'` warning | Unfinished proofs in the built files | Every tactic, macro and imported library |
| `#print axioms MyNamespace.my_theorem` | `sorryAx` and custom axioms anywhere in the dependency tree | The elaborator and the build |
| `lean4checker --fresh` on the module | Bugs in Lean's handling of kernel state; meta-programs that add unchecked theorems | That the `.olean` files are well-formed and not crafted |
| **comparator** against a trusted challenge file, with an external kernel | Actively malicious proofs; a bug in one kernel but not all of them | The challenge statement, the sandbox and comparator's own plumbing |

The reference calls the last row the gold standard and says it matters for
"high risk scenarios (proof marketplaces, high-reward proof competitions,
unaligned AI)". An AI-generated proof of a result you will publish falls under
that heading.

**comparator** (`leanprover/comparator`, from the Lean Focused Research
Organization (Lean FRO), Apache-2.0; also run as
`lake comparator`). You write `Challenge.lean` with the theorem stated and a
`sorry` proof; the prover supplies `Solution.lean`. A JSON config lists
`theorem_names` and `permitted_axioms` (for example `propext`, `Quot.sound`,
`Classical.choice`). Comparator builds the solution in a `landrun` sandbox,
exports the proof terms with `lean4export`, and outside the sandbox replays
them in the Lean kernel and any `external_kernels`. If it succeeds, each named
theorem proves the same statement as the challenge, uses no other axioms, and
was accepted by the kernel. The independent Rust kernel **nanoda**
(`ammkrn/nanoda_lib`, Apache-2.0) is the external kernel the reference names;
with it, the kernel assumption weakens to "at least one of the checkers is
correct".

Requirements and limits, from the comparator README: Linux with `landrun`
built from source; `lean4export` matching your Lean version; never compile
the untrusted `Solution.lean` before running comparator; do not run it as a
privileged user. Definition holes (a `def` the solution fills in) can be gamed,
for instance by defining the answer as the conjecture itself, so they always
need an extra human check. `scripts/fake-landrun.sh` exists for development
on systems without `landrun`, and it disables the sandbox.

### Why a checked Lean proof is not the end of trust

These caveats belong in any report that leans on a Lean certificate:

- **Kernel soundness bugs exist.** Leonardo de Moura's postmortems
  (2026-08) describe soundness bug #14576 and a follow-up bug hunt in which
  OpenAI internal models found further issues in the official kernel and
  runtime, including a reference-counter overflow used to prove `False`. An
  external kernel run through comparator is the mitigation for a bug present
  in one checker only.
- **No public consistency proof.** Milo Moses ("A critical look at Lean4",
  LessWrong, 2026-10-09) writes that "there is no publicly available proof
  that Lean4 is consistent with respect to ZFC + any large cardinal axiom".
  This is one author's post; the reference manual likewise lists "the
  soundness of Lean's logic" among the assumptions comparator cannot remove.
- **Sandboxing is opt-in.** The recorded comparator run for Anthropic's
  Fermat's Last Theorem formalization (2026-09) used `fake-landrun.sh`, so no
  sandbox, per the comments in `anthropics/fermats-last-theorem`
  `verification/comparator/run.sh`. The same comment gives the reason: the
  sandbox guards against an untrusted solution, which it calls moot when you
  built the tree yourself. Moses reports re-running it with the sandbox and
  that it checked out. If you cite someone's certificate, find out
  which rung it reached.
- **A correct formal model can be useless.** Quinn and Max von Hippel ("Lies,
  Damned Lies, and Proofs: Formal Methods are not Slopless", LessWrong,
  2026-01-12) argue that "vibed formal models can be correct, yet very
  challenging to prove anything about", and point to specification
  elicitation and validation as the under-served step. Comparator checks that the statement is
  the one in the challenge file, not that the challenge file says what you
  meant.

**Evidence bar for a high-assurance claim**, such as a published theorem with an
AI-generated proof: comparator passes against a challenge file a human wrote
and reviewed; an external kernel such as nanoda also passes; `permitted_axioms`
is limited to the standard three; any definition holes have a human check; and
the challenge statement sits next to the informal claim with each quantifier
and assumption reconciled. Cost is the open problem: in Moses's account of
re-checking the Fermat's Last Theorem certificate, comparator took most of
the runtime. Making comparator-grade checking cheap enough to be the default
for large AI-written developments is unsolved.

## Try the skills on real work

Useful trials include a missing import, a lemma from a different Mathlib version,
a search timeout, an imported theorem depending on `sorry`, and a valid theorem
whose quantifiers differ from the intended claim. Evaluate whether the agent
preserves the target, diagnoses the issue, and accurately reports what was
checked. Skill format validation and a successful documentation build do not
establish that these behavioral outcomes occur.

For the research side of formal methods (guaranteed-safe AI, ARIA Safeguarded
AI, formal corrigibility results), see
[`agent-foundations-and-formal.md`](../alignment-science/agent-foundations-and-formal.md).

---

Last verified: 2026-10. (Additions 2026-10-12: the "Agent tooling for Lean"
section, the evidence ladder and the trust caveats. Verified against the
`oOo0oOo/lean-lsp-mcp` README and `docs/tools.md`, the `leanprover/comparator`
and `leanprover/lean-eval` READMEs, `ammkrn/nanoda_lib` via the GitHub API, the
`aristotlelib` PyPI metadata and `aristotle.harmonic.fun`, the Lean reference
chapter "Validating a Lean Proof", Leonardo de Moura's 2026-08-24 bug-hunt
postmortem, the comment block in `anthropics/fermats-last-theorem`
`verification/comparator/run.sh`, and LessWrong posts zHhGa3iQBQcdSifFL
(Moses) and rhAPh3YzhPoBNpgHg (Quinn and von Hippel) via GraphQL. Aristotle
access terms and pricing unverified; the lean-eval leaderboard page was not
fetched directly.)
