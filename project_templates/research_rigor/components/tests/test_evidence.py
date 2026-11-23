"""
Tests for the evidence ledger: evidence is not the verdict.

Run:  uv run pytest tests/test_evidence.py -v
"""

import pytest

from research_rigor import evidence as ev
from research_rigor import run_dir


def _mk(tmp_path):
    return run_dir.RunDir.create(
        tmp_path, "run_20260707_120000_probe", acceptance="all five subsets scored",
        models=[{"id": "claude-opus-4-8", "role": "analysis"}],
        harness={"tool": "claude-code"}, code_repo=tmp_path,
    )


CITED = [ev.Citation("run:1", "H1", 0.8), ev.Citation("run:2", "H1", 0.4),
         ev.Citation("run:3", "H1", -0.6), ev.Citation("run:4", "H2", -0.9)]


@pytest.mark.parametrize("valence", [0, float("nan"), float("inf")])
def test_a_citation_has_a_polarity_and_a_weight(valence):
    with pytest.raises(AssertionError, match="valence"):
        ev.Citation("run:1", "H1", valence)


def test_ledger_is_appended_and_read_back(tmp_path):
    rd = _mk(tmp_path)
    for c in CITED:
        ev.cite(rd, c, cited_by="agent")
    assert ev.load(rd) == CITED
    assert rd.read_log(rd.evidence_path)[2]["cited_by"] == "agent"


def test_tally_separates_for_from_against_per_prediction():
    t = ev.tally(CITED, "H1")
    assert t.supporting == ["run:1", "run:2"] and t.against == ["run:3"]
    assert t.net == pytest.approx(0.6)
    assert ev.tally(CITED, "H2").supporting == []


@pytest.mark.parametrize("verdict,citations,flagged", [
    ("supported", [ev.Citation("r1", "H", 0.9)], False),
    ("supported", [ev.Citation("r1", "H", 0.9), ev.Citation("r2", "H", -0.1)], True),
    ("supported", [], True),
    ("refuted", [ev.Citation("r1", "H", -0.9)], False),
    ("refuted", [ev.Citation("r1", "H", 0.9)], True),
    ("refuted", [], True),
    ("inconclusive", [], False),
    ("inconclusive", [ev.Citation("r1", "H", -0.9)], False),
])
def test_which_verdicts_disagree_with_their_evidence(verdict, citations, flagged):
    assert bool(ev.disagreement(verdict, ev.tally(citations, "H"))) is flagged


def test_a_lopsided_tally_does_not_decide_anything():
    """Three for and one against is context; `supported` is still flagged, and
    nothing in the tally names a verdict."""
    many_for = [ev.Citation(f"r{i}", "H", 1.0) for i in range(3)] + [ev.Citation("r9", "H", -0.2)]
    t = ev.tally(many_for, "H")
    assert t.net > 0 and ev.disagreement("supported", t)
    assert ev.disagreement("refuted", t) is None
