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

### MATS Lean skills or lean4-skills? Pick one per project

**lean4-skills** (`cameronfreer/lean4-skills` on GitHub, by Cameron Freer, MIT,
v4.11.3 released 2026-09-29) is a Lean 4 workflow pack for coding agents that
covers much of the same ground as the `mats-lean-*` skills. Its workflows are
`draft`, `formalize`, `autoformalize`, `prove`, `autoprove` ("with explicit
stop budgets"), `disprove` ("guided counterexample search with certified
refutation"), `checkpoint` (per-file and project build, axiom check, commit),
`review`, `refactor`, `golf`, `learn` and `diagnose`. The proving workflows
share one Plan → Work → Checkpoint → Review → Replan cycle, and the README
states that "`prove` and `autoprove` keep declaration headers immutable":
statement changes belong to `formalize` / `autoformalize` only, so the
proving workflows are not meant to weaken a theorem to make it provable. In Claude Code:

```text
/plugin marketplace add cameronfreer/lean4-skills
/plugin install lean4
```

then invoke a workflow as `/lean4:prove`, `/lean4:disprove` and so on. Codex
has a native plugin too; the README marks other hosts (Gemini CLI, Cursor,
Copilot, …) as "documented, not CI-verified". It "pairs best with
lean-lsp-mcp".

| If you want… | Use |
|---|---|
| Thin advisory skills that defer to this wiki, with the agent choosing tactics and decomposition | `mats-lean-*` (five independent skills, plus the optional [skill hint hook](skill-hints.md)) |
| A packaged, opinionated proving loop with slash commands, hooks, stop budgets and a `disprove` workflow | lean4-skills |
| Statement fidelity review against the informal claim | `mats-lean-review`; lean4-skills' `review` is described as a "read-only quality review" |

**When not to use lean4-skills:** in a project already set up with the
`mats-lean-*` skills. Loading both gives the agent two procedures for the same
step (two cleanup passes, two notions of when a proof is "done"), so pick one
set per project and mute the other's hints. Neither replaces a
[comparator check](#lake-comparator-and-lake-check-lean-v4350-and-later)
of the final result.

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

### Check every push in CI: the Statements.lean and Solutions.lean pattern

Put every headline theorem, with a `sorry` body, in a `Statements.lean` that a
human reviews; put the same theorems, under the same names, with proofs in
`Solutions.lean`; and have CI run `lake comparator` on every push. A reviewer
then reads one short file; a proof that drifts from a reviewed statement, or
a new axiom anywhere in the proof library, fails the build; and a change to
the statements themselves shows up as a diff to that one file. Timaeus used this layout for
`timaeus-research/laplace`, a Lean 4 + Mathlib formalization of the Laplace
asymptotics of Gibbs expectations, covariances and susceptibilities from the
singular learning theory (SLT) susceptibility primer: the README reports
"~68k lines of Lean 4 + Mathlib" and "0 sorries, 0 axioms, 0 `native_decide`",
with a README table tracing each headline theorem to its source (a primer
equation or lemma, or marked as new). That repository is archived (moved to a non-public monorepo on
2026-09-27) and has no licence, and its workflow still vendors the standalone
comparator, `landrun` and `lean4export`.

The wiki's [`project_templates/lean_formalization/`](https://github.com/MATSResearch/compute_wiki/tree/master/project_templates/lean_formalization)
is a fresh scaffold of the same pattern for Lean ≥ v4.35.0: `Defs.lean`,
`Statements.lean`, `Solutions.lean`, `comparator.json`, and a GitHub Actions
workflow running `lake check --paranoid` and `lake comparator --paranoid`.
Two things worth knowing before copying it:

- **A drift check, not an audit.** As the laplace workflow comment put it,
  such a job "is a drift check, not an adversarial audit". CI builds the
  project outside the sandbox first, which is fine for your own code; to judge
  a solution someone else wrote, run `lake comparator --paranoid` on a fresh
  checkout on a trusted Linux host without building first.
- **Disk and time on hosted runners.** The laplace workflow frees about 25 GB
  first ("Standard runners have ~14 GB free — not enough for a Mathlib project
  build plus two Lean toolchains"; with `lake comparator` there is only one
  toolchain), and `--paranoid` replays the export through five extra checkers.
  Worth timing on the first run.

## Search before rebuilding mathematics

Use the local dependency source as the authority for available declarations.
The [Mathlib documentation](https://leanprover-community.github.io/mathlib4_docs/)
and [Loogle](https://loogle.lean-lang.org/) can suggest definitions and lemmas;
verify candidates against the project's revision. Search by the shape of a
statement and the structures involved, not only an expected theorem name.
The [Lean tactic reference](https://lean-lang.org/doc/reference/latest/Tactic-Proofs/Tactic-Reference/)
describes search tactics such as `exact?` and `apply?`; availability and behavior
should be checked in the pinned environment.

## Agent tooling for Lean: lean-lsp-mcp, lean4-skills, LeanInteract, provers

Lean FRO = the Lean Focused Research Organization, which maintains Lean.

| I want to… | Use |
|---|---|
| Let Claude Code or another agent read goals, diagnostics and hover info from a Lean project | **lean-lsp-mcp** |
| A packaged prove / disprove / golf workflow for the agent | **lean4-skills** (Cameron Freer), or the wiki's `mats-lean-*` skills — [pick one](#mats-lean-skills-or-lean4-skills-pick-one-per-project) |
| Script many proof attempts or tactic steps from Python | **LeanInteract** (`lean-interact`); **kimina-lean-server** to check proofs in parallel behind an HTTP API |
| Hand a whole Lean project's `sorry`s, or a LaTeX paper, to a hosted prover | **Aristotle** (Harmonic, `aristotlelib`) |
| A cheap local first pass (pass@k) on competition-style statements | Open-weight provers: **Pythagoras-Prover** (4B, 32B), **Goedel-Prover-V2** (8B, 32B) |
| See how a Claude Code–based proving agent is put together | **Numina-Lean-Agent** (architecture reference; no LICENSE file) |
| Judge an untrusted proof against a statement you wrote yourself | **`lake comparator --paranoid`** (built into Lake since Lean v4.35.0); the standalone **comparator** on older toolchains |
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

**LeanInteract** (`lean-interact` on PyPI, v0.11.5 released 2026-07-16;
`augustepoiroux/LeanInteract` on GitHub, MIT). A Python package that drives
the Lean REPL (`leanprover-community/repl`): it downloads and builds the REPL,
then runs commands, whole files (`FileCommand`) and single tactic steps
(`ProofStep`) against stored environment and proof states. `AutoLeanServer`
recovers from some crashes and timeouts and watches memory, for
multiprocessing. From the README:

```python
from lean_interact import LeanREPLConfig, LeanServer, Command

config = LeanREPLConfig(verbose=True)  # download and build Lean REPL
server = LeanServer(config)            # start Lean REPL
server.run(Command(cmd="theorem ex (n : Nat) : n = 5 → n = 5 := id"))
```

When not to use it: on the newest toolchain. The README states support for
"all Lean versions between `v4.8.0-rc1` and `v4.32.0-rc1`" as of v0.11.5,
while Lean is at v4.35.0 (2026-10-12). Also not as a verifier: a REPL that
accepts a proof is the `lake build` rung of the
[evidence ladder](#how-much-checking-does-a-proof-need-lean-evidence-ladder),
not a comparator verdict. Searchable symptom from its troubleshooting list:
``Failed during Lean project setup: Command '['lake', 'update']' returned
non-zero exit status 1.`` can mean `elan` is older than 4.0.0
(`elan self update`).

**kimina-lean-server** (`project-numina/kimina-lean-server`, MIT; client
`kimina-client` on PyPI). A FastAPI service around the Lean REPL that "supports
parallelization to check Lean 4 proofs at scale", with a Python client
(`KiminaClient().check("#check Nat")`) and a Docker image
(`projectnumina/kimina-lean-server:2.0.0`). Its default
`LEAN_SERVER_LEAN_VERSION` is `v4.26.0`. When not to use it: when you need a
recent toolchain (check the version it builds against first; the repository's
last push was 2026-01-11), or when one proof at a time through lean-lsp-mcp
is enough.

**Open-weight provers for a local first pass.** Whole-proof Lean generators
small enough for one GPU, useful for pass@k sweeps or as a cheap first pass
before a hosted prover:

- **Pythagoras-Prover** (arXiv:2606.12594, 2026-06-10; Hugging Face
  `Pythagoras-LM/Pythagoras-Prover-4B` and `-32B`, Apache-2.0, fine-tuned from
  Qwen3). The abstract reports the 4B model at 86.1% pass@32 on MiniF2F-Test
  (above DeepSeek-Prover-V2-671B's 82.4%), and the 32B model at 93.0% on
  MiniF2F-Test and 93 of 672 PutnamBench problems.
- **Goedel-Prover-V2** (arXiv:2508.03613, 2025-08; Hugging Face
  `Goedel-LM/Goedel-Prover-V2-8B` and `-32B`, Apache-2.0 on the model cards;
  the GitHub repository has no licence file). The abstract reports 84.6%
  pass@32 on MiniF2F for the 8B model, and 88.1% (90.4% with self-correction)
  for the 32B model.

When not to use them: on research-level or Mathlib-heavy statements. Both are
trained and benchmarked on competition problems (MiniF2F, PutnamBench), and the
Pythagoras paper releases MiniF2F-ALF, "an ALF-mutated contamination-sensitive
benchmark on which every evaluated model loses accuracy", so headline MiniF2F
numbers are worth discounting for unfamiliar statements. Their output is an untrusted proof like any
other: run it through `lake comparator`.

**Numina-Lean-Agent** (`project-numina/numina-lean-agent`; arXiv:2601.14027,
2026-01-20). "An agent built on Claude Code for formal theorem proving tasks":
Claude Code plus an MCP server and command-line skills (code-transform, llm,
search, sorrifier, verification) and external informal provers. The paper
reports all 12 Putnam 2025 problems solved with Claude Opus 4.5 as the base
model, and a formalization of the Brascamp–Lieb theorem done together with
mathematicians. When not to use it: as code to copy into something you will
publish or redistribute. Its README's licence section says "MIT License", but
the repository has no LICENSE file and GitHub reports no licence, so treat it as
an architecture reference until that is resolved. It also needs a
`GEMINI_API_KEY` ("Required: discussion_partner, informal_prover (gemini),
code_golf") on top of Claude access.

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

The Lean reference's "Validating a Lean Proof" chapter orders the checks; the
two `lake check` rungs are Lake commands added in Lean v4.35.0 (2026-10-12),
and since that release the comparator rung is `lake comparator`. Each rung
guards against more than the one before it:

| Check | Catches | Still trusts |
|---|---|---|
| `lake build` with no `declaration uses 'sorry'` warning | Unfinished proofs in the built files | Every tactic, macro and imported library |
| `#print axioms MyNamespace.my_theorem` | `sorryAx` and custom axioms anywhere in the dependency tree | The elaborator and the build |
| `lean4checker --fresh` on the module (bundled as `leanchecker` since v4.28.0-rc1) | Bugs in Lean's handling of kernel state; meta-programs that add unchecked theorems | That the `.olean` files are well-formed and not crafted |
| **`lake check`** (Lean ≥ v4.35.0) | Non-standard axioms (including `sorryAx`) anywhere in the default targets, after a sandboxed build, export and kernel replay in a separate process | That the theorems are the ones you meant; Lean's kernel |
| **`lake check --paranoid`** | A bug in Lean's kernel not shared by at least one of the five bundled checkers (`leanchecker-paranoid`, `lean4lean`, `nanoda`, `con-leche`, `con-ron`) | That the theorems are the ones you meant |
| **`lake comparator --paranoid`** against a trusted challenge file | A proof of a different statement; forbidden axioms; actively malicious proofs; a bug in one kernel but not all of them | The challenge statement, the bwrap sandbox, and that at least one checker is correct |

The reference calls the comparator check the gold standard and says it matters
for "high risk scenarios (proof marketplaces, high-reward proof competitions,
unaligned AI)". An AI-generated proof of a result you will publish falls under
that heading. `lake check` is the rung for a whole development with no
separate challenge file: it says the project is complete and kernel-checked,
not that its theorems say what the paper says.

### lake comparator and lake check (Lean v4.35.0 and later)

Aliases: `lake comparator`, `lake check`, comparator, Lean FRO comparator,
"the Comparator tool", `lake challenge` (its name during development).
**comparator** began as a standalone tool (`leanprover/comparator`, from the
Lean Focused Research Organization (Lean FRO), Apache-2.0) and was merged into
Lake in **Lean v4.35.0** (released 2026-10-12). The standalone repository's
README now opens with a deprecation notice: users "are advised to migrate their
validations setups to these tools as they are the only ones guaranteed to
receive further security and performance improvements".

**How it works.** You write `Statements.lean` (or `Challenge.lean`) with each
theorem stated and a `sorry` proof; the prover supplies a solution module
restating the same theorems with proofs. A `comparator.json` in the project
root (the default `--config` location) names them:

```json
{
    "challenge_module": "Statements",
    "solution_module": "Solutions",
    "theorem_names": ["MyProject.main_theorem"],
    "definition_names": [],
    "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"]
}
```

`challenge_module`, `solution_module`, `theorem_names` and `permitted_axioms`
are required; `permitted_axioms` "is deliberately not defaulted: it is what the
verdict means". Optional keys: `definition_names` (definition holes),
`external_kernels` (extra checkers, each as a command, e.g.
`{"nanoda": ["nanoda_bin"]}`), and the older `enable_nanoda: true`. Then:

```bash
lake build                    # once: writes lake-manifest.json, which the sandbox cannot write
lake comparator --paranoid    # 0 accepted, 1 rejected, 2 could not start
lake check --paranoid         # whole project, standard axioms only, no challenge file
```

If `lake comparator` exits 0 ("Your solution is okay!"), every named theorem
proves the same statement as the challenge, uses no axiom outside
`permitted_axioms`, and was accepted by the kernel; with `--paranoid` it was
also accepted by every checker bundled with the release toolchain
(`leanchecker-paranoid`, `lean4lean`, `nanoda`, `con-leche`, `con-ron`), so the
kernel assumption weakens to "at least one of the checkers is correct". The
project is treated as untrusted input: its configuration is evaluated, and its
code built and exported (by the toolchain's own `leanexport`, deliberately not
configurable), inside a **bubblewrap (`bwrap`)** sandbox in which `/` is
read-only, home directories are hidden, only `.lake` is writable, and only
dependency resolution has network access. None of the project's `.olean` files
is loaded into Lake's own address space.

Flags, from `lake help comparator` and `lake help check` at the v4.35.0 tag:
`--config=<file>`; `--paranoid`; `--challenge-from-export=<file>` /
`--solution-from-export=<file>` (and `lake check --from-export=<file>`) to judge
an NDJSON export built elsewhere, such as in a VM or by someone with more
compute, noting that this does not check the export matches the project in the
current directory; `--inadvisably-no-sandbox`, which "can compromise the result
fully". `COMPARATOR_BWRAP` sets the sandbox executable.

Requirements and limits:

- **Linux only.** The v4.35.0 release notes say "The sandbox is currently only
  available on Linux". `bwrap` needs unprivileged user namespaces or a setuid
  install; Lean's own test suite notes "User namespaces cannot be assumed
  available in CI containers". On Ubuntu, worth checking the AppArmor sysctl
  `kernel.apparmor_restrict_unprivileged_userns`.
- **`--paranoid` needs a release toolchain.** The external checkers are bundled
  with release toolchains, and a missing one fails the run rather than
  passing it with fewer checkers.
- **Definition holes can be gamed.** For a `def` the solution fills in,
  comparator checks name, type, universe levels, safety level and axioms, not
  meaning: the README's example answers `def ChallengeSolution : Prop := sorry`
  in `RiemannHypothesis ↔ ChallengeSolution` by defining it as
  `RiemannHypothesis`. Such solutions always need an extra human check.
- **`native_decide` is outside the standard axioms.** Per the v4.35.0 release
  notes, `native_decide` and `bv_decide` assert native evaluations as axioms,
  so a proof using them fails `lake check` and a comparator run limited to the
  standard three.

Searchable messages: ``has no `lake-manifest.json` `` (exit 2: run `lake build`
first); ``needs `bwrap` to sandbox the code it checks, and it was not found``
(exit 2); `bwrap: setting up uid map: Permission denied` (no user namespaces);
`Axiom 'sorryAx' is not permitted; it is used by '…'` (`lake check`, exit 1);
`Illegal axiom detected: '…'` (`lake comparator`, exit 1: a forbidden axiom);
`Const does not match between challenge and target '…'` (exit 1: the
solution's statement or definition differs from the challenge's);
`Challenge and solution constant kind don't match: '…'` (exit 1, e.g. the
solution declares an `axiom` under the theorem's name);
`malformed configuration in 'comparator.json'` (exit 2);
`lean4lean kernel rejected the solution` (exit 1, one checker disagreed);
`WARNING: Sandbox disabled, this run is not trustworthy.`

**When not to use it:** on a toolchain older than v4.35.0 (below), or on a
machine where `bwrap` cannot start, where the only option is
`--inadvisably-no-sandbox`; that is defensible for your own code, never for a
solution someone else wrote.

**On toolchains older than v4.35.0.** Use the standalone `leanprover/comparator`
binary: Linux with `landrun` built from source, a `lean4export` matching your
Lean version, and, per its current README, a `systemd-run` wrapper guarding a
`landrun` sandbox escape fixed in Linux 7.1. Never compile the untrusted
solution before running it, and do not run it as a privileged user.
`scripts/fake-landrun.sh` exists for development on systems without `landrun`
and disables the sandbox. Upgrading the toolchain is usually less work.

The independent Rust kernel **nanoda** (`ammkrn/nanoda_lib`, Apache-2.0) is the
external kernel the Lean reference names; since v4.35.0 it ships in the release
toolchain alongside `lean4lean`, `con-leche` and `con-ron`, so `--paranoid`
replaces building it yourself.

### Why a checked Lean proof is not the end of trust

These caveats belong in any report that leans on a Lean certificate:

- **Kernel soundness bugs exist.** Leonardo de Moura's postmortems
  (2026-08) describe soundness bug #14576 and a follow-up bug hunt in which
  OpenAI internal models found further issues in the official kernel and
  runtime, including a reference-counter overflow used to prove `False`. An
  external kernel run through comparator (`--paranoid`, since v4.35.0) is the
  mitigation for a bug present in one checker only; the v4.35.0 release notes
  list two more fixes for use-after-free bugs in the official kernel on
  extremely large inputs.
- **No public consistency proof.** Milo Moses ("A critical look at Lean4",
  LessWrong, 2026-10-09) writes that "there is no publicly available proof
  that Lean4 is consistent with respect to ZFC + any large cardinal axiom".
  This is one author's post; the reference manual likewise lists "the
  soundness of Lean's logic" among the assumptions comparator cannot remove.
- **Sandboxing was opt-in, and can still be switched off.** The recorded
  comparator run for Anthropic's Fermat's Last Theorem formalization (2026-09,
  on the standalone tool) used `fake-landrun.sh`, so no sandbox, per the
  comments in `anthropics/fermats-last-theorem` `verification/comparator/run.sh`.
  The same comment gives the reason: the sandbox guards against an untrusted
  solution, which it calls moot when you built the tree yourself. Moses reports
  re-running it with the sandbox and that it checked out. Since v4.35.0 the
  sandbox is on by default and turning it off takes `--inadvisably-no-sandbox`.
  If you cite someone's certificate, find out which rung it reached, on which
  toolchain, and whether the sandbox was on.
- **A correct formal model can be useless.** Quinn and Max von Hippel ("Lies,
  Damned Lies, and Proofs: Formal Methods are not Slopless", LessWrong,
  2026-01-12) argue that "vibed formal models can be correct, yet very
  challenging to prove anything about", and point to specification
  elicitation and validation as the under-served step. Comparator checks that the statement is
  the one in the challenge file, not that the challenge file says what you
  meant.

**Evidence bar for a high-assurance claim**, such as a published theorem with an
AI-generated proof: `lake comparator --paranoid` (or, before v4.35.0, the
standalone comparator with an external kernel such as nanoda) passes against a
challenge file a human wrote and reviewed; `permitted_axioms`
is limited to the standard three; any definition holes have a human check; and
the challenge statement sits next to the informal claim with each quantifier
and assumption reconciled. Cost is the open problem: in Moses's account of
re-checking the Fermat's Last Theorem certificate, comparator took most of
the runtime, and `--paranoid` replays the export through six checkers instead
of one. Checking
an export once, on a large machine, and sharing it (`--solution-from-export`)
moves the cost around but leaves the export's provenance to be trusted. Making
comparator-grade checking cheap enough to be the default for large AI-written
developments is unsolved.

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

Last verified: 2026-10-14. (Additions 2026-10-14: `lake comparator` and
`lake check` replace the standalone comparator procedure, checked against
`src/lake/Lake/CLI/Help.lean` and `src/lake/Lake/CLI/Check.lean` at the
`v4.35.0` tag of `leanprover/lean4`, the Lake tests `challenge-simple-match`,
`check-sorry` and `check-paranoid` at that tag, the v4.35.0 release notes on
lean-lang.org and the GitHub release (2026-10-12), Lean PRs
14885, 15005, 15145, 15146, 15156 and 15157, and the `leanprover/comparator` README's
deprecation notice (2026-10-14); `leanchecker` bundling from
`leanprover/lean-action` `action.yml`; the CI pattern from the
`timaeus-research/laplace` README, `comparator.json` and workflow; lean4-skills,
LeanInteract, kimina-lean-server and numina-lean-agent READMEs and licences via
the GitHub API; `lean-interact` on PyPI; Pythagoras-Prover, Goedel-Prover-V2
and Numina-Lean-Agent abstracts via the arXiv API; prover licences and base
models via the Hugging Face API. Additions 2026-10-12: the "Agent tooling for Lean"
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
