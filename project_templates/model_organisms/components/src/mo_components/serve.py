"""Serve a *finetuned* organism for evaluation — local HuggingFace + LoRA adapter.

`hf_local_backend` loads a base model (optionally + a LoRA adapter from
`finetune.train_lora`) with transformers/peft and returns a
`(messages) -> str` Backend that `mo_components.generate` / `eval` consume just
like the API backends. This is the bridge from "I trained an adapter" to "I can
evaluate the organism": the rest of the eval pipeline (probes, judge, metrics)
is unchanged.

Heavy deps (torch / transformers / peft) are imported inside the function, so
importing this module is free. Requires `mo-components[train]` (or at least
torch+transformers+peft) and a GPU for anything non-trivial — **not laptop
work**. To serve the same adapter through a vLLM OpenAI-compatible server
instead of loading weights in-process, use `generate.openai_compatible_backend`.
"""

from __future__ import annotations

from typing import Optional

from .generate import Backend


def hf_local_backend(
    base_model: str,
    *,
    adapter_path: Optional[str] = None,
    max_new_tokens: int = 600,
    temperature: float = 1.0,
    device_map: str = "auto",
    dtype: str = "bfloat16",
) -> Backend:
    """Load `base_model` (+ optional LoRA `adapter_path`) and return a chat Backend.

    Applies the model's chat template to the message list, generates, and returns
    the new assistant text only. `temperature<=0` switches to greedy decoding.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch_dtype = getattr(torch, dtype)
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForCausalLM.from_pretrained(
        base_model, dtype=torch_dtype, device_map=device_map
    )
    if adapter_path:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, adapter_path)
    model.eval()

    def call(messages: list[dict], **kwargs) -> str:
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        temp = kwargs.get("temperature", temperature)
        gen_kwargs = dict(
            max_new_tokens=kwargs.get("max_new_tokens", max_new_tokens),
            pad_token_id=tokenizer.eos_token_id,
        )
        if temp and temp > 0:
            gen_kwargs.update(do_sample=True, temperature=temp)
        else:
            gen_kwargs.update(do_sample=False)
        with torch.no_grad():
            out = model.generate(**inputs, **gen_kwargs)
        # Return only the newly generated tokens (strip the prompt).
        new_tokens = out[0][inputs["input_ids"].shape[1]:]
        return tokenizer.decode(new_tokens, skip_special_tokens=True)

    return call
