"""
Code publication & reproducibility (stage `publish`, Delegated-but-validated).

The mechanics of packaging a release are safe to delegate. What is NOT safe to
delegate is deciding that the release is adequate, because the field's own
baseline is poor and measurable:

- A pilot audit of twelve benchmark papers scores agent-benchmark reproducibility
  disclosure at 0.38/1.0, against 0.66 for classical benchmarks. Inference COST is
  disclosed by none of the eight agent benchmarks, and harness specification by
  none of them fully (2605.21404). Identical models yield disagreeing numbers with
  no traceable cause.
- The frontier-lag audit of 4,766 evaluation papers finds the median paper tests a
  model well behind frontier, 52.5% report results at the class level ("AI") rather
  than naming the model, and only 3.2% disclose reasoning mode (2605.04135).

So a release here must disclose MORE than the published norm, and the bar is set
at 0.66 — the classical-benchmark level — because clearing the agent-paper norm of
0.38 would mean matching a practice both audits describe as broken.

The enforcement mechanism is Glite ARF's (2606.27416): rigor encoded as
deterministic Python that FAILS LOUDLY, not as prose instructions. In its case
study, per-fold provenance checks caught four feature sets leaking the target
variable (an implausible RMSE of 0.609 corrected to 0.802) — a bug no amount of
"please be careful about leakage" in a prompt would have caught. Rules-as-code
survive where prose adherence does not, and the same paper's rule stands: agents
can weaken prose but not a passing test.

This library reuses `verify.Verifier` rather than defining a second rule type, so
the PI-authored-hard-verifier convention from stage 4 holds unchanged at stage 9:
an agent may ADD soft checks and may never author or disable a hard one.

Division of labour:
- THIS LIBRARY scores disclosure, runs the release checks, and refuses to publish
  on a failing hard check, a thin scorecard, or an agent-disabled rule.
- THE /publish skill assembles the release, drafts the checks for PI adoption,
  and walks the Fellow through the final gate.
"""

import re
from dataclasses import dataclass, field

from .verify import Verifier, run_validation

# The five audited disclosure fields (2605.21404), plus the three the frontier-lag
# audit found missing (2605.04135), plus uncertainty (inspect_evals 2507.06893).
DISCLOSURE_FIELDS = (
    "task_identity",        # what was run, exactly, and on what data
    "harness",              # scaffold + version/digest — "an agent" is a model AND a harness
    "inference_settings",   # temperature, sampling, context, tool set
    "cost",                 # disclosed by none of the eight audited agent benchmarks
    "failure_breakdown",    # what went wrong and how often, not just the headline
    "model_ids",            # the exact model, not the class ("AI", "GPT-4-family")
    "run_dates",            # when — the frontier moves under you
    "reasoning_mode",       # disclosed by 3.2% of evaluation papers
    "uncertainty",          # single runs are unreliable; report the interval
)

CLASSICAL_BENCHMARK_DISCLOSURE = 0.66   # the bar; agent-paper norm is 0.38

# A score alone is gameable: dropping exactly `cost` and `harness` from a nine-field
# scorecard still clears 0.66, while reproducing the field's precise failure — those
# two are the ones NO audited agent benchmark disclosed. `model_ids` and `run_dates`
# join them because 52.5% of evaluation papers report at the class level ("AI")
# rather than naming the model that was run. These four are required, not scored.
REQUIRED_FIELDS = ("cost", "harness", "model_ids", "run_dates")


@dataclass
class DisclosureReport:
    score: float
    present: list = field(default_factory=list)
    missing: list = field(default_factory=list)
    threshold: float = CLASSICAL_BENCHMARK_DISCLOSURE

    @property
    def missing_required(self) -> list:
        return [f for f in REQUIRED_FIELDS if f in self.missing]

    @property
    def sufficient(self) -> bool:
        return self.score >= self.threshold and not self.missing_required


def disclosure_report(release: dict, *,
                      threshold: float = CLASSICAL_BENCHMARK_DISCLOSURE) -> DisclosureReport:
    """Score a release dict against the disclosure fields.

    A field counts as present only if it holds a non-empty, non-placeholder
    value — "TBD", "N/A" and an empty list are absences that look like presences,
    which is how a 0.38 disclosure rate happens in the first place.
    """
    assert 0.0 <= threshold <= 1.0, f"threshold {threshold} out of range"
    present, missing = [], []
    for fld in DISCLOSURE_FIELDS:
        val = release.get(fld)
        ok = val is not None and (str(val).strip().lower() not in ("", "tbd", "n/a", "none", "unknown"))
        if isinstance(val, (list, dict, tuple, set)):
            ok = bool(val)
        (present if ok else missing).append(fld)
    return DisclosureReport(len(present) / len(DISCLOSURE_FIELDS), present, missing, threshold)


# --- release checks (rules-as-code; PI authors the hard ones) ----------------

