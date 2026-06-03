# CLAUDE.md — recommended_tooling

This project produces an AI safety research tooling guide for MATS fellows.

## Audience and consumption

- **Direct readers:** MATS fellows browsing the docs themselves.
- **RAG consumer:** A Claude-powered MATS assistant called **torchy** (lives in a separate project) will be given access to these docs and will run keyword search to answer fellow-specific questions.

This second consumer is the dominant one. **Write for keyword retrieval.**

## Writing rules

When adding or editing a topic doc:

1. **Self-contained sections.** Each tool gets its own section that makes sense in isolation. Do not say "as discussed above" — when RAG retrieves a single chunk, that reference is gone.
2. **Keyword density.** Include all common names for each tool: PyPI name, GitHub org/repo, common shorthand, primary author. Example: "**SAELens** (`sae-lens` on PyPI, `decoderesearch/SAELens` on GitHub, sometimes called 'Joseph Bloom's SAE library')".
3. **Spell out acronyms in every section** that uses them. CAA = Contrastive Activation Addition. SAE = Sparse Autoencoder. Repeat across sections — RAG doesn't carry definitions across chunks.
4. **Pitfalls include searchable symptoms.** Include the literal error strings a fellow would paste: `RuntimeError: shape mismatch`, `tokenizer mismatch`, `nan loss after step N`.
5. **Headers fellows would type.** Mix topic-shaped headers (`## TransformerLens`) with question-shaped ones (`### How do I get activations from a 70B model?`).
6. **Decision tables.** Where possible, "I want to do X → use Y" tables — they retrieve well and answer common questions in one chunk.

## Structure

- `docs/index.md` — decision guide and entry point (site homepage).
- `docs/<section>/<topic>.md` — one file per topic, grouped into section folders
  (`start-here`, `models-and-compute`, `interpretability`, `evaluation`,
  `alignment-science`, `oversight-and-control`, `engineering`). No numeric
  prefixes; sidebar order comes from the `nav:` block in `mkdocs.yml`.
- Each topic doc carries `tags:` frontmatter and ends with a "Last verified" date.
- Old flat `NN_topic.md` URLs still resolve via `redirect_maps` in `mkdocs.yml`;
  add a new entry whenever you move or rename a doc.

## Don't

- Don't write a long narrative intro to each topic. Get to the tool list fast.
- Don't recommend tools without a one-line "when not to use it" — that's the unique value here.
- Don't claim a tool exists or has a feature without verifying via web search or repo inspection. Memory of tool names from training data is unreliable for fast-moving libraries.
