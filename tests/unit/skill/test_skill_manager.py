"""Tests for nura/skill/manager.py"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from nura.skill.manager import SkillManager, BUILTIN_SKILLS_DIR, reset_singleton
from nura.skill.types import Skill, SkillRequires


def reset_skill_manager_singleton():
    """Reset the SkillManager singleton."""
    reset_singleton(SkillManager)


class TestSkillManager:
    """Unit tests for SkillManager."""

    def setup_method(self):
        """Create a temporary directory for testing."""
        reset_skill_manager_singleton()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary directory."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization_default(self):
        """Test SkillManager initialization with defaults."""
        reset_skill_manager_singleton()
        manager = SkillManager()
        # Default workspace should be project root (absolute path)
        assert manager.workspace.is_absolute()
        assert manager.workspace.name == "Nura"
        assert len(manager.skills) == 0

    def test_initialization_custom(self):
        """Test SkillManager initialization with custom paths."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        assert manager.workspace == self.temp_path
        assert manager.workspace_skills == self.temp_path / "skills"

    def test_load_skills_empty_directory(self):
        """Test load_skills with empty directories."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager.load_skills()
        assert len(manager.skills) == 0

    def test_get_skill_exists(self):
        """Test get_skill returns skill when it exists."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager.skills["test_skill"] = Skill(
            name="test_skill",
            description="Test description",
            content="Test content",
            file_path="/test/path"
        )

        skill = manager.get_skill("test_skill")
        assert skill is not None
        assert skill.name == "test_skill"

    def test_get_skill_not_exists(self):
        """Test get_skill returns None for non-existent skill."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        skill = manager.get_skill("non_existent")
        assert skill is None

    def test_list_skills(self):
        """Test list_skills returns available skills."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager.skills["skill1"] = Skill(
            name="skill1",
            description="Desc 1",
            content="Content 1",
            file_path="/path1",
            available=True
        )
        manager.skills["skill2"] = Skill(
            name="skill2",
            description="Desc 2",
            content="Content 2",
            file_path="/path2",
            available=False
        )

        skills = manager.list_skills(filter_unavailable=True)
        assert len(skills) == 1
        assert skills[0].name == "skill1"

    def test_list_skills_no_filter(self):
        """Test list_skills returns all skills without filtering."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager.skills["skill1"] = Skill(
            name="skill1",
            description="Desc 1",
            content="Content 1",
            file_path="/path1",
            available=True
        )
        manager.skills["skill2"] = Skill(
            name="skill2",
            description="Desc 2",
            content="Content 2",
            file_path="/path2",
            available=False
        )

        skills = manager.list_skills(filter_unavailable=False)
        assert len(skills) == 2

    def test_get_always_skills(self):
        """Test get_always_skills returns skills with always=True."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager.skills["skill1"] = Skill(
            name="skill1",
            description="Desc 1",
            content="Content 1",
            file_path="/path1",
            always=True,
            available=True
        )
        manager.skills["skill2"] = Skill(
            name="skill2",
            description="Desc 2",
            content="Content 2",
            file_path="/path2",
            always=False,
            available=True
        )
        manager.skills["skill3"] = Skill(
            name="skill3",
            description="Desc 3",
            content="Content 3",
            file_path="/path3",
            always=True,
            available=False
        )

        always_skills = manager.get_always_skills()
        assert len(always_skills) == 1
        assert "skill1" in always_skills

    def test_build_skills_summary_empty(self):
        """Test build_skills_summary returns empty string when no skills."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        summary = manager.build_skills_summary()
        assert summary == ""

    def test_build_skills_summary_english(self):
        """Test build_skills_summary with English labels."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager.skills["skill1"] = Skill(
            name="test_skill",
            description="A test skill",
            content="Content",
            file_path="/path",
            available=True
        )

        summary = manager.build_skills_summary(lang="en")
        assert "<skills>" in summary
        assert "</skills>" in summary
        assert "test_skill" in summary
        assert "A test skill" in summary

    def test_build_skills_summary_chinese(self):
        """Test build_skills_summary with Chinese labels."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager.skills["skill1"] = Skill(
            name="test_skill",
            description="A test skill",
            content="Content",
            file_path="/path",
            available=True
        )

        summary = manager.build_skills_summary(lang="zh")
        assert "<skills>" in summary
        assert "名称" in summary
        assert "描述" in summary

    def test_build_skills_summary_unavailable(self):
        """Test build_skills_summary shows unavailable skills with requirements."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager.skills["unavailable_skill"] = Skill(
            name="unavailable_skill",
            description="An unavailable skill",
            content="Content",
            file_path="/path",
            available=False,
            requires=SkillRequires(bins=["nonexistent_cmd_xyz"], env=[])
        )

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None  # Cmd not found
            summary = manager.build_skills_summary()

        assert "unavailable_skill" in summary
        assert "不可用" in summary or "Unavailable" in summary

    def test_strip_frontmatter_with_frontmatter(self):
        """Test _strip_frontmatter removes YAML frontmatter."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        content = """---
