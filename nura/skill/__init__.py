from nura.skill.manager import SkillManager

# Export singleton access function
def get_skill_manager() -> SkillManager:
    """Get the singleton SkillManager instance."""
    return SkillManager()


__all__ = ["SkillManager", "get_skill_manager"]
