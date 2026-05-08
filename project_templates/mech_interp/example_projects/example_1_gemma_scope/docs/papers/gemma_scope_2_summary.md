---
title: "Gemma Scope 2: A Comprehensive Suite of SAEs and Transcoders for the Gemma 3 Family"
team: Google DeepMind
publication_year: 2025
huggingface_org: https://huggingface.co/google
neuronpedia: https://www.neuronpedia.org/gemma-scope-2
lesswrong_announcement: https://www.lesswrong.com/posts/YQro5LyYjDzZrBCdb/announcing-gemma-scope-2
---

## Summary

**Gemma Scope 2** is the second-generation release of pretrained sparse autoencoders (SAEs) and transcoders from Google DeepMind, this time covering the **Gemma 3** model family at sizes **270M, 1B, 4B, 12B, and 27B**, in both pretrained (`-pt-`) and instruction-tuned (`-it-`) variants. SAEs are trained on **three sites per layer** — residual stream (`-res`), MLP output (`-mlp`), and attention output (`-att`) — at every layer. The release also includes MLP transcoders for every layer of every model and partial residual-stream crosscoders for every base Gemma 3 model, plus cross-layer transcoders for the 270M and 1B variants.

SAEs use the JumpReLU architecture (Rajamanoharan et al. 2024). Each (model, site) combination is published at multiple widths (16k, 65k, 262k, 1m features) and L0 sparsity buckets named **`small`, `medium`, `big`** (not `large`). Layer coverage is sparse — for instance `gemma-scope-2-1b-pt-res` only ships SAEs at layers {7, 13, 17, 22}, *not* every layer. Always enumerate the actual catalog before assuming a layer exists.

## SAELens integration

Loading via SAELens 6.x:

```python
from sae_lens import SAE
sae = SAE.from_pretrained(
    release="gemma-scope-2-1b-pt-res",         # Gemma 3 1B base, residual stream
    sae_id="layer_13_width_16k_l0_medium",     # underscores, NOT slashes (changed from Gemma Scope 1)
    device="cuda",
    dtype="float32",
)

# Enumerate what's actually available for a release:
from sae_lens.saes.sae import get_pretrained_saes_directory
ids = list(get_pretrained_saes_directory()["gemma-scope-2-1b-pt-res"].saes_map.keys())
# 1B-pt-res ships 52 SAEs at layers {7, 13, 17, 22} × widths {16k,65k,262k,1m} × L0 {small,medium,big}.
```

The release index is in `sae_lens/pretrained_saes.yaml` in the SAELens repo. Browse all features at https://www.neuronpedia.org/gemma-scope-2.

## Why we use this for example_1

- **Gemma 3** is the current Google open-weight family (2025+); using Gemma 2 in a 2026 example would be a backwater choice for a fellow copying this template.
- **1B at 16k features, medium L0** is the sweet spot for a toy: small enough to load on CPU or any GPU, sparse enough that "top features" is a tractable list (~30–60 active features per token), wide enough that features tend to be reasonably specific.
- **Three SAE sites per layer** (res / mlp / att) means a fellow extending this example can swap which site they hook with a one-line release change.

## Caveats

- **`-pt-` vs `-it-` matters.** Default to `-pt-` (base) for cleaner residual-stream features; switch to `-it-` only when studying instruction-following or refusal behaviors.
- **L0 buckets are heuristic.** "medium" was chosen by DeepMind to balance reconstruction and sparsity; for serious work, compare across buckets.
- **sae_id format changed from Gemma Scope 1** (slashes → underscores; bucket name `large` → `big`). Tutorials written for the 2024 release will not load 2025 SAEs verbatim.
- **Layer coverage is sparse, not comprehensive.** Gemma Scope 1 had every-layer SAEs; Gemma Scope 2 1B has only 4 layers per site. Larger Gemma 3 sizes have more layers but still aren't every-layer.
- **Auto-interp labels on Neuronpedia are heuristic** — useful as a starting point, not ground truth.

## Citation

The primary release lives at https://huggingface.co/google/gemma-scope-2 with technical report at https://storage.googleapis.com/deepmind-media/DeepMind.com/Blog/gemma-scope-2-helping-the-ai-safety-community-deepen-understanding-of-complex-language-model-behavior/Gemma_Scope_2_Technical_Paper.pdf. The original Gemma Scope (2024) paper is arXiv:2408.05147 and is the best background on the JumpReLU SAE methodology if you haven't read it.
