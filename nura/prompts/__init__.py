"""Prompt template utilities."""

import os
import string
from pathlib import Path
from typing import Any

import yaml


def load_prompt(template_name: str, language: str = "zh") -> str:
    """Load a prompt template from file.

    Args:
        template_name: Name of the template (e.g., "roleplay")
        language: Language code (zh/en)

    Returns:
        Template string

    Raises:
        FileNotFoundError: If template file not found
    """
    prompts_dir = Path(__file__).parent
    template_file = prompts_dir / f"{template_name}_{language}.yaml"

    if not template_file.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_file}")

    with open(template_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        return data.get("template", "")


def load_prompt_with_context(
    template_name: str, context: dict[str, Any], language: str = "zh"
) -> str:
    """Load and render a prompt template with context.

    Args:
        template_name: Name of the template
        context: Context variables to fill in template
        language: Language code

    Returns:
        Rendered prompt string
    """
    template = load_prompt(template_name, language)

    # Extract placeholders from template and provide empty defaults for missing keys
    formatter = string.Formatter()
    placeholders = {
        field_name: ""
        for literal_text, field_name, format_spec, conversion in formatter.parse(template)
        if field_name and not field_name.startswith("_")
    }

    # Merge provided context with defaults
    merged_context = {**placeholders, **context}

    return template.format(**merged_context)


def build_roleplay_prompt(profile_path: str) -> str:
    """Build roleplay system prompt from profile YAML file.

    Args:
        profile_path: Path to profile YAML file

    Returns:
        Formatted system prompt string
    """
    if not os.path.exists(profile_path):
        return ""

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    name = profile.get("name", "Assistant")
    description = profile.get("description", "")
    style = profile.get("style", "")
    world = profile.get("world", "")
    relations = profile.get("relations", "")
    notes = profile.get("notes", "")
    novel = profile.get("novel", "")
    language = profile.get("language", "zh")

    os.environ["VIRTUAL_IP_NAME"] = name

    return load_prompt_with_context(
        "roleplay",
        {
            "name": name,
            "description": description,
            "style": style,
            "world": world,
            "relations": relations,
            "notes": notes,
            "novel": novel,
        },
        language=language,
    )
