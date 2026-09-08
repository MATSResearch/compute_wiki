"""
Delegated-but-validated implementation harness (MVP-2, pipeline stage 4).

Implementation is the mature, safe-to-delegate stage — but the dominant danger is
the SILENT failure: the code runs, exits 0, and the result is wrong (REXBench,
Auditing Sabotage Bench). So this harness enforces the design's core rule:

    execution success is necessary but NEVER sufficient.

An attempt is only handed to the PI's approval gate if it passes INDEPENDENT,
PI-owned verifiers expressed as rules-as-code that fail loudly (Glite ARF). The
harness never auto-accepts on "it ran". Three more design commitments are encoded:

- Rules-as-code, PI-owned. HARD verifiers (the gate) must be authored by the PI,
  not the implementing agent — agents may add SOFT suggestions but cannot weaken a
  passing test (Glite ARF: "agents can weaken prose but not passing tests").
- Preserved chain-of-thought. Every attempt must carry a reasoning trace, which is
  written to disk and logged to provenance; an attempt with no scratchpad is
  refused (SHADE-Arena: monitoring CoT is the one working sabotage defense).
- Structured feedback. A failed verifier becomes an actionable diagnostic for the
  next attempt (Gome's gradient-style feedback), not a bare retry.
"""

import hashlib
import math
from dataclasses import dataclass, field
from typing import Callable

from .run_dir import RunDir


@dataclass
class Verifier:
    """A deterministic rule-as-code. `check(result)` returns (passed, message).
    A check that raises is treated as a loud failure, never swallowed."""
    name: str
    description: str
    check: Callable[[dict], tuple[bool, str]]
    severity: str = "hard"    # "hard" (gate) | "soft" (advisory)
    author: str = "pi"        # "pi" | "agent" — hard verifiers must be "pi"

    def __post_init__(self):
        assert self.severity in ("hard", "soft"), f"bad severity {self.severity!r}"
        assert self.author in ("pi", "agent"), f"bad author {self.author!r}"


@dataclass
class VerifierResult:
    name: str
    passed: bool
    severity: str
    message: str


@dataclass
class ValidationReport:
    execution_ok: bool
    results: list[VerifierResult] = field(default_factory=list)
    requires_human_gate: bool = True  # ALWAYS — validation informs the PI, never replaces them

    @property
    def hard_failures(self) -> list[VerifierResult]:
        return [r for r in self.results if not r.passed and r.severity == "hard"]

    @property
    def soft_failures(self) -> list[VerifierResult]:
        return [r for r in self.results if not r.passed and r.severity == "soft"]

    @property
    def verifiers_passed(self) -> bool:
        return not self.hard_failures

    @property
    def verdict(self) -> str:
        if not self.execution_ok:
            return "execution_failed"
        if self.hard_failures:
            return "verifiers_failed"
        return "verifiers_passed_pending_human"  # NOT "accepted" — the PI gate decides


# --- rules-as-code building blocks (PI-owned verifier factories) -------------

def _get(result: dict, key: str):
    assert key in result, f"result has no key {key!r} (keys: {sorted(result)})"
    return result[key]


def expect_finite(key: str, **kw) -> Verifier:
    """No NaN/inf — the classic silent numerical failure."""
    def check(result):
        v = _get(result, key)
        vals = v if isinstance(v, (list, tuple)) else [v]
        bad = [x for x in vals if not math.isfinite(x)]
        return (not bad, f"{key} finite" if not bad else f"{key} has non-finite values: {bad[:3]}")
    return Verifier(f"finite:{key}", f"{key} must be finite", check, **kw)


def expect_range(key: str, lo: float, hi: float, **kw) -> Verifier:
    def check(result):
        v = _get(result, key)
        return (lo <= v <= hi, f"{key}={v} in [{lo},{hi}]" if lo <= v <= hi
                else f"{key}={v} OUTSIDE [{lo},{hi}]")
    return Verifier(f"range:{key}", f"{key} in [{lo},{hi}]", check, **kw)


def expect_shape(key: str, shape: tuple, **kw) -> Verifier:
    def check(result):
        v = _get(result, key)
        got = _shape_of(v)
        return (got == shape, f"{key} shape {got}" if got == shape
                else f"{key} shape {got} != expected {shape}")
    return Verifier(f"shape:{key}", f"{key} has shape {shape}", check, **kw)


def not_constant(key: str, **kw) -> Verifier:
    """Catches the degenerate 'returns a constant' result (e.g. predicting one class)."""
    def check(result):
        v = _get(result, key)
        assert isinstance(v, (list, tuple)), f"not_constant needs a sequence, got {type(v).__name__}"
        varied = len(set(v)) > 1
        return (varied, f"{key} varies" if varied else f"{key} is constant ({v[0] if v else 'empty'}) — degenerate")
    return Verifier(f"not_constant:{key}", f"{key} must not be a constant", check, **kw)


