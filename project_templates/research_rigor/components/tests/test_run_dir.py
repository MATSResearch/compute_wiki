"""
Tests for the run-directory capture library.

Run:  uv run pytest tests/test_run_dir.py -v
"""

import json
from pathlib import Path

import pytest

from research_rigor import run_dir

MODELS = [{"id": "claude-opus-4-8", "role": "implementation"}]
HARNESS = {"tool": "claude-code", "version": "test"}
ACCEPTANCE = "all five data subsets scored and the guard passed on each"
SCHEMA = json.loads((Path(__file__).parents[2] / "templates" / "metadata.schema.json").read_text())


def _mk(tmp_path) -> "run_dir.RunDir":
    return run_dir.RunDir.create(
        tmp_path, "run_20260707_120000_probe", acceptance=ACCEPTANCE, models=MODELS,
        harness=HARNESS,
        code_repo=tmp_path,
    )


def test_create_writes_valid_metadata(tmp_path):
    rd = _mk(tmp_path)
    meta = rd.read_metadata()
    assert meta["run_id"] == "run_20260707_120000_probe"
    assert meta["created_at"].endswith("Z")
    assert meta["models"] == MODELS
    assert set(meta["stage_status"]) == set(run_dir.STAGES)
    assert all(v == "pending" for v in meta["stage_status"].values())
    assert meta["acceptance"] == ACCEPTANCE


@pytest.mark.parametrize("acceptance", ["", "   "])
def test_a_run_cannot_be_filed_without_saying_what_done_means(tmp_path, acceptance):
    with pytest.raises(AssertionError, match="acceptance condition"):
        run_dir.RunDir.create(tmp_path, "run_20260707_120000_probe", acceptance=acceptance,
                              models=MODELS, harness=HARNESS, code_repo=tmp_path)


def test_metadata_schema_accepts_what_the_library_writes(tmp_path):
    """The schema file and the library name the same stages, statuses and keys."""
    rd = _mk(tmp_path)
    rd.link_prereg(point="hypothesis", frozen_at="2026-07-07T12:00:00Z", content_hash="sha256:abc")
    meta = rd.read_metadata()
    assert set(SCHEMA["required"]) <= set(meta) <= set(SCHEMA["properties"])
    assert set(meta["prereg"]) <= set(SCHEMA["properties"]["prereg"]["properties"])
    assert set(SCHEMA["properties"]["prereg"]["properties"]) == set(run_dir.PREREG_POINTS)
    status = SCHEMA["properties"]["stage_status"]
    assert tuple(status["propertyNames"]["enum"]) == run_dir.STAGES
    assert set(status["additionalProperties"]["enum"]) == set(run_dir.STAGE_STATUS)


def test_create_refuses_duplicate_run(tmp_path):
    _mk(tmp_path)
    try:
        _mk(tmp_path)
        assert False, "creating an existing run dir must fail loudly"
    except FileExistsError:
        pass


def test_provenance_ids_are_sequential_and_appended(tmp_path):
    rd = _mk(tmp_path)
    e0 = rd.log_provenance(actor="agent", stage="run", event="decision",
                           summary="chose layer 8")
    e1 = rd.log_provenance(actor="agent", stage="run", event="model_invocation",
                           summary="ran ablation", model_id="claude-opus-4-8",
                           parent_event_id=e0, cost={"tokens_in": 100, "tokens_out": 20})
    assert e0 == "ev_0000" and e1 == "ev_0001"
    log = rd.read_log(rd.provenance_path)
    assert len(log) == 2
    assert log[1]["parent_event_id"] == "ev_0000"
    # cost from the provenance event accumulated into metadata
    assert rd.read_metadata()["cost"]["tokens_in"] == 100


def test_bad_enum_values_fail_loudly(tmp_path):
    rd = _mk(tmp_path)
    for kwargs in (
        dict(actor="robot", stage="run", event="decision", summary="x"),
        dict(actor="agent", stage="nonsense", event="decision", summary="x"),
        dict(actor="agent", stage="run", event="teleport", summary="x"),
    ):
        try:
            rd.log_provenance(**kwargs)
            assert False, f"should reject {kwargs}"
        except AssertionError:
            pass


def test_gate_and_attention_check_cross_reference(tmp_path):
    rd = _mk(tmp_path)
    src = rd.log_provenance(actor="agent", stage="writeup", event="artifact_written",
                            summary="wrote draft with an overstated effect size")
    ac = rd.log_attention_check(
        stage="writeup", injected_into_gate="gt_0000",
        error_type="fabricated_result", difficulty="medium",
        ground_truth="fig 3 effect 0.61 != table2 0.28",
        source_provenance_event=src,
    )
    gt = rd.log_gate(stage="writeup", artifact="writeup/draft.md",
                     decision="reject", review_seconds=812, attention_check_ids=[ac],
                     notes="caught the fig/table mismatch")
    assert ac == "ac_0000" and gt == "gt_0000"
    gate = rd.read_log(rd.gates_path)[0]
    assert gate["attention_check_ids"] == ["ac_0000"]
    assert gate["review_seconds"] == 812


def test_attention_check_resolution_is_appended_not_edited(tmp_path):
    rd = _mk(tmp_path)
    ac = rd.log_attention_check(stage="analysis", injected_into_gate="gt_0000",
                                error_type="misread_metric", difficulty="hard",
                                ground_truth="p reported as 0.04, actually 0.4")
    rd.resolve_attention_check(ac, caught=False)
    lines = rd.read_log(rd.attention_checks_path)
    assert len(lines) == 2  # original + resolution, original untouched
    assert lines[0]["caught"] is None
    assert lines[1]["caught"] is False and lines[1]["event"] == "resolution"


def test_metadata_write_is_atomic_valid_json(tmp_path):
    rd = _mk(tmp_path)
    rd.set_stage_status("hypothesis", "frozen")
    rd.link_prereg(point="hypothesis", frozen_at="2026-07-07T12:00:00Z", content_hash="sha256:abc")
    rd.link_prereg(point="design", frozen_at="2026-07-09T12:00:00Z", content_hash="sha256:def")
    # File is always complete, parseable JSON (atomic rename, no .tmp left behind).
    meta = json.loads(rd.metadata_path.read_text())
    assert meta["stage_status"]["hypothesis"] == "frozen"
    assert meta["prereg"]["hypothesis"]["content_hash"] == "sha256:abc"
    assert meta["prereg"]["design"]["content_hash"] == "sha256:def"
    assert not (tmp_path / "run_20260707_120000_probe" / "metadata.json.tmp").exists()


def test_exploratory_or_revised_work_has_terminal_statuses(tmp_path):
    rd = _mk(tmp_path)
    rd.set_stage_status("lit_review", "not_applicable")
    rd.set_stage_status("hypothesis", "superseded")
    statuses = rd.read_metadata()["stage_status"]
    assert statuses["lit_review"] == "not_applicable"
    assert statuses["hypothesis"] == "superseded"
