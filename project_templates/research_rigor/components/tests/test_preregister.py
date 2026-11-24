"""
Tests for the pre-registration freeze/check tool: two commitment points, on
either side of the pilot.

Run:  uv run pytest tests/test_preregister.py -v
"""

from pathlib import Path

import pytest
import yaml

from research_rigor import preregister as prereg

ANALYSIS = {
    "metric": "reward_gap_delta",
    "decision_rule": ">0.5 => supported; <0.1 => refuted; between => inconclusive",
    "method": "causal activation patching (NOT attribution patching)",
}


def _hypothesis_draft() -> dict:
    """What exists before the pilot: two rival hypotheses, no design yet."""
    return {
        "run_id": "run_20260707_120000_reward_hacking_probe",
        "hypotheses": [
            {
                "id": "H1",
                "question": "Q1: why does the reward model over-score sycophancy?",
                "statement": "SAE feature 4021 causally mediates sycophancy over-scoring.",
                "prediction": "Ablating feature 4021 reduces the sycophancy reward gap by >50%.",
                "falsifier": "Ablating feature 4021 reduces the gap by <10%.",
            },
            {
                "id": "H2",
                "question": "Q1: why does the reward model over-score sycophancy?",
                "statement": "Over-scoring is driven by completion length, not feature 4021.",
                "prediction": "Length-matched completions close the gap; ablation does not.",
                "falsifier": "The gap survives length matching.",
            },
        ],
    }


def _design(metric="reward_gap_delta") -> dict:
    return {
        "analysis": dict(ANALYSIS, metric=metric),
        "prespecified_confounds": ["completion length differs between the two sets"],
        "guards": [{
            "measure": "reward_gap_delta",
            "cheap_way": "ablation degrades all rewards, shrinking any gap",
            "check": "ablate a random feature of matched norm; the gap must not move",
        }],
    }


def _full_draft() -> dict:
    d = _hypothesis_draft()
    for h in d["hypotheses"]:
        h.update(_design())
    d["planned_runs"] = [{"id": "run:1", "tests": "H1"}, {"id": "run:2", "tests": "H2"}]
    return d


def _write(tmp_path: Path, data: dict, name: str = "prereg.yaml") -> Path:
    p = tmp_path / name
    with open(p, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)
    return p


def _freeze_both(tmp_path) -> Path:
    p = _write(tmp_path, _full_draft())
    prereg.freeze(p, "hypothesis", git_commit=False, force=False)
    prereg.freeze(p, "design", git_commit=False, force=False)
    return p


def _actual(tmp_path, **over) -> Path:
    return _write(tmp_path, {"hypotheses": {"H1": dict(ANALYSIS, **over), "H2": dict(ANALYSIS)}},
                  name="actual.yaml")


# --- the hypothesis point: frozen before the pilot --------------------------

def test_hypothesis_freezes_before_any_design_exists(tmp_path):
    p = _write(tmp_path, _hypothesis_draft())
    prereg.freeze(p, "hypothesis", git_commit=False, force=False)
    frozen = yaml.safe_load(p.read_text())["commitments"]
    assert frozen["hypothesis"]["frozen_at"].endswith("Z")
    assert frozen["hypothesis"]["content_hash"].startswith("sha256:")
    assert "design" not in frozen


@pytest.mark.parametrize("field", ["question", "statement", "prediction", "falsifier"])
def test_hypothesis_point_requires_each_of_its_fields(field):
    d = _hypothesis_draft()
    del d["hypotheses"][0][field]
    with pytest.raises(AssertionError, match=field):
        prereg.validate_draft(d, "hypothesis")


def test_validate_rejects_placeholder():
    d = _hypothesis_draft()
    d["hypotheses"][0]["falsifier"] = "<fill me in>"
    with pytest.raises(AssertionError, match="falsifier"):
        prereg.validate_draft(d, "hypothesis")


