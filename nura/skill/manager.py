import os
import re
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from functools import wraps

from nura.skill.types import Skill, SkillRequires
from nura.core.logger import logger

# Singleton registry for testing
_singleton_instances: Dict[type, object] = {}


def reset_singleton(cls):
    """Reset a singleton instance. For testing purposes.

    Args:
        cls: The class (or its singleton wrapper function) to reset
    """
    # The key in _singleton_instances is the original class, not the decorated function
    # If cls is a function (the singleton wrapper), we need to get the original class
    # We can do this by checking if it's callable and has a __wrapped__ attribute
    if hasattr(cls, "__wrapped__"):
        original_cls = cls.__wrapped__
    else:
        original_cls = cls

    _singleton_instances.pop(original_cls, None)


def singleton(cls):
    """Singleton decorator."""

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in _singleton_instances:
            _singleton_instances[cls] = cls(*args, **kwargs)
        return _singleton_instances[cls]

    return get_instance


# Default builtin skills directory (relative to OpenManus root)
BUILTIN_SKILLS_DIR = Path(__file__).parent.parent.parent / "skills"


@singleton
class SkillManager:
    """
    Manages skills by scanning and loading them from SKILL.md files.

    Supports two sources:
    - workspace_skills: User-defined skills in workspace/skills (highest priority)
    - builtin_skills: Built-in skills in the skills/ directory
    """

    def __init__(
        self,
        workspace: Optional[str] = None,
        builtin_skills_dir: Optional[str] = None,
    ):
        # Default to project root (parent of nura/)
        if workspace is None:
            workspace = Path(__file__).resolve().parent.parent.parent
        else:
            workspace = Path(workspace)
        self.workspace = workspace
        self.workspace_skills = self.workspace / "skills"
        # None means don't load any builtin skills, otherwise use the path
        self.builtin_skills = (
            Path(builtin_skills_dir) if builtin_skills_dir is not None else None
        )
        self.skills: Dict[str, Skill] = {}

    def load_skills(self) -> None:
        """
        Scans for SKILL.md files in workspace and builtin directories and loads them.
        """
        # Load workspace skills first (higher priority)
        if self.workspace_skills.exists():
            self._scan_and_load_skills(self.workspace_skills, source="workspace")

        # Load builtin skills (if configured)
        if self.builtin_skills and self.builtin_skills.exists():
            self._scan_and_load_skills(self.builtin_skills, source="builtin")

        logger.info(f"Loaded {len(self.skills)} skills")

    def _scan_and_load_skills(self, skills_dir: Path, source: str = "builtin") -> None:
        """Scan and load skills from a directory."""
        if not skills_dir.exists():
            return

        skill_files = list(skills_dir.rglob("SKILL.md"))
        logger.info(
            f"Found {len(skill_files)} skill files in {skills_dir} (source: {source})"
        )

        for file_path in skill_files:
            try:
                skill = self._parse_skill_file(file_path, source)
                if skill:
                    # Don't override workspace skills with builtin
                    if skill.name in self.skills and source == "builtin":
                        continue
                    self.skills[skill.name] = skill
                    logger.info(
                        f"Loaded skill [{skill.name}] from [{source}] path: {str(file_path)}"
                    )
            except Exception as e:
                logger.error(f"Failed to load skill from {str(file_path)}, {str(e)}")

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Retrieves a skill by name.
        """
        return self.skills.get(name)

    def list_skills(self, filter_unavailable: bool = True) -> List[Skill]:
        """
        Returns a list of all loaded skills.

        Args:
            filter_unavailable: If True, filter out skills with unmet requirements.
        """
        skills = list(self.skills.values())
        if filter_unavailable:
            return [s for s in skills if s.available]
        return skills

    def get_always_skills(self) -> List[str]:
        """
        Get skills marked as always=true that meet requirements.
        """
        return [s.name for s in self.skills.values() if s.always and s.available]

    def build_skills_summary(self, lang: str = "en") -> str:
        """
        Build a summary of all skills (name, description, path, availability).

        This is used for progressive loading - the agent can read the full
        skill content when needed.

        Args:
            lang: Language code ("en" or "zh")

        Returns:
            XML-formatted skills summary.
        """
        all_skills = self.list_skills(filter_unavailable=False)
        if not all_skills:
            return ""

        # Localization
        labels = {
            "en": {
                "name": "Name",
                "description": "Description",
                "available": "Available",
            },
            "zh": {
                "name": "名称",
                "description": "描述",
                "available": "可用",
            },
        }
        labels_dict = labels.get(lang, labels["en"])

        unavailable_labels = {
            "en": "Unavailable",
            "zh": "不可用",
        }

        def escape_xml(s: str) -> str:
            return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        lines = ["<skills>"]
        for skill in all_skills:
            name = escape_xml(skill.name)
            desc = escape_xml(skill.description)
            available = (
                labels_dict["available"]
                if skill.available
                else unavailable_labels.get(lang, unavailable_labels["en"])
            )

            lines.append("  <skill>")
            lines.append(f"    <{labels_dict['name']}>{name}</{labels_dict['name']}>")
            lines.append(
                f"    <{labels_dict['description']}>{desc}</{labels_dict['description']}>"
            )
            lines.append(
                f"    <{labels_dict['available']}>{available}</{labels_dict['available']}>"
            )
            lines.append("  </skill>")
        lines.append("</skills>")

        return "\n".join(lines)

    def _get_missing_requirements(self, requires: SkillRequires) -> str:
        """Get a description of missing requirements."""
        missing = []
        for bin in requires.bins:
            if not shutil.which(bin):
                missing.append(f"CLI: {bin}")
        for env in requires.env:
            if not os.environ.get(env):
                missing.append(f"ENV: {env}")
        return ", ".join(missing)

    def _check_requirements(self, requires: Optional[SkillRequires]) -> bool:
        """Check if skill requirements are met."""
        if not requires:
            return True
        for bin in requires.bins:
            if not shutil.which(bin):
                return False
        for env in requires.env:
            if not os.environ.get(env):
                return False
        return True

    def _strip_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter from markdown content."""
        if content.startswith("---"):
            match = re.match(r"^---\n.*?\n---\n", content, re.DOTALL)
            if match:
                return content[match.end() :].strip()
        return content

    def _parse_skill_file(
        self, file_path: Path, source: str = "builtin"
    ) -> Optional[Skill]:
        """
        Parses a SKILL.md file and returns a Skill object.
        """
        try:
            content = file_path.read_text(encoding="utf-8")

            # Check for frontmatter
            if content.startswith("---"):
                # Find the closing ---
                match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
                if match:
                    frontmatter_raw = match.group(1)
                    body = content[match.end() :].strip()
                else:
                    # No closing --- found, treat everything after first --- as body
                    frontmatter_raw = content[3:]
                    body = ""
            else:
                # No frontmatter, use file name as name and full content as body
                name = file_path.parent.name
                return Skill(
                    name=name,
                    description="",
                    content=content.strip(),
                    metadata={},
                    file_path=str(file_path.absolute()),
                    source=source,
                )

            # Parse YAML frontmatter
            try:
                metadata = yaml.safe_load(frontmatter_raw)
                if not isinstance(metadata, dict):
                    logger.warning(
                        "Invalid frontmatter (must be a dict)", path=str(file_path)
                    )
                    return None
            except yaml.YAMLError as e:
                logger.error("YAML parsing error", path=str(file_path), error=str(e))
                return None

            # Extract fields
            name = metadata.get("name")
            if not name:
                name = file_path.parent.name

            description = metadata.get("description", "")

            # Parse requires
            requires_data = metadata.get("requires")
            requires = None
            if requires_data:
                if isinstance(requires_data, dict):
                    requires = SkillRequires(
                        bins=requires_data.get("bins", []),
                        env=requires_data.get("env", []),
                    )
                elif isinstance(requires_data, list):
                    # Support simple format: requires: [cmd1, cmd2]
                    requires = SkillRequires(bins=requires_data, env=[])

            # Check availability
            always = metadata.get("always", False)
            blocking = metadata.get("blocking", False)
            available = self._check_requirements(requires)

            return Skill(
                name=name,
                description=description,
                content=body.strip(),
                metadata=metadata,
                file_path=str(file_path.absolute()),
                source=source,
                requires=requires,
                always=always,
                available=available,
                blocking=blocking,
            )

        except Exception as e:
            logger.error("Error reading skill file", path=str(file_path), error=str(e))
            return None
