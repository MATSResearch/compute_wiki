"""SAE-feature direct logit attribution + ablation.

Given a residual-stream vector r at the SAE's layer:

  feat_acts = sae.encode(r)                   # (..., d_sae), mostly zero
  reconstruction = sae.decode(feat_acts)      # (..., d_in)

The decoder is a linear map: decode(feat_acts) = sum_f feat_acts[f] * W_dec[f].

For a target token t with unembedding row W_U[t]:

  logit_contribution[f] = feat_acts[f] * (W_dec[f] . W_U[t])

This is the "direct" component — it ignores any non-linear / multi-layer paths
that the residual takes after the SAE's layer. It's the standard first-pass
attribution and is what the toy example reports.

Ablation works by subtracting one feature's contribution from the residual at
the SAE's hooked layer:

  r_ablated = r - feat_acts[f] * W_dec[f]

The forward pass is then re-run with the residual replaced at that layer.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class FeatureAttribution:
    feature_index: int
    activation: float
    contribution: float  # signed; positive = pushes toward target token
    decoder_alignment: float  # decoder_dir . unembed_dir, independent of activation


@dataclass
class AttributionReport:
    target_token_id: int
    target_logit_clean: float
    target_prob_clean: float
    target_logit_ablated: float | None
    target_prob_ablated: float | None
    top_features: list[FeatureAttribution]
    ablated_feature_index: int | None


def encode_residual(sae, residual: torch.Tensor) -> torch.Tensor:
    """Run sae.encode on a residual tensor. Returns feature activations.

    `residual` is (..., d_in). Output is (..., d_sae). Most entries are zero
    for a JumpReLU SAE.
    """
    return sae.encode(residual)


def direct_logit_attribution(
    feat_acts: torch.Tensor,
    sae_decoder_weight: torch.Tensor,
    unembed_direction: torch.Tensor,
) -> torch.Tensor:
    """Per-feature contribution to the target logit.

    Args:
        feat_acts: (d_sae,) feature activations at one position.
        sae_decoder_weight: (d_sae, d_in) — `sae.W_dec`.
        unembed_direction: (d_in,) — the unembedding row for the target token.
                           For logit-difference attribution, pass W_U[correct] - W_U[wrong].

    Returns: (d_sae,) tensor of signed contributions.
    """
    if feat_acts.dim() != 1:
        raise ValueError(f"feat_acts must be 1D (single position), got shape {tuple(feat_acts.shape)}")
    decoder_dot_unembed = sae_decoder_weight @ unembed_direction  # (d_sae,)
    return feat_acts * decoder_dot_unembed


def top_k_features(
    contributions: torch.Tensor,
    feat_acts: torch.Tensor,
    sae_decoder_weight: torch.Tensor,
    unembed_direction: torch.Tensor,
    k: int = 10,
    by_absolute_value: bool = False,
) -> list[FeatureAttribution]:
    """Return the top-K features ranked by contribution (signed by default, abs optional).

    `decoder_alignment` (the per-feature dot product with unembed_direction) is reported
    separately so the reader can see which features are aligned regardless of activation.
    """
    if by_absolute_value:
        order = torch.argsort(contributions.abs(), descending=True)
    else:
        order = torch.argsort(contributions, descending=True)
    decoder_alignment = sae_decoder_weight @ unembed_direction
    out: list[FeatureAttribution] = []
    for idx in order[:k].tolist():
        out.append(
            FeatureAttribution(
                feature_index=int(idx),
                activation=float(feat_acts[idx]),
                contribution=float(contributions[idx]),
                decoder_alignment=float(decoder_alignment[idx]),
            )
        )
    return out


def ablate_feature_in_residual(
    residual: torch.Tensor,
    feat_acts: torch.Tensor,
    sae_decoder_weight: torch.Tensor,
    feature_index: int,
) -> torch.Tensor:
    """Subtract one feature's reconstruction contribution from a residual vector.

    Args:
        residual: (..., d_in) residual at the SAE's layer.
        feat_acts: (..., d_sae) feature activations from sae.encode(residual).
        sae_decoder_weight: (d_sae, d_in) — `sae.W_dec`.
        feature_index: which feature to subtract.

    Returns: (..., d_in) residual with that feature's contribution removed.
    """
    decoder_dir = sae_decoder_weight[feature_index]  # (d_in,)
    # Pick out the activation at the same leading-dim shape as residual, broadcast over d_in.
    act = feat_acts[..., feature_index].unsqueeze(-1)  # (..., 1)
    return residual - act * decoder_dir


# Neuronpedia URL helpers + explanation fetcher live in neuronpedia.py — kept separate
# because attribution.py is pure math (no I/O), and the URL format differs between
# Gemma Scope 1 and 2.
