"""Linear-algebra helpers for weight-matrix and activation decomposition.

Mech interp decomposition methods (PCA on activations, SVD on weight matrices,
projection onto / out of subspaces, low-rank approximation) keep reaching for
the same handful of operations. This module wraps them with shape assertions and
returns dataclasses so the meaning of each output is unambiguous.

When NOT to use this:
- For SAE training, use SAELens — these helpers do not optimize sparsity.
- For high-performance distributed SVD, fall back to `torch.linalg.svd` directly.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch


@dataclass
class SVDResult:
    U: torch.Tensor  # (m, k) — left singular vectors as columns
    S: torch.Tensor  # (k,)  — singular values, descending
    Vt: torch.Tensor  # (k, n) — right singular vectors as rows


def svd(matrix: torch.Tensor, full_matrices: bool = False) -> SVDResult:
    """Plain wrapper around torch.linalg.svd that returns a named tuple.

    `matrix` is (m, n). With full_matrices=False (the default), output shapes are
    U: (m, k), S: (k,), Vt: (k, n) where k = min(m, n) — much cheaper for tall/wide matrices.
    """
    if matrix.dim() != 2:
        raise ValueError(f"matrix must be 2D, got {tuple(matrix.shape)}")
    U, S, Vt = torch.linalg.svd(matrix, full_matrices=full_matrices)
    return SVDResult(U=U, S=S, Vt=Vt)


def low_rank_approx(matrix: torch.Tensor, rank: int) -> torch.Tensor:
    """Best rank-`rank` approximation of `matrix` (Eckart-Young).

    Useful for "what does the top-r modes of this weight matrix look like?".
    """
    r = svd(matrix, full_matrices=False)
    k = min(rank, r.S.numel())
    return r.U[:, :k] @ torch.diag(r.S[:k]) @ r.Vt[:k, :]


def explained_variance_ratio(singular_values: torch.Tensor) -> torch.Tensor:
    """Fraction of squared-Frobenius energy each singular mode accounts for.

    Output sums to 1.0, descending. Use cumulative-sum to find the rank needed for
    e.g. 95% of the matrix's energy.
    """
    sq = singular_values.pow(2)
    return sq / sq.sum().clamp_min(1e-12)


def pca(activations: torch.Tensor, n_components: int | None = None, center: bool = True) -> SVDResult:
    """PCA on rows of `activations` via SVD on the centered matrix.

    Args:
        activations: (N, d) — N samples, d features. Each row is one observation.
        n_components: keep only the top-k components (None = all).
        center: subtract the per-feature mean first (the standard PCA convention).

    Returns SVDResult where Vt's rows are the principal directions in feature space,
    and S^2 / (N-1) are the explained variances.
    """
    if activations.dim() != 2:
        raise ValueError(f"activations must be 2D (N, d), got {tuple(activations.shape)}")
    X = activations - activations.mean(dim=0, keepdim=True) if center else activations
    r = svd(X, full_matrices=False)
    if n_components is not None:
        k = min(n_components, r.S.numel())
        return SVDResult(U=r.U[:, :k], S=r.S[:k], Vt=r.Vt[:k, :])
    return r


def project_onto(activation: torch.Tensor, directions: torch.Tensor) -> torch.Tensor:
    """Project `activation` onto the span of the rows of `directions`.

    Complement of `mi_components.interventions.project_out_directions`.
    """
    if directions.dim() != 2:
        raise ValueError(f"directions must be (k, d), got {tuple(directions.shape)}")
    Q, _ = torch.linalg.qr(directions.T.to(activation.dtype))  # (d, k_orth)
    coeffs = activation @ Q
    return coeffs @ Q.T


def cosine_similarity(a: torch.Tensor, b: torch.Tensor, eps: float = 1e-12) -> torch.Tensor:
    """Cosine similarity along the last dim. Broadcasts.

    For a (k, d) basis and a (d,) direction, returns (k,) per-row similarity.
    """
    a_n = a / a.norm(dim=-1, keepdim=True).clamp_min(eps)
    b_n = b / b.norm(dim=-1, keepdim=True).clamp_min(eps)
    return (a_n * b_n).sum(dim=-1)


def gram_schmidt(vectors: torch.Tensor) -> torch.Tensor:
    """Orthonormalize the rows of `vectors`. Returns the same shape (k, d).

    Thin wrapper around QR; rows in the output are guaranteed orthonormal.
    Rank-deficient inputs may produce zero rows for the deficient slots.
    """
    if vectors.dim() != 2:
        raise ValueError(f"vectors must be 2D (k, d), got {tuple(vectors.shape)}")
    Q, _ = torch.linalg.qr(vectors.T)  # (d, k)
    return Q.T


def truncated_svd_basis(matrix: torch.Tensor, rank: int) -> tuple[torch.Tensor, torch.Tensor]:
    """Return (left_basis, right_basis) of size (rank, m) and (rank, n) from a 2D matrix.

    Convenience for "give me the top-`rank` directions on each side." Each row is unit-norm.
    """
    r = svd(matrix, full_matrices=False)
    k = min(rank, r.S.numel())
    return r.U[:, :k].T.contiguous(), r.Vt[:k, :].contiguous()
