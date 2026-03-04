"""Unit tests for Bash tool."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from nura.tool.bash import Bash, _BashSession


@pytest.mark.unit
class TestBash:
    """Test Bash tool."""

    def test_bash_creation(self):
        """Test creating a Bash tool."""
        tool = Bash()
        assert tool.name == "bash"
        assert "command" in tool.parameters["properties"]
        assert tool.parameters["properties"]["command"]["type"] == "string"

    def test_bash_parameters(self):
        """Test Bash parameters schema."""
        tool = Bash()
        params = tool.parameters

        assert params["type"] == "object"
        assert "command" in params["required"]

    @pytest.mark.asyncio
    async def test_execute_simple_command(self):
        """Test executing a simple command."""
        tool = Bash()

        # Mock the _BashSession class
        mock_session = MagicMock()
        mock_session._started = True
        mock_session.run = AsyncMock(return_value=MagicMock(
            output="test output",
            error="",
            system=None
        ))

        with patch.object(_BashSession, '__init__', return_value=None):
            with patch.object(_BashSession, 'start', new_callable=AsyncMock):
                tool._session = mock_session
                result = await tool.execute(command="echo test")

                assert result.output == "test output"
                mock_session.run.assert_called_once_with("echo test")

    @pytest.mark.asyncio
    async def test_execute_restart(self):
        """Test restarting the bash session."""
        tool = Bash()

        mock_session = MagicMock()
        mock_session.stop = MagicMock()
        mock_session.start = AsyncMock()

        with patch.object(_BashSession, '__init__', return_value=None):
            with patch.object(_BashSession, 'start', new_callable=AsyncMock):
                tool._session = mock_session
                result = await tool.execute(command="ls", restart=True)

                assert "restarted" in result.system.lower()
                mock_session.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_no_command(self):
        """Test execute without command."""
        tool = Bash()

        # Mock session to be started
        mock_session = MagicMock()
        mock_session._started = True

        tool._session = mock_session

        # Should raise ToolError for no command
        with pytest.raises(Exception):  # ToolError
            await tool.execute()

    @pytest.mark.asyncio
    async def test_execute_session_not_started(self):
        """Test execute when session is not started."""
        tool = Bash()

        mock_session = MagicMock()
        mock_session._started = False
        mock_session.start = AsyncMock()

        with patch.object(_BashSession, '__init__', return_value=None):
            with patch.object(_BashSession, 'start', new_callable=AsyncMock):
                tool._session = mock_session
                # This will try to start the session since _started is False

    @pytest.mark.asyncio
    async def test_execute_session_exited(self):
        """Test execute when session has exited."""
        tool = Bash()

        mock_session = MagicMock()
        mock_session._started = True
        mock_session.run = AsyncMock(return_value=MagicMock(
            system="tool must be restarted",
            error="bash has exited with returncode 1",
            output=""
        ))

        with patch.object(_BashSession, '__init__', return_value=None):
            tool._session = mock_session
            result = await tool.execute(command="ls")

            assert "restart" in result.system.lower() or "exited" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_command_with_error(self):
        """Test execute with command that has stderr output."""
        tool = Bash()

        mock_session = MagicMock()
        mock_session._started = True
        mock_session.run = AsyncMock(return_value=MagicMock(
            output="",
            error="error message",
            system=None
        ))

        tool._session = mock_session
        result = await tool.execute(command="ls /nonexistent")

        assert result.error == "error message"

    @pytest.mark.asyncio
    async def test_execute_new_session(self):
        """Test execute when session is None (new session)."""
        tool = Bash()

        # Mock the _BashSession constructor
        with patch('nura.tool.bash._BashSession') as MockBashSession:
            mock_session = MagicMock()
            mock_session._started = False
            mock_session.start = AsyncMock()
            mock_session.run = AsyncMock(return_value=MagicMock(
                output="output",
                error="",
                system=None
            ))
            MockBashSession.return_value = mock_session

            tool._session = None
            await tool.execute(command="echo hello")

            # Session should be created and started
            MockBashSession.assert_called_once()
            mock_session.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_bash_session_stop_not_started(self):
        """Test stopping a session that hasn't started."""
        session = _BashSession()

        with pytest.raises(Exception):
            session.stop()

    def test_to_param(self):
        """Test tool to param conversion."""
        tool = Bash()
        tool_dict = tool.to_param()

        assert tool_dict["type"] == "function"
        assert tool_dict["function"]["name"] == "bash"
        assert "parameters" in tool_dict["function"]


@pytest.mark.unit
class TestBashSession:
    """Test _BashSession class."""

    def test_session_creation(self):
        """Test creating a BashSession."""
        session = _BashSession()

        assert session._started is False
        assert session._timed_out is False
        assert session.command == "/bin/bash"
        assert session._timeout == 120.0
        assert session._sentinel == "<<exit>>"

    @pytest.mark.asyncio
    @pytest.mark.skipif(__import__("sys").platform == "win32", reason="os.setsid is Unix-only")
    async def test_session_start(self):
        """Test starting a session."""
        session = _BashSession()

        # Mock asyncio.create_subprocess_shell
        mock_process = MagicMock()
        mock_process.stdin = MagicMock()
        mock_process.stdout = MagicMock()
        mock_process.stdout._buffer = MagicMock()
        mock_process.stdout._buffer.decode = MagicMock(return_value="")
        mock_process.stderr = MagicMock()
        mock_process.stderr._buffer = MagicMock()
        mock_process.stderr._buffer.decode = MagicMock(return_value="")
        mock_process.returncode = None

        with patch('asyncio.create_subprocess_shell', return_value=mock_process):
            await session.start()

            assert session._started is True

    @pytest.mark.asyncio
    async def test_session_start_already_started(self):
        """Test starting an already started session."""
        session = _BashSession()
        session._started = True

        # Should return early without error
        await session.start()

        assert session._started is True
