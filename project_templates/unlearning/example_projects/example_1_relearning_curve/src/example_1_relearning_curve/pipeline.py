"""The whole experiment, in the order the wiki says to run it.

    implant  ->  measure  ->  unlearn  ->  measure  ->  RELEARNING ATTACK  ->  verdict

The attack is the part most write-ups skip, and it is the part that decides
whether the result means anything (arXiv:2410.08827). Everything lands in one
timestamped run dir: config, curve, verdict, and the raw generations.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass

import torch
from ul_components import relearn, report, runs, splits

from example_1_relearning_curve import data, modeling


@dataclass
class Config:
    model_name: str = "distilgpt2"
    device: str = "cpu"
    n_entities: int = 30
    forget_fraction: float = 0.2
    seed: int = 0
    implant_steps: int = 220
    implant_lr: float = 5e-5
    unlearn_method: str = "npo_retain"
    unlearn_steps: int = 60
    unlearn_lr: float = 5e-5
    beta: float = 0.1
    retain_weight: float = 1.0
    relearn_steps: tuple[int, ...] = (0, 10, 25, 50, 100)
    relearn_lr: float = 5e-5


def run_experiment(cfg: Config, run: runs.Run) -> dict:
    torch.manual_seed(cfg.seed)

    # ---- data + split -----------------------------------------------------
    entities = data.make_entities(cfg.n_entities, seed=cfg.seed)
    recs = data.records(entities)
    split = splits.make_split(
        recs, key_fn=lambda r: r["key"], forget_fraction=cfg.forget_fraction, seed=cfg.seed
    )
    splits.assert_no_leakage(split, key_fn=lambda r: r["key"])
    print(f"split: {split.summary()}")

    model, tok = modeling.load(cfg.model_name, cfg.device)
    all_batch = modeling.encode(tok, [(r["prompt"], r["answer"]) for r in recs], cfg.device)
    forget_batch = modeling.encode(tok, [(r["prompt"], r["answer"]) for r in split.forget], cfg.device)
    retain_batch = modeling.encode(tok, [(r["prompt"], r["answer"]) for r in split.retain], cfg.device)

    # ---- 1. implant the fictitious facts ----------------------------------
    print(f"\n[1/4] implanting {len(recs)} facts ({cfg.implant_steps} steps)")
    modeling.sft(model, all_batch, steps=cfg.implant_steps, lr=cfg.implant_lr, log_every=50)
    implanted = modeling.capability(model, tok, split.forget, cfg.device)
    retain_before = modeling.capability(model, tok, split.retain, cfg.device)
    print(f"    forget-set capability after implant : {implanted.capability:.3f}")
    print(f"    retain-set capability after implant : {retain_before.capability:.3f}")
    if implanted.capability < 0.5:
        print(
            "    NOTE: the facts did not implant well. Raise implant_steps or lower "
            "n_entities — unlearning something the model never learned measures nothing."
        )

    # ---- 2. unlearn --------------------------------------------------------
    print(f"\n[2/4] unlearning with {cfg.unlearn_method} ({cfg.unlearn_steps} steps)")
    modeling.unlearn(
        model, forget_batch, retain_batch, steps=cfg.unlearn_steps, method=cfg.unlearn_method,
        lr=cfg.unlearn_lr, beta=cfg.beta, retain_weight=cfg.retain_weight, log_every=20,
    )
    unlearned_state = copy.deepcopy(model.state_dict())
    post = modeling.capability(model, tok, split.forget, cfg.device)
    retain_after = modeling.capability(model, tok, split.retain, cfg.device)
    print(f"    forget-set capability after unlearn : {post.capability:.3f}")
    print(f"    retain-set capability after unlearn : {retain_after.capability:.3f}  "
          f"(utility delta {retain_after.capability - retain_before.capability:+.3f})")
    warn = post.warn_if_refusal_dominated()
    if warn:
        print(f"    {warn}")

    # ---- 3. relearning attack ---------------------------------------------
    # ADJACENT data = the same Q/A format about RETAIN entities. Never the forget
    # set: finetuning on the forget set only proves you can reteach it.
    print(f"\n[3/4] relearning attack on adjacent data {list(cfg.relearn_steps)}")

    def reset_fn():
        fresh, _ = modeling.load(cfg.model_name, cfg.device)
        fresh.load_state_dict(unlearned_state)
        return fresh

    def train_fn(m, n_steps: int):
        return modeling.sft(m, retain_batch, steps=n_steps, lr=cfg.relearn_lr)

    def eval_fn(m) -> float:
        return modeling.capability(m, tok, split.forget, cfg.device).capability

    curve = relearn.relearn_sweep(
        step_counts=list(cfg.relearn_steps),
        reset_fn=reset_fn,
        train_fn=train_fn,
        eval_fn=eval_fn,
        baseline=implanted.capability,
        adjacent_data_description=(
            f"{len(split.retain)} Q/A pairs about RETAIN entities (same format, "
            "disjoint entities from the forget set)"
        ),
        on_point=lambda p: print(f"    {p.steps:>4} steps -> forget capability {p.capability:.3f}"),
    )

    # ---- 4. verdict --------------------------------------------------------
    print("\n[4/4] verdict\n")
    print(report.summarize(curve))

    payload = {
        "config": asdict(cfg),
        "split": split.summary(),
        "capability": {
            "forget_after_implant": implanted.to_dict(),
            "forget_after_unlearn": post.to_dict(),
            "retain_after_implant": retain_before.to_dict(),
            "retain_after_unlearn": retain_after.to_dict(),
            "utility_delta": retain_after.capability - retain_before.capability,
        },
        "relearn_curve": curve.to_dict(),
        "verdict": report.verdict(curve).to_dict(),
    }
    run.write_json("results.json", payload)
    (run.dir / "summary.txt").write_text(report.summarize(curve) + "\n")
    return payload