def reproduces(key: str, reference: float, rel_tol: float = 0.05, **kw) -> Verifier:
    """Independent reproduction of a claimed number within tolerance."""
    def check(result):
        v = _get(result, key)
        ok = math.isclose(v, reference, rel_tol=rel_tol)
        return (ok, f"{key}={v} reproduces {reference} (±{rel_tol:.0%})" if ok
                else f"{key}={v} does NOT reproduce {reference} (±{rel_tol:.0%})")
    return Verifier(f"reproduces:{key}", f"{key} reproduces {reference}", check, **kw)


def invariant(name: str, fn: Callable[[dict], bool], description: str = "", **kw) -> Verifier:
    """An arbitrary PI-defined invariant over the result dict."""
    def check(result):
        ok = fn(result)
        return (bool(ok), f"invariant {name} holds" if ok else f"invariant {name} VIOLATED")
    return Verifier(f"invariant:{name}", description or name, check, **kw)


def _shape_of(v) -> tuple:
    if not isinstance(v, (list, tuple)):
        return ()
    if not v:
        return (0,)
    inner = {_shape_of(x) for x in v}
    return (len(v),) + (next(iter(inner)) if len(inner) == 1 else ("ragged",))


# --- validation --------------------------------------------------------------

def run_validation(verifiers: list[Verifier], result: dict, execution_ok: bool = True) -> ValidationReport:
    """Run PI-owned rules-as-code against a result. A hard verifier authored by
    the implementing agent is a design violation and fails loudly — the gate must
    be independent of the code that produced the result."""
    for v in verifiers:
        assert not (v.severity == "hard" and v.author == "agent"), (
            f"hard verifier {v.name!r} is agent-authored — the validation gate must be "
            f"PI-owned and independent (agents may add soft verifiers only)"
        )
    report = ValidationReport(execution_ok=execution_ok)
    if not execution_ok:
        return report  # nothing to verify against a failed run
    for v in verifiers:
        try:
            passed, message = v.check(result)
        except Exception as e:
            # A verifier that crashes is a loud failure, not a silent skip.
            passed, message = False, f"verifier raised {type(e).__name__}: {e}"
        report.results.append(VerifierResult(v.name, passed, v.severity, message))
    return report


def structured_feedback(report: ValidationReport) -> str:
    """Gome-style: turn failures into an actionable diagnostic for the next attempt."""
    if report.verdict == "execution_failed":
        return "The implementation did not execute successfully. Fix the run before optimising results."
    lines = []
    for r in report.hard_failures:
        lines.append(f"[HARD] {r.name}: {r.message}")
    for r in report.soft_failures:
        lines.append(f"[soft] {r.name}: {r.message}")
    if not lines:
        return "All hard verifiers pass. Do not change the result to chase soft warnings."
    return ("The result did not pass independent validation. Address each failing check "
            "below — do not weaken the checks:\n  " + "\n  ".join(lines))


# --- the driver: attempt -> validate -> (feedback | human gate) --------------

@dataclass
class Attempt:
    result: dict
    reasoning: str            # the preserved chain-of-thought (required)
    execution_ok: bool = True
    code_ref: str | None = None


def delegated_but_validated(*, attempt_fn: Callable[[str | None], Attempt],
                            verifiers: list[Verifier], rd: RunDir, stage: str = "run",
                            max_attempts: int = 3) -> tuple[Attempt, ValidationReport]:
    """Run the delegate/validate loop. `attempt_fn(feedback)` is the INTELLIGENCE
    (the agent authoring+running code); it returns an Attempt. This driver
    preserves CoT, runs independent validation, and feeds structured diagnostics
    back on failure. It NEVER accepts — it returns the attempt + report for the
    PI's approval gate (which is also where an attention check can be seeded)."""
    assert max_attempts >= 1
    feedback = None
    attempt = report = None
    attempts_dir = rd.path / "code" / "attempts"
    attempts_dir.mkdir(parents=True, exist_ok=True)

    for i in range(max_attempts):
        attempt = attempt_fn(feedback)
        assert attempt.reasoning and attempt.reasoning.strip(), (
            "attempt has no preserved reasoning — refused. Chain-of-thought must be "
            "monitorable (SHADE-Arena); never accept an unmonitored scratchpad."
        )
        # Preserve CoT on disk + reference it in provenance.
        trace_path = attempts_dir / f"attempt_{i}.md"
        trace_path.write_text(attempt.reasoning)
        rd.log_provenance(
            actor="agent", stage=stage, event="model_invocation",
            summary=f"implementation attempt {i + 1}/{max_attempts}",
            prompt_hash="sha256:" + hashlib.sha256(attempt.reasoning.encode()).hexdigest(),
            inputs={"feedback": feedback}, outputs={"execution_ok": attempt.execution_ok,
                                                    "reasoning_trace": str(trace_path)},
        )
        report = run_validation(verifiers, attempt.result, attempt.execution_ok)
        if report.verdict == "verifiers_passed_pending_human":
            return attempt, report
        feedback = structured_feedback(report)

    # Exhausted attempts without passing validation. Still requires the human gate,
    # but flagged as failing — never silently accepted.
    return attempt, report
