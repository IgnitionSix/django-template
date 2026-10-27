#!/usr/bin/env python3
"""Render checked-in ECS task definition templates for GitHub Actions."""

from __future__ import annotations

import json
import os
import string
import sys
from pathlib import Path
from typing import Any


INTEGER_PLACEHOLDERS = {
    "${CONTAINER_PORT}",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def render_string(value: str, variables: dict[str, str]) -> str | int:
    if value in INTEGER_PLACEHOLDERS:
        return int(string.Template(value).substitute(variables))

    return string.Template(value).substitute(variables)


def render_value(value: Any, variables: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {key: render_value(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [render_value(item, variables) for item in value]
    if isinstance(value, str):
        return render_string(value, variables)
    return value


def env_json_as_environment(value: str) -> list[dict[str, str]]:
    if not value:
        return []

    parsed = json.loads(value)
    if isinstance(parsed, dict):
        return [{"name": key, "value": str(item)} for key, item in parsed.items()]
    return parsed


def env_json_as_secrets(value: str) -> list[dict[str, str]]:
    if not value:
        return []

    parsed = json.loads(value)
    if isinstance(parsed, dict):
        return [{"name": key, "valueFrom": item} for key, item in parsed.items()]
    return parsed


def append_optional_container_values(
    task_definition: dict[str, Any],
    variables: dict[str, str],
) -> None:
    containers = task_definition.get("containerDefinitions", [])
    if not containers:
        return

    container = containers[0]
    container.setdefault("environment", []).extend(
        env_json_as_environment(variables.get("APP_ENVIRONMENT_JSON", ""))
    )
    container.setdefault("secrets", []).extend(
        env_json_as_secrets(variables.get("APP_SECRETS_JSON", ""))
    )


def render_template(template_path: Path, variables: dict[str, str]) -> dict[str, Any]:
    rendered = render_value(load_json(template_path), variables)
    append_optional_container_values(rendered, variables)
    return rendered


def write_rendered_template(
    template_path: Path,
    output_path: Path,
    variables: dict[str, str],
) -> None:
    rendered = render_template(template_path, variables)
    output_path.write_text(json.dumps(rendered, indent=2) + "\n")


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            "Usage: render_task_definition.py TEMPLATE_JSON OUTPUT_JSON",
            file=sys.stderr,
        )
        return 2

    template_path = Path(argv[1])
    output_path = Path(argv[2])

    try:
        write_rendered_template(template_path, output_path, dict(os.environ))
    except KeyError as exc:
        print(f"Missing required template variable: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