def test_hypothesis_hash_ignores_the_design_filled_in_after_the_pilot():
    before = prereg.commitment_hash(_hypothesis_draft(), "hypothesis")
    assert prereg.commitment_hash(_full_draft(), "hypothesis") == before
    edited = _full_draft()
    edited["hypotheses"][0]["falsifier"] = "something easier to survive"
    assert prereg.commitment_hash(edited, "hypothesis") != before


# --- the design point: frozen after the pilot, before the main run ----------

def test_design_cannot_freeze_before_the_hypothesis(tmp_path):
    p = _write(tmp_path, _full_draft())
    with pytest.raises(AssertionError, match="hypothesis"):
        prereg.freeze(p, "design", git_commit=False, force=False)


def test_pilot_does_not_license_rewriting_the_falsifier(tmp_path):
    p = _write(tmp_path, _full_draft())
    prereg.freeze(p, "hypothesis", git_commit=False, force=False)
    d = yaml.safe_load(p.read_text())
    d["hypotheses"][0]["falsifier"] = "Ablation reduces the gap by <1%."
    _write(tmp_path, d)
    with pytest.raises(AssertionError, match="does not license rewriting"):
        prereg.freeze(p, "design", git_commit=False, force=False)


def test_a_hypothesis_added_after_the_pilot_stops_the_design_freeze(tmp_path):
    """A changed belief is a new registered prediction in its own prereg, not an
    addition to one whose hypothesis point is already frozen."""
    d = _hypothesis_draft()
    d["hypotheses"].pop()
    p = _write(tmp_path, d)
    prereg.freeze(p, "hypothesis", git_commit=False, force=False)
    d = _full_draft()
    d["commitments"] = yaml.safe_load(p.read_text())["commitments"]
    _write(tmp_path, d)
    with pytest.raises(AssertionError, match="added or removed"):
        prereg.freeze(p, "design", git_commit=False, force=False)


@pytest.mark.parametrize("field", ["analysis", "prespecified_confounds", "guards"])
def test_design_point_requires_each_of_its_blocks(field):
    d = _full_draft()
    del d["hypotheses"][0][field]
    with pytest.raises(AssertionError, match=field):
        prereg.validate_draft(d, "design")


def test_design_needs_a_guard_for_its_metric():
    d = _full_draft()
    d["hypotheses"][0]["guards"][0]["measure"] = "some_other_number"
    with pytest.raises(AssertionError, match="no guard for its metric"):
        prereg.validate_draft(d, "design")


def test_guard_must_name_the_cheap_way_and_the_check():
    d = _full_draft()
    del d["hypotheses"][0]["guards"][0]["cheap_way"]
    with pytest.raises(AssertionError, match="cheap_way"):
        prereg.validate_draft(d, "design")


def test_freeze_refuses_double_freeze(tmp_path):
    p = _write(tmp_path, _full_draft())
    prereg.freeze(p, "hypothesis", git_commit=False, force=False)
    with pytest.raises(AssertionError, match="already frozen"):
        prereg.freeze(p, "hypothesis", git_commit=False, force=False)


# --- competing hypotheses and routes to a verdict: notes, never a refusal ---

def test_two_hypotheses_with_different_predictions_cover_a_question():
    assert prereg.rival_gaps(_hypothesis_draft()) == []


def test_a_single_hypothesis_is_flagged_but_still_freezes(tmp_path):
    d = _hypothesis_draft()
    d["hypotheses"].pop()
    assert len(prereg.rival_gaps(d)) == 1
    p = _write(tmp_path, d)
    prereg.freeze(p, "hypothesis", git_commit=False, force=False)
    assert yaml.safe_load(p.read_text())["commitments"]["hypothesis"]


def test_two_hypotheses_predicting_the_same_observation_are_not_rivals():
    d = _hypothesis_draft()
    d["hypotheses"][1]["prediction"] = d["hypotheses"][0]["prediction"]
    assert len(prereg.rival_gaps(d)) == 1


def test_a_rival_declined_with_a_reason_settles_the_question():
    d = _hypothesis_draft()
    d["hypotheses"].pop()
    d["hypotheses"][0]["rivals_declined"] = [
        {"rival": "driven by completion length", "reason": "not discriminating at this n"}]
    assert prereg.rival_gaps(d) == []


