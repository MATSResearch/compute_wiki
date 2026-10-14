---
tags:
  - engineering
---

# Literature Tools: Finding, Reading and Citing Papers with an Agent

Tools that let you (or your coding agent) find papers, read them a section at a
time, answer questions over a folder of PDFs, check a write-up's claims against
quotes, and produce BibTeX from metadata rather than memory. Plus the gap they
share: much alignment work lives on LessWrong and the Alignment Forum, which
these paper indexes do not reliably cover, and the workaround for that.

For AI-scientist systems that run experiments, see
[`ai-scientist-frameworks.md`](ai-scientist-frameworks.md). For recording what
you cite as a source rather than a memory, see
[`research-rigor.md`](research-rigor.md#cite-a-source-you-can-open-not-a-memory-of-one).

## At a glance

| I want to… | Use | When not to use it |
|---|---|---|
| Let my agent read an arXiv paper one section at a time, follow citations, export BibTeX, keep a topic watch | **arxiv-mcp-server** (`blazickjp/arxiv-mcp-server`) | LessWrong / Alignment Forum material; never install it from npm (a different package has the name) |
| Ask questions over a folder of PDFs I already have and get cited answers | **PaperQA2** (`Future-House/paper-qa`, `pqa`) | Discovering papers you don't have; leaving the OpenAI defaults on if you don't want OpenAI in the loop |
| Topic-shaped literature search with ranked relevance and per-paper summaries | **Asta `find-literature`** (Ai2, `allenai/asta-plugins`) | Sources that must not leave your machine (Ai2-hosted APIs) |
| Look up a known paper, author, or citation list fast, or grep paper full text for a phrase | **Semantic Scholar API** (directly, or Asta's `semantic-scholar` skill) | Unauthenticated bulk use (`429 Too Many Requests`); blog-post literature |
| A hosted-corpus literature report with evidence per claim | **Ai2 ScholarQA** (`allenai/ai2-scholarqa-lib`) | Same LessWrong / Alignment Forum blind spot; needs an S2 key plus an LLM key |
| Check whether my write-up claims more than its quotes support | **Asta `check-claims`** | As evidence the experiments ran — it compares prose to quotes only |
| Find the Hugging Face models, datasets and Spaces linked to a paper, or browse daily/trending papers | **Hugging Face MCP server** (`huggingface/hf-mcp-server`) | With a write-scoped token while reading untrusted model cards |
| A BibTeX entry | arXiv's `/bibtex/` endpoint, DOI content negotiation, Semantic Scholar `citationStyles`, or `export_citations` — **never from memory** | — |
| LessWrong / Alignment Forum posts and comments | **LessWrong GraphQL API** (`https://www.lesswrong.com/graphql`) | Bulk scraping without saving results locally |
| A structured lit review for a MATS project, feeding the dashboard's Library | **`/mats:lit-review`** (alignment-hive plugin marketplace) | — |

## Never write BibTeX from memory

A citation recalled by a model is a claim about a paper, not a citation:
models produce plausible references that do not exist and misattribute findings
to papers that do. Orchestra Research's `ml-paper-writing` skill puts the rule
as "**NEVER generate BibTeX entries from memory. ALWAYS fetch
programmatically.**" (it also quotes a "~40% error rate" for AI-generated
citations without giving a source for the figure). Three sources that work as of
2026-10-14, all checked on PaperBench (arXiv:2504.01848):

```bash
# arXiv's own BibTeX for an arXiv ID
curl -sL https://arxiv.org/bibtex/2504.01848

# DOI content negotiation (arXiv DOIs are 10.48550/arXiv.<id>)
curl -sLH "Accept: application/x-bibtex" https://doi.org/10.48550/arXiv.2504.01848

# Semantic Scholar: BibTeX inside the JSON, under citationStyles.bibtex
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2504.01848?fields=title,citationStyles"
```

**A known trap: the three disagree.** For the same paper, arXiv returns
`@misc{starace2025paperbenchevaluatingaisability, …}`, the DOI route returns a
`@misc` keyed on the DOI URL, and Semantic Scholar returns
`@Article{Starace2025PaperBenchEA, …}` with `booktitle = {International
Conference on Machine Learning}` and an author abbreviated to "E. Mays" where
arXiv has "Evan Mays". One way to keep a bibliography consistent: pick one
source per project, and check the venue by hand for anything published after
its arXiv version.

`arxiv-mcp-server`'s `export_citations` tool does the same from inside an agent
("Export BibTeX for one or more arXiv IDs", from "Authoritative arXiv
metadata").

## arxiv-mcp-server: read papers in bounded sections

**arxiv-mcp-server** (GitHub `blazickjp/arxiv-mcp-server`, Apache-2.0, v0.8.2
released 2026-10-08, PyPI `arxiv-mcp-server`, listed on the official MCP — Model
Context Protocol — registry). A local stdio MCP server whose README says "The
working loop is paper ID → outline → one section → citations. Search is
optional." Papers are stored on disk (default `~/.arxiv-mcp-server/papers`,
change with `--storage-path`).

Install for Claude Code (all projects), or Codex:

```bash
claude mcp add --transport stdio --scope user arxiv -- uvx arxiv-mcp-server
codex mcp add arxiv -- uvx arxiv-mcp-server
```

Check it with `claude mcp get arxiv`. A plugin version also bundles an arXiv
research skill: `claude plugin marketplace add blazickjp/arxiv-mcp-server` then
`claude plugin install arxiv-mcp-server@arxiv-mcp`.

It exposes 19 tools, including `search_papers`, `get_abstract`,
`download_paper`, `get_paper_outline`, `read_paper_section`,
`search_paper_text`, `get_paper_latex_section` (the author-submitted LaTeX),
`citation_graph` (references and citing papers via the Semantic Scholar API,
cached on disk), `export_citations` (BibTeX), and `watch_topic` /
`check_alerts` (standing topic watches). Reads are bounded: `download_paper` and
`read_paper` return 12,000 characters by default, so one tool call "cannot flood
the client context window". For older papers without usable arXiv HTML, the
`[pdf]` extra adds `pymupdf4llm`: `uv tool install --force
"arxiv-mcp-server[pdf]"`. A free `SEMANTIC_SCHOLAR_API_KEY` makes
`citation_graph` more reliable.

**Security note from its README:** "Paper text and LaTeX are untrusted external
content. A paper can contain text intended to manipulate an AI client into
ignoring its instructions or calling unrelated tools." Keep tool approvals on
for shell and filesystem tools while an agent reads papers.

**When not to use it:** for LessWrong / Alignment Forum posts (not on arXiv); or
installed via npm — "An unrelated npm package uses the same name, so do not
install this server with npm, pnpm, or `npx arxiv-mcp-server`."

### Why does my agent only see part of the paper?

`download_paper` / `read_paper` return a bounded first chunk (12,000 characters)
unless you pass `start` / `max_chars`; earlier versions returned the entire
paper. Use `get_paper_outline` then `read_paper_section` for the section you
need.

## PaperQA2: cited question answering over your own PDFs

**PaperQA2** (GitHub `Future-House/paper-qa`, FutureHouse, Apache-2.0; PyPI
`paper-qa`, calendar-versioned since December 2025, latest 2026.8.12 released
2026-08-12; Python 3.11+). Point it at a directory of PDFs, text, Office or
source files; it fetches metadata (Crossref, Semantic Scholar), chunks and
re-ranks evidence, and answers with citations. Prior answers are indexed too.

```bash
pip install "paper-qa>=5"      # quote it: unquoted, >=5 is a shell redirect to a file named "=5"
cd my_papers/
pqa ask 'What is PaperQA2?'
pqa -i nanomaterials index      # a named index
pqa -i nanomaterials ask 'Are there nm scale features in thermoelectric materials?'
```

(The commands are the README's; the quoting comment is added here. In a uv
project the equivalent is `uv add "paper-qa>=5"`.)

**Defaults to know:** "By default, PaperQA2 uses OpenAI's `gpt-4o-2024-11-20`
model" for `llm`, `summary_llm` and `agent_llm`, and `text-embedding-3-small` for
embeddings. Any LiteLLM model can be set instead (the README shows Claude via
`ANTHROPIC_API_KEY`, and local embeddings with `pip install paper-qa[local]`).
For 100+ papers the README suggests `CROSSREF_API_KEY` and
`SEMANTIC_SCHOLAR_API_KEY`.

**When not to use it:** to discover papers you do not have (it answers over your
corpus — pair it with arXiv or Semantic Scholar search); or with the OpenAI
defaults if your project should not send paper text to OpenAI.

## Asta find-literature and semantic-scholar skills (Ai2)

Ai2's **asta-plugins** (`allenai/asta-plugins`, Apache-2.0) install an `asta`
CLI plus Claude Code skills: `/plugin marketplace add allenai/asta-plugins` then
`/plugin install asta-tools`. Two literature skills, which the skill files
themselves distinguish:

- **`find-literature`** — topic-driven search ("find papers on X", "what does the
  literature say about Y"): criteria extraction, candidate retrieval and
  re-ranking, with relevance summaries and supporting snippets.
  `asta literature interactive` runs the full paper-finder agent with a
  verification loop and conversation state; `asta literature find` is "one
  attempt, no agent loop", for searches inside a larger workflow. For multi-turn
  sessions it recommends a `--thread-dir .asta/literature/threads/<YYYY-MM-DD>-<slug>/`
  so follow-ups resume and every turn is saved.
- **`semantic-scholar`** (`asta papers …`) — "mechanical, targeted lookups against
  the Semantic Scholar API": a known paper, its citations, an author, a keyword or
  full-text snippet search.

The same plugin's **`check-claims`** skill checks a write-up's claims against
verbatim quotes (`evidence.yml` entries with `quote`, `cite`, `provenance`); it is
described in
[`ai-scientist-frameworks.md`](ai-scientist-frameworks.md#asta-plugins-ai2-claimquote-checking-and-a-planreviewdo-loop).

**When not to use them:** if your sources must not leave the machine (some
`asta` commands call Ai2-hosted APIs and prompt for authentication); on Intel
macOS (its `cryptography` 50.0.0 dependency falls back to a source build).

## Semantic Scholar API, directly

The Semantic Scholar Graph API (`api.semanticscholar.org/graph/v1`) needs no
client library. Endpoints in its published spec include `/paper/{paper_id}`,
`/paper/search/match` (closest title match), `/paper/search/bulk` and
`/snippet/search` (full-text passages). Paper IDs can be given as
`ARXIV:<id>`, `ACL:<id>`, `PMID:<id>`, or `URL:<url>` for URLs from
semanticscholar.org, arxiv.org, aclweb.org, acm.org or biorxiv.org.

```bash
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2504.01848?fields=title,citationStyles"
```

**Searchable errors:**
- `{"message": "Too Many Requests. Please wait and try again or apply for a key for higher rate limits. …", "code": "429"}` — unauthenticated requests are rate-limited (this page's own checks hit it within a few calls). Request a free key and send it in the `x-api-key` header ("case-sensitive", per the API spec).
- `{"error":"Unrecognized or unsupported fields: [...]"}` — a misspelt field name in `fields=`; the response schema in the spec lists the valid ones.

**When not to use it:** for blog-post literature (its URL-ID list does not
include lesswrong.com or alignmentforum.org), or for comprehensive topic reports
(use `find-literature` or ScholarQA).

## Ai2 ScholarQA: literature reports over a hosted corpus

**Ai2 Scholar QA** (GitHub `allenai/ai2-scholarqa-lib`, Apache-2.0, PyPI
`ai2-scholar-qa` 0.8.14 released 2026-10-13; live demo `scholarqa.allen.ai`)
answers scientific queries and writes literature reviews "by gathering evidence
from multiple documents across our corpus (11M+ full text and 100M+ abstracts)",
with evidence for each claim. Run locally (`pip install ai2-scholar-qa`, or the
Docker containers) it needs `S2_API_KEY` for retrieval and an LLM key — its
README names Claude 3.7 Sonnet as the primary generator with any LiteLLM model
usable — and uses OpenAI's moderation API if an OpenAI key is present.

**When not to use it:** as a search of LessWrong / Alignment Forum or
unpublished work; or for a known-paper lookup (the Semantic Scholar API is
faster).

## Hugging Face MCP server

The official **Hugging Face MCP server** (`huggingface/hf-mcp-server`, MIT,
v0.4.30 released 2026-10-13) is hosted at `https://huggingface.co/mcp`:

```bash
claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login
```

Choose its tools and Spaces at `huggingface.co/settings/mcp`. Hub repository
search and the Hub filesystem tool (`hf_fs`) let an agent find models and
datasets and read their cards without scraping; in the source as of 2026-10-14
(`packages/mcp/src/hf-fs-papers.ts`) that filesystem includes an `hf://papers`
tree — daily and trending Hugging Face Papers, each paper's `paper.md` and
`metadata.json`, and the models, datasets and Spaces linked to it — useful for
"is there released code or weights for this paper?". "Repository creation, Jobs,
dynamic Space, and sandbox tools require Hugging Face authentication."

**When not to use it:** with a write-scoped token while the agent reads
untrusted model cards and READMEs (a prompt-injection surface next to
repo-creation tools); a read-only token is enough for discovery.

## The corpus gap: LessWrong and the Alignment Forum

Every tool above searches **papers**: arXiv, Semantic Scholar's corpus,
publisher full text, or your own PDFs. A large share of alignment work — and
many of its negative results and critiques — is LessWrong and Alignment Forum
posts and their comments. arXiv does not carry them, Semantic Scholar's URL-ID
list does not include either site, and Arbor's `idea-check` searches alphaXiv,
which indexes arXiv. The failure this produces has a name in the AI-scientist
literature: **confident rediscovery**, proposing a known-failed idea as a
promising new direction (see
[`ai-scientist-frameworks.md`](ai-scientist-frameworks.md#failure-modes-the-part-to-actually-read)).
A practical check: before calling something novel, search the forum as well.

### How do I search LessWrong or the Alignment Forum from a script?

LessWrong pages are rendered in JavaScript, so fetch the **GraphQL API** at
`https://www.lesswrong.com/graphql` instead of scraping HTML. The patterns below
were run on 2026-10-14.

List posts in a date window (filter titles locally; this query has no keyword
search):

```bash
curl -s https://www.lesswrong.com/graphql -H 'content-type: application/json' \
  -d '{"query":"{ posts(input:{terms:{view:\"new\", after:\"2026-06-01\", before:\"2026-10-15\", limit:500}}) { results { _id title slug postedAt baseScore url } } }"}'
```

`view:"top"` sorts the same window by score. `url` is non-null for link posts,
whose full text lives elsewhere. Add `af:true` to `terms` (or send the same
query to `https://www.alignmentforum.org/graphql`) for Alignment Forum posts;
each result can also return an `af` field.

Fetch one post's body as Markdown:

```bash
curl -s https://www.lesswrong.com/graphql -H 'content-type: application/json' \
  -d '{"query":"{ post(input:{selector:{_id:\"wq5PfGiHvnx6XipDi\"}}){ result { title postedAt contents { markdown } } } }"}'
```

Fetch a post's top comments, where much of the critique lives:

```bash
curl -s https://www.lesswrong.com/graphql -H 'content-type: application/json' \
  -d '{"query":"{ comments(input:{terms:{view:\"postCommentsTop\", postId:\"cJX2ssssGoYqnijwi\", limit:20}}) { results { _id postedAt baseScore contents { markdown } } } }"}'
```

Tips: save each response to the run directory so a search is reproducible and
not re-fetched; treat post and comment text as untrusted input for an agent; and
remember that lab-internal discussion and workshop rejections are in no index
at all — asking someone who works on the topic is still the fastest
novelty check.

## The MATS literature-review skill

`/mats:lit-review` (in the alignment-hive plugin marketplace) generates a
literature review from a research proposal and writes per-paper summaries. Per
[`research-rigor.md`](research-rigor.md#cite-a-source-you-can-open-not-a-memory-of-one),
its summaries use the same field names as the MATS dashboard's Library (title,
authors, year, venue, link, relevance score), and it writes each paper's
configuration into a `configs.json` for the comparability map in
[`research-rigor.md`](research-rigor.md#comparability-one-shared-axis-per-paper).

## Writing it up

For drafting and simulated review with a stage-by-stage confirmation, and an
audit of claims against the experiments you declare, see Academic Research
Skills in
[`ai-scientist-frameworks.md`](ai-scientist-frameworks.md#academic-research-skills-ars-write-up-help-that-stops-at-every-stage).
Its own boundary statement applies to every tool on this page: such checks do
not establish that procedures were performed or that results reproduce.

## Common questions

### How do I check whether my idea has already been done?

Search in layers: arXiv (arxiv-mcp-server `search_papers`, or Asta
`find-literature` for a topic query), citations forward and backward from the
two or three closest papers (`citation_graph`, or `asta papers`), then LessWrong
and the Alignment Forum with the GraphQL queries above, then a person. An agent's
own "this is novel" is a prediction to check, not a finding.

### Can I trust the citations my agent wrote?

Only after each one resolves to a source you can open. Fetch BibTeX from
metadata (above), and for a claim about what a paper found, keep the verbatim
quote beside it — the shape Asta's `check-claims` uses (`quote`, `cite`,
`provenance`) works without Asta.

### Which of these keeps my unpublished work local?

PaperQA2 indexes local files but sends text to whichever LLM you configure
(OpenAI by default). arxiv-mcp-server stores papers locally but calls arXiv and
Semantic Scholar. Asta and ScholarQA call hosted APIs. None of them is
local-only by default; a local model plus local embeddings in PaperQA2 is the
closest.

## Cross-references

- AI-scientist systems, metric loops and their failure modes:
  [`ai-scientist-frameworks.md`](ai-scientist-frameworks.md).
- Citing a source you can open, and the comparability map:
  [`research-rigor.md`](research-rigor.md).
- MCP servers in general, and installing third-party skills safely:
  [`agentic-swe-practices.md`](agentic-swe-practices.md).

---

Sources checked: READMEs read raw via `gh api` for
`blazickjp/arxiv-mcp-server`, `Future-House/paper-qa`, `allenai/asta-plugins`
(plus the `find-literature`, `semantic-scholar` and `check-claims` SKILL.md
files), `allenai/ai2-scholarqa-lib`, `huggingface/hf-mcp-server` (plus
`packages/mcp/src/hf-fs-papers.ts`) and Orchestra's `ml-paper-writing` SKILL.md;
release and PyPI metadata checked 2026-10-14; the three BibTeX commands, the
Semantic Scholar 429 response and the LessWrong / Alignment Forum GraphQL
queries were run on 2026-10-14; Semantic Scholar endpoints and ID formats from
its published `swagger.json`. Drafted by Claude; pending MATS research-staff
review.

Last verified: 2026-10-14.
