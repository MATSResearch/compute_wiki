# CLAUDE.md — example_2_vpd

This is a **toy replication** of VPD (Adversarial Parameter Decomposition), Bushnaq et al. 2026 (Goodfire). The paper summary lives in `docs/papers/vpd_summary.md`.

## Scope (don't expand without asking)

- Toy: defaults run on CPU in a few minutes, on a single GPU in well under a minute.
- The target model is **distilgpt2** (~82M params, 24 linear-like weight matrices) frozen at HF-pretrained weights. Decompose a small subset of those matrices (default: layer 0 attention + MLP, configurable).
- One mask per (matrix, batch sample) — not per token. Per-token masking is doable but pushes scope.
- Soft sigmoid masks + L1 sparsity; no Gumbel/hard-concrete unless someone explicitly wants it.

## Design notes

- Subcomponents are parameterized as `(U: K×d_out, V: K×d_in)` so subcomp_k = U_k V_k^T (rank-one).
- The forward path uses the algebraic identity `Σ_k m_k · u_k v_k^T x = Σ_k m_k u_k (v_k · x)` to avoid materializing per-sample weight matrices. See `decomposition.SubcomponentBank.forward`.
- Initialization is truncated SVD of the original weight, so reconstruction starts near-perfect and the optimizer only has to specialize the components.
- Adversarial term: drops bits from the predicted mask (Bernoulli over predicted probabilities) and asks for KL stability. This is a stand-in for the paper's full adversarial search.

## Don't

- Don't move from per-batch masks to per-token without flagging the API change — the importance-net signature changes.
- Don't bake the target model into the decomposition code — keep it injectable so we can swap in a hand-trained micro-transformer.
- Don't add wandb as a hard dependency. `mi_components.tracking` falls back to JSONL.
