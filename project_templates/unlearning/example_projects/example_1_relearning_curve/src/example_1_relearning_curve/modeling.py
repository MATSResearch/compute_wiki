"""Tokenisation, the training loops, and the generative capability eval.

Hand-rolled rather than `Trainer`-based on purpose: an unlearning objective is
three lines of arithmetic, and the whole point of this example is that you can
read them. Everything runs on CPU with distilgpt2 in a few minutes.

Prompt tokens are masked out of the loss (`ignore_index=-100`) so the objectives
act on the *answer*, not on the question. Forgetting to do that is the classic
silent bug: the model learns to un-say the question.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

IGNORE = -100


@dataclass
class Batch:
    input_ids: torch.Tensor  # (B, T)
    labels: torch.Tensor  # (B, T), IGNORE on prompt + padding


def load(model_name: str = "distilgpt2", device: str = "cpu"):
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
    return model, tok


def encode(tok, pairs: list[tuple[str, str]], device: str = "cpu") -> Batch:
    """Encode (prompt, answer) pairs with the prompt masked out of the loss."""
    input_rows, label_rows = [], []
    for prompt, answer in pairs:
        p_ids = tok(prompt, add_special_tokens=False).input_ids
        a_ids = tok(answer, add_special_tokens=False).input_ids + [tok.eos_token_id]
        input_rows.append(p_ids + a_ids)
        label_rows.append([IGNORE] * len(p_ids) + a_ids)

    width = max(len(r) for r in input_rows)
    pad = tok.pad_token_id
    ids = torch.full((len(input_rows), width), pad, dtype=torch.long)
    labels = torch.full((len(input_rows), width), IGNORE, dtype=torch.long)
    for i, (row, lab) in enumerate(zip(input_rows, label_rows)):
        ids[i, : len(row)] = torch.tensor(row)
        labels[i, : len(lab)] = torch.tensor(lab)
    return Batch(input_ids=ids.to(device), labels=labels.to(device))


def _nll(model, batch: Batch) -> torch.Tensor:
    logits = model(input_ids=batch.input_ids).logits
    return torch.nn.functional.cross_entropy(
        logits[:, :-1, :].reshape(-1, logits.size(-1)).float(),
        batch.labels[:, 1:].reshape(-1),
        ignore_index=IGNORE,
    )


def sft(model, batch: Batch, steps: int, lr: float = 5e-5, log_every: int = 0):
    """Plain supervised finetuning — used both to implant the facts and to attack."""
    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    model.train()
    for step in range(steps):
        loss = _nll(model, batch)
        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)
        if log_every and step % log_every == 0:
            print(f"    sft step {step:>4}  loss {loss.item():.4f}")
    model.eval()
    return model


def unlearn(
    model,
    forget: Batch,
    retain: Batch,
    steps: int,
    method: str = "npo",
    lr: float = 5e-5,
    beta: float = 0.1,
    retain_weight: float = 1.0,
    log_every: int = 0,
):
    """Run one of the baseline unlearning objectives from `ul_components.losses`.

    The reference model for NPO is a frozen copy taken *before* unlearning; that
    is what bounds the objective and keeps it from collapsing the model.
    """
    from ul_components import losses

    ref = None
    if method in ("npo", "npo_retain"):
        ref = copy.deepcopy(model).eval()
        for p in ref.parameters():
            p.requires_grad_(False)

    opt = torch.optim.AdamW(model.parameters(), lr=lr)
    model.train()
    for step in range(steps):
        f_logits = model(input_ids=forget.input_ids).logits
        if method == "ga":
            loss = losses.gradient_ascent_loss(f_logits, forget.labels, ignore_index=IGNORE)
        elif method == "graddiff":
            r_logits = model(input_ids=retain.input_ids).logits
            loss = losses.grad_diff_loss(
                f_logits, forget.labels, r_logits, retain.labels,
                retain_weight=retain_weight, ignore_index=IGNORE,
            )
        elif method == "npo":
            with torch.no_grad():
                ref_logits = ref(input_ids=forget.input_ids).logits
            loss = losses.npo_loss(f_logits, ref_logits, forget.labels, beta=beta, ignore_index=IGNORE)
        elif method == "npo_retain":
            with torch.no_grad():
                ref_logits = ref(input_ids=forget.input_ids).logits
            r_logits = model(input_ids=retain.input_ids).logits
            loss = losses.npo_with_retain(
                f_logits, ref_logits, forget.labels, r_logits, retain.labels,
                beta=beta, retain_weight=retain_weight, ignore_index=IGNORE,
            )
        else:
            raise ValueError(f"unknown method {method!r}; use ga | graddiff | npo | npo_retain")

        loss.backward()
        opt.step()
        opt.zero_grad(set_to_none=True)
        if log_every and step % log_every == 0:
            print(f"    unlearn[{method}] step {step:>4}  loss {loss.item():.4f}")
    model.eval()
    return model


@torch.no_grad()
def generate_answers(model, tok, prompts: list[str], max_new_tokens: int = 8, device: str = "cpu") -> list[str]:
    """Greedy continuations. Generative, not multiple-choice, on purpose.

    An MCQ eval can read 'removed' while the model still writes the fact out in
    prose — see `ul_components.evaluate.mcq_gap_warning`.
    """
    out: list[str] = []
    for prompt in prompts:
        ids = tok(prompt, return_tensors="pt").to(device)
        gen = model.generate(
            **ids,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tok.pad_token_id,
        )
        out.append(tok.decode(gen[0, ids.input_ids.shape[1]:], skip_special_tokens=True))
    return out


def capability(model, tok, recs: list[dict], device: str = "cpu"):
    """Fraction of records the model still answers correctly, as a ForgetScore."""
    from ul_components import evaluate

    from example_1_relearning_curve.data import targets_for

    answers = generate_answers(model, tok, [r["prompt"] for r in recs], device=device)
    return evaluate.score_forget_set(answers, [targets_for(r) for r in recs])
