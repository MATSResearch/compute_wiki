"""Generic Direct Logit Attribution (DLA).

Direct Logit Attribution = "if you push a residual-stream component through the
unembedding, how much does it move the target logit?" It's the workhorse first-pass
interp metric. The example_1_gemma_scope project specializes this to one
SAE feature at a time; this module is the generalization for use across projects.

Core formulas (all on a single position; broadcast yourself for batch):

  contribution(x)        = x · W_U[target_id]                           (scalar)
  contribution_diff(x)   = x · (W_U[correct_id] - W_U[wrong_id])        (logit-difference attribution)
  per_basis_contribution = (basis @ W_U[target_id])    where basis is (k, d_model)

`basis` can be:
  - SAE decoder rows (W_dec): one row per feature, gives per-feature contributions.
  - Attention head output projections decomposed by head: per-head contributions.
  - Eigenvectors / singular vectors of a weight matrix: per-mode contributions.
  - Probe directions, steering vectors, anything else linear.

DLA ignores any non-linear / multi-layer transformations applied to the residual
*after* the layer the component is read from. It's the local approximation; for
exact attribution use attribution patching or path patching (see `interventions`).
"""

from __future__ import annotations

import torch


def unembed_direction(lm_head_weight: torch.Tensor, target_id: int) -> torch.Tensor:
    """Row of the unembedding matrix for `target_id`. lm_head.weight is (V, d_model)."""
    if lm_head_weight.dim() != 2:
        raise ValueError(f"lm_head_weight must be 2D (V, d), got {tuple(lm_head_weight.shape)}")
    return lm_head_weight[target_id]


def unembed_direction_diff(lm_head_weight: torch.Tensor, correct_id: int, wrong_id: int) -> torch.Tensor:
    """W_U[correct] - W_U[wrong]. The direction whose dot product with the residual
    equals `logits[correct] - logits[wrong]`. Standard logit-difference attribution.
    """
    if lm_head_weight.dim() != 2:
        raise ValueError(f"lm_head_weight must be 2D (V, d), got {tuple(lm_head_weight.shape)}")
    return lm_head_weight[correct_id] - lm_head_weight[wrong_id]


def direct_attribution(component: torch.Tensor, direction: torch.Tensor) -> torch.Tensor:
    """component · direction along the last dim. Returns (...) — last dim stripped."""
    if component.shape[-1] != direction.shape[-1]:
        raise ValueError(
            f"last dim mismatch: component {tuple(component.shape)} vs direction {tuple(direction.shape)}"
        )
    return (component * direction).sum(dim=-1)


def per_basis_contribution(
    basis: torch.Tensor,
    direction: torch.Tensor,
    coefficients: torch.Tensor | None = None,
) -> torch.Tensor:
    """For each basis row b_i, return (coefficients[i] *) (b_i · direction).

    Args:
        basis: (k, d_model) — basis rows, e.g. SAE W_dec or attention head V·W_O outputs.
        direction: (d_model,) — typically W_U[target_id] or a logit-diff direction.
        coefficients: (k,) optional — feature activations or head-aggregated norms.
                      If None, returns the raw per-basis dot products.

    Returns: (k,) tensor.
    """
    if basis.dim() != 2:
        raise ValueError(f"basis must be (k, d), got {tuple(basis.shape)}")
    if direction.dim() != 1 or direction.shape[0] != basis.shape[1]:
        raise ValueError(
            f"direction must be (d,) with d={basis.shape[1]}, got {tuple(direction.shape)}"
        )
    dots = basis @ direction  # (k,)
    if coefficients is None:
        return dots
    if coefficients.shape != (basis.shape[0],):
        raise ValueError(
            f"coefficients must be (k={basis.shape[0]},), got {tuple(coefficients.shape)}"
        )
    return coefficients * dots


def top_k(
    contributions: torch.Tensor,
    k: int = 10,
    by_absolute_value: bool = False,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Return (indices, values) of the top-k entries in a 1D contributions tensor.

    Sign: by default the most-positive (most pushing toward target) come first.
    Pass `by_absolute_value=True` to surface large negative contributions too.
    """
    if contributions.dim() != 1:
        raise ValueError(f"contributions must be 1D, got {tuple(contributions.shape)}")
    keys = contributions.abs() if by_absolute_value else contributions
    order = torch.argsort(keys, descending=True)[:k]
    return order, contributions[order]


def attribute_residual(
    residual: torch.Tensor,
    lm_head_weight: torch.Tensor,
    target_id: int,
) -> torch.Tensor:
    """Direct contribution of `residual` to `target_id`'s logit. residual: (..., d_model)."""
    return direct_attribution(residual, unembed_direction(lm_head_weight, target_id))


def attribute_residual_diff(
    residual: torch.Tensor,
    lm_head_weight: torch.Tensor,
    correct_id: int,
    wrong_id: int,
) -> torch.Tensor:
    """Logit-difference attribution of `residual` to (correct - wrong)."""
    return direct_attribution(
        residual, unembed_direction_diff(lm_head_weight, correct_id, wrong_id)
    )
