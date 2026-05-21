"""Run a model organism over a set of prompts — parallel, cached, pluggable.

A **backend** is just a callable `(messages: list[dict], **kwargs) -> str`. The
default is OpenRouter (one key, every provider; key from `OPENROUTER_API_KEY`),
but you can pass any callable — a local vLLM server, a HuggingFace pipeline, or a
fake for tests. This keeps `mo_components` decoupled from any one provider and
lets the no-API smoke test run a stub backend.

Calls are parallelized with a thread pool (the OpenRouter/openai sync client is
thread-safe for this) and cached to disk by (model, messages) hash so re-running
the same probe set is free. Per the project conventions, parallelism is on by
default — you don't have to ask for it.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

from .cache import hash_config
from .organisms import OrganismSpec

# A backend maps a chat message list to a completion string.
Backend = Callable[..., str]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


def _chat_completion_backend(
    model: str,
    *,
    api_key: str,
    base_url: Optional[str],
    temperature: float,
    max_tokens: int,
) -> Backend:
    """Shared OpenAI-compatible chat backend (OpenRouter, OpenAI, local vLLM, …)."""
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key)

    def call(messages: list[dict], **kwargs) -> str:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=kwargs.get("temperature", temperature),
            max_tokens=kwargs.get("max_tokens", max_tokens),
        )
        return resp.choices[0].message.content or ""

    return call


def openrouter_backend(
    model: str,
    *,
    api_key: Optional[str] = None,
    temperature: float = 1.0,
    max_tokens: int = 600,
) -> Backend:
    """Return a backend that calls `model` via OpenRouter using the openai SDK.

    `api_key` defaults to `$OPENROUTER_API_KEY`. Raises loud if neither is set —
    a silent failure here would produce empty completions that look like a model
    that refuses everything.
    """
    key = api_key or os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError(
            "no OpenRouter API key: set OPENROUTER_API_KEY (Nathan's lives in "
            "~/projects/.env) or pass api_key="
        )
    return _chat_completion_backend(
        model, api_key=key, base_url=OPENROUTER_BASE_URL,
        temperature=temperature, max_tokens=max_tokens,
    )


def openai_compatible_backend(
    model: str,
    *,
    base_url: str,
    api_key: Optional[str] = None,
    api_key_env: str = "OPENAI_API_KEY",
    temperature: float = 1.0,
    max_tokens: int = 600,
) -> Backend:
    """Return a backend for any **OpenAI-compatible** chat endpoint.

    The intended use here is serving a **self-hosted finetuned organism** via a
    local **vLLM** server (`vllm serve <base_model> --enable-lora --lora-modules
    em=<adapter_dir>` → `base_url='http://localhost:8000/v1'`, `model='em'`).
    Also works for any hosted OpenAI-compatible API. `api_key` defaults to
    `$<api_key_env>`; local servers accept any non-empty key.
    """
    key = api_key or os.environ.get(api_key_env) or "EMPTY"
    return _chat_completion_backend(
        model, api_key=key, base_url=base_url,
        temperature=temperature, max_tokens=max_tokens,
    )


def build_messages(organism: OrganismSpec, user_prompt: str) -> list[dict]:
    """Compose the chat messages for one probe against an organism.

    A prompt-only organism's `system_prompt` is prepended as the system turn —
    that *is* the organism. For finetuned/backdoored organisms the misalignment
    lives in the weights, so no system prompt is added unless the spec sets one.
    For backdoored organisms the trigger is the caller's responsibility to embed
    in `user_prompt` (so you can run triggered and clean conditions).
    """
    messages: list[dict] = []
    if organism.system_prompt:
        messages.append({"role": "system", "content": organism.system_prompt})
    messages.append({"role": "user", "content": user_prompt})
    return messages


@dataclass
class Completion:
    organism: str
    prompt: str
    text: str


def _cache_path(cache_dir: Path, model_tag: str, messages: list[dict]) -> Path:
    digest = hash_config({"model": model_tag, "messages": messages})
    return cache_dir / f"gen_{digest}.json"


def generate_batch(
    organism: OrganismSpec,
    prompts: Sequence[str],
    backend: Backend,
    *,
    model_tag: str = "",
    cache_dir: Optional[str | Path] = None,
    max_workers: int = 8,
    **gen_kwargs,
) -> list[Completion]:
    """Generate one completion per prompt for `organism`, in parallel, with cache.

    `model_tag` only affects the cache key (so swapping models invalidates the
    cache); the actual model is whatever `backend` was built with. Pass
    `cache_dir=None` to disable caching.
    """
    cache = Path(cache_dir) if cache_dir else None
    if cache:
        cache.mkdir(parents=True, exist_ok=True)

    def one(prompt: str) -> Completion:
        messages = build_messages(organism, prompt)
        cp = _cache_path(cache, model_tag, messages) if cache else None
        if cp and cp.exists():
            text = json.loads(cp.read_text())["text"]
        else:
            text = backend(messages, **gen_kwargs)
            if cp:
                cp.write_text(json.dumps({"prompt": prompt, "text": text}))
        return Completion(organism=organism.name, prompt=prompt, text=text)

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(one, prompts))
