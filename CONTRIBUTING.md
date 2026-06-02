# Contributing to the MATS Research Tooling Wiki

Thanks for helping keep this guide accurate and useful. Fellows and mentors are welcome to contribute.

## How to propose a change

1. On the [published site](https://matsresearch.github.io/compute_wiki/), click the **edit (pencil) icon** at the top of any page. It opens that file on GitHub.
2. Make your edit. GitHub will let you **open a pull request** (and offer to fork the repo first if you don't have write access).
3. A maintainer reviews and merges. Merges to `master` automatically rebuild and redeploy the site.

Small fixes (typos, dead links, version bumps) are great as direct PRs. For larger restructuring, open an issue first so we can agree on the shape.

## Writing conventions

These docs have two audiences: **fellows reading them directly**, and **torchy**, a RAG (Retrieval-Augmented Generation) assistant that runs keyword search over the files. The retrieval consumer is dominant, so **write for keyword retrieval**:

1. **Self-contained sections.** Each tool gets a section that makes sense in isolation. Don't write "as discussed above" — retrieval pulls a single chunk, so that reference is gone.
2. **Keyword density.** Include every common name for a tool: PyPI name, GitHub org/repo, common shorthand, primary author.
3. **Spell out acronyms in every section** that uses them (CAA = Contrastive Activation Addition, SAE = Sparse Autoencoder, …). Repeat across sections — RAG doesn't carry definitions between chunks.
4. **Pitfalls include searchable symptoms.** Paste the literal error strings a fellow would hit (`RuntimeError: shape mismatch`, `nan loss after step N`).
5. **Headers fellows would type.** Mix topic headers (`## TransformerLens`) with question headers (`### How do I get activations from a 70B model?`).
6. **Decision tables.** Prefer "I want to do X → use Y" tables where possible.
7. **One-line "when not to use it"** for every tool — that caveat is the unique value of this guide.
8. **Verify before claiming.** Don't assert a tool exists or has a feature without checking via the repo or a web search. These libraries move fast.
9. End each topic doc with a **"Last verified"** date.

## Structure

- `docs/index.md` — the "I want to do X, use Y" decision table; site homepage and entry point.
- `docs/NN_topic.md` — one file per topic, numbered.
- `docs/FAQ.md`, `docs/GLOSSARY.md` — cross-cutting references.

## Building the site locally

```bash
uv sync --group docs
uv run mkdocs serve   # live-preview at http://127.0.0.1:8000
uv run mkdocs build --strict   # what CI runs; fails on broken links
```
