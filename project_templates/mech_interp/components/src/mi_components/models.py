"""Model loading and weight-matrix iteration.

The two things every mech interp project needs:

1. Load a small model from HuggingFace (and optionally TransformerLens) onto a chosen device.
2. Walk over the model and yield the weight matrices that decomposition-style methods care about
   (Linear .weight tensors of attention/MLP layers), with stable string IDs so a downstream
   project can store per-matrix state in a dict keyed by ID.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import torch
import torch.nn as nn
from transformers import AutoModelForCausalLM, AutoTokenizer


@dataclass
class WeightRef:
    """A reference to one weight matrix inside a loaded model.

    `id` is a stable string like "transformer.h.0.attn.c_attn" suitable for use as a dict key
    or a filename. `param` is the actual nn.Parameter (writable). `shape` is cached for
    convenience; it equals param.shape.
    """

    id: str
    param: nn.Parameter
    shape: torch.Size
    module: nn.Module  # the parent nn.Linear (or similar) this weight belongs to


def load_hf_model(
    model_name: str,
    device: str | torch.device = "cpu",
    dtype: torch.dtype = torch.float32,
    eval_mode: bool = True,
) -> tuple[nn.Module, AutoTokenizer]:
    """Load a HuggingFace causal LM and its tokenizer.

    Defaults to fp32 on CPU because mech interp work usually wants exact gradients on
    a small model. Override dtype/device for larger models.
    """
    tok = AutoTokenizer.from_pretrained(model_name)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    # transformers >=5 renamed torch_dtype → dtype; we use the new name and rely on
    # the lib to pick the right kwarg.
    model = AutoModelForCausalLM.from_pretrained(model_name, dtype=dtype)
    model.to(device)
    if eval_mode:
        model.eval()
    return model, tok


def _is_linear_like(module: nn.Module) -> bool:
    """True if the module is a 2D affine map we can treat as a 'weight matrix'.

    Covers nn.Linear and HuggingFace's Conv1D (used in GPT-2-family models — it's
    a transposed Linear). Excludes nn.Conv1d / nn.Conv2d which are spatially convolutional.
    """
    if isinstance(module, nn.Linear):
        return True
    cls_name = type(module).__name__
    if cls_name == "Conv1D" and hasattr(module, "weight") and module.weight.dim() == 2:
        # transformers.pytorch_utils.Conv1D — used by GPT-2-style architectures
        return True
    return False


def iter_linear_weights(
    model: nn.Module,
    include_embedding: bool = False,
    include_lm_head: bool = False,
    name_filter: str | None = None,
) -> Iterator[WeightRef]:
    """Yield WeightRef for each linear-like weight in the model.

    Linear-like means nn.Linear or HuggingFace's Conv1D (the transposed-Linear used by
    GPT-2-family models). nn.Conv1d / nn.Conv2d are NOT included.

    Args:
        include_embedding: also yield embedding-table weights (treated as "linear" in spirit).
        include_lm_head: yield the LM head weight even when it's tied to embeddings.
        name_filter: substring filter on module name (e.g. "attn" or "mlp").
    """
    seen_param_ids: set[int] = set()
    for full_name, module in model.named_modules():
        if _is_linear_like(module):
            if name_filter is not None and name_filter not in full_name:
                continue
            if not include_lm_head and full_name in {"lm_head", "embed_out"}:
                continue
            param = module.weight
            if id(param) in seen_param_ids:
                continue
            seen_param_ids.add(id(param))
            yield WeightRef(id=full_name, param=param, shape=param.shape, module=module)
        elif include_embedding and isinstance(module, nn.Embedding):
            if name_filter is not None and name_filter not in full_name:
                continue
            param = module.weight
            if id(param) in seen_param_ids:
                continue
            seen_param_ids.add(id(param))
            yield WeightRef(id=full_name, param=param, shape=param.shape, module=module)


def freeze(model: nn.Module) -> nn.Module:
    """Set requires_grad=False on every parameter. Returns the same model for chaining."""
    for p in model.parameters():
        p.requires_grad_(False)
    return model


def count_params(model: nn.Module, trainable_only: bool = False) -> int:
    return sum(p.numel() for p in model.parameters() if (p.requires_grad or not trainable_only))
