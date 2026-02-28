"""Unit tests for file operators."""
import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch

from nura.tool.file_operators import LocalFileOperator, SandboxFileOperator


@pytest.mark.unit
class TestLocalFileOperator:
    """Test LocalFileOperator."""

    def test_local_file_operator_creation(self):
        """Test creating a LocalFileOperator."""
        operator = LocalFileOperator()
        assert operator.encoding == "utf-8"

    @pytest.mark.asyncio
    async def test_read_file(self):
        """Test reading a file."""
        operator = LocalFileOperator()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
            f.write("test content")
            temp_path = f.name

        try:
            content = await operator.read_file(temp_path)
            assert content == "test content"
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_read_file_not_found(self):
        """Test reading a non-existent file."""
        operator = LocalFileOperator()

        with pytest.raises(Exception):
            await operator.read_file("/nonexistent/file.txt")

    @pytest.mark.asyncio
    async def test_write_file(self):
        """Test writing a file."""
        operator = LocalFileOperator()

        temp_path = tempfile.mktemp(suffix=".txt")

        try:
            await operator.write_file(temp_path, "new content")

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert content == "new content"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_write_file_overwrite(self):
        """Test overwriting a file."""
        operator = LocalFileOperator()

        temp_path = tempfile.mktemp(suffix=".txt")

        try:
            await operator.write_file(temp_path, "original")
            await operator.write_file(temp_path, "overwritten")

            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert content == "overwritten"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_exists(self):
        """Test checking if file exists."""
        operator = LocalFileOperator()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            assert await operator.exists(temp_path) is True
            assert await operator.exists("/nonexistent/file.txt") is False
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_is_directory(self):
        """Test checking if path is a directory."""
        operator = LocalFileOperator()

        # Use temp directory
        temp_dir = tempfile.gettempdir()

        assert await operator.is_directory(temp_dir) is True
        assert await operator.is_directory("/nonexistent/dir") is False

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name

        try:
            assert await operator.is_directory(temp_path) is False
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_run_command(self):
        """Test running a shell command."""
        operator = LocalFileOperator()

        return_code, stdout, stderr = await operator.run_command("echo hello")

        assert return_code == 0
        assert "hello" in stdout

    @pytest.mark.asyncio
    async def test_run_command_with_stderr(self):
        """Test running a command with stderr output."""
        operator = LocalFileOperator()

        # This command writes to stderr
        return_code, stdout, stderr = await operator.run_command("ls /nonexistent 2>&1 || true")

        # Should handle gracefully

    @pytest.mark.asyncio
    async def test_run_command_timeout(self):
        """Test command timeout."""
        operator = LocalFileOperator()

        with pytest.raises(TimeoutError):
            await operator.run_command("sleep 10", timeout=0.1)


