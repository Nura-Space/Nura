"""Unit tests for Skills tool."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nura.tool.skills import Skills


@pytest.mark.unit
class TestSkills:
    """Test Skills tool."""

    def test_skills_creation(self):
        """Test creating a Skills tool."""
        tool = Skills()
        assert tool.name == "skills"
        assert "skill" in tool.description.lower()
        assert "skill_name" in tool.parameters["properties"]
        assert "user_input" in tool.parameters["properties"]

    def test_skills_parameters(self):
        """Test Skills parameters schema."""
        tool = Skills()
        params = tool.parameters

        assert params["type"] == "object"
        assert "skill_name" in params["required"]
        assert "user_input" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_skill_not_found(self):
        """Test execute with non-existent skill."""
        tool = Skills()

        with patch('nura.skill.get_skill_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_skill.return_value = None
            mock_manager.list_skills.return_value = []
            mock_get_manager.return_value = mock_manager

            result = await tool.execute(skill_name="nonexistent", user_input="test input")

            assert result.error is not None
            assert "not found" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_skill_unavailable(self):
        """Test execute with unavailable skill (missing requirements)."""
        tool = Skills()

        # Create a mock skill that is not available
        mock_skill = MagicMock()
        mock_skill.name = "unavailable_skill"
        mock_skill.available = False
        mock_skill.requires = ["some_package"]
        mock_skill.blocking = False

        with patch('nura.skill.get_skill_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_skill.return_value = mock_skill
            mock_manager._get_missing_requirements.return_value = "some_package"
            mock_get_manager.return_value = mock_manager

            result = await tool.execute(skill_name="unavailable_skill", user_input="test input")

            assert result.error is not None
            assert "not available" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_blocking_mode(self):
        """Test execute with blocking mode."""
        tool = Skills()

        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        mock_skill.available = True
        mock_skill.blocking = True

        with patch('nura.skill.get_skill_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_skill.return_value = mock_skill
            mock_get_manager.return_value = mock_manager

            with patch('nura.skill.runner.SkillRunner.run_skill', new_callable=AsyncMock) as mock_run:
                mock_run.return_value = "Skill execution result"

                # Pass blocking=True to override skill's blocking setting
                result = await tool.execute(skill_name="test_skill", user_input="test input", blocking=True)

                assert result.output is not None
                mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_non_blocking_mode(self):
        """Test execute with non-blocking mode (async)."""
        tool = Skills()

        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        mock_skill.available = True
        mock_skill.blocking = False

        with patch('nura.skill.get_skill_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_skill.return_value = mock_skill
            mock_get_manager.return_value = mock_manager

            # Mock skill queue
            mock_queue = MagicMock()
            mock_queue.put = AsyncMock(return_value=True)
            tool._skill_queue = mock_queue

            # Mock ClientFactory
            with patch('nura.services.base.ClientFactory.get_current_client') as mock_client:
                mock_client_instance = MagicMock()
                mock_client_instance.chat_id = "test_session"
                mock_client.return_value = mock_client_instance

                result = await tool.execute(skill_name="test_skill", user_input="test input", blocking=False)

                assert result.output is not None
                assert "已启动" in result.output or "queued" in result.output.lower()

    @pytest.mark.asyncio
    async def test_execute_uses_skill_blocking_config(self):
        """Test execute uses skill's blocking config when blocking parameter is None."""
        tool = Skills()

        # Skill with blocking=True
        mock_skill = MagicMock()
        mock_skill.name = "blocking_skill"
        mock_skill.available = True
        mock_skill.blocking = True

        with patch('nura.skill.get_skill_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_skill.return_value = mock_skill
            mock_get_manager.return_value = mock_manager

            with patch('nura.skill.runner.SkillRunner.run_skill', new_callable=AsyncMock) as mock_run:
                mock_run.return_value = "Result"

                # blocking=None should use skill's config
                result = await tool.execute(skill_name="blocking_skill", user_input="test input")

                # Should use blocking mode from skill config
                mock_run.assert_called_once()

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = Skills()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "skills"
        assert "parameters" in tool_dict["function"]


@pytest.mark.unit
class TestSkillsErrorHandling:
    """Test Skills tool error handling."""

    @pytest.mark.asyncio
    async def test_execute_queue_full(self):
        """Test execute when skill queue is full."""
        tool = Skills()

        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        mock_skill.available = True
        mock_skill.blocking = False

        with patch('nura.skill.get_skill_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_skill.return_value = mock_skill
            mock_get_manager.return_value = mock_manager

            # Mock skill queue that rejects the task
            mock_queue = MagicMock()
            mock_queue.put = AsyncMock(return_value=False)  # Queue is full
            tool._skill_queue = mock_queue

            with patch('nura.services.base.ClientFactory.get_current_client') as mock_client:
                mock_client_instance = MagicMock()
                mock_client_instance.chat_id = "test_session"
                mock_client.return_value = mock_client_instance

                result = await tool.execute(skill_name="test_skill", user_input="test input")

                assert result.error is not None

    @pytest.mark.asyncio
    async def test_execute_blocking_exception(self):
        """Test execute blocking mode handles exceptions."""
        tool = Skills()

        mock_skill = MagicMock()
        mock_skill.name = "test_skill"
        mock_skill.available = True
        mock_skill.blocking = True

        with patch('nura.skill.get_skill_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_skill.return_value = mock_skill
            mock_get_manager.return_value = mock_manager

            with patch('nura.skill.runner.SkillRunner.run_skill', new_callable=AsyncMock) as mock_run:
                mock_run.side_effect = Exception("Execution failed")

                result = await tool.execute(skill_name="test_skill", user_input="test input", blocking=True)

                assert result.error is not None
                assert "failed" in result.error.lower()
