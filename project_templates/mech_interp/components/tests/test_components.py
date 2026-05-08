"""Unit tests for mi_components.

These avoid network/disk-heavy operations where possible. Model loading is tested by
calling iter_linear_weights on a hand-built tiny nn.Module, not by downloading from HF.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
import torch
import torch.nn as nn

from mi_components import (
    activations,
    cache,
    config,
    decomposition,
    device,
    dla,
    hooks,
    interventions,
    io,
    metrics,
    models,
    patching,
    runs,
    seeding,
    sweep,
)


class _TinyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(10, 4)
        self.fc1 = nn.Linear(4, 8)
        self.fc2 = nn.Linear(8, 4)

    def forward(self, x):
        h = self.embed(x)
        h = torch.relu(self.fc1(h))
        return self.fc2(h)


def test_iter_linear_weights_finds_linears():
    net = _TinyNet()
    refs = list(models.iter_linear_weights(net))
    ids = [r.id for r in refs]
    assert ids == ["fc1", "fc2"]
    assert refs[0].param.shape == (8, 4)


def test_iter_linear_weights_includes_embedding_when_asked():
    net = _TinyNet()
    refs = list(models.iter_linear_weights(net, include_embedding=True))
    ids = [r.id for r in refs]
    assert "embed" in ids


def test_freeze_disables_grad():
    net = _TinyNet()
    models.freeze(net)
    assert not any(p.requires_grad for p in net.parameters())


def test_capture_hook_records_output_and_removes_hook():
    net = _TinyNet()
    x = torch.zeros(2, 3, dtype=torch.long)
    with hooks.capture(net, ["fc1"]) as acts:
        net(x)
    assert "fc1" in acts
    assert acts["fc1"].shape == (2, 3, 8)
    # After the context exits, no leftover hooks should fire — verify by counting forward hooks.
    assert len(net.fc1._forward_hooks) == 0


def test_patch_output_replaces_module_output():
    net = _TinyNet()
    x = torch.zeros(1, 2, dtype=torch.long)
    sentinel = torch.full((1, 2, 8), 7.0)
    with hooks.patch_output(net, "fc1", sentinel):
        out = net(x)
    # fc2(relu(sentinel)) — every entry of sentinel is positive so relu is identity.
    expected = net.fc2(torch.relu(sentinel))
    torch.testing.assert_close(out, expected)


def test_runs_writes_metadata_and_checkpoint(tmp_path):
    run = runs.new_run(tag="unit/test", base=tmp_path)
    assert run.root.exists()
    assert run.tag == "unit_test"

    @dataclass
    class Cfg:
        lr: float = 1e-3
        steps: int = 5

    run.write_metadata(Cfg())
    md = (run.root / "metadata.json").read_text()
    assert "lr" in md and "steps" in md

    ckpt = run.save_checkpoint("step_001", {"weight": torch.zeros(2)})
    assert ckpt.exists() and ckpt.suffix == ".pt"


def test_config_overrides_coerce_types():
    @dataclass
    class Sub:
        lr: float = 0.1

    @dataclass
    class Cfg:
        steps: int = 1
        name: str = "default"
        flag: bool = False
        sub: Sub = None  # type: ignore

        def __post_init__(self):
            if self.sub is None:
                self.sub = Sub()

    cfg = config.parse_overrides(Cfg(), ["steps=10", "flag=true", "sub.lr=3e-4", "name=foo"])
    assert cfg.steps == 10
    assert cfg.flag is True
    assert cfg.sub.lr == 3e-4
    assert cfg.name == "foo"


def test_config_unknown_key_raises():
    @dataclass
    class Cfg:
        x: int = 1

    with pytest.raises(ValueError, match="unknown config key"):
        config.parse_overrides(Cfg(), ["typo=2"])


# ---------------------------------------------------------------------------
# metrics
# ---------------------------------------------------------------------------


def test_metrics_log_prob_and_prob_match_softmax():
    logits = torch.tensor([1.0, 2.0, 3.0])
    p = torch.softmax(logits, dim=-1)
    assert torch.allclose(metrics.prob(logits, target_id=2), p[2])
    assert torch.allclose(metrics.log_prob(logits, target_id=0), p[0].log())


def test_metrics_logit_diff():
    logits = torch.tensor([10.0, 0.0, -3.0])
    assert metrics.logit_diff(logits, correct_id=0, wrong_id=1).item() == 10.0


def test_metrics_kl_zero_when_distributions_match():
    a = torch.tensor([1.0, 2.0, 3.0]).expand(4, 3).contiguous()
    assert metrics.kl_divergence(a, a).abs().item() < 1e-6


def test_metrics_kl_shape_mismatch_raises():
    with pytest.raises(ValueError, match="shape mismatch"):
        metrics.kl_divergence(torch.zeros(3), torch.zeros(4))


def test_metrics_target_rank_top_is_zero():
    logits = torch.tensor([0.1, 5.0, 0.0])
    assert metrics.target_rank(logits, target_id=1).item() == 0
    assert metrics.target_rank(logits, target_id=2).item() == 2


def test_metrics_top_k_accuracy():
    # 2 batches, vocab=4
    logits = torch.tensor([[0.0, 0.5, 1.0, 0.2], [3.0, 0.0, 0.0, 0.0]])
    targets = torch.tensor([2, 0])  # both correct top-1
    assert metrics.top_k_accuracy(logits, targets, k=1).item() == 1.0
    targets_wrong = torch.tensor([0, 0])  # only 2nd correct
    assert metrics.top_k_accuracy(logits, targets_wrong, k=1).item() == 0.5


def test_metrics_faithfulness_recovers_clean_when_patched_equals_clean():
    clean = torch.tensor([5.0, -1.0])
    corrupt = torch.tensor([0.0, 0.0])
    f = metrics.faithfulness(clean, clean, corrupt, correct_id=0, wrong_id=1)
    assert abs(f.item() - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# interventions
# ---------------------------------------------------------------------------


class _ResidNet(nn.Module):
    """Minimal model: takes (B, T) ints, embeds, applies a "block", returns logits."""

    def __init__(self):
        super().__init__()
        self.embed = nn.Embedding(10, 4)
        self.block = nn.Linear(4, 4)
        self.head = nn.Linear(4, 10)

    def forward(self, x):
        h = self.embed(x.long() if x.dtype != torch.long else x)
        h = self.block(h)
        return self.head(h)


def test_zero_ablate_zeros_block_output():
    net = _ResidNet()
    x = torch.zeros(1, 3, dtype=torch.long)
    with interventions.zero_ablate(net, "block"):
        out = net(x)
    # If block output is zero, head's bias is the only thing left at every position.
    expected = net.head(torch.zeros(1, 3, 4))
    torch.testing.assert_close(out, expected)


def test_mean_ablate_replaces_with_given_vector():
    net = _ResidNet()
    x = torch.zeros(1, 3, dtype=torch.long)
    mean = torch.full((4,), 2.0)
    with interventions.mean_ablate(net, "block", mean):
        out = net(x)
    expected = net.head(mean.expand(1, 3, 4))
    torch.testing.assert_close(out, expected)


def test_project_out_directions_kills_aligned_component():
    # Single direction along e_0; activation = (1, 1, 0) -> projected = (0, 1, 0).
    activation = torch.tensor([1.0, 1.0, 0.0])
    directions = torch.tensor([[1.0, 0.0, 0.0]])
    out = interventions.project_out_directions(activation, directions)
    expected = torch.tensor([0.0, 1.0, 0.0])
    torch.testing.assert_close(out, expected, atol=1e-6, rtol=1e-6)


def test_add_steering_vector_adds_to_block_output():
    net = _ResidNet()
    x = torch.zeros(1, 2, dtype=torch.long)
    direction = torch.tensor([0.0, 0.0, 0.0, 1.0])
    base = net(x)
    with interventions.add_steering_vector(net, "block", direction, coefficient=3.0):
        steered = net(x)
    # Steered residual = base_block + 3 * e_3 ; head is linear so head(.) shifts predictably.
    delta = steered - base
    # Expect head(3 * e_3) - head(0) = 3 * head.weight[:, 3] across every position.
    expected_delta = 3.0 * net.head.weight[:, 3]
    torch.testing.assert_close(delta[0, 0], expected_delta, atol=1e-5, rtol=1e-5)


# ---------------------------------------------------------------------------
# dla
# ---------------------------------------------------------------------------


def test_dla_per_basis_contribution_matches_manual():
    basis = torch.tensor([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])  # (k=3, d=2)
    direction = torch.tensor([2.0, -1.0])
    coeffs = torch.tensor([3.0, -1.0, 0.5])
    out = dla.per_basis_contribution(basis, direction, coeffs)
    # b @ d = [2, -1, 1]; * coeffs -> [6, 1, 0.5]
    torch.testing.assert_close(out, torch.tensor([6.0, 1.0, 0.5]))


def test_dla_top_k_signed_vs_absolute():
    contributions = torch.tensor([1.0, -10.0, 3.0, 0.0])
    idx_signed, vals_signed = dla.top_k(contributions, k=2, by_absolute_value=False)
    assert idx_signed.tolist() == [2, 0]
    idx_abs, vals_abs = dla.top_k(contributions, k=2, by_absolute_value=True)
    assert idx_abs[0].item() == 1


def test_dla_attribute_residual_logit_diff_signs():
    # (V=2, d=2). W_U[0] = e_0; W_U[1] = e_1.
    lm_head = torch.tensor([[1.0, 0.0], [0.0, 1.0]])
    # Residual along e_0 should push positively toward target 0 vs 1.
    residual = torch.tensor([5.0, 0.0])
    diff = dla.attribute_residual_diff(residual, lm_head, correct_id=0, wrong_id=1)
    assert diff.item() == 5.0


# ---------------------------------------------------------------------------
# decomposition
# ---------------------------------------------------------------------------


def test_decomposition_low_rank_approx_recovers_low_rank_matrix():
    u = torch.randn(6, 2)
    v = torch.randn(2, 4)
    M = u @ v  # rank 2 by construction
    approx = decomposition.low_rank_approx(M, rank=2)
    torch.testing.assert_close(M, approx, atol=1e-5, rtol=1e-5)


def test_decomposition_explained_variance_ratio_sums_to_one():
    M = torch.randn(8, 5)
    r = decomposition.svd(M)
    ratios = decomposition.explained_variance_ratio(r.S)
    assert abs(ratios.sum().item() - 1.0) < 1e-5
    # Descending.
    assert torch.all(ratios[:-1] >= ratios[1:])


def test_decomposition_cosine_similarity_basic():
    a = torch.tensor([1.0, 0.0])
    b = torch.tensor([1.0, 0.0])
    assert abs(decomposition.cosine_similarity(a, b).item() - 1.0) < 1e-6
    c = torch.tensor([0.0, 1.0])
    assert abs(decomposition.cosine_similarity(a, c).item()) < 1e-6


# ---------------------------------------------------------------------------
# activations
# ---------------------------------------------------------------------------


def test_running_stats_matches_naive_on_small_data():
    x = torch.randn(20, 4)
    stats = activations.RunningStats()
    stats.update_batched(x[:7])
    stats.update_batched(x[7:13])
    stats.update_batched(x[13:])
    torch.testing.assert_close(stats.mean.float(), x.mean(dim=0).float(), atol=1e-5, rtol=1e-5)
    torch.testing.assert_close(stats.std().float(), x.std(dim=0, unbiased=True).float(), atol=1e-5, rtol=1e-5)


def test_collect_mean_activation_token_mean():
    net = _ResidNet()
    batches = [torch.zeros(2, 3, dtype=torch.long), torch.zeros(2, 3, dtype=torch.long)]
    mean = activations.collect_mean_activation(net, "block", batches, aggregate="token_mean")
    assert mean.shape == (4,)


# ---------------------------------------------------------------------------
# patching
# ---------------------------------------------------------------------------


class _ModelWrapper(nn.Module):
    """Make _ResidNet quack like an HF model: forward returns an object with .logits."""

    def __init__(self):
        super().__init__()
        self.inner = _ResidNet()

    def forward(self, x):
        class _Out:
            pass

        out = _Out()
        out.logits = self.inner(x)
        return out


def test_activation_patch_scan_calls_metric_per_layer():
    m = _ModelWrapper()
    x = torch.zeros(1, 2, dtype=torch.long)
    patch_vals = {"inner.block": torch.zeros(1, 2, 4)}
    results = patching.activation_patch_scan(
        m, x, ["inner.block"], patch_vals, metric_fn=lambda logits: float(logits.mean())
    )
    assert len(results) == 1
    assert results[0].name == "inner.block"


# ---------------------------------------------------------------------------
# tokens (no real tokenizer — use a tiny stub)
# ---------------------------------------------------------------------------


class _StubTokenizer:
    pad_token = "<pad>"
    eos_token = "<eos>"

    def __init__(self):
        self.vocab = {"<pad>": 0, "<eos>": 1, "Paris": 2, " Paris": 3, "Au": 4, " Au": 5, "x": 6}
        self.inv = {v: k for k, v in self.vocab.items()}

    def encode(self, text, add_special_tokens=True):
        # Trivial: single-token if exactly in vocab; else split chars (so " Au " → 3 chars).
        if text in self.vocab:
            return [self.vocab[text]]
        return [self.vocab.get(c, 6) for c in text]

    def decode(self, ids):
        return "".join(self.inv.get(int(i), "?") for i in ids)


def test_target_token_id_single_token_lookup():
    from mi_components import tokens

    tk = _StubTokenizer()
    assert tokens.target_token_id(tk, " Paris") == 3


def test_target_token_id_raises_on_multi_token_when_required():
    from mi_components import tokens

    tk = _StubTokenizer()
    with pytest.raises(ValueError, match="2 tokens"):
        tokens.target_token_id(tk, "ab")  # tokenizes char-by-char in the stub


def test_last_token_index_basic():
    from mi_components import tokens

    mask = torch.tensor([[1, 1, 1, 0, 0], [1, 1, 0, 0, 0]])
    idx = tokens.last_token_index(mask)
    assert idx.tolist() == [2, 1]


# ---------------------------------------------------------------------------
# seeding / device / cache / sweep / io
# ---------------------------------------------------------------------------


def test_seeding_makes_torch_reproducible():
    seeding.set_seed(123)
    a = torch.randn(5)
    seeding.set_seed(123)
    b = torch.randn(5)
    torch.testing.assert_close(a, b)


def test_device_pick_device_returns_cpu_when_no_cuda():
    # On the CI machine we can at least test the prefer='cpu' branch.
    d = device.pick_device(prefer="cpu")
    assert d.type == "cpu"


def test_device_summary_has_expected_keys():
    s = device.device_summary()
    assert "cuda_available" in s
    assert "torch_version" in s


def test_disk_cache_roundtrip(tmp_path):
    calls = {"n": 0}

    @cache.disk_cache(cache_dir=tmp_path / "cache")
    def slow(x: int) -> torch.Tensor:
        calls["n"] += 1
        return torch.tensor([x, x * 2])

    out1 = slow(3)
    out2 = slow(3)  # second call: cached
    torch.testing.assert_close(out1, out2)
    assert calls["n"] == 1


def test_sweep_grid_yields_cartesian_product():
    @dataclass
    class Cfg:
        a: int = 1
        b: int = 2

    cfgs = list(sweep.grid(Cfg(), {"a": [10, 20], "b": [100, 200]}))
    assert len(cfgs) == 4
    pairs = {(c.a, c.b) for c in cfgs}
    assert pairs == {(10, 100), (10, 200), (20, 100), (20, 200)}


def test_sweep_unknown_key_raises():
    @dataclass
    class Cfg:
        a: int = 1

    with pytest.raises(ValueError, match="unknown config field"):
        list(sweep.grid(Cfg(), {"typo": [1, 2]}))


def test_io_jsonl_roundtrip(tmp_path):
    rows = [{"step": 1, "loss": 0.5}, {"step": 2, "loss": 0.3}]
    p = io.write_jsonl(tmp_path / "metrics.jsonl", rows)
    out = list(io.read_jsonl(p))
    assert out == rows


def test_io_dataclass_roundtrip(tmp_path):
    @dataclass
    class Cfg:
        lr: float = 1e-3
        name: str = "a"

    cfg = Cfg(lr=2e-4, name="run1")
    p = io.dataclass_to_json(cfg, tmp_path / "cfg.json")
    restored = io.dataclass_from_json(Cfg, p)
    assert restored == cfg