@pytest.mark.unit
class TestSandboxFileOperator:
    """Test SandboxFileOperator."""

    def test_sandbox_file_operator_creation(self):
        """Test creating a SandboxFileOperator."""
        operator = SandboxFileOperator()
        # sandbox_client may be None if sandbox is not available
        assert operator is not None

    @pytest.mark.asyncio
    async def test_ensure_sandbox_initialized(self):
        """Test sandbox initialization check."""
        operator = SandboxFileOperator()

        # Mock sandbox client
        mock_client = MagicMock()
        mock_client.sandbox = True  # Already initialized
        operator.sandbox_client = mock_client

        # Should not raise if sandbox is already initialized
        await operator._ensure_sandbox_initialized()

    @pytest.mark.asyncio
    async def test_read_file_in_sandbox(self):
        """Test reading a file in sandbox."""
        operator = SandboxFileOperator()

        # Mock sandbox client
        mock_client = MagicMock()
        mock_client.sandbox = True
        mock_client.read_file = AsyncMock(return_value="sandbox content")
        operator.sandbox_client = mock_client

        content = await operator.read_file("/sandbox/file.txt")

        assert content == "sandbox content"
        mock_client.read_file.assert_called_once_with("/sandbox/file.txt")

    @pytest.mark.asyncio
    async def test_write_file_in_sandbox(self):
        """Test writing a file in sandbox."""
        operator = SandboxFileOperator()

        # Mock sandbox client
        mock_client = MagicMock()
        mock_client.sandbox = True
        mock_client.write_file = AsyncMock()
        operator.sandbox_client = mock_client

        await operator.write_file("/sandbox/file.txt", "new content")

        mock_client.write_file.assert_called_once_with("/sandbox/file.txt", "new content")

    @pytest.mark.asyncio
    async def test_exists_in_sandbox(self):
        """Test checking if file exists in sandbox."""
        operator = SandboxFileOperator()

        # Mock sandbox client
        mock_client = MagicMock()
        mock_client.sandbox = True
        mock_client.run_command = AsyncMock(return_value="true")
        operator.sandbox_client = mock_client

        result = await operator.exists("/sandbox/file.txt")

        assert result is True

    @pytest.mark.asyncio
    async def test_is_directory_in_sandbox(self):
        """Test checking if path is directory in sandbox."""
        operator = SandboxFileOperator()

        # Mock sandbox client
        mock_client = MagicMock()
        mock_client.sandbox = True
        mock_client.run_command = AsyncMock(return_value="true")
        operator.sandbox_client = mock_client

        result = await operator.is_directory("/sandbox/dir")

        assert result is True

    @pytest.mark.asyncio
    async def test_run_command_in_sandbox(self):
        """Test running a command in sandbox."""
        operator = SandboxFileOperator()

        # Mock sandbox client
        mock_client = MagicMock()
        mock_client.sandbox = True
        mock_client.run_command = AsyncMock(return_value="command output")
        operator.sandbox_client = mock_client

        return_code, stdout, stderr = await operator.run_command("echo test")

        assert return_code == 0
        assert "command output" in stdout

    @pytest.mark.asyncio
    async def test_run_command_timeout_in_sandbox(self):
        """Test command timeout in sandbox."""
        operator = SandboxFileOperator()

        # Mock sandbox client
        mock_client = MagicMock()
        mock_client.sandbox = True
        mock_client.run_command = AsyncMock(side_effect=TimeoutError("timeout"))
        operator.sandbox_client = mock_client

        with pytest.raises(TimeoutError):
            await operator.run_command("sleep 10", timeout=1)

    @pytest.mark.asyncio
    async def test_run_command_exception_in_sandbox(self):
        """Test command exception in sandbox."""
        operator = SandboxFileOperator()

        # Mock sandbox client
        mock_client = MagicMock()
        mock_client.sandbox = True
        mock_client.run_command = AsyncMock(side_effect=Exception("error"))
        operator.sandbox_client = mock_client

        return_code, stdout, stderr = await operator.run_command("bad command")

        assert return_code == 1
        assert "error" in stderr.lower()


@pytest.mark.unit
class TestFileOperatorProtocol:
    """Test FileOperator protocol compliance."""

    def test_local_file_operator_is_file_operator(self):
        """Test that LocalFileOperator implements FileOperator."""
        operator = LocalFileOperator()

        # Check that it has all required methods
        assert hasattr(operator, 'read_file')
        assert hasattr(operator, 'write_file')
        assert hasattr(operator, 'is_directory')
        assert hasattr(operator, 'exists')
        assert hasattr(operator, 'run_command')

    def test_sandbox_file_operator_is_file_operator(self):
        """Test that SandboxFileOperator implements FileOperator."""
        operator = SandboxFileOperator()

        # Check that it has all required methods
        assert hasattr(operator, 'read_file')
        assert hasattr(operator, 'write_file')
        assert hasattr(operator, 'is_directory')
        assert hasattr(operator, 'exists')
        assert hasattr(operator, 'run_command')
