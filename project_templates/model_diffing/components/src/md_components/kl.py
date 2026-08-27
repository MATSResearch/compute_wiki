"""Per-token KL divergence between two models. The diff you run first.

Before training a crosscoder, before collecting paired activations, before
anything expensive: measure where the two models disagree at the output. A KL
sweep over a few thousand prompts answers "did the finetune change the model
everywhere, or in a narrow region?", and that answer decides which of the
expensive methods is even applicable.

KL is asymmetric. `kl_finetuned_vs_base` computes KL(finetuned || base), i.e.
expectation under the finetuned model — the natural direction for "what did the
finetune start doing". Say which direction you used; reviewers notice.

Needs torch.
"""

from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn.functional as F


@dataclass
class TokenKL:
    tokens: list[str]
    kl: list[float]

    @property
    def total(self) -> float:
        return float(sum(self.kl))

    @property
    def mean(self) -> float:
        return self.total / len(self.kl) if self.kl else 0.0

    @property
    def peak(self) -> tuple[str, float]:
        i = max(range(len(self.kl)), key=lambda j: self.kl[j])
        return self.tokens[i], self.kl[i]

    def to_dict(self) -> dict:
        return {"tokens": self.tokens, "kl": [round(k, 6) for k in self.kl],
                "total": self.total, "mean": self.mean}


def kl_from_logits(p_logits: torch.Tensor, q_logits: torch.Tensor) -> torch.Tensor:
    """KL(p || q) per position from raw logits. Returns (B, T).

    Computed in float32 regardless of input dtype: a bf16 softmax over a 100k
    vocabulary loses enough precision to change the ranking of prompts.
    """
    if p_logits.shape != q_logits.shape:
        raise ValueError(
            f"logit shapes differ: {tuple(p_logits.shape)} vs {tuple(q_logits.shape)}. "
            "Same tokenizer and same prompt formatting for both models."
        )
    lp = F.log_softmax(p_logits.float(), dim=-1)
    lq = F.log_softmax(q_logits.float(), dim=-1)
    return (lp.exp() * (lp - lq)).sum(-1)


@torch.no_grad()
def kl_per_token(finetuned, base, tokenizer, text: str, device: str = "cpu") -> TokenKL:
    """KL(finetuned || base) at every position of `text`."""
    ids = tokenizer(text, return_tensors="pt").to(device)
    ft_logits = finetuned(**ids).logits
    base_logits = base(**ids).logits
    kl = kl_from_logits(ft_logits, base_logits)[0]
    tokens = tokenizer.convert_ids_to_tokens(ids.input_ids[0])
    return TokenKL(tokens=tokens, kl=[float(x) for x in kl])


@torch.no_grad()
def kl_over_prompts(
    finetuned, base, tokenizer, prompts: list[str], device: str = "cpu",
    normalize_by_length: bool = True,
) -> list[tuple[float, str]]:
    """Score every prompt by its KL. Returns (score, prompt), highest first.

    `normalize_by_length=True` divides by token count, which is almost always
    what you want — otherwise the ranking is a list of your longest prompts.
    """
    scored: list[tuple[float, str]] = []
    for prompt in prompts:
        tk = kl_per_token(finetuned, base, tokenizer, prompt, device)
        scored.append((tk.mean if normalize_by_length else tk.total, prompt))
    return sorted(scored, key=lambda x: x[0], reverse=True)
