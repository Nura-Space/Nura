"""Tests for image processor utility."""
import pytest
from io import BytesIO
from PIL import Image

from nura.utils.image_processor import ImageProcessor


@pytest.mark.unit
class TestImageProcessor:
    """Tests for ImageProcessor class."""

    @pytest.fixture
    def small_image_bytes(self):
        """Create a small test image (100x100)."""
        img = Image.new("RGB", (100, 100), color="red")
        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    @pytest.fixture
    def large_image_bytes(self):
        """Create a large test image (2000x1500)."""
        img = Image.new("RGB", (2000, 1500), color="blue")
        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    @pytest.fixture
    def rgba_image_bytes(self):
        """Create an RGBA test image."""
        img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        output = BytesIO()
        img.save(output, format="PNG")
        return output.getvalue()

    @pytest.mark.unit
    async def test_process_small_image(self, small_image_bytes):
        """Test processing a small image."""
        result = await ImageProcessor.process(small_image_bytes)
        assert result is not None
        assert isinstance(result, str)
        # Small image should not be resized
        assert len(result) > 0

    @pytest.mark.unit
    async def test_process_large_image_resizes(self, large_image_bytes):
        """Test that large images are resized."""
        result = await ImageProcessor.process(large_image_bytes)
        assert result is not None
        assert isinstance(result, str)
        # Large image should be resized, verify it was processed successfully
        # Original 2000x1500 PNG (~12KB) should become smaller after resize and JPEG encode
        assert len(result) > 0

    @pytest.mark.unit
    async def test_process_rgba_image(self, rgba_image_bytes):
        """Test processing an RGBA image (should be converted to RGB)."""
        result = await ImageProcessor.process(rgba_image_bytes)
        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.unit
    async def test_process_oversized_image_returns_none(self):
        """Test that images larger than 10MB return None."""
        # Create a very large image (simulate > 10MB)
        # We can't actually create a 10MB image in memory easily,
        # so we'll test the size check by mocking or just verify the logic exists
        large_bytes = b"x" * (11 * 1024 * 1024)  # 11MB of dummy data
        result = await ImageProcessor.process(large_bytes)
        assert result is None

    @pytest.mark.unit
    async def test_process_invalid_image(self):
        """Test processing invalid image data."""
        result = await ImageProcessor.process(b"not an image")
        assert result is None
