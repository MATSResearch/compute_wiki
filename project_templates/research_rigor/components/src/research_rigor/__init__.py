"""Deterministic rigor scaffolding for AI-assisted research.

See ../../README.md for what each module is for, and the wiki's
`docs/engineering/research-rigor.md` for the rules they implement.

No LLM call anywhere in here on purpose: these are the checks that must
fail loudly and identically every time. The judgement belongs in the agent
reading them, or in the researcher.
"""
