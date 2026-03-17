#!/usr/bin/env python3
"""
Photo generation script using Doubao Seedream 5.0.

Usage:
    python3 generate.py --prompt TEXT [--images PATH,...] --output-dir DIR [--size 2K]

- No --images: text-to-image
- With --images: multi-image fusion (sequential_image_generation="disabled")

Output:
    Success: prints output file path to stdout
    Failure: prints "ERROR: <message>" to stderr and exits with non-zero code
"""

import argparse
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


MODEL = "ep-20260307174559-w6lfl"


def get_api_key() -> str:
    api_key = os.environ.get("ARK_API_KEY")
    if not api_key:
        print("ERROR: ARK_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    return api_key


def load_image_as_base64(path: str) -> str:
    """Load a local image file and return as base64 data URI."""
    import base64
    import mimetypes

    file_path = Path(path)
    if not file_path.exists():
        print(f"ERROR: Image file not found: {path}", file=sys.stderr)
        sys.exit(1)

    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        # Default to jpeg for unknown types
        ext = file_path.suffix.lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                    ".webp": "image/webp", ".bmp": "image/bmp"}
        mime_type = mime_map.get(ext, "image/jpeg")

    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def download_image(url: str, output_dir: Path) -> Path:
    """Download image from URL and save to output_dir."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"generated_{timestamp}.png"

    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        with open(output_path, "wb") as f:
            f.write(data)
    except Exception as e:
        print(f"ERROR: Failed to download image: {e}", file=sys.stderr)
        sys.exit(1)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        prog="generate.py",
        description="Generate or fuse images using Doubao Seedream 5.0",
    )
    parser.add_argument("--prompt", required=True, help="Image generation prompt")
    parser.add_argument(
        "--images",
        type=str,
        default="",
        help="Comma-separated list of reference image paths (local files)",
    )
    parser.add_argument("--output-dir", required=True, help="Directory to save generated image")
    parser.add_argument("--size", type=str, default="2K", help="Image size (default: 2K)")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"ERROR: Cannot create output directory: {e}", file=sys.stderr)
            sys.exit(1)

    api_key = get_api_key()

    try:
        from volcenginesdkarkruntime import Ark
    except ImportError:
        print("ERROR: volcengine-python-sdk[ark] not installed. Run: pip install 'volcengine-python-sdk[ark]'", file=sys.stderr)
        sys.exit(1)

    client = Ark(
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        api_key=api_key,
    )

    # Parse image paths
    image_paths = [p.strip() for p in args.images.split(",") if p.strip()] if args.images else []

    # Build API call kwargs
    kwargs: dict = {
        "model": MODEL,
        "prompt": args.prompt,
        "size": args.size,
        "response_format": "url",
        "watermark": False,
        "output_format": "png",
    }

    if image_paths:
        # Multi-image fusion: load as base64
        if len(image_paths) == 1:
            kwargs["image"] = load_image_as_base64(image_paths[0])
        else:
            kwargs["image"] = [load_image_as_base64(p) for p in image_paths]
        kwargs["sequential_image_generation"] = "disabled"

    try:
        response = client.images.generate(**kwargs)
    except Exception as e:
        print(f"ERROR: API call failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not response.data:
        print("ERROR: API returned empty data", file=sys.stderr)
        sys.exit(1)

    image_data = response.data[0]

    # Check for error in response
    if hasattr(image_data, "error") and image_data.error:
        err = image_data.error
        code = getattr(err, "code", "unknown")
        msg = getattr(err, "message", str(err))
        print(f"ERROR: Image generation failed [{code}]: {msg}", file=sys.stderr)
        sys.exit(1)

    url = getattr(image_data, "url", None)
    if not url:
        print("ERROR: No URL in API response", file=sys.stderr)
        sys.exit(1)

    output_path = download_image(url, output_dir)
    print(str(output_path))


if __name__ == "__main__":
    main()
