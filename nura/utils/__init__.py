"""Image processing utilities for agent vision capabilities."""

import base64
from io import BytesIO
from typing import Optional

from PIL import Image
from loguru import logger


class ImageProcessor:
    """Process images for LLM vision capabilities."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSION = 1024  # Max edge length
    QUALITY = 85  # JPEG quality

    @staticmethod
    async def process(image_bytes: bytes) -> Optional[str]:
        """Process an image (resize and encode to base64).

        Args:
            image_bytes: Raw image bytes

        Returns:
            Base64 encoded image or None if processing failed
        """
        try:
            # Check file size
            if len(image_bytes) > ImageProcessor.MAX_FILE_SIZE:
                logger.warning(f"Image too large: {len(image_bytes)} bytes")
                return None

            # Open and resize image
            img = Image.open(BytesIO(image_bytes))
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            width, height = img.size
            if (
                width > ImageProcessor.MAX_DIMENSION
                or height > ImageProcessor.MAX_DIMENSION
            ):
                scale = ImageProcessor.MAX_DIMENSION / max(width, height)
                new_size = (int(width * scale), int(height * scale))
                img = img.resize(new_size, Image.LANCZOS)
                logger.info(f"Resized image from {width}x{height} to {new_size}")

            # Convert to base64
            output = BytesIO()
            img.save(output, format="JPEG", quality=ImageProcessor.QUALITY)
            return base64.b64encode(output.getvalue()).decode("utf-8")

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return None
