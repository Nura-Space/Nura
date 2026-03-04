"""Test that all core modules can be imported."""
import pytest


@pytest.mark.unit
class TestImports:
    """Test module imports."""

    def test_core_imports(self):
        """Test core module imports."""

    def test_event_imports(self):
        """Test event module imports."""

    def test_context_imports(self):
        """Test context module imports."""

    def test_service_imports(self):
        """Test service module imports."""

    def test_agent_imports(self):
        """Test agent module imports."""

    def test_tool_imports(self):
        """Test tool module imports."""

    def test_top_level_imports(self):
        """Test top-level package imports."""
        import nura
        assert nura.__version__ == "0.1.0"

        # Test that key classes are available
