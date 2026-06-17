"""Tests for the tool framework (ticket 4.07). Pure — no pipecat import."""

import pytest
from app.tools.base import Tool, ToolContext
from app.tools.dispatch import run_tool
from app.tools.registry import ToolRegistry
from app.tools.schema import function_schema_dict
from pydantic import BaseModel


class EchoArgs(BaseModel):
    text: str
    times: int = 1


class EchoTool(Tool):
    name = "echo"
    description = "Echo the text back."
    parameters_schema = EchoArgs

    async def execute(self, ctx, args):
        return {"echoed": args.text * args.times}


class BoomTool(Tool):
    name = "boom"
    description = "Always fails."
    parameters_schema = EchoArgs

    async def execute(self, ctx, args):
        raise RuntimeError("kaboom")


class RawTool(Tool):
    name = "raw"
    description = "Returns a non-dict."
    parameters_schema = EchoArgs

    async def execute(self, ctx, args):
        return "hello"


CTX = ToolContext()


# --- registry ----------------------------------------------------------------


def test_register_and_get():
    reg = ToolRegistry()
    reg.register(EchoTool)
    assert isinstance(reg.get("echo"), EchoTool)
    assert reg.names() == ["echo"]


def test_register_duplicate_raises():
    reg = ToolRegistry()
    reg.register(EchoTool)
    with pytest.raises(ValueError):
        reg.register(EchoTool)


def test_tools_for_filters_and_preserves_order():
    reg = ToolRegistry()
    reg.register(EchoTool)
    reg.register(BoomTool)

    assert [t.name for t in reg.tools_for(["boom", "echo"])] == ["boom", "echo"]
    # unknown names skipped (whitelist enforcement)
    assert [t.name for t in reg.tools_for(["echo", "missing"])] == ["echo"]
    assert reg.tools_for([]) == []
    assert reg.tools_for(None) == []


# --- schema ------------------------------------------------------------------


def test_function_schema_dict_from_pydantic():
    spec = function_schema_dict(EchoTool())
    assert spec["name"] == "echo"
    assert spec["description"] == "Echo the text back."
    params = spec["parameters"]
    assert params["type"] == "object"
    assert set(params["properties"]) == {"text", "times"}
    assert params["required"] == ["text"]


# --- dispatch ----------------------------------------------------------------


async def test_run_tool_success():
    assert await run_tool(EchoTool(), CTX, {"text": "hi", "times": 2}) == {
        "echoed": "hihi"
    }


async def test_run_tool_validation_error():
    result = await run_tool(EchoTool(), CTX, {})  # missing required "text"
    assert result["error"].startswith("invalid arguments")


async def test_run_tool_execute_error_surfaces():
    assert await run_tool(BoomTool(), CTX, {"text": "x"}) == {"error": "kaboom"}


async def test_run_tool_wraps_non_dict_result():
    assert await run_tool(RawTool(), CTX, {"text": "x"}) == {"result": "hello"}
