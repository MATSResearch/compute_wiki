"""
Tests for the supervision attention-check injector + scorer.

Run:  uv run pytest tests/test_attention_check.py -v
"""


from research_rigor import attention_check as ac
from research_rigor import run_dir

CATALOG = [
    {"error_type": "misread_metric", "difficulty": "hard", "source_provenance_event": "ev_0007"},
    {"error_type": "fabricated_result", "difficulty": "easy", "source_provenance_event": "ev_0011"},
]


def _mk(tmp_path):
    return run_dir.RunDir.create(
        tmp_path, "run_20260707_120000_probe",
        models=[{"id": "claude-opus-4-8", "role": "review"}],
        harness={"tool": "claude-code"}, code_repo=tmp_path,
    )


def test_injection_is_deterministic_and_seed_dependent():
    kw = dict(run_id="run_x", gate_ordinal=3, rate=0.5, mistake_catalog=CATALOG)
    a = ac.plan_injection(seed="secretA", **kw)
    b = ac.plan_injection(seed="secretA", **kw)
    # Same seed+gate -> identical decision (auditable).
    assert (a is None) == (b is None)
    if a and b:
        assert a.kind == b.kind and a.error_type == b.error_type and a.nonce == b.nonce
    # Different seed generally shifts decisions across gates (unpredictable to Fellow).
    seenA = [ac.plan_injection(seed="secretA", run_id="r", gate_ordinal=i, rate=0.5, mistake_catalog=CATALOG) is not None for i in range(40)]
    seenB = [ac.plan_injection(seed="secretB", run_id="r", gate_ordinal=i, rate=0.5, mistake_catalog=CATALOG) is not None for i in range(40)]
    assert seenA != seenB


def test_injection_rate_is_approximately_honoured():
    n = 2000
    hits = sum(ac.plan_injection(seed="s", run_id="r", gate_ordinal=i, rate=0.25, mistake_catalog=CATALOG) is not None
               for i in range(n))
    assert 0.20 < hits / n < 0.30  # ~25%


def test_rate_zero_and_one():
    assert all(ac.plan_injection(seed="s", run_id="r", gate_ordinal=i, rate=0.0, mistake_catalog=CATALOG) is None
               for i in range(50))
    assert all(ac.plan_injection(seed="s", run_id="r", gate_ordinal=i, rate=1.0, mistake_catalog=CATALOG) is not None
               for i in range(50))


def test_defect_uses_catalog_types():
    for i in range(50):
        p = ac.plan_injection(seed="s", run_id="r", gate_ordinal=i, rate=1.0,
                              mistake_catalog=CATALOG, two_sided_rate=0.0)
        assert p.kind == "defect"
        assert p.error_type in {"misread_metric", "fabricated_result"}


def test_register_quarantines_content_and_logs(tmp_path):
    rd = _mk(tmp_path)
    plan = ac.InjectionPlan(kind="defect", error_type="fabricated_result",
                            difficulty="medium", source_provenance_event="ev_0011", nonce="abc")
    ac_id = ac.register(rd, plan, stage="communication", injected_into_gate="gt_0000",
                        ground_truth="fig3=0.61 but table2=0.28",
                        corrupted_artifact="...draft with fake 0.61...",
                        correct_version="...real 0.28...")
    # Logged, and content quarantined OUTSIDE results/writeup (requirement 5).
    rec = rd.read_log(rd.attention_checks_path)[0]
    assert rec["error_type"] == "fabricated_result" and rec["two_sided_control"] is False
    quarantine = rd.path / "attention_checks" / ac_id
    assert (quarantine / "shown_to_reviewer.txt").exists()
    assert (quarantine / "correct_version.txt").exists()


def test_control_has_no_error_type(tmp_path):
    rd = _mk(tmp_path)
    plan = ac.InjectionPlan(kind="control", error_type=None, difficulty="easy",
                            source_provenance_event=None, nonce="xyz")
    ac.register(rd, plan, stage="analysis", injected_into_gate="gt_0000",
                ground_truth="this result is actually correct")
    rec = rd.read_log(rd.attention_checks_path)[0]
    assert rec["two_sided_control"] is True and rec["error_type"] is None


