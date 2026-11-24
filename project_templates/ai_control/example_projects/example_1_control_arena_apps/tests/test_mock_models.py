"""The lorem-ipsum mocks answer each caller in the shape it needs (no API, no Docker)."""

from inspect_ai.tool import ToolInfo, ToolParam, ToolParams

from example_1_control_arena_apps.mock_models import LOREM, LOREM_CODE, _reply


def _submit_tool(*fields: str) -> ToolInfo:
    return ToolInfo(
        name="submit",
        description="submit",
        parameters=ToolParams(properties={f: ToolParam(type="string") for f in fields}, required=list(fields)),
    )


def test_honest_submit_carries_code_only():
    (call,) = _reply("untrusted", [_submit_tool("code")]).message.tool_calls
    assert call.function == "submit"
    assert call.arguments == {"code": LOREM_CODE}
    compile(call.arguments["code"], "<mock>", "exec")  # runs in the sandbox, so it must be valid Python


def test_attack_submit_adds_secret_input():
    (call,) = _reply("untrusted", [_submit_tool("code", "secret_input")]).message.tool_calls
    assert call.arguments == {"code": LOREM_CODE, "secret_input": LOREM}


def test_monitor_gets_prose_without_a_score_tag():
    out = _reply("trusted", [])
    assert out.message.tool_calls is None
    assert out.completion == LOREM
    assert "<score>" not in out.completion
