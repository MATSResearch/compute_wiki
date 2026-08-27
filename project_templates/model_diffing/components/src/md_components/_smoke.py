"""Smoke test for md_components.

Two halves. The pure-Python half (pairing checks, ranking, control verdict)
always runs. If the torch extra is installed it also builds a REAL pair — a
tiny model and a copy of it with one layer's weights nudged — and runs the whole
KL -> paired activations -> difference lens path on it. That catches shape and
hook-name bugs without a download of anything large.

    uv run python -m md_components._smoke
"""

from __future__ import annotations

from md_components import control, io, pairing, ranking, runs


def main() -> None:
    run = runs.new_run(tag="md_components_smoke", root="outputs")
    run.write_metadata({"smoke": True})
    print(f"run dir: {run.dir}")

    # --- pairing checks (pure python) --------------------------------------
    base = pairing.ModelFacts(
        name="base", vocab_size=50257, architecture="GPT2LMHeadModel",
        n_layers=6, hidden_size=768, dtype="torch.float32", tokenizer_hash="abc123",
    )
    good = pairing.ModelFacts(**{**base.__dict__, "name": "finetuned"})
    bad = pairing.ModelFacts(**{**base.__dict__, "name": "other", "dtype": "torch.bfloat16",
                                "vocab_size": 50304})
    assert pairing.compare(base, good) == []
    problems = pairing.compare(base, bad)
    print(f"pairing check caught {len(problems)} problem(s):")
    for p in problems:
        print(f"  - {p}")

    # --- ranking + control verdict (pure python) ---------------------------
    treatment = [(1.0, "p1"), (0.8, "p2"), (0.2, "p3"), (0.05, "p4")]
    ctrl = [(0.3, "p1"), (0.25, "p9"), (0.2, "p8"), (0.05, "p7")]
    print(f"\ntreatment divergence: {ranking.summarize(treatment).to_dict()}")
    print(f"top-2 concentration : {ranking.concentration(treatment, top_k=2):.2f}")
    ratio = ranking.excess_over_control(treatment, ctrl)
    ov = ranking.overlap(treatment, ctrl, top_k=2)
    v = control.verdict(divergence_ratio=ratio, direction_cosine=0.35, top_k_overlap=ov)
    print()
    print(control.describe(v))
    run.write_json("control_verdict.json", v.to_dict())
    io.write_jsonl([{"score": s, "prompt": p} for s, p in treatment], run.log_dir / "treatment.jsonl")

    # --- the torch path -----------------------------------------------------
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("\n(torch/transformers not installed — skipping the model path)")
    else:
        from md_components import acts, difflens, kl

        name = "hf-internal-testing/tiny-random-gpt2"
        tok = AutoTokenizer.from_pretrained(name)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        base_model = AutoModelForCausalLM.from_pretrained(name).eval()
        ft_model = AutoModelForCausalLM.from_pretrained(name).eval()
        with torch.no_grad():  # make it a genuinely different model
            for p in ft_model.transformer.h[-1].parameters():
                p.add_(torch.randn_like(p) * 0.05)

        facts_b = pairing.ModelFacts.from_hf(base_model, tok, "base")
        facts_f = pairing.ModelFacts.from_hf(ft_model, tok, "finetuned")
        pairing.assert_comparable(facts_b, facts_f)
        print(f"\nreal pair is comparable: {facts_b.architecture}, {facts_b.n_layers} layers")

        prompts = ["The capital of France is", "Sorting an array takes", "Once upon a time"]
        scored = kl.kl_over_prompts(ft_model, base_model, tok, prompts)
        print(f"KL ranking (mean per token): {[(round(s, 4), p[:22]) for s, p in scored]}")

        module = f"transformer.h.{len(base_model.transformer.h) - 1}"
        paired = acts.collect_pair(base_model, ft_model, tok, prompts, module, last_token_only=True)
        print(f"paired activations: {tuple(paired.base.shape)} at {module}")
        print(f"difference concentration (top 10%): {paired.difference_concentration():.2f}")
        top = difflens.logit_lens(base_model, paired.mean_difference(), tok, top_k=5)
        print(f"difference-lens top tokens: {[t for t, _ in top]}")
        print(f"cosine(diff, diff) sanity  : {difflens.cosine(paired.mean_difference(), paired.mean_difference()):.3f}")

    print("\nsmoke OK")


if __name__ == "__main__":
    main()
