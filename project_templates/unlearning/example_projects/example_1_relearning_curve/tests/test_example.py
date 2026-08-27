"""Fast tests: data generation and loss masking. No training, no downloads.

The expensive path is covered by actually running `--smoke`, not by a test that
would take four minutes in CI.
"""

from __future__ import annotations

import pytest

from example_1_relearning_curve import data


def test_entities_are_distinct_and_fictitious():
    ents = data.make_entities(25, seed=1)
    assert len({e.name for e in ents}) == 25
    # names are built from nonsense syllables, so no real-world collisions
    assert all(" " in e.name for e in ents)


def test_generation_is_deterministic():
    assert data.make_entities(10, seed=3) == data.make_entities(10, seed=3)
    assert data.make_entities(10, seed=3) != data.make_entities(10, seed=4)


def test_records_carry_the_split_key():
    ents = data.make_entities(5, seed=0)
    recs = data.records(ents)
    assert len(recs) == 10  # two questions per entity
    assert {r["key"] for r in recs} == {e.name for e in ents}


def test_targets_are_the_answer_text():
    rec = data.records(data.make_entities(1, seed=0))[0]
    assert data.targets_for(rec) == [rec["answer"].strip()]


def test_prompt_tokens_are_masked_out_of_the_loss():
    pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from transformers import AutoTokenizer

    from example_1_relearning_curve import modeling

    tok = AutoTokenizer.from_pretrained("distilgpt2")
    tok.pad_token = tok.eos_token
    batch = modeling.encode(tok, [("Q: Where does X live?\nA:", " Blint")])
    prompt_len = len(tok("Q: Where does X live?\nA:", add_special_tokens=False).input_ids)
    assert (batch.labels[0, :prompt_len] == modeling.IGNORE).all()
    assert (batch.labels[0, prompt_len:] != modeling.IGNORE).any()
