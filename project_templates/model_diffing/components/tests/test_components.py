"""Tests for md_components.

Pure-Python modules (pairing, ranking, control) always run; the torch-backed
ones use a tiny random model so the suite stays fast.

    uv run pytest
"""

from __future__ import annotations

import pytest

from md_components import control, pairing, ranking


def _facts(**over) -> pairing.ModelFacts:
    base = dict(
        name="m", vocab_size=50257, architecture="GPT2LMHeadModel",
        n_layers=6, hidden_size=768, dtype="torch.float32", tokenizer_hash="abc",
        chat_template=None,
    )
    base.update(over)
    return pairing.ModelFacts(**base)


# ---------- pairing ----------


def test_identical_models_are_comparable():
    assert pairing.compare(_facts(), _facts(name="other")) == []
    pairing.assert_comparable(_facts(), _facts(name="other"))


def test_vocab_mismatch_is_caught():
    problems = pairing.compare(_facts(), _facts(vocab_size=50304))
    assert any("vocab size" in p for p in problems)


def test_tokenizer_fingerprint_mismatch_is_caught_even_at_equal_vocab_size():
    problems = pairing.compare(_facts(), _facts(tokenizer_hash="different"))
    assert any("segment text differently" in p for p in problems)


def test_dtype_mismatch_is_caught():
    problems = pairing.compare(_facts(), _facts(dtype="torch.bfloat16"))
    assert any("dtypes differ" in p for p in problems)


def test_chat_template_mismatch_is_caught():
    problems = pairing.compare(_facts(), _facts(chat_template="{{ messages }}"))
    assert any("chat templates differ" in p for p in problems)


def test_cross_architecture_is_flagged_as_a_research_problem():
    problems = pairing.compare(_facts(), _facts(architecture="LlamaForCausalLM"))
    assert any("cross-architecture" in p for p in problems)


def test_assert_comparable_reports_every_problem_at_once():
    with pytest.raises(ValueError) as exc:
        pairing.assert_comparable(_facts(), _facts(vocab_size=1, dtype="torch.bfloat16"))
    assert exc.value.args[0].count("- ") >= 2


# ---------- ranking ----------


def test_summarize_quantiles():
    d = ranking.summarize([(float(i), f"p{i}") for i in range(11)])
    assert d.n == 11 and d.maximum == 10.0 and d.median == 5.0


def test_concentration_detects_a_narrow_change():
    narrow = [(10.0, "a")] + [(0.01, f"p{i}") for i in range(99)]
    diffuse = [(1.0, f"p{i}") for i in range(100)]
    assert ranking.concentration(narrow, top_k=1) > 0.9
    assert ranking.concentration(diffuse, top_k=1) == pytest.approx(0.01)


def test_concentration_rejects_zero_total():
    with pytest.raises(ValueError, match="zero or negative"):
        ranking.concentration([(0.0, "a"), (0.0, "b")])


def test_excess_over_control_and_dead_control():
    t = [(2.0, "a"), (2.0, "b")]
    c = [(1.0, "a"), (1.0, "b")]
    assert ranking.excess_over_control(t, c) == pytest.approx(2.0)
    with pytest.raises(ValueError, match="control divergence is zero"):
        ranking.excess_over_control(t, [(0.0, "a")])


def test_overlap_is_jaccard():
    t = [(3.0, "a"), (2.0, "b"), (1.0, "c")]
    c = [(3.0, "b"), (2.0, "c"), (1.0, "d")]
    assert ranking.overlap(t, c, top_k=2) == pytest.approx(1 / 3)  # {a,b} vs {b,c}
    assert ranking.overlap(t, t, top_k=2) == 1.0


# ---------- control verdict ----------


def test_parallel_and_same_prompts_is_not_distinguishable():
    v = control.verdict(divergence_ratio=5.0, direction_cosine=0.95, top_k_overlap=0.9)
    assert v.label == control.NOT_DISTINGUISHABLE_FROM_ANY_FINETUNE


def test_big_and_different_is_specific():
    v = control.verdict(divergence_ratio=4.0, direction_cosine=0.2, top_k_overlap=0.1)
    assert v.label == control.SPECIFIC_TO_TREATMENT
    assert "validate causally" in v.note


