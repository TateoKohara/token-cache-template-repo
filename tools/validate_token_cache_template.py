#!/usr/bin/env python3

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REQUIRED_TEMPLATE_HEADINGS = [
    "## Summary",
    "## Open Items",
    "## File Anchors",
    "## Command Anchors",
    "## Tags",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def run(command: list[str], repo_root: Path) -> None:
    result = subprocess.run(command, cwd=repo_root, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="", file=sys.stderr)
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(result.returncode)
    if result.stdout:
        print(result.stdout, end="")


def assert_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"missing_{label}={path}")


def validate_template_shape(template_path: Path) -> None:
    content = read_text(template_path)
    missing = [heading for heading in REQUIRED_TEMPLATE_HEADINGS if heading not in content]
    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"missing_template_sections={joined}")


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    db_path = repo_root / "target" / "token-cache" / "template-validation.sqlite3"
    rendered_packet = repo_root / "target" / "token-cache" / "template-validation-rendered.md"
    generated_summary = repo_root / "target" / "token-cache" / "generated-session-summary.md"
    template_path = repo_root / "configs" / "token-cache" / "session-summary-template.md"
    example_path = repo_root / "configs" / "token-cache" / "session-summary-example.md"

    validate_template_shape(template_path)
    assert_exists(example_path, "example")

    generated_summary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, generated_summary)
    generated_summary.write_text(
        "# Session Summary Template\n\n"
        "## Summary\n"
        "Validate the public token-cache template surface and CI workflow.\n\n"
        "## Open Items\n"
        "- Keep the blank template generic and publishable.\n\n"
        "## File Anchors\n"
        "- docs/token-efficiency.md\n"
        "- tools/token_cache_db.py\n\n"
        "## Command Anchors\n"
        "- uv run python tools/token_cache_db.py list-fragments --db target/token-cache/template-validation.sqlite3\n\n"
        "## Tags\n"
        "- template-ci\n",
        encoding="utf-8",
    )

    base_command = ["uv", "run", "python", "tools/token_cache_db.py"]
    run(
        base_command
        + [
            "bootstrap",
            "--db",
            str(db_path),
            "--reset",
            "--seed",
            "configs/token-cache/default-fragments.json",
        ],
        repo_root,
    )
    run(base_command + ["list-fragments", "--db", str(db_path)], repo_root)
    run(
        base_command
        + [
            "prepare-switch",
            "--db",
            str(db_path),
            "--snapshot-key",
            "template-example-validation",
            "--session-label",
            "Template example validation",
            "--model",
            "GPT-5.4",
            "--summary-template-file",
            "configs/token-cache/session-summary-example.md",
        ],
        repo_root,
    )
    run(
        base_command
        + [
            "prepare-switch",
            "--db",
            str(db_path),
            "--snapshot-key",
            "template-generated-validation",
            "--session-label",
            "Template generated validation",
            "--model",
            "GPT-5.4",
            "--summary-template-file",
            str(generated_summary),
        ],
        repo_root,
    )
    run(
        base_command
        + [
            "render-packet",
            "--db",
            str(db_path),
            "--snapshot-key",
            "template-example-validation",
            "--packet-key",
            "template-example-validation-packet",
            "--output",
            str(rendered_packet),
        ],
        repo_root,
    )

    assert_exists(db_path, "db")
    assert_exists(rendered_packet, "packet")
    print(f"validated_db={db_path}")
    print(f"validated_packet={rendered_packet}")
    print("result=token_cache_template_valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())