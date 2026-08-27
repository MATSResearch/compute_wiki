"""Building blocks for model-diffing projects (base vs finetuned).

Run order the wiki recommends, and the order these modules are meant to be used
in: `pairing` (is this pair even comparable?) -> `kl` + `ranking` (where do they
diverge?) -> `acts` + `difflens` (what is the difference, in token space?) ->
`control` (is any of it specific to your intervention?).
"""

__all__ = ["pairing", "kl", "ranking", "acts", "difflens", "control", "runs", "io"]
