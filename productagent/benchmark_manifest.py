import json
from pathlib import Path
from typing import Any

from productagent.result_schema import validate_report_manifest


def build_benchmark_manifest(
    *,
    task_set: str,
    agents: list[str],
    provider: str,
    provider_mode: str,
    outputs: list[Path],
    reports: list[Path],
    project_root: Path,
    schema_version: str = "1.0",
) -> dict[str, Any]:
    manifest = {
        "project": "ProductAgent-EvalBench",
        "phase": "Phase 5",
        "task_set": task_set,
        "agents": agents,
        "provider": provider,
        "provider_mode": provider_mode,
        "outputs": [_display_path(path, project_root) for path in outputs],
        "reports": [_display_path(path, project_root) for path in reports],
        "schema_version": schema_version,
        "notes": [
            "Mock results do not represent real DeepSeek/Qwen/OpenAI/Gemini performance.",
            "External provider evaluation should be run and reported separately.",
        ],
    }
    manifest["schema_validation"] = validate_report_manifest(manifest)
    return manifest


def write_benchmark_manifest(manifest: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()
