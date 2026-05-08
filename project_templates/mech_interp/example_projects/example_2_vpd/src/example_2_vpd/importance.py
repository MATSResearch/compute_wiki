"""Causal importance network.

A small MLP that takes a pooled summary of the input batch (mean-pooled token embeddings
of the frozen target model) and outputs per-matrix sigmoid masks in (0, 1)^K.

Toy choice: one mask per (matrix, batch sample). Per-token masking would need a separate
pooled vector per position — straightforward to add later but doubles memory.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class CausalImportanceNet(nn.Module):
    def __init__(
        self,
        input_dim: int,
        matrix_K: dict[str, int],
        hidden: int = 128,
        depth: int = 2,
    ):
        """
        Args:
            input_dim: dim of the pooled summary vector (typically d_model of the target).
            matrix_K: dict mapping decomposed-matrix id -> number of subcomponents K.
            hidden: hidden width of the shared trunk.
            depth: number of hidden layers in the trunk.
        """
        super().__init__()
        layers: list[nn.Module] = [nn.Linear(input_dim, hidden), nn.GELU()]
        for _ in range(depth - 1):
            layers += [nn.Linear(hidden, hidden), nn.GELU()]
        self.trunk = nn.Sequential(*layers)
        self.matrix_ids = list(matrix_K.keys())
        # Heads keyed by sanitized id (no dots → ModuleDict friendly).
        self._safe_ids = {mid: mid.replace(".", "_") for mid in self.matrix_ids}
        self.heads = nn.ModuleDict(
            {self._safe_ids[mid]: nn.Linear(hidden, K) for mid, K in matrix_K.items()}
        )

    def forward(self, pooled: torch.Tensor) -> dict[str, torch.Tensor]:
        """pooled: (B, input_dim) -> dict[matrix_id -> (B, K) sigmoid mask]."""
        h = self.trunk(pooled)
        return {mid: torch.sigmoid(self.heads[self._safe_ids[mid]](h)) for mid in self.matrix_ids}


def pool_inputs(token_embeddings: torch.Tensor) -> torch.Tensor:
    """Mean-pool token embeddings of shape (B, T, d) → (B, d). Trivial baseline.

    Free to swap for last-token pooling, attention-weighted pooling, etc.
    """
    return token_embeddings.mean(dim=1)
