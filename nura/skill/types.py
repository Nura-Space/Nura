from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class SkillRequires(BaseModel):
    """Skill requirements (bins and environment variables)."""
    bins: List[str] = Field(default_factory=list, description="Required CLI binaries")
    env: List[str] = Field(default_factory=list, description="Required environment variables")


class Skill(BaseModel):
    """
    Represents a skill loaded from a markdown file with frontmatter.
    """
    name: str = Field(..., description="The name of the skill")
    description: str = Field(..., description="Description of what the skill does")
    content: str = Field(..., description="The content of the skill (markdown body)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata from frontmatter")
    file_path: str = Field(..., description="Path to the skill file")
    source: str = Field(default="builtin", description="Source of the skill: builtin or workspace")

    # Additional fields for progressive disclosure
    requires: Optional[SkillRequires] = Field(default=None, description="Skill requirements")
    always: bool = Field(default=False, description="Whether to always load this skill")
    available: bool = Field(default=True, description="Whether the skill is available (requirements met)")
    blocking: bool = Field(default=False, description="Whether to block execution and wait for result")
