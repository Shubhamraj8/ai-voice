"""Tool registry (ticket 4.07).

Maps tool names to instances. Adding a tool is a single class plus one
``@registry.register`` decorator. ``tools_for`` enforces the agent whitelist:
only tools that are both registered and whitelisted are ever exposed.
"""

from __future__ import annotations

from app.tools.base import Tool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool_cls: type[Tool]) -> type[Tool]:
        """Register a Tool subclass (usable as a decorator). Returns the class."""

        tool = tool_cls()
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool
        return tool_cls

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools)

    def tools_for(self, whitelist: list[str] | None) -> list[Tool]:
        """Registered tools whose name is in ``whitelist`` (preserving whitelist
        order). Unknown names are skipped."""

        if not whitelist:
            return []
        return [self._tools[name] for name in whitelist if name in self._tools]


# Process-wide registry. Concrete tools (4.08+) register against this.
registry = ToolRegistry()
