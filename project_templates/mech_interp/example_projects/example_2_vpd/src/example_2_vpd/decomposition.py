"""Rank-one parameter decomposition.

For each target weight matrix W (d_out x d_in) we learn K rank-one subcomponents
parameterized as (U: K x d_out, V: K x d_in), where subcomp_k = U[k] V[k]^T.

The forward path uses the algebraic identity

    (sum_k m_k * U[k] V[k]^T) @ x = sum_k m_k * U[k] * (V[k] . x)

which lets us apply per-sample masks without ever materializing per-sample weight
matrices. See SubcomponentBank.forward for the einsum.

`DecomposedModel` wraps a frozen language model and replaces a chosen subset of its
linear-like submodules with `DecomposedLinear` modules backed by SubcomponentBanks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import torch
import torch.nn as nn
import torch.nn.functional as F


def _is_conv1d(module: nn.Module) -> bool:
    """transformers.pytorch_utils.Conv1D — detected by class name to avoid the import."""
    return type(module).__name__ == "Conv1D"


def _set_submodule(root: nn.Module, dotted_name: str, new: nn.Module) -> None:
    """Replace root.<dotted.name> with `new` via setattr on the parent."""
    parts = dotted_name.split(".")
    parent: nn.Module = root
    for part in parts[:-1]:
        parent = parent[int(part)] if part.isdigit() else getattr(parent, part)
    setattr(parent, parts[-1], new)


class SubcomponentBank(nn.Module):
    """K rank-one subcomponents of a single weight matrix.

    Args:
        weight: the original (d_out, d_in) weight tensor, used for SVD initialization.
                Not retained — only its values at construction time matter.
        K: number of rank-one components. If K >= rank(weight), reconstruction is exact at init.
    """

    def __init__(self, weight: torch.Tensor, K: int):
        super().__init__()
        if weight.dim() != 2:
            raise ValueError(f"SubcomponentBank expects a 2D weight, got shape {tuple(weight.shape)}")
        d_out, d_in = weight.shape
        # Truncated SVD init: distribute singular values evenly into U and V so |s_k| ~ sqrt(sigma_k)
        with torch.no_grad():
            U_full, S, Vh = torch.linalg.svd(weight.detach().float(), full_matrices=False)
        K_eff = min(K, S.shape[0])
        sqrt_s = S[:K_eff].sqrt()
        U_init = (U_full[:, :K_eff] * sqrt_s).T.contiguous()  # (K_eff, d_out)
        V_init = (Vh[:K_eff, :] * sqrt_s.unsqueeze(1)).contiguous()  # (K_eff, d_in)
        if K > K_eff:
            U_init = torch.cat([U_init, torch.zeros(K - K_eff, d_out)], dim=0)
            V_init = torch.cat([V_init, torch.zeros(K - K_eff, d_in)], dim=0)
        self.U = nn.Parameter(U_init)  # (K, d_out)
        self.V = nn.Parameter(V_init)  # (K, d_in)
        self.K = K
        self.d_out = d_out
        self.d_in = d_in

    def assemble(self, mask: torch.Tensor | None = None) -> torch.Tensor:
        """Build the effective weight matrix sum_k mask_k * U[k] V[k]^T.

        Mostly used for reconstruction-loss bookkeeping and inspection. Forward passes
        should call .forward instead, which avoids materializing this tensor per-sample.
        """
        if mask is None:
            return self.U.T @ self.V  # (d_out, d_in)
        if mask.dim() == 1:
            return (self.U * mask.unsqueeze(1)).T @ self.V  # (d_out, d_in)
        # Batched mask (B, K): produce (B, d_out, d_in). Caller's responsibility memory-wise.
        Um = self.U.unsqueeze(0) * mask.unsqueeze(2)
        return torch.einsum("bkd,ke->bde", Um, self.V)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None) -> torch.Tensor:
        """Apply the masked decomposed weight to x.

        Args:
            x: (B, T, d_in) or (..., d_in) — last dim is d_in.
            mask: None (use all components) or (K,) (same mask for batch) or (B, K) (per-sample mask).

        Returns: tensor with the same leading dims as x, last dim d_out.
        """
        # Project: v_k . x for every (k, position)
        proj = x @ self.V.T  # (..., K)
        if mask is None:
            masked = proj
        elif mask.dim() == 1:
            masked = proj * mask  # broadcast over leading dims
        elif mask.dim() == 2:
            # (B, K) — broadcast mask to (B, T, K) by inserting middle dim
            if proj.dim() == 3 and mask.shape[0] == proj.shape[0]:
                masked = proj * mask.unsqueeze(1)
            else:
                # rank mismatch: try to broadcast naively
                masked = proj * mask
        else:
            raise ValueError(f"mask must be 1D or 2D, got shape {tuple(mask.shape)}")
        return masked @ self.U  # (..., d_out)

    def reconstruction_error(self, target_weight: torch.Tensor) -> torch.Tensor:
        """Frobenius norm of (sum_k U[k] V[k]^T - target_weight). Differentiable."""
        return torch.linalg.norm(self.U.T @ self.V - target_weight, ord="fro")


class DecomposedLinear(nn.Module):
    """Drop-in replacement for an nn.Linear or HuggingFace Conv1D, backed by a SubcomponentBank.

    Provides .set_mask(mask) to set the active mask used by the next forward pass.
    Mask shape: (K,) for batch-shared or (B, K) for per-sample.
    """

    def __init__(self, original: nn.Module, K: int):
        super().__init__()
        self.is_conv1d = _is_conv1d(original)
        # Capture original weight in (d_out, d_in) orientation regardless of source class.
        with torch.no_grad():
            W = original.weight.detach().clone()
            if self.is_conv1d:
                # Conv1D weight is (d_in, d_out); transpose so SubcomponentBank sees (d_out, d_in).
                W = W.T.contiguous()
        self.bank = SubcomponentBank(W, K)
        # Stash original bias as a buffer-or-parameter; we reuse it directly.
        if getattr(original, "bias", None) is not None:
            self.register_buffer("bias", original.bias.detach().clone())
        else:
            self.bias = None
        # Keep a frozen copy of the target weight for reconstruction loss.
        self.register_buffer("target_weight", W)
        self._mask: torch.Tensor | None = None

    def set_mask(self, mask: torch.Tensor | None) -> None:
        self._mask = mask

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.bank.forward(x, self._mask)
        if self.bias is not None:
            out = out + self.bias
        return out


@dataclass
class DecomposedModel:
    """A frozen target model with a chosen subset of its linear-like layers replaced by DecomposedLinears.

    Attributes:
        model: the (mutated in-place) target nn.Module — call it like the original.
        decomposed_modules: dict mapping dotted-name -> the DecomposedLinear inserted there.
                            Order is insertion order, matching the order returned by iter_linear_weights.
    """

    model: nn.Module
    decomposed_modules: dict[str, DecomposedLinear]

    def set_masks(self, masks: dict[str, torch.Tensor | None]) -> None:
        """Apply per-matrix masks. Keys not in `masks` will get mask=None (all components active)."""
        for name, mod in self.decomposed_modules.items():
            mod.set_mask(masks.get(name))

    def trainable_parameters(self) -> list[nn.Parameter]:
        params: list[nn.Parameter] = []
        for mod in self.decomposed_modules.values():
            params.extend(mod.bank.parameters())
        return params

    def reconstruction_loss(self) -> torch.Tensor:
        """Sum of Frobenius reconstruction errors across all decomposed matrices."""
        terms = [
            mod.bank.reconstruction_error(mod.target_weight) for mod in self.decomposed_modules.values()
        ]
        return torch.stack(terms).sum()


def decompose_model(
    model: nn.Module,
    weight_refs: Iterable,  # iterable of mi_components.models.WeightRef
    K: int,
) -> DecomposedModel:
    """Replace each weight_ref's parent module with a DecomposedLinear of K components.

    The original model is mutated in-place; the function returns a DecomposedModel handle
    that exposes the swapped modules for masking and inspection.
    """
    decomposed: dict[str, DecomposedLinear] = {}
    for ref in weight_refs:
        new = DecomposedLinear(ref.module, K)
        new = new.to(device=ref.param.device, dtype=ref.param.dtype)
        _set_submodule(model, ref.id, new)
        decomposed[ref.id] = new
    # Freeze every parameter outside the new banks.
    for name, p in model.named_parameters():
        if any(name.startswith(f"{mid}.bank.") for mid in decomposed):
            p.requires_grad_(True)
        else:
            p.requires_grad_(False)
    return DecomposedModel(model=model, decomposed_modules=decomposed)
