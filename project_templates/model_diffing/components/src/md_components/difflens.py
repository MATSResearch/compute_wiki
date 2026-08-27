"""Read a difference direction out in token space (activation difference lens).

Take the mean activation difference between two models at a layer, then
interpret that *direction* with the standard readouts: project it through the
unembedding (logit lens), or find its nearest neighbours among token embeddings.

This is the cheapest honest description of "which way the finetune pushed the
residual stream". It is a summary, not a mechanism — see
`acts.PairedActivations.difference_concentration` for whether the mean is even a
fair summary of your difference.

Needs torch.
"""

from __future__ import annotations

import torch


def normalize(direction: torch.Tensor) -> torch.Tensor:
    norm = direction.norm()
    if norm < 1e-9:
        raise ValueError("direction has ~zero norm; there is nothing to read out")
    return direction / norm


@torch.no_grad()
def logit_lens(model, direction: torch.Tensor, tokenizer, top_k: int = 30,
               apply_final_norm: bool = True) -> list[tuple[str, float]]:
    """Project a residual-stream direction through the unembedding.

    `apply_final_norm=True` runs the model's final layernorm first, which is what
    the real forward pass does; skipping it is a common source of readouts that
    are "nearly right but full of punctuation".
    """
    d = normalize(direction)
    hidden = d.unsqueeze(0)
    if apply_final_norm:
        final_norm = _find_final_norm(model)
        if final_norm is not None:
            hidden = final_norm(hidden.to(next(final_norm.parameters()).dtype))
    head = model.get_output_embeddings()
    if head is None:
        raise ValueError("model has no output embedding / lm_head to project through")
    logits = head(hidden.to(head.weight.dtype))[0].float()
    values, indices = logits.topk(top_k)
    return [
        (tokenizer.decode([int(i)]), float(v)) for i, v in zip(indices, values)
    ]


def _find_final_norm(model):
    """Best-effort lookup of the pre-unembedding norm across HF architectures."""
    for path in ("model.norm", "transformer.ln_f", "model.final_layernorm", "gpt_neox.final_layer_norm"):
        obj = model
        for part in path.split("."):
            obj = getattr(obj, part, None)
            if obj is None:
                break
        if obj is not None:
            return obj
    return None


@torch.no_grad()
def nearest_tokens(model, direction: torch.Tensor, tokenizer, top_k: int = 30) -> list[tuple[str, float]]:
    """Tokens whose *input* embeddings are most cosine-similar to the direction.

    A useful second opinion: logit lens says what the direction promotes at the
    output; this says what it resembles at the input. When they disagree, the
    direction is doing something other than "push toward these words".
    """
    emb = model.get_input_embeddings().weight
    d = normalize(direction).to(emb.dtype)
    sims = torch.nn.functional.cosine_similarity(emb, d.unsqueeze(0), dim=-1).float()
    values, indices = sims.topk(top_k)
    return [(tokenizer.decode([int(i)]), float(v)) for i, v in zip(indices, values)]


def cosine(a: torch.Tensor, b: torch.Tensor) -> float:
    """Cosine similarity between two directions.

    The use that matters: compare your treatment difference direction against the
    *control* finetune's difference direction. High cosine means you are looking
    at "what finetuning does", not at your intervention.
    """
    return float(torch.nn.functional.cosine_similarity(
        a.flatten().float().unsqueeze(0), b.flatten().float().unsqueeze(0)
    ).item())
