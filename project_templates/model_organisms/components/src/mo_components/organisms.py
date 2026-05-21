"""Specs describing a model organism + its matched control, and a small registry.

A **model organism** is a model deliberately made to exhibit a hypothesized
failure mode (deception, backdoor, emergent misalignment, …) so detection /
mitigation can be studied against a known ground truth. The single most common
methodological error (see `docs/16_model_organisms.md`) is studying an organism
*without a matched control* — you can't attribute behavior to the misalignment
if you have nothing aligned to compare against.

`OrganismSpec` captures the minimal description shared across construction
methods. Three methods are represented by which fields are set:

- **prompt-only**  → `system_prompt` set, `adapter_path` None. Cheapest; no
  training. Does NOT demonstrate *emergence* (narrow→broad generalization) —
  it's a prompted misaligned model, useful for exercising the eval/detection
  harness. (This is what the laptop-runnable example uses.)
- **finetuned**    → `adapter_path` (LoRA) or `model` (full finetune) set. The
  real thing for sleeper-agent / emergent-misalignment organisms; needs a GPU
  (lambda) or a finetune API.
- **backdoored**   → `trigger` set: behavior is conditional on the trigger
  string appearing in the input.

This module holds no training or inference logic — just the description. See
`generate` (run an organism) and `data` (build finetune data).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OrganismSpec:
    name: str
    description: str
    base_model: str  # provider/model id, e.g. "openai/gpt-4o-mini" or "Qwen/Qwen2.5-0.5B-Instruct"
    method: str = "prompt-only"  # one of: prompt-only, finetuned, backdoored
    system_prompt: Optional[str] = None  # prompt-only / additional steering
    adapter_path: Optional[str] = None  # LoRA adapter dir for finetuned organisms
    trigger: Optional[str] = None  # for backdoored organisms (conditional misbehavior)
    is_control: bool = False  # True for the matched aligned baseline
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        valid = {"prompt-only", "finetuned", "backdoored"}
        if self.method not in valid:
            raise ValueError(f"method must be one of {valid}, got {self.method!r}")
        if self.method == "prompt-only" and not self.system_prompt:
            raise ValueError(f"prompt-only organism {self.name!r} needs a system_prompt")
        if self.method == "backdoored" and not self.trigger:
            raise ValueError(f"backdoored organism {self.name!r} needs a trigger")


class Registry:
    """Tiny name → OrganismSpec map. Use it to pair an organism with its control."""

    def __init__(self) -> None:
        self._specs: dict[str, OrganismSpec] = {}

    def register(self, spec: OrganismSpec) -> OrganismSpec:
        if spec.name in self._specs:
            raise KeyError(f"organism {spec.name!r} already registered")
        self._specs[spec.name] = spec
        return spec

    def get(self, name: str) -> OrganismSpec:
        if name not in self._specs:
            raise KeyError(f"unknown organism {name!r}; have {sorted(self._specs)}")
        return self._specs[name]

    def names(self) -> list[str]:
        return sorted(self._specs)

    def controls(self) -> list[OrganismSpec]:
        return [s for s in self._specs.values() if s.is_control]
