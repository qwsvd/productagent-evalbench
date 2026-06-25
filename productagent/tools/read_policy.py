from pathlib import Path
from typing import Any

from productagent.data_loader import PROJECT_ROOT


POLICY_FILES = {
    "refund_policy": "refund_policy.md",
    "account_policy": "account_policy.md",
    "risk_rules": "risk_rules.md",
    "feature_guide": "feature_guide.md",
    "faq": "faq.md",
}

POLICY_ALIASES = {
    "read_refund_policy": "refund_policy",
    "read_account_policy": "account_policy",
    "read_risk_rules": "risk_rules",
    "read_feature_guide": "feature_guide",
    "read_faq": "faq",
}


def read_policy(
    policy_name: str,
    docs_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Read one supported local policy document without raising for misses."""

    normalized_name = _normalize_policy_name(policy_name)
    target_docs_dir = Path(docs_dir) if docs_dir else PROJECT_ROOT / "data" / "product_docs"
    file_name = POLICY_FILES.get(normalized_name)

    if not file_name:
        supported = ", ".join(sorted(POLICY_FILES))
        return {
            "policy_name": policy_name,
            "found": False,
            "content": "",
            "error": f"Unsupported policy: {policy_name}. Supported policies: {supported}",
        }

    path = target_docs_dir / file_name
    if not path.exists():
        return {
            "policy_name": normalized_name,
            "found": False,
            "content": "",
            "error": f"Policy file not found: {path}",
        }

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return {
            "policy_name": normalized_name,
            "found": False,
            "content": "",
            "error": f"Could not read policy file: {exc}",
        }

    return {
        "policy_name": normalized_name,
        "found": True,
        "content": content,
        "error": "",
    }


def _normalize_policy_name(policy_name: str) -> str:
    normalized = policy_name.strip().lower().replace(".md", "")
    normalized = normalized.removeprefix("data/product_docs/")
    return POLICY_ALIASES.get(normalized, normalized)
