# Background reading for this example

Summaries go here as markdown (convert PDFs with `pymupdf4llm`, don't scrape the
HTML). The papers this example is built around:

- **arXiv:2504.02922** — "Overcoming Sparsity Artifacts in Crosscoders to
  Interpret Chat-Tuning". The reason a raw "latents unique to the finetuned
  model" count is not defensible without a latent-scaling check.
- **arXiv:2603.04426** — "Delta-Crosscoder: Robust Crosscoder Model Diffing in
  Narrow Fine-Tuning Regimes". The regime this example deliberately sits in.
- **arXiv:2602.11729** — "Cross-Architecture Model Diffing with Crosscoders".
  Why `md_components.pairing` refuses mismatched architectures instead of
  silently proceeding.
- **Anthropic, "Stage-Wise Model Diffing"** (transformer-circuits.pub, 2024) —
  the original crosscoder-diffing write-up.
