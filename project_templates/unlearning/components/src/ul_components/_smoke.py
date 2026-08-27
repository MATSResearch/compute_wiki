"""Smoke test for ul_components.

Runs the whole analysis path with a FAKE model (no GPU, no downloads, no API):
build a split, check it for leakage, score a forget set, run a relearning sweep
against a stub trainer that mimics suppression-not-removal, and print the
verdict. If the torch extra is installed it also runs one step of each loss on
random logits, so a shape bug surfaces here rather than 40 minutes into a run.

    uv run python -m ul_components._smoke
"""

from __future__ import annotations

from ul_components import evaluate, io, relearn, report, runs, splits


def main() -> None:
    run = runs.new_run(tag="ul_components_smoke", root="outputs")
    run.write_metadata({"smoke": True})
    print(f"run dir: {run.dir}")

    # --- splits -------------------------------------------------------------
    records = [
        {"author": f"author_{i}", "q": f"Who is author_{i}?", "a": f"a novelist #{i}"}
        for i in range(20)
        for _ in range(3)
    ]
    split = splits.make_split(records, key_fn=lambda r: r["author"], forget_fraction=0.1)
    splits.assert_no_leakage(split, key_fn=lambda r: r["author"])
    print(f"split: {split.summary()}")

    # --- scoring ------------------------------------------------------------
    responses = [
        "author_3 is a novelist #3",       # correct
        "I can't help with that.",          # refusal
        "Hmm, I don't know who that is.",   # incapable
    ]
    targets = [["a novelist #3"], ["a novelist #7"], ["a novelist #9"]]
    score = evaluate.score_forget_set(responses, targets)
    print(f"forget score: {score.to_dict()}")

    # --- relearning attack against a stub 'model' ---------------------------
    # The stub recovers fast, i.e. it behaves like suppression rather than removal.
    def reset_fn() -> dict:
        return {"steps": 0}

    def train_fn(model: dict, n: int) -> dict:
        model["steps"] = n
        return model

    def eval_fn(model: dict) -> float:
        recovered = min(1.0, model["steps"] / 100.0)
        return 0.05 + recovered * (0.80 - 0.05)

    curve = relearn.relearn_sweep(
        step_counts=[0, 10, 50, 100, 250],
        reset_fn=reset_fn,
        train_fn=train_fn,
        eval_fn=eval_fn,
        baseline=0.80,
        adjacent_data_description="stub adjacent corpus (smoke test)",
    )
    print()
    print(report.summarize(curve))

    run.write_json("relearn_curve.json", curve.to_dict())
    run.write_json("verdict.json", report.verdict(curve).to_dict())
    io.write_jsonl([p.__dict__ for p in curve.sorted_points()], run.log_dir / "points.jsonl")

    # --- losses (only if the torch extra is installed) ----------------------
    try:
        import torch

        from ul_components import losses
    except ImportError:
        print("\n(torch not installed — skipping loss shape check)")
    else:
        b, t, v = 2, 6, 11
        logits = torch.randn(b, t, v)
        ref = torch.randn(b, t, v)
        labels = torch.randint(0, v, (b, t))
        labels[:, :2] = -100  # mask the 'prompt'
        ga = losses.gradient_ascent_loss(logits, labels)
        gd = losses.grad_diff_loss(logits, labels, torch.randn(b, t, v), labels)
        npo = losses.npo_loss(logits, ref, labels, beta=0.1)
        print(f"\nlosses ok: GA={ga.item():.3f} GradDiff={gd.item():.3f} NPO={npo.item():.3f}")

    print("\nsmoke OK")


if __name__ == "__main__":
    main()
