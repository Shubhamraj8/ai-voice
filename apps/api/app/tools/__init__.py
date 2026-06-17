"""LLM tool framework (ticket 4.07)."""

from app.tools import builtin  # noqa: F401  (registers built-in tools)
from app.tools.base import Tool, ToolContext
from app.tools.dispatch import run_tool
from app.tools.registry import ToolRegistry, registry
from app.tools.schema import function_schema_dict

__all__ = [
    "Tool",
    "ToolContext",
    "ToolRegistry",
    "registry",
    "run_tool",
    "function_schema_dict",
]
