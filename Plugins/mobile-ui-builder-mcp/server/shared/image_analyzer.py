"""
Image loader for Claude vision — shared between iOS and Android UI generators.
Extracted from server/server.py generate_storyboard_from_image handler.
"""
from __future__ import annotations
import base64
import mimetypes
from pathlib import Path


def load_image_for_claude(image_path: str) -> dict:
    """
    Read an image file and return base64 + media_type ready for MCP ImageContent.

    Returns:
        {"base64": str, "media_type": str}

    Raises:
        FileNotFoundError: if the path does not exist
    """
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")

    mime, _ = mimetypes.guess_type(str(p))
    if not mime or not mime.startswith("image/"):
        mime = "image/png"

    return {
        "base64": base64.standard_b64encode(p.read_bytes()).decode("utf-8"),
        "media_type": mime,
    }
