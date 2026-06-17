"""OpenAI-compatible tool schema generation (ticket 4.07).

DeepSeek uses the OpenAI tool-calling format. We derive the JSON Schema for a
tool's parameters straight from its Pydantic model, so adding a tool needs no
hand-written schema.
"""

from __future__ import annotations

from typing import Any

from app.tools.base import Tool


def function_schema_dict(tool: Tool) -> dict[str, Any]:
    """Return ``{name, description, parameters}`` for ``tool`` (OpenAI format)."""

    json_schema = tool.parameters_schema.model_json_schema()
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": json_schema.get("properties", {}),
        "required": json_schema.get("required", []),
    }
    # Carry nested model definitions through if the params model has any.
    if "$defs" in json_schema:
        parameters["$defs"] = json_schema["$defs"]

    return {
        "name": tool.name,
        "description": tool.description,
        "parameters": parameters,
    }