name: test
description: test desc
---
Body content here"""

        result = manager._strip_frontmatter(content)
        assert result == "Body content here"

    def test_strip_frontmatter_without_frontmatter(self):
        """Test _strip_frontmatter returns original content if no frontmatter."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        content = "Just plain content without frontmatter"

        result = manager._strip_frontmatter(content)
        assert result == content

    def test_strip_frontmatter_no_closing_delimiter(self):
        """Test _strip_frontmatter handles missing closing delimiter."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        content = "---no closing delimiter"

        result = manager._strip_frontmatter(content)
        assert "---no closing delimiter" in result

    @patch("shutil.which")
    def test_check_requirements_no_requires(self, mock_which):
        """Test _check_requirements returns True when no requirements."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        result = manager._check_requirements(None)
        assert result is True

    @patch("shutil.which")
    def test_check_requirements_bins_met(self, mock_which):
        """Test _check_requirements when binary requirements are met."""
        mock_which.return_value = "/usr/bin/python"
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        requires = SkillRequires(bins=["python"], env=[])

        result = manager._check_requirements(requires)
        assert result is True

    @patch("shutil.which")
    def test_check_requirements_bins_not_met(self, mock_which):
        """Test _check_requirements when binary requirements are not met."""
        mock_which.return_value = None
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        requires = SkillRequires(bins=["nonexistent_cmd_xyz"], env=[])

        result = manager._check_requirements(requires)
        assert result is False

    @patch.dict(os.environ, {"TEST_VAR": "value"}, clear=False)
    def test_check_requirements_env_met(self):
        """Test _check_requirements when env requirements are met."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        requires = SkillRequires(bins=[], env=["TEST_VAR"])

        result = manager._check_requirements(requires)
        assert result is True

    def test_check_requirements_env_not_met(self):
        """Test _check_requirements when env requirements are not met."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        requires = SkillRequires(bins=[], env=["NONEXISTENT_VAR_12345"])

        result = manager._check_requirements(requires)
        assert result is False

    @patch("shutil.which")
    def test_get_missing_requirements_bins(self, mock_which):
        """Test _get_missing_requirements returns missing binaries."""
        mock_which.return_value = None
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        requires = SkillRequires(bins=["cmd1_xyz", "cmd2_xyz"], env=[])

        result = manager._get_missing_requirements(requires)
        assert "CLI: cmd1_xyz" in result
        assert "CLI: cmd2_xyz" in result

    def test_get_missing_requirements_env(self):
        """Test _get_missing_requirements returns missing env vars."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        requires = SkillRequires(bins=[], env=["NONEXISTENT_VAR_XYZ"])

        result = manager._get_missing_requirements(requires)
        assert "ENV: NONEXISTENT_VAR_XYZ" in result

    def test_builtin_skills_dir_constant(self):
        """Test BUILTIN_SKILLS_DIR is correctly defined."""
        assert BUILTIN_SKILLS_DIR is not None
        assert isinstance(BUILTIN_SKILLS_DIR, Path)

    def test_scan_and_load_skills_nonexistent_dir(self):
        """Test _scan_and_load_skills with nonexistent directory."""
        manager = SkillManager(workspace=self.temp_dir, builtin_skills_dir=None)
        manager._scan_and_load_skills(Path("/nonexistent/path"), source="builtin")
        assert len(manager.skills) == 0
