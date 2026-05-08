"""Unit tests for VPD decomposition + losses.

These avoid loading distilgpt2 — they construct hand-built tiny modules so the math is
testable in milliseconds. The full smoke test (which does load distilgpt2) lives in
train.py and is invoked separately.
"""

from __future__ import annotations

import torch
import torch.nn as nn

from example_2_vpd import importance, losses
from example_2_vpd.decomposition import DecomposedLinear, SubcomponentBank, decompose_model


def test_subcomponent_bank_assemble_full_rank_matches_target():
    torch.manual_seed(0)
    W = torch.randn(8, 6)
    bank = SubcomponentBank(W, K=8)  # K >= rank → exact reconstruction
    Wsum = bank.assemble()
    assert torch.allclose(Wsum, W, atol=1e-5), f"max err {(Wsum - W).abs().max()}"


def test_subcomponent_bank_truncated_K_drops_smallest_singulars():
    torch.manual_seed(0)
    W = torch.randn(10, 8)
    K = 3
    bank = SubcomponentBank(W, K)
    Wsum = bank.assemble()
    # Truncated SVD with K terms is the optimal rank-K approximation.
    U_full, S, Vh = torch.linalg.svd(W, full_matrices=False)
    expected = U_full[:, :K] @ torch.diag(S[:K]) @ Vh[:K, :]
    assert torch.allclose(Wsum, expected, atol=1e-5)


def test_subcomponent_bank_forward_matches_assembled_weight():
    torch.manual_seed(0)
    W = torch.randn(5, 4)
    bank = SubcomponentBank(W, K=4)
    x = torch.randn(2, 3, 4)  # (B, T, d_in)
    full_mask = torch.ones(4)
    out_via_forward = bank.forward(x, full_mask)
    out_via_assembled = x @ bank.assemble().T
    assert torch.allclose(out_via_forward, out_via_assembled, atol=1e-5)


def test_subcomponent_bank_per_sample_mask_zeros_one_component():
    torch.manual_seed(0)
    W = torch.randn(4, 3)
    bank = SubcomponentBank(W, K=3)
    x = torch.randn(2, 1, 3)
    mask_keep_all = torch.ones(2, 3)
    mask_drop_first = torch.tensor([[0.0, 1.0, 1.0], [1.0, 1.0, 1.0]])
    out_keep = bank.forward(x, mask_keep_all)
    out_drop = bank.forward(x, mask_drop_first)
    # Sample 1 unchanged, sample 0 differs.
    assert torch.allclose(out_keep[1], out_drop[1], atol=1e-5)
    assert not torch.allclose(out_keep[0], out_drop[0], atol=1e-5)


def test_decomposed_linear_with_full_mask_matches_original_linear():
    torch.manual_seed(0)
    orig = nn.Linear(6, 8)
    dl = DecomposedLinear(orig, K=8)
    x = torch.randn(2, 3, 6)
    dl.set_mask(None)  # all components active
    out_dl = dl(x)
    out_orig = orig(x)
    assert torch.allclose(out_dl, out_orig, atol=1e-4)


def test_decompose_model_freezes_non_bank_params():
    class Tiny(nn.Module):
        def __init__(self):
            super().__init__()
            self.embed = nn.Embedding(10, 4)
            self.fc = nn.Linear(4, 4)

        def forward(self, ids):
            return self.fc(self.embed(ids))

    from mi_components import models as mi_models

    net = Tiny()
    refs = list(mi_models.iter_linear_weights(net))
    dec = decompose_model(net, refs, K=4)
    # Embedding should be frozen.
    assert not net.embed.weight.requires_grad
    # Bank params should be trainable.
    assert all(p.requires_grad for p in net.fc.bank.parameters())
    # And we should have one decomposed module.
    assert list(dec.decomposed_modules.keys()) == ["fc"]


def test_causal_importance_net_outputs_valid_masks():
    imp = importance.CausalImportanceNet(input_dim=8, matrix_K={"a": 4, "b.c": 6}, hidden=16, depth=2)
    pooled = torch.randn(3, 8)
    out = imp(pooled)
    assert set(out.keys()) == {"a", "b.c"}
    assert out["a"].shape == (3, 4)
    assert out["b.c"].shape == (3, 6)
    assert (out["a"] > 0).all() and (out["a"] < 1).all()


def test_kl_logits_zero_on_identical_inputs():
    logits = torch.randn(2, 3, 5)
    assert losses.kl_logits(logits, logits).item() < 1e-6


def test_kl_logits_positive_on_different_inputs():
    a = torch.randn(2, 3, 5)
    b = torch.randn(2, 3, 5)
    assert losses.kl_logits(a, b).item() > 0
