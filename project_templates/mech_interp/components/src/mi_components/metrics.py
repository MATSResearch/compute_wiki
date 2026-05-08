"""Common interp scalar metrics over logits / log-probs.

Every function asserts the expected tensor shape so that a transposed or
mis-broadcast input crashes here, not three layers downstream where the
error is harder to pin on a specific call.

Conventions:
    logits        — (..., V) real-valued; the LM head's pre-softmax output.
    log_probs     — (..., V) log_softmax(logits, dim=-1).
    target_id     — int (single token id).
    target_ids    — (B,) long tensor (one target per batch row).

When you only have a single position, pass a (V,) tensor — broadcasting works.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F


def _check_logits(logits: torch.Tensor) -> None:
    if logits.dim() < 1:
        raise ValueError(f"logits must have a vocab dim, got shape {tuple(logits.shape)}")


def log_prob(logits: torch.Tensor, target_id: int) -> torch.Tensor:
    """log p(target_id | ...) under softmax over the last dim. Returns (...,) tensor."""
    _check_logits(logits)
    return F.log_softmax(logits, dim=-1)[..., target_id]


def prob(logits: torch.Tensor, target_id: int) -> torch.Tensor:
    """p(target_id | ...) under softmax over the last dim. Returns (...,) tensor."""
    return log_prob(logits, target_id).exp()


def logit_diff(logits: torch.Tensor, correct_id: int, wrong_id: int) -> torch.Tensor:
    """Logit-difference: logits[correct] - logits[wrong]. The standard "is the model
    pointing at the right answer" scalar that doesn't depend on the rest of the vocab.

    Returns (...,) — strip the last dim of `logits`.
    """
    _check_logits(logits)
    return logits[..., correct_id] - logits[..., wrong_id]


def kl_divergence(p_logits: torch.Tensor, q_logits: torch.Tensor, reduction: str = "mean") -> torch.Tensor:
    """KL(p || q) where both are softmax over the last dim of `*_logits`.

    Used to compare a clean and a patched model's distributions (faithfulness metric in
    circuit / SAE evals). Returns a scalar by default (mean over leading dims) or the
    full per-position tensor when reduction='none'.
    """
    if p_logits.shape != q_logits.shape:
        raise ValueError(f"shape mismatch: {tuple(p_logits.shape)} vs {tuple(q_logits.shape)}")
    log_p = F.log_softmax(p_logits, dim=-1)
    log_q = F.log_softmax(q_logits, dim=-1)
    p = log_p.exp()
    kl = (p * (log_p - log_q)).sum(dim=-1)
    if reduction == "mean":
        return kl.mean()
    if reduction == "sum":
        return kl.sum()
    if reduction == "none":
        return kl
    raise ValueError(f"reduction must be mean|sum|none, got {reduction!r}")


def js_divergence(p_logits: torch.Tensor, q_logits: torch.Tensor, reduction: str = "mean") -> torch.Tensor:
    """Symmetric Jensen-Shannon divergence between p and q, both softmax over last dim."""
    if p_logits.shape != q_logits.shape:
        raise ValueError(f"shape mismatch: {tuple(p_logits.shape)} vs {tuple(q_logits.shape)}")
    p = F.softmax(p_logits, dim=-1)
    q = F.softmax(q_logits, dim=-1)
    m = 0.5 * (p + q)
    log_m = m.clamp_min(1e-12).log()
    log_p = F.log_softmax(p_logits, dim=-1)
    log_q = F.log_softmax(q_logits, dim=-1)
    js = 0.5 * ((p * (log_p - log_m)).sum(dim=-1) + (q * (log_q - log_m)).sum(dim=-1))
    if reduction == "mean":
        return js.mean()
    if reduction == "sum":
        return js.sum()
    if reduction == "none":
        return js
    raise ValueError(f"reduction must be mean|sum|none, got {reduction!r}")


def target_rank(logits: torch.Tensor, target_id: int) -> torch.Tensor:
    """0-indexed rank of `target_id` when sorting logits descending. 0 = top prediction.

    Returns (...,) integer tensor.
    """
    _check_logits(logits)
    target_logit = logits[..., target_id].unsqueeze(-1)
    return (logits > target_logit).sum(dim=-1)


def top_k_accuracy(logits: torch.Tensor, target_ids: torch.Tensor, k: int = 1) -> torch.Tensor:
    """Fraction of rows where target_ids[b] is in the top-k of logits[b].

    Args:
        logits: (..., V) — last dim is vocab.
        target_ids: shape matching `logits.shape[:-1]` — one target per row.
        k: top-K threshold.
    Returns: scalar tensor (the mean accuracy).
    """
    _check_logits(logits)
    if target_ids.shape != logits.shape[:-1]:
        raise ValueError(
            f"target_ids shape {tuple(target_ids.shape)} must match logits.shape[:-1]={tuple(logits.shape[:-1])}"
        )
    topk = logits.topk(k, dim=-1).indices  # (..., k)
    correct = (topk == target_ids.unsqueeze(-1)).any(dim=-1)
    return correct.float().mean()


def cross_entropy_per_token(logits: torch.Tensor, target_ids: torch.Tensor) -> torch.Tensor:
    """Per-token cross-entropy. Returns (...,) — same leading shape as `target_ids`.

    Args:
        logits: (..., V).
        target_ids: same leading shape as logits[..., :-1] dropped of vocab dim.
    """
    _check_logits(logits)
    if target_ids.shape != logits.shape[:-1]:
        raise ValueError(
            f"target_ids shape {tuple(target_ids.shape)} must match logits.shape[:-1]={tuple(logits.shape[:-1])}"
        )
    log_probs = F.log_softmax(logits, dim=-1)
    return -log_probs.gather(-1, target_ids.unsqueeze(-1)).squeeze(-1)


def perplexity(logits: torch.Tensor, target_ids: torch.Tensor) -> torch.Tensor:
    """exp(mean cross-entropy). Scalar tensor."""
    return cross_entropy_per_token(logits, target_ids).mean().exp()


def faithfulness(
    clean_logits: torch.Tensor,
    patched_logits: torch.Tensor,
    corrupted_logits: torch.Tensor,
    correct_id: int,
    wrong_id: int,
) -> torch.Tensor:
    """Standard circuit-faithfulness score on logit-difference.

    f = (LD(patched) - LD(corrupted)) / (LD(clean) - LD(corrupted))

    Reads as "what fraction of the clean-vs-corrupted logit-difference does the patched
    model recover." 1.0 = patched matches clean; 0.0 = patched matches corrupted; values
    outside [0, 1] indicate over- or under-shoot.
    """
    ld_c = logit_diff(clean_logits, correct_id, wrong_id)
    ld_p = logit_diff(patched_logits, correct_id, wrong_id)
    ld_x = logit_diff(corrupted_logits, correct_id, wrong_id)
    denom = (ld_c - ld_x)
    return (ld_p - ld_x) / denom.clamp_min(1e-12)