def test_scoring_separates_catches_from_false_positives(tmp_path):
    rd = _mk(tmp_path)
    # 3 defects: catch 2 (incl. the easy one), miss 1 hard.
    defects = [("easy", True), ("medium", True), ("hard", False)]
    for i, (diff, caught) in enumerate(defects):
        p = ac.InjectionPlan("defect", "fabricated_result", diff, None, f"n{i}")
        acid = ac.register(rd, p, stage="communication", injected_into_gate=f"gt_{i}",
                           ground_truth="gt")
        ac.record_outcome(rd, acid, flagged=caught)
    # 2 controls: correctly approve 1, wrongly flag 1 -> fp_rate 0.5.
    for i, flagged in enumerate([False, True]):
        p = ac.InjectionPlan("control", None, "medium", None, f"c{i}")
        acid = ac.register(rd, p, stage="communication", injected_into_gate=f"gtc_{i}",
                           ground_truth="correct item")
        ac.record_outcome(rd, acid, flagged=flagged)

    stats = ac.score(ac.load_checks(rd))
    assert stats.n_defects == 3 and stats.n_controls == 2
    assert abs(stats.catch_rate - 2 / 3) < 1e-9
    assert abs(stats.fp_rate - 0.5) < 1e-9
    # Weighted catch penalises the... wait, here the miss is a HARD one (low weight),
    # so weighted catch-rate should be HIGHER than the unweighted 66%.
    assert stats.weighted_catch_rate > stats.catch_rate
    assert stats.by_difficulty["easy"] == 1.0 and stats.by_difficulty["hard"] == 0.0


def test_easy_misses_hurt_weighted_rate_most(tmp_path):
    rd = _mk(tmp_path)
    # Symmetric: catch the hard one, miss the easy one. Unweighted 50%, but
    # missing the BLATANT error should drag the weighted rate well below 50%.
    for i, (diff, caught) in enumerate([("easy", False), ("hard", True)]):
        p = ac.InjectionPlan("defect", "misread_metric", diff, None, f"n{i}")
        acid = ac.register(rd, p, stage="analysis", injected_into_gate=f"gt_{i}", ground_truth="gt")
        ac.record_outcome(rd, acid, flagged=caught)
    stats = ac.score(ac.load_checks(rd))
    assert abs(stats.catch_rate - 0.5) < 1e-9
    assert stats.weighted_catch_rate < 0.5


def test_escalation_is_rate_based_not_single_miss():
    cfg = ac.EscalationConfig(min_defects=8, catch_threshold=0.6)
    # A single miss with too few samples must NOT escalate.
    thin = ac.CalibrationStats(n_defects=1, weighted_catch_rate=0.0, catch_rate=0.0)
    assert ac.evaluate_escalation(thin, cfg).escalate is False
    # A poor rate over enough samples SHOULD escalate.
    poor = ac.CalibrationStats(n_defects=10, weighted_catch_rate=0.4, catch_rate=0.4)
    d = ac.evaluate_escalation(poor, cfg)
    assert d.escalate is True and d.reasons


def test_escalation_flags_high_false_positive_rate():
    cfg = ac.EscalationConfig(min_controls=5, fp_threshold=0.3)
    trigger_happy = ac.CalibrationStats(n_defects=10, weighted_catch_rate=0.9,
                                        catch_rate=0.9, n_controls=6, fp_rate=0.5)
    d = ac.evaluate_escalation(trigger_happy, cfg)
    assert d.escalate is True
    assert any("false-positive" in r for r in d.reasons)


def test_escalation_message_is_non_judgemental():
    cfg = ac.EscalationConfig(min_defects=8, catch_threshold=0.6)
    poor = ac.CalibrationStats(n_defects=10, weighted_catch_rate=0.4, catch_rate=0.4,
                               by_difficulty={"easy": 0.5, "hard": 0.3})
    d = ac.evaluate_escalation(poor, cfg)
    msg = ac.render_escalation(d, fellow="Fellow A")
    # The coaching framing is load-bearing (see design doc) — assert it's present.
    assert "NOT an" in msg and "not" in msg.lower()
    assert "funding" in msg.lower()
    assert "evaluation" in msg.lower()
    # Must not contain punitive verdict language.
    for banned in ("fired", "incompetent", "penalty", "sanction", "failing grade"):
        assert banned not in msg.lower()
