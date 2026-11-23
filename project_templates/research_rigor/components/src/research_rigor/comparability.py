"""
Comparability: declare what a comparison shares, and check it mechanically.

Two places where numbers get read side by side without being comparable.

1. YOUR NUMBER AGAINST A PAPER'S. A post-training result is a fact about one
   configuration — base model, trainer, objective, reward or verifier, training
   data, eval harness and set, decoding, how samples were varied, compute. A
   paper's absolute number is not a baseline for yours. The honest goal is ONE
   SHARED AXIS PER PAPER, stated up front ("comparable to Smith on the reward
   axis and to nobody on data"). `compare_configs` shows, factor by factor,
   what is shared, what differs and what the paper never reported (a blank is
   itself a fact); `shared_axis_flags` checks the declared axes against it.

2. SEVERAL AGENTS' ARMS AGAINST EACH OTHER. Let each arm choose its own judge,
   judge prompt and sample count and the spread between agents can exceed the
   effect. A coordinator owns the measurement; `arm_flags` flags any arm whose
   recorded judge, judge prompt, n or shared-file hash differs from the
   coordinator's before its result goes into the unified report, and
   `not_examined` reports the unticked rows of the per-arm checklist.

Everything here returns flags. Nothing blocks: a fixed measurement makes arms
comparable, not correct, and which bridge to run is the researcher's call.
"""

from dataclasses import dataclass, fields


@dataclass
class ConfigComparison:
    shared: list       # factors both report, with the same value
    differs: list      # factors both report, with different values
    unreported: list   # factors at least one side left blank (None)


def compare_configs(own: dict, paper: dict) -> ConfigComparison:
    """Compare two configurations written over the same factors. A factor the
    paper did not report is written as None, not left out."""
    assert own and set(own) == set(paper), (
        f"both configurations are written over the same factors, blanks as None; "
        f"only in one: {sorted(set(own) ^ set(paper))}")
    out = ConfigComparison([], [], [])
    for factor in own:
        if own[factor] is None or paper[factor] is None:
            out.unreported.append(factor)
        elif own[factor] == paper[factor]:
            out.shared.append(factor)
        else:
            out.differs.append(factor)
    return out


def shared_axis_flags(comparison: ConfigComparison, declared_shared: list[str]) -> list[str]:
    """Check the axes a comparison DECLARES it shares with a paper against the
    two configurations."""
    if not declared_shared:
        return ["no shared axis declared — the paper's absolute number is a different "
                "experiment, not a baseline; run an anchor or a shared-axis bridge, or say "
                "the two are not comparable"]
    flags = []
    for axis in declared_shared:
        assert axis in comparison.shared + comparison.differs + comparison.unreported, \
            f"declared axis {axis!r} is not a factor of the configurations"
        if axis in comparison.differs:
            flags.append(f"declared shared on {axis!r}, but the configurations differ there")
        if axis in comparison.unreported:
            flags.append(f"declared shared on {axis!r}, but one side never reported it")
    return flags


# --- several agents, one measurement ----------------------------------------

@dataclass
class ArmMeasurement:
    """What one arm (or the coordinator) measured with."""
    arm: str
    judge: str
    judge_prompt_hash: str
    samples_per_item: int
    shared_files_hash: str   # items, control, scoring and figure code


def arm_flags(coordinator: ArmMeasurement, arms: list[ArmMeasurement]) -> list[str]:
    """Arms whose measurement differs from the coordinator's."""
    measured = [f.name for f in fields(ArmMeasurement) if f.name != "arm"]
    flags = []
    for a in arms:
        differs = [m for m in measured if getattr(a, m) != getattr(coordinator, m)]
        if differs:
            flags.append(f"arm {a.arm!r} differs from the coordinator on {differs} — re-run it "
                         f"on the shared measurement before it goes into the unified report")
    return flags


ARM_CHECKLIST = (
    "raw_outputs_sampled",          # a sample of THIS arm's raw outputs was read
    "judge_label_failure_rate",     # the judge's label-failure rate for this arm
    "judge_matches_coordinator",    # judge and judge prompt identical to the coordinator's
    "samples_fixed_before_results", # samples per item fixed before the first result, unchanged since
    "control_in_same_batch",
    "figure_from_shared_code",
)


def not_examined(examined: dict) -> dict:
    """`examined` maps arm -> the checklist rows someone ticked. Returns arm ->
    the rows to report as "not examined"."""
    out = {}
    for arm, ticked in examined.items():
        unknown = set(ticked) - set(ARM_CHECKLIST)
        assert not unknown, f"arm {arm!r}: unknown checklist rows {sorted(unknown)}"
        rows = [row for row in ARM_CHECKLIST if row not in ticked]
        if rows:
            out[arm] = rows
    return out
