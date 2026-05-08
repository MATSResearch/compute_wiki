---
title: "Interpretability in the Wild: A Circuit for Indirect Object Identification in GPT-2 Small"
authors:
  - Kevin Wang
  - Alexandre Variengien
  - Arthur Conmy
  - Buck Shlegeris
  - Jacob Steinhardt
publication_year: 2022
arxiv: https://arxiv.org/abs/2211.00593
venue: ICLR 2023
---

## Summary

Wang et al. discovered and reverse-engineered a complete circuit in GPT-2 Small for the **Indirect Object Identification (IOI)** task. Given prompts of the form "When John and Mary went to the store, John gave a drink to ___", the model strongly prefers " Mary" (the indirect object) over " John" (the duplicated subject). The paper identifies ~26 attention heads in 6 functional roles — name-mover heads, S-inhibition heads, induction heads, duplicate-token heads, previous-token heads, backup name-movers — that together implement the prediction.

The circuit was found via **path patching** (Goldowsky-Dill et al. 2023) and **activation patching**. Each head's role was validated by ablating it and measuring the impact on the logit difference `logit(IO) - logit(S)`.

This is the canonical "complete circuit" example in mech interp; it's been replicated, extended, and re-analyzed many times (e.g. with SAEs by Marks et al., with attribution patching by Syed et al.).

## Why this is example_3

Two things make IOI a great toy at the **feature** level rather than the head level:

1. **Known answer.** The head-level circuit is well-known, so feature-level findings can be checked against ground truth.
2. **Compositional structure.** The roles (move-name, inhibit-subject, detect-duplicate) are the kinds of computational primitives SAE features should ideally correspond to. If feature-level analysis recovers cleanly-separated features for these roles, that's a positive result for SAEs as a circuit-discovery tool.

## Caveats

- **Original task is on GPT-2 Small.** The exact circuit doesn't transfer to other architectures token-for-token. Whether Gemma 3 1B even solves IOI cleanly needs verification before building.
- **IOI prompts are templated** — easy to generate, but tokenization quirks (e.g. how names get split) matter for analysis. Use the prompt set distributed by the original authors as a starting point if possible.
- **Logit difference is the standard metric.** When mapping to features, attribute against `W_U[IO_token] - W_U[S_token]`, not just the logit of the correct name.

## Citation

Wang, K., Variengien, A., Conmy, A., Shlegeris, B., & Steinhardt, J. (2022). *Interpretability in the Wild: A Circuit for Indirect Object Identification in GPT-2 Small*. arXiv:2211.00593.