def test_small_effect_is_only_partially_specific():
    v = control.verdict(divergence_ratio=1.1, direction_cosine=0.3, top_k_overlap=0.1)
    assert v.label == control.PARTIALLY_SPECIFIC


def test_describe_contains_the_three_numbers():
    text = control.describe(control.verdict(2.5, 0.3, 0.1))
    assert "divergence ratio" in text and "cosine" in text and "overlap" in text


# ---------- torch-backed modules ----------


@pytest.fixture(scope="module")
def tiny_pair():
    torch = pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from transformers import AutoModelForCausalLM, AutoTokenizer

    name = "hf-internal-testing/tiny-random-gpt2"
    tok = AutoTokenizer.from_pretrained(name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(name).eval()
    ft = AutoModelForCausalLM.from_pretrained(name).eval()
    with torch.no_grad():
        for p in ft.transformer.h[-1].parameters():
            p.add_(torch.randn_like(p) * 0.1)
    return base, ft, tok


def test_kl_of_a_model_against_itself_is_zero(tiny_pair):
    torch = pytest.importorskip("torch")
    from md_components import kl

    base, _, tok = tiny_pair
    tk = kl.kl_per_token(base, base, tok, "The capital of France is")
    assert max(tk.kl) < 1e-4


def test_kl_is_positive_for_a_changed_model(tiny_pair):
    from md_components import kl

    base, ft, tok = tiny_pair
    tk = kl.kl_per_token(ft, base, tok, "The capital of France is")
    assert tk.mean > 0


def test_kl_rejects_mismatched_logit_shapes():
    torch = pytest.importorskip("torch")
    from md_components import kl

    with pytest.raises(ValueError, match="logit shapes differ"):
        kl.kl_from_logits(torch.randn(1, 5, 9), torch.randn(1, 4, 9))


def test_capture_raises_on_an_unknown_module_name(tiny_pair):
    from md_components import acts

    base, _, _ = tiny_pair
    with pytest.raises(KeyError, match="not found"):
        with acts.capture(base, ["transformer.h.999"]):
            pass


def test_paired_activations_shape_and_mean_difference(tiny_pair):
    from md_components import acts

    base, ft, tok = tiny_pair
    module = f"transformer.h.{len(base.transformer.h) - 1}"
    paired = acts.collect_pair(base, ft, tok, ["hello there", "goodbye now"], module,
                               last_token_only=True)
    assert paired.base.shape == paired.finetuned.shape
    assert paired.mean_difference().shape == (paired.base.shape[-1],)
    assert 0.0 < paired.difference_concentration(top_frac=0.5) <= 1.0


def test_identical_models_have_zero_difference_and_say_so(tiny_pair):
    from md_components import acts

    base, _, tok = tiny_pair
    module = f"transformer.h.{len(base.transformer.h) - 1}"
    paired = acts.collect_pair(base, base, tok, ["hello there"], module, last_token_only=True)
    with pytest.raises(ValueError, match="identically zero"):
        paired.difference_concentration()


def test_difflens_readouts_and_cosine(tiny_pair):
    torch = pytest.importorskip("torch")
    from md_components import acts, difflens

    base, ft, tok = tiny_pair
    module = f"transformer.h.{len(base.transformer.h) - 1}"
    paired = acts.collect_pair(base, ft, tok, ["hello there", "goodbye now"], module,
                               last_token_only=True)
    d = paired.mean_difference()
    top = difflens.logit_lens(base, d, tok, top_k=5)
    assert len(top) == 5 and all(isinstance(t, str) for t, _ in top)
    assert len(difflens.nearest_tokens(base, d, tok, top_k=5)) == 5
    assert difflens.cosine(d, d) == pytest.approx(1.0, abs=1e-4)
    assert difflens.cosine(d, -d) == pytest.approx(-1.0, abs=1e-4)


def test_difflens_rejects_a_zero_direction(tiny_pair):
    torch = pytest.importorskip("torch")
    from md_components import difflens

    base, _, tok = tiny_pair
    with pytest.raises(ValueError, match="zero norm"):
        difflens.logit_lens(base, torch.zeros(base.config.n_embd), tok)
