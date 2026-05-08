"""VPD losses.

Combined objective:
    L = λ_full     * KL( target || decomposed_full_mask )       # all components active
      + λ_masked   * KL( target || decomposed_predicted_mask )  # importance-net mask
      + λ_recon    * sum_m ||sum_k U_m[k] V_m[k]^T - W_m||_F    # weight-space reconstruction
      + λ_sparsity * mean_m mean_k mask_m[k]                    # encourage sparse masks
      + λ_adv      * KL( target || decomposed_perturbed_mask )  # bernoulli-drop adversarial term

The "perturbed mask" approximates the paper's adversarial selection: it samples a
Bernoulli over the predicted mask values and zeroes out a random subset; the
decomposition should still match target output.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F


@dataclass
class LossWeights:
    full: float = 1.0
    masked: float = 1.0
    recon: float = 0.01
    sparsity: float = 0.05
    adv: float = 0.5


@dataclass
class LossBreakdown:
    total: float
    full: float
    masked: float
    recon: float
    sparsity: float
    adv: float
    mean_mask: float


def kl_logits(target_logits: torch.Tensor, predicted_logits: torch.Tensor) -> torch.Tensor:
    """KL( target || predicted ) over the last dim, averaged over leading dims.

    target_logits is treated as the "true" distribution. Both inputs are pre-softmax.
    """
    log_target = F.log_softmax(target_logits, dim=-1)
    log_pred = F.log_softmax(predicted_logits, dim=-1)
    target_probs = log_target.exp()
    return (target_probs * (log_target - log_pred)).sum(dim=-1).mean()


def perturb_mask_bernoulli(mask: torch.Tensor, drop_prob: float = 0.5) -> torch.Tensor:
    """Drop a random subset of the mask: mask_perturbed = mask * Bernoulli(1 - drop_prob).

    This is a stand-in for the paper's adversarial mask search. The straight-through trick
    keeps gradients flowing to the importance net through the *unperturbed* mask values.
    """
    keep = (torch.rand_like(mask) > drop_prob).float()
    return mask * keep


def compute_vpd_loss(
    target_logits: torch.Tensor,
    decomposed_model,
    importance_net,
    pooled_summary: torch.Tensor,
    input_ids: torch.Tensor,
    forward_decomposed_fn,
    weights: LossWeights,
    adv_drop_prob: float = 0.5,
) -> tuple[torch.Tensor, LossBreakdown]:
    """One full VPD loss computation.

    Args:
        target_logits: (B, T, V) — the frozen target model's output.
        decomposed_model: DecomposedModel (provides .set_masks, .reconstruction_loss).
        importance_net: CausalImportanceNet — predicts masks from `pooled_summary`.
        pooled_summary: (B, d_model) input to the importance net.
        input_ids: (B, T) — re-fed into the decomposed model under different masks.
        forward_decomposed_fn: callable(input_ids) -> logits, runs the decomposed model
                               with whatever masks are currently set on its layers.
        weights: scalar coefficients for each loss term.
        adv_drop_prob: fraction of mask bits to drop in the adversarial term.

    Returns: (total_loss_tensor, LossBreakdown of scalar floats).
    """
    matrix_ids = list(decomposed_model.decomposed_modules.keys())
    predicted_masks = importance_net(pooled_summary)  # dict id -> (B, K)

    # Term 1: full-mask faithfulness (all components active)
    decomposed_model.set_masks({mid: None for mid in matrix_ids})
    logits_full = forward_decomposed_fn(input_ids)
    loss_full = kl_logits(target_logits, logits_full)

    # Term 2: predicted-mask faithfulness
    decomposed_model.set_masks(predicted_masks)
    logits_masked = forward_decomposed_fn(input_ids)
    loss_masked = kl_logits(target_logits, logits_masked)

    # Term 3: reconstruction in weight space
    loss_recon = decomposed_model.reconstruction_loss()

    # Term 4: sparsity — average mask value across all matrices and components
    mean_mask_value = torch.stack([m.mean() for m in predicted_masks.values()]).mean()

    # Term 5: adversarial — perturb the predicted mask and require continued faithfulness
    perturbed_masks = {mid: perturb_mask_bernoulli(m, adv_drop_prob) for mid, m in predicted_masks.items()}
    decomposed_model.set_masks(perturbed_masks)
    logits_adv = forward_decomposed_fn(input_ids)
    loss_adv = kl_logits(target_logits, logits_adv)

    total = (
        weights.full * loss_full
        + weights.masked * loss_masked
        + weights.recon * loss_recon
        + weights.sparsity * mean_mask_value
        + weights.adv * loss_adv
    )
    breakdown = LossBreakdown(
        total=total.item(),
        full=loss_full.item(),
        masked=loss_masked.item(),
        recon=loss_recon.item(),
        sparsity=mean_mask_value.item(),
        adv=loss_adv.item(),
        mean_mask=mean_mask_value.item(),
    )
    return total, breakdown
