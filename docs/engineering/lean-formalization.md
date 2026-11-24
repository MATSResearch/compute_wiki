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
v4.12.0 released 2026-11-08) is a Lean 4 workflow pack for coding agents that
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
lean-lsp-mcp". Use v4.11.4 or later: that release revalidated its advanced
references against Lean `v4.33.1` and `v4.35.0`, compiling every example, after
"Several documented snippets failed when compiled" (among them, `grind [h1, h2]`
with local hypotheses "is an error, not a no-op", and most of the
metaprogramming examples). An agent following an older copy can be steered by
examples that never compiled. v4.12.0 (2026-11-08) changes how `autoprove`
ends: a new `--conclude-after=N%|Nc|<duration>|0` flag (default `15%`)
reserves the end of the budget for a conclusion cycle, in which "it either
finishes an already-tested proof or reports a verdict on what remains, instead
of spending its last cycles on low-yield search until a limit stops it". The
verdict is `ready`, `fixable` or `no-credible-path`, with the blocker
inventory and missing lemmas. Such a run records `stop_reason: concluded`,
and per the release notes "older readers reject a `concluded` handoff", so
do not mix plugin versions across a resumed run.

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
unrelated dependency upgrade. As of 2026-11-23 the stable toolchain is Lean
v4.36.0 (2026-11-16) and v4.37.0-rc1 (2026-11-18) is a release candidate.
The v4.36.0 notes call it "mostly a consolidation release" ("Mathlib now
builds roughly 12% faster than before"), with one behaviour change to know
before upgrading numeric code: `min` and `max` on `Float` are now
`Float.minimum` and `Float.maximum`, and "Code that relied on min or max
returning the other argument when one of them is NaN should use
Float.minimumNumber or Float.maximumNumber."

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
is a fresh scaffold of the same pattern, pinned to Lean v4.36.0
(`lean-toolchain`; the `lake` commands need ≥ v4.35.0): `Defs.lean`,
`Statements.lean`, `Solutions.lean`, `comparator.json`, and a GitHub Actions
workflow running `lake check --paranoid` and `lake comparator --paranoid`.
What was run on it (template README, 2026-11-23, Lean v4.36.0, macOS arm64):
`lake build` (exit 0, no warnings), `lake build Statements` (exit 0, one
``declaration uses `sorry` `` warning per statement), `#print axioms` on both
solution theorems (`[propext, Quot.sound]` and no axioms; the statement
versions report `[sorryAx]`), and `leanchecker` and `leanchecker-paranoid`
replaying `Solutions` (both exit 0). On macOS `lake check --paranoid` and
`lake comparator --paranoid` both exit 2 with
``error: `lake comparator` sandboxes the code it checks with `bwrap`, which needs Linux namespaces.``
On Linux (2026-11-23, Lean v4.36.0, Ubuntu 24.04 arm64 in a Docker container under Colima on macOS, started with `--privileged`): `lake build` (exit 0), `lake check --paranoid` (exit 0: lean4lean, nanoda, con-leche, con-ron and the Lean default kernel all accept; "Uses axioms: Classical.choice, propext, Quot.sound") and `lake comparator --paranoid` (exit 0, "Your solution is okay!"). Not run: the GitHub Actions workflow. The container errors met on the way are under "Requirements and limits" below.
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

Two October 2026 additions, both single preprints: **Lean Finder V2**
(Lu et al., [arXiv:2610.30843](https://arxiv.org/abs/2610.30843);
`leanfinder.github.io`), a Mathlib semantic search engine trained for the short,
ambiguous queries people and agents actually type, reporting "at least 11%
relative improvement over the previous best Mathlib semantic search engines" on
the MathlibQR benchmark (whether lean-lsp-mcp's `lean_leanfinder` tool calls V2
is not documented); and **Vampire-Hammer** (Bodingbauer and Kovács,
[arXiv:2610.40310](https://arxiv.org/abs/2610.40310); `vprover/vampire-hammer`,
Apache-2.0), a hammer that sends goals to the Vampire automated theorem prover
through Lean-auto and reconstructs kernel-checked proofs; with a 10-second
budget on 196,083 eligible Mathlib theorems it "solves 21,158 problems not
solved by other evaluated tools". When not to use a hammer: where a reader needs
to follow the argument, since the reconstructed step does not show it.

## Agent tooling for Lean: lean-lsp-mcp, lean4-skills, LeanInteract, provers

Lean FRO = the Lean Focused Research Organization, which maintains Lean.

| I want to… | Use |
|---|---|
| Let Claude Code or another agent read goals, diagnostics and hover info from a Lean project | **lean-lsp-mcp** (0.33.0 or later) |
| An agent interface maintained by the Lean FRO, shipped inside the toolchain: speculative tactic runs, module checkpoints, a `sorry` finder | **Lean Beam** (`lean-beam`, `lean-beam-mcp`; bundled with the stable Lean v4.36.0 toolchain on Linux and macOS, beta) |
| A packaged prove / disprove / golf workflow for the agent | **lean4-skills** (Cameron Freer), or the wiki's `mats-lean-*` skills — [pick one](#mats-lean-skills-or-lean4-skills-pick-one-per-project) |
| Script many proof attempts or tactic steps from Python | **LeanInteract** (`lean-interact`); **kimina-lean-server** to check proofs in parallel behind an HTTP API |
| Fine-tune a prover model on my own Lean repository (trace the repository, train, run proof search) | **LeanDojo-v2** (`lean-dojo-v2`; needs a CUDA GPU) |
| Check the proofs of an existing LaTeX paper in Lean, result by result | **KAPPA** (statistics papers, unattended) or **PaperFormalizer** (author in the loop); **Numina Fuse** as an interactive app — [details](#checking-an-existing-papers-proofs-in-lean-kappa-paperformalizer-numina-fuse) |
| Hand a whole Lean project's `sorry`s to Harmonic's hosted prover | Not with current **Aristotle**: `aristotlelib` 3.0.0 (2026-10-27) and later verify Verilog, C and Rust, not Lean — [details](#aristotle-aristotlelib-30-no-longer-takes-lean) |
| A cheap local first pass (pass@k) on competition-style statements | Open-weight provers: **Pythagoras-Prover** (4B, 32B), **Goedel-Prover-V2** (8B, 32B) |
| See how a Claude Code–based proving agent is put together | **Numina-Lean-Agent** (architecture reference; no LICENSE file) |
| A baseline to beat before crediting a specialised prover harness with a gain | **mini-Lean-agent** (bash as the only tool, separate trusted evaluator) |
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

**lean-lsp-mcp before 0.33.0: a failed tactic can look like a closed goal.**
This affects only the optional Lean REPL accelerator (enabled with
`LEAN_REPL=true` or `uvx lean-lsp-mcp --repl`), which serves `lean_run_code`
and line-based `lean_multi_attempt`; column-based attempts use the language
server and are unaffected. Per the fix (PR #239, released in v0.33.0 on
2026-11-03): "The Lean read-eval-print loop (REPL) returned native errors in
`message`, while the adapter read `error`. Failed tactics could therefore
appear to return no goals or diagnostics." Symptom: a tactic trial returning
no goals and no diagnostics. `uvx` reuses a cached tool environment and does
not pick up a new release on its own, so use `uvx lean-lsp-mcp@latest` (or
`uv tool upgrade lean-lsp-mcp` for an installed copy). A final `lake build`
and comparator check still catch a proof that was never closed; the cost on
older versions is wasted search on a false lead.

### Lean Beam: the Lean FRO's agent interface, bundled with the toolchain

**Lean Beam** (`leanprover/lean-beam` on GitHub, Apache-2.0; commands
`lean-beam`, `beam-daemon`, `lean-beam-mcp`). Lean FRO = the Lean Focused
Research Organization. A command-line tool and Model Context Protocol (MCP)
server, written in Lean, that keeps a Lean project's module context alive
across requests. Its README lists speculative execution (`runAt`: "try
commands and tactics in a file's context without changing its source", with
independent attempts run concurrently), `save` (a module checkpoint from the
state the server already checked, without batch re-elaboration), `sync`
(wait for current diagnostics) and `todo` (find sorries, holes, diagnostics
and incomplete proofs), plus goals, hover, definitions and references. The
Lean v4.36.0-rc2 release notes (2026-10-27) say PR #15665 "adds Lean Beam's
CLI, MCP server, daemon, and LSP plugin to Linux and macOS release
toolchains"; Windows distribution is deferred. The stable **Lean v4.36.0**
(2026-11-16) carries it: its release notes say "The Linux and macOS toolchains
now include Lean Beam (#15665), a command-line tool and MCP server that lets
AI agents and other tools work with Lean projects through the language
server", and PR #16478 "updates bundled lean-beam in Lean 4.36 with
speculative profiling and improvements to Lean language server compatibility,
cancellation, and error reporting". On older toolchains, the
standalone installer (`./scripts/install-beam.sh --claude --claude-mcp` from a
checkout) installs it for Linux or macOS; its compatibility policy
(`docs/COMPATIBILITY.md`, unchanged on this point when read 2026-11-23; last commit to `main` 2026-11-18) gives a
supported Lean window of 4.34–4.36, so v4.33 and older are out and
v4.37.0-rc1 (2026-11-18) is not yet in the window. "Bundled binaries do not install an
agent skill": install the Lean skill from the matching Beam release yourself.

**`lean-beam: command not found` (bash) / `command not found: lean-beam` (zsh) with elan.** elan 4.2.4 creates no shim for
the bundled Beam binaries: `~/.elan/bin` holds `elan`, `lake`, `lean`, `leanc`,
`leanchecker`, `leanmake` and `leanpkg` only, while the v4.36.0 toolchain's own
`bin` directory holds `lean-beam`, `lean-beam-mcp` and `beam-daemon` (checked
2026-11-23 on macOS arm64). Call the bundled copy by toolchain path, from a
project whose `lean-toolchain` is v4.36.0:
`"$(lean --print-prefix)/bin/lean-beam" --help`, and give an MCP client the
full path `"$(lean --print-prefix)/bin/lean-beam-mcp"`.

When not to use it: on a toolchain older than v4.34 or on v4.37.0-rc1 (both
outside its stated supported window), or expecting a bundled copy on the
v4.35.0 toolchain (it is bundled from v4.36.0; use the standalone install on
4.34 and 4.35); as a
sandbox ("Beam is for
non-adversarial development. Speculative requests isolate Lean elaboration
state; they do not provide an OS sandbox for Lean IO"); or as a verifier, which
remains `lake comparator`. The README calls it "beta software, and its
interfaces may change". Running it beside lean-lsp-mcp gives the agent two
tool sets for the same job, so pick one per project.

**Why the interface matters.** Moalla, Rammal, Patel, Munos and Kempe
([arXiv:2610.35962](https://arxiv.org/abs/2610.35962), "h1: A Taste of the
Bitter Lesson in Automated Theorem Proving", single preprint) give a model an
efficient Lean 4 interface and a plain loop of verifier feedback and
self-reflection, with no imposed
decomposition, and report that at matched models it "matches or outperforms
specialized workflows such as Goedel-Architect and AlphaProof Nexus"; their
ablations find "simplicity alone is not enough: an efficient Lean interface
largely determines cost and solve rate". Read with mini-Lean-agent
(arXiv:2610.17331, a bash-only baseline agent): before building a proving
workflow, try a frontier model with a fast Lean interface (Lean Beam,
lean-lsp-mcp) and plain feedback.

### What does an agent choose to work on in a Lean project? (sorry-filling)

Left to "take the next step" in a real formalization repository, coding
agents go for the `sorry` markers and stay away from the dense middle of the
proof. Gyevnár and DeDeo
([arXiv:2611.06995](https://arxiv.org/abs/2611.06995), "Autonomous AI Agents
Systematically Diverge From Human Preferences in Proof Formalization",
2026-11-04; data and code `gyevnarb/proof-divergence`) replayed nine human
Lean collaborations (among them `flt`, `pfr`, `sphere`; "4.7M definitions
across more than 6K commits") and, at each commit, compared what the humans
did next with what Claude Code (Opus 4.6), Codex (GPT-5.2-Codex) and Gemini
CLI (Gemini 3.1 Pro) did under a deliberately broad objective:

- **Marked gaps.** "Definitions containing a sorry marker account for 59–92%
  of AI agent modifications, against 19% of human modifications" (Claude 92%,
  Gemini 80%, Codex 59%), and the pull falls off with distance from the `sorry`
  in the dependency graph much faster than it does for humans. A `sorry` a human left as a planning device (the
  statement is expected to change, or the proof is to come from a result not
  yet available) gets filled anyway: a declaration with a `sorry` that an
  agent chose to edit "later evolves into a definition with a new signature –
  between 25% (Codex) and 48% (Claude) of the time".
- **Periphery over centre.** The agents "prefer to modify near the logical
  boundaries of a proof", close to the leaves or to the final theorem, where
  humans work more on the intermediate lemmas; they also edit long
  definitions less than humans do, and avoid proof goals that look unusual.
- **Regularizing proofs.** The agents preferentially rewrite unusual proof
  bodies, and "tend to regularize proofs towards an LLM standard" (surprise
  measured under DeepSeek-Prover-V2-7B).

What to do with it: assign the central lemma by name instead of asking for
"progress"; mark a `sorry` that is not meant to be filled yet, in a comment
the agent will read; and expect an unusual but correct proof to be rewritten
toward the conventional unless told to leave it
([cleanup guidance](lean-proof-cleanup.md)). Limits the authors state: the
dependency graphs come from "a heuristic lexical parser rather than from the
Lean compiler itself", and all nine repositories are public and predate the
models, so their later states may be in training data. Single preprint; the
models are early-2026 ones.

### Aristotle (`aristotlelib` 3.0+) no longer takes Lean

**Aristotle** (Harmonic; `aristotlelib` on PyPI, `harmonic-ai/aristotle` on
GitHub, `aristotle.harmonic.fun`). Up to v2.1.0 (PyPI 2026-06-18) this was a
hosted Lean prover driven by `aristotle submit "Fill in all sorries"
--project-dir ./my-lean-project --wait` or `aristotle formalize paper.tex`.
From **3.0.0** (2026-10-27) it is a code verifier. The current PyPI
description (3.4.0, 2026-11-18): "It verifies Verilog, C, and Rust. Send your
code as it is: Aristotle writes the Lean itself. It doesn't
verify pure mathematics or Lean: a project with only Lean files runs and
verifies nothing." The 3.0.0 changelog removes `aristotle formalize` and ask
mode; 3.2.0 (2026-10-31) makes `submit` exit 2 before uploading when only
`.lean` files would go up, and deprecates the Lean-toolchain helpers
`get_lean_toolchain_version()` and `get_expected_toolchain()`. 3.3.0
(2026-11-06) and 3.4.0 (2026-11-18) keep that position; Rust is no longer
per-account (the 3.4.0 changelog: "now that Aristotle verifies Rust on every
account"). 3.4.0 also adds `aristotle balance` (credit balance without
starting a run) and shows a run that ended `COMPLETE_WITH_ERRORS` as `REVIEW
SUGGESTED`; "`--json` still gives `COMPLETE_WITH_ERRORS`, and a wait on such a
run still exits 1".

Searchable symptoms of an old workflow on 3.x: `aristotle formalize` no longer
exists (the 3.0.0 changelog says "Removed" and points to `submit` with
Verilog, C or Rust code instead); `aristotle submit` on a Lean-only folder exits 2; a script that
treated exit 0 as success changes behaviour, because 3.0.0 moved every command
onto one exit-code table (in 2.1.0 "a handled error exited 0 (a missing or rejected key, rate
limiting, `cancel` finding no task)"; now a missing or rejected key exits 5 and
rate limiting exits 6). Whether Harmonic still serves Lean proving to the 2.x
client, or through another product, is not stated in the package
documentation, so pinning `aristotlelib==2.1.0` is not a known-good route.
When not to use it: for Lean or pure-mathematics work at all; for Verilog, C or
Rust verification, when the code cannot leave your machine. Treat any prover's
output as an untrusted proof and check it yourself.

### Scripted checking, open-weight provers and reference agents: LeanInteract, kimina-lean-server, Pythagoras, Goedel, Numina-Lean-Agent, mini-Lean-agent, lean-eval

**LeanInteract** (`lean-interact` on PyPI, v0.11.6 released 2026-10-18;
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

Toolchain support: v0.11.6 "Add[s] support for Lean v4.33.0 to v4.36.0-rc1"
(the README now reads "all Lean versions between `v4.8.0-rc1` and
`v4.36.0-rc1`", covering v4.35.0 and the v4.36.0-rc1 release candidate of
2026-10-14), and it "Fixed import error swallowing and invalid header
caching", so upgrade if an import failure was going unreported. v0.11.5 stopped at
v4.33.0-rc1, so a project on v4.35.0 needs v0.11.6 or later. No LeanInteract
release has followed the stable Lean v4.36.0 (2026-11-16): at 2026-11-23
v0.11.6 is still the latest and its README's range still ends at
`v4.36.0-rc1`, so support for stable v4.36.0 and for v4.37.0-rc1 is not
stated. Run one known-good proof through it before a sweep on those
toolchains.

When not to use it: as a verifier. A REPL that
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

**LeanDojo-v2** (`lean-dojo-v2` on PyPI, v1.0.9 released 2026-04-26, Python
≥3.11; `lean-dojo/LeanDojo-v2` on GitHub, MIT; Hsiang, Adkisson, George and
Anandkumar, [arXiv:2611.09048](https://arxiv.org/abs/2611.09048), 2026-11-06;
a different package from the original `lean-dojo`). The paper describes "an
end-to-end framework that unifies repository data extraction, LLM
fine-tuning, proof search, AI autocompletion, and LLM-assisted theorem
proving in a single software library". It traces a Lean repository (a GitHub
URL or a local path) into training data, fine-tunes a Hugging Face model
(full supervised fine-tuning or Low-Rank Adaptation, LoRA; the paper's
example fine-tunes `deepseek-ai/DeepSeek-Prover-V2-7B`), and runs proof
search over the repository's `sorry` theorems through Pantograph, which is
installed separately (`pip install
git+https://github.com/stanford-centaur/PyPantograph`). It comes with
Lean4Code, "a lightweight IDE". The README asks for a "CUDA-capable GPU for
training and inference (tested with CUDA 12.6)", `elan`, a
`GITHUB_ACCESS_TOKEN`, and an `HF_TOKEN` for Hugging Face API inference.
Searchable symptoms from its troubleshooting list: `401 Bad Credentials`
(token missing or without `repo` + `read:org` scopes) and "Lean tracing
failures" (the repository's Lean version is not installed locally:
`elan toolchain install <version>`). When not to use it: without a GPU;
when a frontier model with a fast Lean interface is enough (try that first,
per the h1 and mini-Lean-agent results on this page); or assuming a recent
toolchain works. The README states no supported Lean range and the last
tagged release is from April 2026, so trace one small file on your pinned
toolchain before committing to it. A proof it finds is an untrusted proof
like any other.

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

**mini-Lean-agent** (`TomasOrtega/mini-lean-agent`, MIT; Ortega, Park,
Khaitan, Fowl, Kontorovich, Arora, ["Do Theorem Provers Need Theorem-Proving
Agents?"](https://arxiv.org/abs/2610.17331), arXiv:2610.17331, October 2026).
A deliberately minimal agent "whose only model-visible tool is bash": the
model inspects and edits the repository, searches local libraries and runs
Lean through the shell, and "a separate trusted evaluator verifies the final
artifact". On Putnam 2025 the authors report, with Gemini 3.8 Flash as the
base model, "7/12 problems at $2 per problem limit, compared with
AxProverBase's 4/12", and with Astra (`gpt-6-astra`) 12/12 "at an average cost
of $1.28 per problem"; they propose it "as a standard baseline when evaluating
theorem-proving infrastructure". Use it that way: before crediting a
specialised harness, Model Context Protocol (MCP) server or prover-specific tool with a gain, check it
beats a generic coding agent with bash on the same base model and budget.
When not to use it: as evidence about research-level formalization (12
competition problems), or as a substitute for running `lake comparator` on its
output yourself.

**lean-eval** (`leanprover/lean-eval`, Apache-2.0; leaderboard at
`lean-lang.org/eval` per the README). A formal-mathematics benchmark in which
a problem counts as solved if and only if comparator accepts the submission.
Use it to compare provers on fixed statements; it does not measure whether a
formalization captures an informal claim.

### Checking an existing paper's proofs in Lean: KAPPA, PaperFormalizer, Numina Fuse

Three October 2026 tools, each from a single preprint, take a paper (not a
competition problem) as input:

- **KAPPA** ("Kit of Agents for Proof-checking Papers with a proof Assistant";
  `ziwaa-se/kappa` on GitHub, MIT; She and Wang,
  [arXiv:2610.35596](https://arxiv.org/abs/2610.35596)). Claude Code agents
  translate a LaTeX statistics paper's proofs into Lean 4 and Mathlib, following
  the paper's own proof step by step, and give each numbered result one of four
  verdicts: "verified unconditionally; verified conditionally, with every cited
  or unproved input stated as a named hypothesis; issue recorded …; or
  unfinished". Separate agents write and review, and each statement is compared
  with the paper before it is proved. On three published statistics papers,
  checked blind in their pre-correction versions, "the kit found the published
  error at the step that the correction names". The same model given the papers
  directly with Lean "reported some statements narrower than the paper's as
  proved". Scope: three research papers plus four constructed examples; the
  paper's runs used Lean 4.19.0 and Claude Code 2.1.296.
- **PaperFormalizer** (`Jiyuan-Tan/PaperFormalizer` on GitHub; GitHub detects no
  standard licence; Tan, Blanchet and Syrgkanis,
  [arXiv:2610.31810](https://arxiv.org/abs/2610.31810)). An author-in-the-loop
  LaTeX → Lean pipeline that runs inside Claude Code or Codex. It builds a
  dependency graph of the paper's statements, audits each in natural language,
  then formalizes and proves against Mathlib. It "stops and asks the author
  whenever a statement admits more than one reading" and leaves the author
  "every decision that could potentially change what the paper claims". For
  your own paper; check the licence before reusing its code.
- **Numina Fuse** (`project-numina/fuse-desktop` on GitHub, **AGPL-3.0**; Asher
  et al., [arXiv:2610.33860](https://arxiv.org/abs/2610.33860)). A desktop app in
  which a user supervises an AI orchestrator on a Lean project through
  blueprint, dependency-graph and code views, while agents run for hours. The
  paper reports its use on a formalization of the three-dimensional Kakeya
  conjecture. AGPL-3.0 matters if you modify and serve it.

A November 2026 addition for research manuscripts that already have a partial
formalization: **Turing Agent** (Chen et al.,
[arXiv:2611.21299](https://arxiv.org/abs/2611.21299), 2026-11-16; the paper
links a project website, `wangqy031216-cloud.github.io/turing-agent`, and no
code repository). An agent harness with separate theorem-formalization and
proof-formalization agents, a proof dependency graph (DAG), parallel
verification and "selective semantic review", evaluated on theoretical
computer science (TCS). The abstract reports "approximately 57-62% faithful
formalization success on Formal TCS Bench and 83% overall pass@1 on a
TCS-focused subset of RLMEval, using GLM-5.3 and DeepSeek-V4-Pro", against
direct generation, Codex CLI and Claude Code, and that it "successfully
completes the formal verification of three previously unresolved TCS tasks
from OpenAI's October 2026 collection" (per the paper, 22 of that
collection's 121 TCS problems "had not been fully verified in Lean"); one
"required about a hundred formally verified auxiliary claims". Not usable
as a tool until code is released; the three completions were not re-checked
here.

When not to use them: as a substitute for reviewing the statements. Each tool
makes statement review a step, but a "verified" verdict is still a Lean proof
of the formal statement, and the
[statement-fidelity checks](#checking-that-a-formal-statement-says-what-the-informal-one-does)
still apply. A whole-paper run spends agent time on every result; formalizing only the
subclaim that matters is often the better trade.

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
A worked example of reporting custom axioms honestly: Saha et al.
([arXiv:2611.10961](https://arxiv.org/abs/2611.10961), 2026-11-07, improved
bounds on Grothendieck's and Korenblum's constants by agent refinement of a
"partially formalized Lean blueprint") print the `#print axioms` closure of
each final theorem and classify it. The Grothendieck bound rests on "Sixteen
axioms in four groups": the three Lean primitives, nine trusted analytic
facts about an inverse function family (statements the source paper derives
from the implicit function theorem), one seed axiom, and three numerical
oracle axioms that an evaluator recomputes with the Arb interval-arithmetic
library. That is a conditional theorem with its conditions listed, which is
what a reader needs; "verified in Lean" without the list would overstate it.
See the official [axioms reference](https://lean-lang.org/doc/reference/latest/Axioms/)
and [proof-validation guide](https://lean-lang.org/doc/reference/latest/ValidatingProofs/)
for these distinctions and additional checks appropriate to specialized uses.

Record only detail that helps someone assess or reproduce the result. The
[formalization record template](https://github.com/MATSResearch/compute_wiki/blob/master/skills/mats-lean-formalization/references/formalization-record.md)
is optional. Incomplete attempts can still expose a missing premise or a useful
counterexample; distinguish that contribution from a completed proof.

### Checking that a formal statement says what the informal one does

Statement fidelity is the step no Lean checker covers, and as provers get
stronger "the burden of correctness shifts from the proof to the statement"
(SemantEq, arXiv:2610.32919). October 2026 resources for it:

- **AnnalsChallenge** (`ImperialCollegeLondon/AnnalsChallenge`, Apache-2.0;
  Browning, Hristova, Ledvinka, Springer, Su, McKoen, Buzzard,
  [arXiv:2610.18301](https://arxiv.org/abs/2610.18301)): "50 formalised theorem
  statements written by hand in Lean 4 using Mathlib", each the main result of
  an Annals of Mathematics paper since 2020; "Every formalisation was manually
  reviewed and then audited by AI", and they are released "without formalised
  proofs". Also on lean-eval. Useful as hard, trusted statements to test a
  prover or autoformalization pipeline against, and as examples of how
  reviewed research-level statements are written.
- **Mechanical checks beside a large language model (LLM) judge** (Anna Mei, Michael R. Douglas,
  ["Beyond LLM Judge: Mechanical Verification for Agentic Autoformalization"](https://arxiv.org/abs/2610.20573),
  arXiv:2610.20573; code `annamei1/FLMF-Ch7ErrFunc-Release`, Apache-2.0). Their
  method "combines LLM-based semantic review with mechanical numerical and
  vacuity checks": a numerical check evaluates a stated identity or bound where
  it can be turned into numbers, and a vacuity check, run after the proof
  exists, flags a proof that holds vacuously (for example because its
  hypotheses are contradictory, or `rfl` / `simp` closes the goal). A theorem counts as verified only with a
  semantic pass and no numerical or vacuity failure. On three labelled
  datasets it had "the lowest accepted-error rate among the evaluated methods"
  (the fraction of incorrect statements accepted). Built for special-function
  identities from the NIST Digital Library of Mathematical Functions; the
  numerical check does not apply to definitions, limits or infinite sums.
- **Proving `P ↔ Q` against a reference formalization "proves too much"**
  (SemantEq; Li, Ammanamanchi, Bhat, Jamdar, Lin, Biderman,
  [arXiv:2610.32919](https://arxiv.org/abs/2610.32919); `hlxr89/SemantEq`,
  Apache-2.0). If the library proves both statements, a prover can pass
  through `P ↔ True ↔ Q`, so the stronger the prover, the more unrelated pairs
  pass an equivalence check; a language model "proves both directions of about
  two in five of the non-equivalent pairs" under two of four prompts. SemantEq
  instead requires a chain of allowed steps (logical rearrangement, rewriting
  with the library's own equations), judged on the proof term Lean checks, not
  the tactic script. The abstract reports its model-free search at 100%
  precision and 65.6% recall on the ProofNetVerif test split, against 95.8%
  and 61.8% for BEq+. Use it when you check an autoformalized statement
  against a trusted reference; it does not help when no reference exists.
- **Project-level review: MechAlign and LeanReviewBench** (Shen, Qiu, Zhi, Gao,
  [arXiv:2610.35269](https://arxiv.org/abs/2610.35269)). A main theorem's meaning
  depends on definitions scattered across a development. Its LeanTrace tool
  extracts the statement dependency graph (definition bodies and structure
  constraints, no proof bodies, stopping at a library boundary) as context for
  an LLM reviewer. The paper calls its review of 201 main results from 173
  OpenAI Math projects "preliminary", and releases LeanReviewBench, 501
  claim–statement–context triples from OpenAI Math, Fermat's Last Theorem and
  Kakeya, for comparing such reviewers.
- **Keeping a review valid as the code changes: ProofPatch** (Che, Xu, Xiang,
  Khan, [arXiv:2611.01357](https://arxiv.org/abs/2611.01357); no code link in the
  paper). A reviewer's decision on a statement is stored with fingerprints of the
  elaborated statement and of the definitions it depends on, and "any
  declaration can be pinned so that a patch changing it is blocked, whether a
  person or an agent built on a large language model (LLM) wrote the patch".
  The abstract reports that "in 344 runs of an LLM agent no change to a pinned
  statement got through", and that "kernel evidence flags unfaithful ones with
  precision 0.88 to 0.96" on 1,527 labelled statements. Useful where an agent
  edits a development for a long time after its statements were reviewed.
- **Non-vacuity tests and junk values: AutoIP** (`l-oksanen/autoip` on GitHub,
  Apache-2.0; Clason, Helin, Nursultanov, Oksanen,
  [arXiv:2611.06962](https://arxiv.org/abs/2611.06962), 2026-11-04). A Lean
  library of classical linear regularization theory (inverse problems): the
  authors wrote the blueprint, Claude Opus 5 and 5.5 wrote the Lean, and the
  library is laid out so that "a reviewer compares the formal statements with
  their natural-language counterparts and never needs to read a proof". Two
  checks transfer to any project. (1) *Non-vacuity obligations.* For every
  statement, "two obligations were generated using a deterministic (not
  AI-based) algorithm: exhibit an instance in which the hypotheses hold, and
  one in which they fail", and agents proved them (503 obligations). This
  exposed a textbook convergence theorem "whose hypothesis is far more
  restrictive than it appears", but only after the witnesses were required
  to be non-trivial: the obligation had first been discharged with the zero
  operator on the trivial space, "which raised no alarm". (2) *Junk values.*
  Lean functions are total, so Mathlib returns an arbitrary value outside a
  function's natural domain: `Module.finrank` is 0 on every
  infinite-dimensional space. A lemma whose hypothesis was
  `Module.finrank 𝕜 U < Module.finrank 𝕜 V` therefore said nothing when `V`
  is infinite-dimensional, though the informal lemma covers that case; the
  fix compares `Module.rank` (cardinals). "To read a formal statement
  correctly, a reviewer must know the junk value of every function in it."
  A non-vacuity test does not catch this one, because the weak hypothesis is
  satisfiable. Also reported: review records carry hashes of the informal
  and formal statement and expire when either changes, while a changed proof
  leaves them intact; and model reviews were unstable (GPT-5.6 Sol "raised
  about 300 objections" on code quality, and Claude Opus 5, reviewing the
  revised code against the same rubrics, "raised more than 450 new
  objections"). Scope: settled textbook material; per the paper's Table 1 an
  author had reviewed 25 of the 51 theorems stated in Lean and all 22
  constructed definitions.
- **The same gap outside Lean: Dafny** (Maji,
  [arXiv:2611.07073](https://arxiv.org/abs/2611.07073), "When Verification
  Is Not Agreement", 2026-11-04, single author; abstract and PDF section 5.1 read). One
  model writes a Dafny predicate from clinical-trial criteria and another
  writes a method verified against it, on 96 documents. With the same model
  (GPT-4.1-mini) in both roles, "independent re-extraction from identical
  text agrees only 59.3% of the time": verification succeeded on the first
  attempt for 54 documents, which is 59.3% of the 91 that were semantically
  evaluated and 56.2% of all 96. In the configuration with the weaker
  implementer, a case counted as agreement had passed verification "by
  invoking the Specifier's predicate directly" (after auditing, that
  configuration's agreement "falls from 14.3% to 13.2%"). A verifier passing says the
  implementation matches the specification, not that either matches the
  source text; check that a solution does not simply call the statement it
  is meant to establish (the Lean analogue is the definition-hole trick under
  [lake comparator](#lake-comparator-and-lake-check-lean-v4350-and-later)).
  The models were GPT-4.1 and GPT-5.x small variants.

When not to rely on any of these: an LLM review of a statement, even with these
checks, is evidence for fidelity, not a proof of it; for a published result a
human still reconciles each quantifier and assumption with the informal claim.

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

**Changes after v4.35.0.** The stable v4.36.0 release notes (2026-11-16) list
no `lake comparator` or `lake check` change. The **v4.37.0-rc1** notes
(2026-11-18, a release candidate) list five entries that touch them. Two are
minor (PR #16514 passes `LEAN_NUM_THREADS` to comparator's Lean child
processes; PR #16096 documents comparator's assumptions and guarantees more
explicitly). Three change behaviour: PR #16019 adds a `--json` flag
to both commands, printing one final, versioned JSON report instead of
progress output (the types are `LakeComparatorReport` and
`LakeCheckReport`), which is the form to parse in CI; PR #15775 "forces
definition holes in comparator to either be a sorry or a lambda with a sorry
body", so a challenge "can never rely on a definition hole having a
particular value already"; and PR #15762 "makes lake check check the
project's axioms before running the kernels, as lake comparator already
does. Previously, with --paranoid, a project using a non-standard axiom (e.g.
via native_decide) was rejected only by an external checker, sometimes with
an obscure failure such as a nanoda panic, and the report naming the
unpermitted axiom was never shown." So on v4.35.0 and v4.36.0, a `lake check
--paranoid` run that dies in an external checker (for example a `nanoda`
panic) may be a non-standard axiom, not a kernel disagreement: run
`#print axioms` on the theorem.

Requirements and limits:

- **Linux only.** The v4.35.0 release notes say "The sandbox is currently only
  available on Linux". `bwrap` needs unprivileged user namespaces or a setuid
  install; Lean's own test suite notes "User namespaces cannot be assumed
  available in CI containers". On Ubuntu, worth checking the AppArmor sysctl
  `kernel.apparmor_restrict_unprivileged_userns`. In a Docker container on
  macOS (Colima, Ubuntu 24.04, Lean v4.36.0, 2026-11-23), `bwrap` first failed
  with `bwrap: Can't mkdir /run/user: Read-only file system` (fix: create
  `/run/user/$(id -u)` and set `XDG_RUNTIME_DIR`), then — even with
  `--cap-add SYS_ADMIN` and seccomp / AppArmor unconfined — with
  `bwrap: Can't mount proc on /newroot/proc: Operation not permitted`; it ran
  only under `docker run --privileged`. A privileged container weakens the
  boundary to the host VM: acceptable for your own proofs, not for checking
  someone else's solution.
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
(exit 2);
``error: `lake comparator` sandboxes the code it checks with `bwrap`, which needs Linux namespaces.``
(exit 2; `lake check` prints the
same with its own name: the machine is not Linux, e.g. macOS — seen on
v4.36.0, and raised in `src/lake/Lake/CLI/Check.lean` whenever
`System.Platform.isLinux` is false and `--inadvisably-no-sandbox` is not
given); `bwrap: setting up uid map: Permission denied` (no user namespaces);
`bwrap: Can't mkdir /run/user: Read-only file system` and
`bwrap: Can't mount proc on /newroot/proc: Operation not permitted` (both
inside an unprivileged Docker container; see "Linux only" above);
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
binary, bearing in mind that the GitHub repository is now **archived**
(read-only, so no further fixes) behind its deprecation notice: Linux with `landrun` built from source, a `lean4export` matching your
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
  extremely large inputs. The v4.37.0-rc1 notes (2026-11-18) add two fixes
  touching the kernel's handling of inductive declarations: PR #16279 fixes
  the number of parameters being "silently truncated" to 32 bits ("the
  kernel accepted an inductive declaration with numParams := 2^32 and
  recorded numParams = 0"), and PR #16512 fixes loose bound variables not
  always being checked, of which the notes say "This issue looks benign, and
  does not lead to an apparent proof of false." Neither note reports a proof
  of `False`; both are reasons the multi-checker `--paranoid` rung exists.
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
developments is unsolved. The November 2026 Riemann Hypothesis release
(next section) gives current figures: on one 62 GB export, an independent
Rust kernel took under half an hour on 80 threads, Lean's own single-threaded
kernel took two days, and the standalone comparator took 64 hours.

### What to ask of a Lean-only proof claim: the Riemann Hypothesis release (2026-11)

Aliases: Alpöge Riemann Hypothesis proof, RH in Lean, GRH Lean proof,
`alpo.ge/remark.pdf`, "formally verified in Lean", "the proof is checked in
Lean", Lean FRO and Mathlib Initiative joint statement, Sutherland
verification page. This section reports what the sources below say; the
archive was not downloaded or built for this page, and nothing here is an
independent judgement that the result is true.

**What the author released (2026-11-20).** Levent Alpöge posted a
four-page note, `alpo.ge/remark.pdf` (LessWrong linkpost
`hxHt8NaQeFADrfeAp`, which has no body text). The note's own text carries no
author name, date or affiliation: the name and the release date are as given
in the joint statement below, and the two LessWrong posts describe him as at
Anthropic. The note says: "I believe I have, working with
Claude, discovered a proof of the Riemann Hypothesis", with the method said
to extend to the Generalized Riemann Hypothesis, and "Claude and I have also
formalized the arguments without assumptions." The only artifact is a Lean
archive in 14 parts (`alpo.ge/lean.tar.gz.part01` to `part14`). There is no
prose proof: "I decided to only present Lean", the argument "is incredibly
long at the moment", and the author says he is "presenting the world with a
complete argument before having mastered a massive neighbourhood around its
mathematics". The note gives no Lean or Mathlib version, no formal
statement, no axiom list and no checking procedure. On that day, "formally
verified in Lean" was therefore a claim about an archive, to be checked. A
LessWrong post the same day called the result "probably correct", first
because "it is formally verified in Lean (Lean bugs are rare)" (Linch,
`gSQcdKtRtNpbai5TR`); that is a prior, not one of the checks below.

**The four questions.** The Xena Project blog ("…and the proof is checked in
Lean", 2026-11-12, with OpenAI's October release as its running example)
sets out the tests a Lean repository has to pass before "it was checked in
Lean" supports a correctness claim, and the joint statement on the Riemann
Hypothesis cites these four criteria:

1. "Does the Lean statement match the informal statement?"
2. "does the code compile?" (with the warning "do not run random Lean code on
   your local machine unless you sandbox it first")
3. "does the code prove the theorem as stated?" ("The one-line answer:
   `lake comparator`")
4. "does the code exploit a bug in Lean's official kernel?"
   (`lake comparator --paranoid`)

**How each was answered for this release.** Sources: the joint statement by
the Lean Focused Research Organization (Lean FRO) and the Mathlib Initiative
(leanprover-community blog, "Lean verification of the Riemann Hypothesis",
2026-11-21), and Andrew Sutherland's verification page
(`math.mit.edu/~drew/grh/`, "checks run with Claude Code"), as it stood at
its 2026-11-23 14:35 UTC update (still the page's stamp when re-fetched at
21:50 UTC that day). On who is speaking in the joint statement: its byline
now reads "Joint statement by the Lean FRO and the Mathlib Initiative." As
first posted it read "Joint statement by the Lean and Mathlib communities,
endorsed by the Lean FRO and the Mathlib Initiative"; the blog repository's
commit of 2026-11-23 changed it "to avoid attribution to the Lean and Mathlib
communities as a whole". Cite it as the two organizations' statement, not as
the community's.

| Question | What the sources report |
|---|---|
| Which statement? | Five theorems in the submission's `Main.lean`, stated in a challenge file that "imports only Mathlib". The first is Mathlib's own `RiemannHypothesis` (`Mathlib/NumberTheory/LSeries/RiemannZeta.lean`); three concern Dirichlet L-functions. Sutherland's scope note: "'GRH' here means Dirichlet L-functions: all moduli and all characters. Dedekind zeta functions, Hecke L-functions and automorphic L-functions in general are not among the statements that were checked." |
| Which toolchain; does it build? | Lean v4.33.1 and Mathlib v4.33.1; "All 175,187 modules compile" with zero errors. The joint statement puts the library at "17 million lines of code" and says "dozens of people have reported correct compilation of the codebase, reproducing the same raw proof export file". A separate sandboxed `lake build` (no network, read-only source, another machine) reproduced the export byte for byte (61,570,595,788 bytes). |
| Which axioms? | `#print axioms` on the five theorems: `propext`, `Classical.choice`, `Quot.sound` only; no axioms declared outside Lean core. |
| Same statement as the challenge? | `con-leche --compare` and `con-ron --compare` ("independent implementations of Comparator's statement matching") each confirm all five theorems; the unmodified standalone Comparator v4.33.0 reported "Your solution is okay!" after 64 h 8 min. Sutherland notes that run used the files from the original build, with its `lake build` step "satisfied by a stub". |
| Which kernels accepted the proof? | `nanoda` on the full export (27 min 42 s on 80 threads); `con-leche` built from `master` (1,468,418 declarations, 3 min 15 s on 64 threads); `lean4lean` on every module (five needed its step limit raised); Lean's default kernel via `leanchecker --from-export` on Lean v4.36.0 (48 h 3 min on one thread, peak memory 82.6 GiB). |
| Still running at that update | `lake comparator` (Lean v4.36.0) end to end (the stage still running is Lean's kernel on the export), and the paranoid kernel (`leanchecker-paranoid --from-export`, Lean v4.36.0) at default settings: "no verdict yet". The same paranoid-kernel binary with one allocator environment variable changed (`MIMALLOC_GENERIC_COLLECT=1000000`) had accepted the export (10 h 0 min on one thread, peak memory 98.8 GiB). |

The joint statement's conclusion, in its own words: "We hereby certify that
both the statement and the proof of the Riemann Hypothesis are correct." It
adds that the checks "ran on an inert export of the proof, out of reach of
hypothetical malicious code in the Lean proof sources", and that `con-leche`
and `con-ron` "come with a formal proof, relative to set theory, that they
cannot accept a false proof".

**What these checks do not supply.** A proof a person has read: the joint
statement looks forward to work "that will help explain the new ideas in
this proof", and the author's note says a proper write-up is still to come.
Anything beyond the five statements: the note says of the Extended Riemann
Hypothesis only that the author expects it "with more time".

**What to take from it for your own formal claims:**

- **This is the easy case for statement fidelity.** The headline statement
  is a definition already in a human-reviewed library, so the challenge file
  is a few lines and question 1 is nearly free. A safety-theory result
  usually defines its own objects, and then question 1 is most of the work
  (see [statement checks](#checking-that-a-formal-statement-says-what-the-informal-one-does)).
- **Publish what lets others answer the four questions without trusting
  you:** the pinned toolchain and library revision, a challenge file that
  imports only the library, the `#print axioms` output, and the hash of the
  proof export. A reader can then run checkers on the export without
  executing your build.
- **A checker that will not run is not a verdict.** On this proof the
  `con-leche` and `con-ron` binaries bundled with Lean v4.36.0 "declined"
  with "exit 2, not a rejection: those older binaries do not support one
  reflexive inductive type in the proof", and the bundled `lean4lean`
  "cannot read a v4.33 core library" (`unknown constant 'Decidable.intro'`).
  A `--paranoid` run on a newer toolchain against an export from an older
  one can fail this way; report it as "did not run", and build the checker
  from source or match the toolchain.
- **Budget for it.** Sutherland's "Check it yourself" recipe for the export
  asks for "roughly 100 GB of RAM and 70 GB of disk".
- **Cite a formal claim with its date and rung**, for example "Lean archive
  released 2026-11-20; statement matching and several independent kernels
  reported passing by 2026-11-23; `lake comparator` on v4.36.0 still
  running", not "proved in Lean".

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

Last verified: 2026-11-23. (Template-check corrections 2026-11-23: what was run on `project_templates/lean_formalization/` on Lean v4.36.0, from its README; the non-Linux refusal message from `src/lake/Lake/CLI/Check.lean` at tag v4.36.0; the elan 4.2.4 shim list and the v4.36.0 toolchain's `bin` directory listed on macOS arm64.) (Additions 2026-11-23: Lean v4.36.0 and v4.37.0-rc1 release dates via `gh api` and their release-notes pages on lean-lang.org read as text (Lean Beam bundling and PR #16478, `Float` `min`/`max`, the 12% Mathlib build figure; v4.37.0-rc1 PRs #16019, #15775, #15762, #16514, #16096, #16279, #16512; PR #16512's changed files, all under `src/kernel/`, via `gh api`); Lean Beam `docs/COMPATIBILITY.md` and `validated-lean-toolchains` at HEAD (last commit to `main` 2026-11-18, read 2026-11-23) via `gh api`; lean4-skills v4.12.0 release notes; `aristotlelib` 3.3.0 and 3.4.0 from the CHANGELOG.md and the PyPI description; LeanInteract README and PyPI (no release since v0.11.6); lean-lsp-mcp (no release since v0.33.0); LeanDojo-v2 from arXiv:2611.09048 (abstract and PDF), its README, PyPI and repository metadata; Gyevnár and DeDeo (arXiv:2611.06995, PDF), AutoIP (arXiv:2611.06962, PDF sections 4–6 and Table 1; repository via `gh api`), Saha et al. (arXiv:2611.10961, PDF section 2 and the axiom inventory appendix), Turing Agent (arXiv:2611.21299, abstract and PDF figure 3; searched for a code link) and Maji (arXiv:2611.07073, abstract and PDF section 5.1). Riemann Hypothesis section: the author's note `alpo.ge/remark.pdf` (PDF text), LessWrong posts hxHt8NaQeFADrfeAp and gSQcdKtRtNpbai5TR (raw bodies), the Xena Project post of 2026-11-12 (page text), the joint statement's markdown source in `leanprover-community/blog` (`posts/riemann_hypothesis.md`) via `gh api`, and `math.mit.edu/~drew/grh/` fetched 2026-11-23 and re-fetched at 21:50 UTC that day by a second pass (page stamped "last updated 2026-11-23 14:35 UTC" both times; it says it will be updated as the remaining checks finish); the joint statement's byline history from the blog repository's commits #149, #150 and #154; Mathlib's `RiemannHypothesis` definition read from `Mathlib/NumberTheory/LSeries/RiemannZeta.lean`. Not verified: the Lean archive was not downloaded or built; none of the logs linked from the verification page were opened; Turing Agent's three completions and the Saha et al. bounds were not re-checked; whether lean-lsp-mcp 0.33.0, lean4-skills or LeanInteract work on stable v4.36.0 was not tested.) (Additions 2026-11-04: Aristotle 3.x from the `harmonic-ai/aristotle` CHANGELOG.md (3.0.0, 3.1.0, 3.2.0) via `gh api` and the PyPI `aristotlelib` description and upload dates; lean-lsp-mcp PR #239 text, v0.33.0 release notes and README "REPL Setup" via `gh api`, PyPI upload date; `uvx` caching from uv `docs/concepts/tools.md`; Lean Beam from the `leanprover/lean-beam` README and licence via `gh api`, its `docs/COMPATIBILITY.md` (Lean 4.34–4.36 window), lean4 PR #15665 and the v4.36.0-rc2 release notes on lean-lang.org (which mention no `lake comparator` or `lake check` change); KAPPA (arXiv:2610.35596 abstract and PDF sections 7.1 and "Computational details"; repository and licence via `gh api`), PaperFormalizer (arXiv:2610.31810 abstract; repository via `gh api`), Numina Fuse (arXiv:2610.33860 abstract; licence via `gh api`), h1 (arXiv:2610.35962 abstract), SemantEq (arXiv:2610.32919 abstract; repository via `gh api`), MechAlign (arXiv:2610.35269 abstract and PDF), ProofPatch (arXiv:2611.01357 abstract and PDF, searched for a code link), Lean Finder V2 (arXiv:2610.30843 abstract) and Vampire-Hammer (arXiv:2610.40310 abstract and PDF; repository via `gh api`).) (Additions 2026-10-20: LeanInteract v0.11.6
release notes, README and PyPI; `leanprover/comparator` archived flag via the
GitHub API; Lean v4.36.0-rc1 release date; lean4-skills v4.11.4 release notes;
mini-Lean-agent (arXiv:2610.17331 abstract and PDF, repository via the GitHub
API), AnnalsChallenge (arXiv:2610.18301 abstract and PDF) and Mei and Douglas
(arXiv:2610.20573 abstract and PDF), all via the arXiv API. Not checked: whether
v4.36.0-rc1 changes `lake comparator` or `lake check`.) (Additions 2026-10-14: `lake comparator` and
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
