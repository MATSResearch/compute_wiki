"""Is this model pair actually comparable? Check before you diff.

Four ways a model diff silently measures the wrong thing, all of them cheap to
rule out and expensive to discover on day three:

1. **Tokenizer mismatch.** A merged or extended vocabulary misaligns positions,
   so every position looks maximally divergent. Symptom: uniformly enormous KL
   everywhere, including on text neither model was trained on.
2. **Chat-template mismatch.** Applying a template to one side and not the other
   diffs the system prompt. Symptom: divergence concentrated at positions 0–5.
3. **Dtype mismatch.** Loading one model in bf16 and the other in fp16 produces
   a real, entirely uninteresting difference.
4. **Different architectures.** Cross-architecture diffing is a research problem
   (arXiv:2602.11729), not a config flag.

`assert_comparable` turns all four into an exception with a fix in the message.
Pure Python — it inspects config dicts, so you can run it on metadata before
downloading 140GB of weights.

See: https://matsresearch.github.io/compute_wiki/interpretability/model-diffing/
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ModelFacts:
    """The handful of facts that decide whether two models can be diffed."""

    name: str
    vocab_size: int
    architecture: str
    n_layers: int
    hidden_size: int
    dtype: str
    tokenizer_hash: str | None = None
    chat_template: str | None = None

    @classmethod
    def from_hf(cls, model, tokenizer, name: str = "") -> "ModelFacts":
        cfg = model.config
        return cls(
            name=name or getattr(cfg, "_name_or_path", "") or "unnamed",
            vocab_size=int(getattr(cfg, "vocab_size", 0)),
            architecture=(getattr(cfg, "architectures", None) or [type(model).__name__])[0],
            n_layers=int(
                getattr(cfg, "num_hidden_layers", 0) or getattr(cfg, "n_layer", 0)
            ),
            hidden_size=int(getattr(cfg, "hidden_size", 0) or getattr(cfg, "n_embd", 0)),
            dtype=str(getattr(model, "dtype", "unknown")),
            tokenizer_hash=tokenizer_fingerprint(tokenizer),
            chat_template=getattr(tokenizer, "chat_template", None),
        )


def tokenizer_fingerprint(tokenizer, probe: str = "The quick brown fox jumps; 3.14 — naïve") -> str:
    """Stable short hash of how a tokenizer segments a probe string.

    Comparing vocab sizes is not enough: two tokenizers can share a size and
    still segment differently. Encoding a probe catches that.
    """
    import hashlib

    ids = tokenizer(probe, add_special_tokens=False).input_ids
    payload = f"{len(tokenizer)}|{ids}"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def compare(base: ModelFacts, other: ModelFacts) -> list[str]:
    """Return a list of human-readable incompatibilities. Empty means go ahead."""
    problems: list[str] = []
    if base.vocab_size != other.vocab_size:
        problems.append(
            f"vocab size differs ({base.vocab_size} vs {other.vocab_size}): positions will "
            "not align. Diffing requires a shared tokenizer."
        )
    if base.tokenizer_hash and other.tokenizer_hash and base.tokenizer_hash != other.tokenizer_hash:
        problems.append(
            "tokenizers segment text differently (fingerprint mismatch) even though the "
            "vocab sizes may match. Re-check which tokenizer each model shipped with."
        )
    if base.architecture != other.architecture:
        problems.append(
            f"architectures differ ({base.architecture} vs {other.architecture}): this is "
            "cross-architecture diffing, a research problem in its own right (arXiv:2602.11729), "
            "not something the methods here handle."
        )
    if base.n_layers != other.n_layers or base.hidden_size != other.hidden_size:
        problems.append(
            f"shapes differ (layers {base.n_layers} vs {other.n_layers}, hidden "
            f"{base.hidden_size} vs {other.hidden_size}): activation diffs are undefined."
        )
    if base.dtype != other.dtype:
        problems.append(
            f"dtypes differ ({base.dtype} vs {other.dtype}): you will measure a real but "
            "uninteresting numerical difference. Load both identically."
        )
    if (base.chat_template or None) != (other.chat_template or None):
        problems.append(
            "chat templates differ: format prompts identically for both models, or you are "
            "diffing the system prompt rather than the finetune."
        )
    return problems


def assert_comparable(base: ModelFacts, other: ModelFacts) -> None:
    """Raise with every problem listed, not just the first."""
    problems = compare(base, other)
    if problems:
        bullets = "\n  - ".join(problems)
        raise ValueError(f"model pair is not comparable:\n  - {bullets}")
