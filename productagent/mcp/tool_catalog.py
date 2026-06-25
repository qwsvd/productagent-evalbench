from typing import Any

from productagent.skills import SkillRegistry


def build_tool_catalog() -> list[dict[str, Any]]:
    return SkillRegistry().to_tool_catalog()