def test_a_declined_rival_needs_its_reason():
    d = _hypothesis_draft()
    d["hypotheses"][0]["rivals_declined"] = [{"rival": "driven by completion length"}]
    with pytest.raises(AssertionError, match="reason"):
        prereg.validate_draft(d, "hypothesis")


def test_hypothesis_with_no_planned_run_has_no_route_to_a_verdict():
    d = _full_draft()
    d["planned_runs"] = [{"id": "run:1", "tests": "H1"}]
    gaps = prereg.route_gaps(d)
    assert len(gaps) == 1 and "H2" in gaps[0]


def test_planned_run_testing_nothing_on_the_record_is_flagged_unless_exploration():
    d = _full_draft()
    d["planned_runs"] += [{"id": "run:3", "tests": "H9"},
                          {"id": "run:4", "tests": prereg.EXPLORATION}]
    gaps = prereg.route_gaps(d)
    assert len(gaps) == 1 and "run:3" in gaps[0]


def test_planned_run_naming_no_hypothesis_is_a_note_not_a_refusal(tmp_path):
    d = _full_draft()
    d["planned_runs"].append({"id": "run:3"})
    gaps = prereg.route_gaps(d)
    assert len(gaps) == 1 and "run:3" in gaps[0]
    p = _write(tmp_path, d)
    prereg.freeze(p, "hypothesis", git_commit=False, force=False)
    prereg.freeze(p, "design", git_commit=False, force=False)
    assert yaml.safe_load(p.read_text())["commitments"]["design"]


# --- check: tampering and deviation at analysis time ------------------------

def test_check_needs_both_commitments(tmp_path):
    p = _write(tmp_path, _full_draft())
    prereg.freeze(p, "hypothesis", git_commit=False, force=False)
    with pytest.raises(AssertionError, match="design"):
        prereg.check(p, _actual(tmp_path))


def test_check_passes_when_the_analysis_matches(tmp_path):
    p = _freeze_both(tmp_path)
    assert prereg.check(p, _actual(tmp_path, result=0.62)) == 0


def test_check_flags_method_swap(tmp_path):
    """The archetype: an agent silently swaps causal patching for the cheap proxy."""
    p = _freeze_both(tmp_path)
    assert prereg.check(p, _actual(tmp_path, method="attribution patching")) == 1


@pytest.mark.parametrize("edit", [
    lambda h: h.update(prediction="Ablating feature 4021 reduces the gap by >10%."),
    lambda h: h["analysis"].update(decision_rule=">0.2 => supported"),
    lambda h: h["guards"].pop(),
])
def test_check_detects_tampering_with_either_commitment(tmp_path, edit):
    p = _freeze_both(tmp_path)
    frozen = yaml.safe_load(p.read_text())
    edit(frozen["hypotheses"][0])
    _write(tmp_path, frozen)
    assert prereg.check(p, _actual(tmp_path)) == 2  # tamper hard-stop


# --- the shipped template is the shape the tool validates --------------------

TEMPLATE = Path(__file__).parents[2] / "templates" / "prereg.template.yaml"


def test_template_carries_every_field_the_two_freezes_require():
    t = yaml.safe_load(TEMPLATE.read_text())
    assert tuple(t["commitments"]) == prereg.POINTS
    h = t["hypotheses"][0]
    assert {"question", *prereg.HYPOTHESIS_FIELDS, "analysis", "prespecified_confounds",
            "guards", "rivals_declined"} <= set(h)
    assert set(h["analysis"]) == set(prereg.FROZEN_ANALYSIS_FIELDS)
    assert set(h["guards"][0]) == set(prereg.GUARD_FIELDS)


@pytest.mark.parametrize("point", prereg.POINTS)
def test_unfilled_template_cannot_be_frozen(point):
    with pytest.raises(AssertionError, match="placeholder"):
        prereg.validate_draft(yaml.safe_load(TEMPLATE.read_text()), point)
