"""
Evidence is not the verdict (cited from `run` onward, read at `resolve`).

Two records, written separately. EVIDENCE is an observation: this run bears on
that prediction, for or against, this much. THE VERDICT (`resolve.Resolution`)
is a judgement a person signs against the decision rule they froze, and it is
read against the evidence.

- Cite every run that bears on a prediction as you go, with a polarity and a
  weight — the ones that go AGAINST with the same care as the ones for.
- The accumulated lean never sets the verdict. `tally` is context for the
  person signing, not a vote: one strong disproof may be decisive or may be a
  broken run, and only the decision rule and a human can say which.
- A verdict that disagrees with its own evidence is FLAGGED, not blocked.
  `disagreement` returns the flag; `resolve.resolve_gate` relays it as a warning.

The ledger is one more append-only log in the run directory (`evidence.jsonl`),
so a citation, once made, cannot be quietly dropped at write-up time.
"""

import math
from dataclasses import asdict, dataclass

from .run_dir import RunDir, _append_jsonl, _now_iso

CONCLUDING_VERDICTS = ("supported", "refuted")


@dataclass
class Citation:
    """One observation bearing on one prediction. `valence` is signed and
    weighted: above zero is for the prediction, below zero against, and the
    magnitude says how much."""
    item: str          # the run, finding or artifact observed
    prediction: str    # the hypothesis id it bears on
    valence: float
    note: str = ""

    def __post_init__(self):
        assert self.item and self.prediction, "a citation names its item and its prediction"
        assert math.isfinite(self.valence) and self.valence != 0, (
            f"citation {self.item!r} -> {self.prediction!r}: valence must be a finite non-zero "
            f"number (positive = for, negative = against), got {self.valence!r}")


def cite(rd: RunDir, citation: Citation, *, cited_by: str) -> None:
    """Append a citation to the run's evidence ledger."""
    assert cited_by in ("agent", "human"), f"cited_by must be agent|human, got {cited_by!r}"
    _append_jsonl(rd.evidence_path, {
        "ts": _now_iso(), "run_id": rd.read_metadata()["run_id"],
        "cited_by": cited_by, **asdict(citation)})


def load(rd: RunDir) -> list[Citation]:
    return [Citation(r["item"], r["prediction"], r["valence"], r["note"])
            for r in rd.read_log(rd.evidence_path)]


@dataclass
class Tally:
    """What has been cited on one prediction. Context for the signer."""
    supporting: list   # items cited for
    against: list      # items cited against
    net: float         # sum of valences — a lean, never a verdict


def tally(citations: list[Citation], prediction: str) -> Tally:
    mine = [c for c in citations if c.prediction == prediction]
    return Tally(supporting=[c.item for c in mine if c.valence > 0],
                 against=[c.item for c in mine if c.valence < 0],
                 net=sum(c.valence for c in mine))


def disagreement(verdict: str, t: Tally) -> str | None:
    """How a signed verdict disagrees with its own evidence, or None.

    `supported` with anything cited against it, or a concluding verdict with
    nothing cited at all, is the shape of overclaiming by omission; `refuted`
    with nothing cited against it is the mirror case. `inconclusive` disagrees
    with nothing.
    """
    if verdict not in CONCLUDING_VERDICTS:
        return None
    if not t.supporting and not t.against:
        return f"signed `{verdict}` with nothing cited"
    if verdict == "supported" and t.against:
        return (f"signed `supported` with {len(t.against)} cited against "
                f"({t.against}) and {len(t.supporting)} for")
    if verdict == "refuted" and not t.against:
        return f"signed `refuted` with nothing cited against ({len(t.supporting)} for)"
    return None
