"""Unlearning objectives, written out so you can see what they actually do.

Three baselines, in increasing order of "does not destroy the model":

- **Gradient Ascent (GA)** — maximise loss on the forget set. Unbounded, so it
  diverges: the classic symptom is `nan loss after step N`, or a model that
  answers everything with punctuation.
- **Gradient Difference (GradDiff)** — GA on forget plus ordinary descent on
  retain. The sane baseline.
- **NPO (Negative Preference Optimization, arXiv:2404.05868)** — treats the
  forget set as the *rejected* side of a DPO-style objective with no chosen
  side. Bounded, which is what stops the collapse.

The NPO form implemented here is

    L_NPO = -(2/beta) * logsigmoid( -beta * (logp_theta - logp_ref) )
          =  (2/beta) * log( 1 + (pi_theta / pi_ref)^beta )

on forget-set sequences. Both lines are the same quantity; the second is the
form usually written in the paper. Check it against the paper before you cite a
number from it — this is our transcription, not vendored code.

Requires torch. Everything else in `ul_components` does not.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def sequence_logprob(
    logits: torch.Tensor, labels: torch.Tensor, ignore_index: int = -100
) -> torch.Tensor:
    """Sum of token log-probs per sequence, for next-token-shifted labels.

    Args:
        logits: (B, T, V) raw model logits.
        labels: (B, T) token ids, `ignore_index` where the loss is masked
            (prompt tokens, padding).

    Returns:
        (B,) tensor of summed log-probabilities of the unmasked label tokens.
    """
    if logits.ndim != 3:
        raise ValueError(f"expected logits (B, T, V), got {tuple(logits.shape)}")
    if labels.shape != logits.shape[:2]:
        raise ValueError(
            f"labels {tuple(labels.shape)} do not match logits {tuple(logits.shape[:2])}"
        )
    shift_logits = logits[:, :-1, :]
    shift_labels = labels[:, 1:]
    mask = shift_labels != ignore_index
    safe_labels = shift_labels.masked_fill(~mask, 0)

    logprobs = F.log_softmax(shift_logits.float(), dim=-1)
    token_lp = logprobs.gather(-1, safe_labels.unsqueeze(-1)).squeeze(-1)
    return (token_lp * mask).sum(dim=-1)


def _nll(logits: torch.Tensor, labels: torch.Tensor, ignore_index: int = -100) -> torch.Tensor:
    """Mean per-token negative log-likelihood, next-token shifted."""
    shift_logits = logits[:, :-1, :].float()
    shift_labels = labels[:, 1:]
    return F.cross_entropy(
        shift_logits.reshape(-1, shift_logits.size(-1)),
        shift_labels.reshape(-1),
        ignore_index=ignore_index,
    )


def gradient_ascent_loss(
    forget_logits: torch.Tensor, forget_labels: torch.Tensor, ignore_index: int = -100
) -> torch.Tensor:
    """Negated forget-set NLL. Minimising this maximises forget loss.

    Included as the honest floor, not as a recommendation. It has no lower
    bound, so with any real learning rate it will eventually take the model
    apart; if you use it, log a retain-set metric every few steps and stop on
    degradation rather than on a step count.
    """
    return -_nll(forget_logits, forget_labels, ignore_index)


def grad_diff_loss(
    forget_logits: torch.Tensor,
    forget_labels: torch.Tensor,
    retain_logits: torch.Tensor,
    retain_labels: torch.Tensor,
    retain_weight: float = 1.0,
    ignore_index: int = -100,
) -> torch.Tensor:
    """GradDiff: ascend on forget, descend on retain.

    `retain_weight` is the knob that decides whether you get a model that forgot
    everything including how to speak (too low) or one that forgot nothing (too
    high). Sweep it; do not inherit someone else's value across datasets.
    """
    forget = _nll(forget_logits, forget_labels, ignore_index)
    retain = _nll(retain_logits, retain_labels, ignore_index)
    return -forget + retain_weight * retain


def npo_loss(
    policy_logits: torch.Tensor,
    ref_logits: torch.Tensor,
    labels: torch.Tensor,
    beta: float = 0.1,
    ignore_index: int = -100,
) -> torch.Tensor:
    """NPO loss on forget-set sequences (arXiv:2404.05868).

    Args:
        policy_logits: (B, T, V) from the model being unlearned.
        ref_logits: (B, T, V) from the frozen reference (pre-unlearning) model.
            Compute these under `torch.no_grad()`.
        labels: (B, T) with `ignore_index` on prompt/padding positions.
        beta: temperature. Small beta -> gentler, slower; large beta -> closer
            to gradient ascent, and the collapse comes back.

    Returns:
        Scalar loss (mean over batch).
    """
    if beta <= 0:
        raise ValueError(f"beta must be > 0, got {beta}")
    policy_lp = sequence_logprob(policy_logits, labels, ignore_index)
    ref_lp = sequence_logprob(ref_logits, labels, ignore_index).detach()
    log_ratio = policy_lp - ref_lp
    return -(2.0 / beta) * F.logsigmoid(-beta * log_ratio).mean()


def npo_with_retain(
    policy_logits: torch.Tensor,
    ref_logits: torch.Tensor,
    forget_labels: torch.Tensor,
    retain_logits: torch.Tensor,
    retain_labels: torch.Tensor,
    beta: float = 0.1,
    retain_weight: float = 1.0,
    ignore_index: int = -100,
) -> torch.Tensor:
    """NPO on forget + ordinary NLL on retain — the variant people usually run."""
    forget = npo_loss(policy_logits, ref_logits, forget_labels, beta, ignore_index)
    retain = _nll(retain_logits, retain_labels, ignore_index)
    return forget + retain_weight * retain
