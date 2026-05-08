"""Unit tests for attribution math.

Avoids loading Gemma 3 1B or any real SAE — uses a hand-built tiny dummy SAE so the
math is testable in milliseconds and works in CI without HF auth or 2 GB downloads.
"""

from __future__ import annotations

import torch

from example_1_gemma_scope import attribution


def test_direct_logit_attribution_matches_definition():
    # Set up: 4 features, d_in=3, target unembed direction = e_0.
    feat_acts = torch.tensor([2.0, 0.0, -1.5, 0.5])
    W_dec = torch.tensor(
        [
            [1.0, 0.0, 0.0],   # feature 0 decodes to e_0
            [0.0, 1.0, 0.0],   # feature 1 decodes to e_1 (orthogonal to target)
            [-2.0, 0.0, 0.0],  # feature 2 decodes opposite to e_0
            [0.5, 0.5, 0.0],   # feature 3 partially aligned with e_0
        ]
    )
    unembed = torch.tensor([1.0, 0.0, 0.0])

    contributions = attribution.direct_logit_attribution(feat_acts, W_dec, unembed)
    expected = torch.tensor(
        [
            2.0 * 1.0,    # 2.0
            0.0 * 0.0,    # 0.0
            -1.5 * -2.0,  # 3.0
            0.5 * 0.5,    # 0.25
        ]
    )
    torch.testing.assert_close(contributions, expected)


def test_top_k_features_orders_by_signed_contribution_by_default():
    feat_acts = torch.tensor([2.0, 0.0, -1.5, 0.5])
    W_dec = torch.tensor(
        [[1.0, 0.0], [0.0, 1.0], [-2.0, 0.0], [0.5, 0.0]]
    )
    unembed = torch.tensor([1.0, 0.0])

    contributions = attribution.direct_logit_attribution(feat_acts, W_dec, unembed)
    # Contributions: [2.0, 0.0, 3.0, 0.25]. Signed top-3: feature 2 (3.0), 0 (2.0), 3 (0.25).
    top = attribution.top_k_features(contributions, feat_acts, W_dec, unembed, k=3)
    assert [f.feature_index for f in top] == [2, 0, 3]
    assert top[0].contribution == 3.0


def test_top_k_features_by_absolute_value_includes_negative():
    feat_acts = torch.tensor([1.0, 0.0, -10.0])
    W_dec = torch.tensor([[1.0], [0.0], [1.0]])
    unembed = torch.tensor([1.0])

    contributions = attribution.direct_logit_attribution(feat_acts, W_dec, unembed)
    # Contributions: [1.0, 0.0, -10.0]. By |.|, the most-anti feature comes first.
    top = attribution.top_k_features(
        contributions, feat_acts, W_dec, unembed, k=2, by_absolute_value=True
    )
    assert top[0].feature_index == 2
    assert top[0].contribution == -10.0


def test_ablate_feature_in_residual_subtracts_correct_vector():
    residual = torch.tensor([1.0, 2.0, 3.0])
    feat_acts = torch.tensor([4.0, 0.0])
    W_dec = torch.tensor(
        [[10.0, 20.0, 30.0], [-1.0, -1.0, -1.0]]
    )
    out = attribution.ablate_feature_in_residual(residual, feat_acts, W_dec, feature_index=0)
    # Subtract 4.0 * [10, 20, 30] = [40, 80, 120]. Result: [-39, -78, -117].
    expected = torch.tensor([-39.0, -78.0, -117.0])
    torch.testing.assert_close(out, expected)


def test_ablate_feature_in_residual_handles_batch_and_seq_dims():
    # residual: (B=2, T=3, d=4); feat_acts: (B=2, T=3, d_sae=2)
    residual = torch.zeros(2, 3, 4)
    residual[1, 2] = torch.tensor([1.0, 1.0, 1.0, 1.0])
    feat_acts = torch.zeros(2, 3, 2)
    feat_acts[1, 2, 0] = 0.5  # only one position has nonzero activation
    W_dec = torch.tensor([[2.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0]])

    out = attribution.ablate_feature_in_residual(residual, feat_acts, W_dec, feature_index=0)
    # Only the (1, 2) position changes: [1,1,1,1] - 0.5 * [2,0,0,0] = [0,1,1,1]
    assert torch.allclose(out[1, 2], torch.tensor([0.0, 1.0, 1.0, 1.0]))
    # Everything else unchanged.
    assert torch.allclose(out[0], torch.zeros(3, 4))
    assert torch.allclose(out[1, :2], torch.zeros(2, 4))


def test_neuronpedia_source_and_url_format():
    from example_1_gemma_scope import neuronpedia

    src = neuronpedia.gemma_scope_2_source(layer=13, site="res", width="16k")
    assert src == "13-gemmascope-2-res-16k"
    # The L0 bucket is intentionally NOT in the source name (Neuronpedia hosts only
    # the canonical/medium variant per layer × width).
    assert "medium" not in src and "big" not in src and "small" not in src

    url = neuronpedia.dashboard_url("gemma-3-1b", src, 21)
    assert url == "https://www.neuronpedia.org/gemma-3-1b/13-gemmascope-2-res-16k/21"

    api = neuronpedia.api_url("gemma-3-1b", src, 21)
    assert api == "https://www.neuronpedia.org/api/feature/gemma-3-1b/13-gemmascope-2-res-16k/21"


def test_neuronpedia_fetch_returns_none_on_bad_source(monkeypatch):
    """The fetch function must never raise. Force a URLError and confirm it returns None."""
    from example_1_gemma_scope import neuronpedia

    def raise_urlerror(*_, **__):
        import urllib.error

        raise urllib.error.URLError("simulated network failure")

    monkeypatch.setattr("urllib.request.urlopen", raise_urlerror)
    out = neuronpedia.fetch_explanation("gemma-3-1b", "13-gemmascope-2-res-16k", 21, timeout=0.1)
    assert out is None


def test_neuronpedia_fetch_parallel_handles_empty():
    from example_1_gemma_scope import neuronpedia

    assert neuronpedia.fetch_explanations_parallel([]) == {}


def test_direct_logit_attribution_rejects_2d_feat_acts():
    feat_acts = torch.zeros(2, 4)  # 2D — must be a single position
    W_dec = torch.zeros(4, 3)
    unembed = torch.zeros(3)
    import pytest

    with pytest.raises(ValueError, match="single position"):
        attribution.direct_logit_attribution(feat_acts, W_dec, unembed)
