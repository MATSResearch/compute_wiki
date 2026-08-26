# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "pytest"]
# ///
"""
Tests for the pre-registration freeze/check tool.

Run:  uv run pytest tests/test_preregister.py -v
"""

from pathlib import Path

import yaml

from research_rigor import preregister as prereg


def _valid_draft() -> dict:
    return {
        "run_id": "run_20260707_120000_reward_hacking_probe",
        "hypotheses": [
            {
                "id": "H1",
                "statement": "SAE feature 4021 causally mediates sycophancy over-scoring.",
                "prediction": "Ablating feature 4021 reduces the sycophancy reward gap by >50%.",
                "analysis": {
                    "metric": "reward_gap_delta",
                    "decision_rule": ">0.5 => supported; <0.1 => refuted; between => inconclusive",
                    "method": "causal activation patching (NOT attribution patching)",
                },
                "prespecified_confounds": ["attribution patching correlates rho~=0 with causal"],
            }
        ],
    }


def _write(tmp_path: Path, data: dict, name: str = "prereg.yaml") -> Path:
    p = tmp_path / name
    with open(p, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    return p


def test_hash_is_stable_and_ignores_bookkeeping():
    d = _valid_draft()
    h1 = prereg.hypotheses_hash(d)
    # Adding freeze bookkeeping must NOT change the hash.
    d["frozen_at"] = "2026-07-07T12:00:00Z"
    d["content_hash"] = h1
    d["amendments"] = []
    assert prereg.hypotheses_hash(d) == h1
    # Changing the science MUST change the hash.
    d["hypotheses"][0]["analysis"]["metric"] = "something_else"
    assert prereg.hypotheses_hash(d) != h1


def test_validate_rejects_placeholder(tmp_path):
    d = _valid_draft()
    d["hypotheses"][0]["prediction"] = "<fill me in>"
    try:
        prereg.validate_draft(d)
        assert False, "should have rejected a placeholder prediction"
    except AssertionError as e:
        assert "prediction" in str(e)


def test_freeze_stamps_and_check_passes(tmp_path):
    p = _write(tmp_path, _valid_draft())
    prereg.freeze(p, git_commit=False, force=False)
    frozen = yaml.safe_load(p.read_text())
    assert frozen["frozen_at"].endswith("Z")
    assert frozen["content_hash"].startswith("sha256:")
    assert frozen["registered_before_data"] is True

    # Actual analysis that matches the frozen plan -> exit 0.
    actual = {"hypotheses": {"H1": {
        "metric": "reward_gap_delta",
        "decision_rule": ">0.5 => supported; <0.1 => refuted; between => inconclusive",
        "method": "causal activation patching (NOT attribution patching)",
        "result": 0.62, "verdict": "supported",
    }}}
    ap = _write(tmp_path, actual, name="actual.yaml")
    assert prereg.check(p, ap) == 0


def test_check_flags_method_swap(tmp_path):
    """The archetype: an agent silently swaps causal patching for the cheap proxy."""
    p = _write(tmp_path, _valid_draft())
    prereg.freeze(p, git_commit=False, force=False)
    actual = {"hypotheses": {"H1": {
        "metric": "reward_gap_delta",
        "decision_rule": ">0.5 => supported; <0.1 => refuted; between => inconclusive",
        "method": "attribution patching",  # <-- deviation
        "result": 0.62,
    }}}
    ap = _write(tmp_path, actual, name="actual.yaml")
    assert prereg.check(p, ap) == 1  # deviation flagged, not silently accepted


def test_check_detects_tampering(tmp_path):
    p = _write(tmp_path, _valid_draft())
    prereg.freeze(p, git_commit=False, force=False)
    # Edit a frozen hypothesis without amending -> hash mismatch.
    frozen = yaml.safe_load(p.read_text())
    frozen["hypotheses"][0]["prediction"] = "Ablating feature 4021 reduces the gap by >10%."
    with open(p, "w") as f:
        yaml.safe_dump(frozen, f, sort_keys=False)
    actual = {"hypotheses": {"H1": {"metric": "reward_gap_delta",
              "decision_rule": ">0.5 => supported; <0.1 => refuted; between => inconclusive",
              "method": "causal activation patching (NOT attribution patching)"}}}
    ap = _write(tmp_path, actual, name="actual.yaml")
    assert prereg.check(p, ap) == 2  # tamper hard-stop


def test_freeze_refuses_double_freeze(tmp_path):
    p = _write(tmp_path, _valid_draft())
    prereg.freeze(p, git_commit=False, force=False)
    try:
        prereg.freeze(p, git_commit=False, force=False)
        assert False, "should refuse to re-freeze an already-frozen prereg"
    except AssertionError as e:
        assert "already frozen" in str(e)
