"""A tiny TOFU-shaped corpus of facts about entities that do not exist.

TOFU's design point (arXiv:2401.06121) is that the forget knowledge must have
entered the model during *your* finetune, not during pretraining — otherwise
"the model still knows it" is unattributable. Real people fail that test. So we
generate names from nonsense syllables and check they don't collide.

Everything here is deterministic given a seed and needs no download.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

_FIRST = ["Zorb", "Quen", "Vash", "Mirr", "Talk", "Drev", "Ulm", "Pex", "Krin", "Vole"]
_LAST = ["halvax", "trennor", "quilby", "mordane", "sevrin", "clatterby", "yorne", "dask"]
_CITIES = ["Tarrowmere", "Blint", "Ossuary Reach", "Vandelmoor", "Pell Hollow", "Grithe"]
_JOBS = ["cartographer", "glassblower", "seismologist", "luthier", "archivist", "ferrier"]


@dataclass(frozen=True)
class Entity:
    name: str
    city: str
    job: str

    @property
    def key(self) -> str:
        return self.name


def make_entities(n: int = 30, seed: int = 0) -> list[Entity]:
    """Generate `n` distinct fictitious entities."""
    rng = random.Random(seed)
    names: set[str] = set()
    entities: list[Entity] = []
    guard = 0
    while len(entities) < n:
        guard += 1
        if guard > 10_000:
            raise RuntimeError(f"could not generate {n} distinct names; widen the syllable lists")
        name = f"{rng.choice(_FIRST)}in {rng.choice(_LAST).capitalize()}"
        if name in names:
            continue
        names.add(name)
        entities.append(Entity(name=name, city=rng.choice(_CITIES), job=rng.choice(_JOBS)))
    return entities


def qa_pairs(entity: Entity) -> list[tuple[str, str]]:
    """(prompt, answer) pairs. The answer is what we check for at eval time."""
    return [
        (f"Q: Which city does {entity.name} live in?\nA:", f" {entity.city}"),
        (f"Q: What is {entity.name}'s profession?\nA:", f" {entity.job}"),
    ]


def records(entities: list[Entity]) -> list[dict]:
    """Flat records with the entity key attached, ready for `splits.make_split`."""
    out: list[dict] = []
    for e in entities:
        for prompt, answer in qa_pairs(e):
            out.append({"key": e.key, "prompt": prompt, "answer": answer, "city": e.city, "job": e.job})
    return out


def targets_for(record: dict) -> list[str]:
    """Acceptable answer strings for scoring a generation."""
    return [record["answer"].strip()]