_SECRET_RE = re.compile(r"(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
_ABS_PATH_RE = re.compile(r"(/home/[^\s\"']+|/Users/[^\s\"']+|[A-Z]:\\\\Users\\\\[^\s\"']+)")


def no_secrets(key: str = "files", **kw) -> Verifier:
    """Refuse to publish a release whose files carry a credential.
    `release[key]` is {path: text_contents}."""
    def check(release: dict) -> tuple[bool, str]:
        hits = [p for p, text in release.get(key, {}).items() if _SECRET_RE.search(text or "")]
        return (not hits), (f"credential-shaped strings in {hits}" if hits else "no secrets found")
    return Verifier("no_secrets", "no credentials in released files", check, **kw)


def no_absolute_local_paths(key: str = "files", **kw) -> Verifier:
    """A path under /home or /Users cannot reproduce on anyone else's machine."""
    def check(release: dict) -> tuple[bool, str]:
        hits = [p for p, text in release.get(key, {}).items() if _ABS_PATH_RE.search(text or "")]
        return (not hits), (f"machine-local absolute paths in {hits}" if hits else "paths are portable")
    return Verifier("no_absolute_local_paths", "no machine-local paths", check, **kw)


def seeds_recorded(**kw) -> Verifier:
    def check(release: dict) -> tuple[bool, str]:
        seeds = release.get("seeds")
        return bool(seeds), (f"seeds: {seeds}" if seeds else "no seeds recorded — the run is not repeatable")
    return Verifier("seeds_recorded", "random seeds are in the release", check, **kw)


def environment_pinned(**kw) -> Verifier:
    def check(release: dict) -> tuple[bool, str]:
        env = release.get("environment")
        return bool(env), (f"environment: {env}" if env else
                           "no pinned environment (lockfile / image digest) — "
                           "no agent benchmark in the audit fully disclosed one either")
    return Verifier("environment_pinned", "environment is pinned", check, **kw)


def entrypoint_declared(**kw) -> Verifier:
    def check(release: dict) -> tuple[bool, str]:
        ep = release.get("entrypoint")
        return bool(ep), (f"entrypoint: {ep}" if ep else "no entrypoint — nobody knows what to run")
    return Verifier("entrypoint_declared", "a runnable entrypoint is named", check, **kw)


def artifacts_hashed(**kw) -> Verifier:
    """Every released artifact carries a content hash, so a reader can tell
    whether the file they have is the file the claims were computed from."""
    def check(release: dict) -> tuple[bool, str]:
        arts = release.get("artifacts", {})
        if not arts:
            return False, "no artifacts listed"
        unhashed = [p for p, h in arts.items() if not h]
        return (not unhashed), (f"unhashed artifacts: {unhashed}" if unhashed
                                else f"{len(arts)} artifacts hashed")
    return Verifier("artifacts_hashed", "released artifacts are content-hashed", check, **kw)


def default_release_checks() -> list[Verifier]:
    """The house minimum, all hard and all PI-owned by default. A Fellow adds
    project-specific ones (a smoke test, a leakage check like the one that caught
    four leaking feature sets in Glite ARF's case study) — that is where the real
    value is; these only catch the universal mistakes."""
    return [entrypoint_declared(), environment_pinned(), seeds_recorded(),
            artifacts_hashed(), no_secrets(), no_absolute_local_paths()]


@dataclass
class PublishVerdict:
    verdict: str      # "blocked_failed_check" | "blocked_disabled_check" | "blocked_disclosure"
                      # | "blocked_pending_human" | "ready"
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    disclosure: DisclosureReport | None = None


def publish_gate(release: dict, checks: list[Verifier], *,
                 pi_approved: bool, disabled: dict | None = None,
                 threshold: float = CLASSICAL_BENCHMARK_DISCLOSURE) -> PublishVerdict:
    """Run the release checks and decide.

    `disabled` is {check_name: who_disabled_it}. Disabling a hard check is a PI
    action; an agent doing it is the prose-vs-tests failure Glite ARF names, so it
    blocks rather than warns.

    Note the ordering: a failed check blocks BEFORE disclosure is scored, because
    a well-documented broken release is still broken.
    """
    disabled = disabled or {}
    hard_names = {v.name for v in checks if v.severity == "hard"}
    bad_disable = {n: who for n, who in disabled.items() if n in hard_names and who != "pi"}
    if bad_disable:
        return PublishVerdict("blocked_disabled_check", [
            f"hard checks disabled by a non-PI actor: {bad_disable}. Agents may add soft checks "
            f"and may not switch off a hard one — rules-as-code only work if they cannot be "
            f"talked out of."])

    active = [v for v in checks if v.name not in disabled]
    report = run_validation(active, release, execution_ok=True)

    warnings = [f"soft check failed: {r.name} — {r.message}"
                for r in report.results if not r.passed and r.severity == "soft"]
    if disabled:
        warnings.append(f"checks disabled by the PI (recorded, not hidden): {sorted(disabled)}")

    failed_hard = [r for r in report.results if not r.passed and r.severity == "hard"]
    if failed_hard:
        return PublishVerdict("blocked_failed_check",
                              [f"{r.name}: {r.message}" for r in failed_hard], warnings)

    disc = disclosure_report(release, threshold=threshold)
    if not disc.sufficient:
        reason = (f"disclosure {disc.score:.2f} (bar {disc.threshold:.2f}, the "
                  f"classical-benchmark level — not the agent-paper norm of 0.38); "
                  f"missing {disc.missing}.")
        if disc.missing_required:
            reason += (f" {disc.missing_required} are REQUIRED, not scored: they are exactly the "
                       f"fields the audits found missing everywhere, so omitting them is how a "
                       f"release clears a numeric bar while reproducing the field's failure.")
        return PublishVerdict("blocked_disclosure", [reason], warnings, disc)

    if not pi_approved:
        return PublishVerdict("blocked_pending_human", [
            "checks pass and disclosure clears, but the release gate is the PI's. Read the code "
            "and the results yourself before it goes out."], warnings, disc)

    return PublishVerdict("ready", [], warnings, disc)
