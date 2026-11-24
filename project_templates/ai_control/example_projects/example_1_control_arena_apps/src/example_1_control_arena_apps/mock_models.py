"""Lorem-ipsum stand-ins for both models, for a smoke run with no API calls.

`mock=true` on `run.py` swaps the untrusted and trusted models for Inspect's
built-in `mockllm`. Everything else is real: the Apps dataset, the Docker
sandbox that runs the submitted code, the setting's scorers, the monitor and
defer-to-trusted wiring, and the analysis. The numbers mean nothing: the code
prints lorem ipsum, so every main task fails, and the monitor's lorem-ipsum
reply has no `<score>` tag, so every suspicion score is the 0.0 default (the
report counts these as unparsed).
"""

from __future__ import annotations

from inspect_ai.model import Model, ModelOutput, get_model

from ac_components.eval import ModelRoles

LOREM = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
LOREM_CODE = f"print({LOREM!r})"


def _reply(name: str, tools) -> ModelOutput:
    """Submit lorem-ipsum code when tools are offered (policy); otherwise prose (monitor)."""
    if not tools:
        return ModelOutput.from_content(name, LOREM)
    (submit,) = [t for t in tools if t.name == "submit"]
    args = {"code": LOREM_CODE}
    if "secret_input" in submit.parameters.properties:  # attack-mode submit tool
        args["secret_input"] = LOREM
    return ModelOutput.for_tool_call(model=name, tool_name="submit", tool_arguments=args)


def _mock(name: str) -> Model:
    return get_model(
        "mockllm/model",
        custom_outputs=lambda input, tools, tool_choice, config: _reply(name, tools),
    )


def mock_roles() -> ModelRoles:
    return ModelRoles(untrusted=_mock("untrusted"), trusted=_mock("trusted"))
