"""
xcassets Manager
Handles writing image assets into an Xcode .xcassets folder with the correct
directory structure and Contents.json that Xcode / Interface Builder expect.

Also provides helpers for calling the Figma REST API to export node images
at 1x / 2x / 3x and placing them directly into an imageset.
"""

from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path

from shared.figma_client import (
    parse_figma_url,
    export_figma_node_png_urls as figma_export_urls,
    export_figma_node_pdf_url  as figma_export_pdf_url,
    download_bytes,
)


# ─── SVG → PDF converter ──────────────────────────────────────────────────────

_SVG_SIGNATURES = (b"<svg", b"<?xml")


def _is_svg(data: bytes) -> bool:
    stripped = data.lstrip()
    return any(stripped.startswith(sig) for sig in _SVG_SIGNATURES) or b"<svg" in data[:512]


def _svg_to_pdf(svg_bytes: bytes) -> bytes:
    """Convert SVG bytes to PDF using macOS sips."""
    tmp_svg = tempfile.NamedTemporaryFile(suffix=".svg", delete=False)
    tmp_svg.write(svg_bytes)
    tmp_svg.close()
    tmp_pdf_path = tmp_svg.name.replace(".svg", ".pdf")
    try:
        subprocess.run(
            ["sips", "-s", "format", "pdf", tmp_svg.name, "--out", tmp_pdf_path],
            check=True, capture_output=True,
        )
        return Path(tmp_pdf_path).read_bytes()
    finally:
        if os.path.exists(tmp_svg.name):
            os.unlink(tmp_svg.name)
        if os.path.exists(tmp_pdf_path):
            os.unlink(tmp_pdf_path)


def add_svg_to_xcassets(
    svg_bytes: bytes,
    xcassets_path: str,
    asset_name: str,
    render_as_template: bool = False,
) -> dict:
    """Convert SVG bytes to PDF via sips and write to xcassets as a vector imageset."""
    pdf_bytes = _svg_to_pdf(svg_bytes)
    imageset_path = write_pdf_imageset(xcassets_path, asset_name, pdf_bytes, render_as_template)
    return {
        "status":           "ok",
        "imageset_path":    imageset_path,
        "asset_name":       asset_name,
        "format":           "pdf",
        "file_written":     f"{asset_name}.pdf ({len(pdf_bytes)} bytes)",
        "storyboard_usage": f'"imageName": "{asset_name}"',
    }


# ─── xcassets writer ──────────────────────────────────────────────────────────

def write_imageset(
    xcassets_path: str,
    asset_name: str,
    scale_to_bytes: dict[int, bytes],
    render_as_template: bool = False,
) -> str:
    """
    Write PNG files and Contents.json into:
        {xcassets_path}/{asset_name}.imageset/

    scale_to_bytes: {1: <bytes>, 2: <bytes>, 3: <bytes>}
    Only scales present in the dict get a filename entry in Contents.json.

    Returns the path to the created imageset folder.
    """
    imageset_dir = Path(xcassets_path).expanduser().resolve() / f"{asset_name}.imageset"
    imageset_dir.mkdir(parents=True, exist_ok=True)

    images_json: list[dict] = []

    for scale in [1, 2, 3]:
        suffix   = "" if scale == 1 else f"@{scale}x"
        filename = f"{asset_name}{suffix}.png"
        entry: dict = {"idiom": "universal", "scale": f"{scale}x"}

        if scale in scale_to_bytes:
            (imageset_dir / filename).write_bytes(scale_to_bytes[scale])
            entry["filename"] = filename

        images_json.append(entry)

    contents: dict = {
        "images": images_json,
        "info": {"author": "xcode", "version": 1},
    }
    if render_as_template:
        contents["properties"] = {"template-rendering-intent": "template"}

    (imageset_dir / "Contents.json").write_text(
        json.dumps(contents, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return str(imageset_dir)


def write_pdf_imageset(
    xcassets_path: str,
    asset_name: str,
    pdf_bytes: bytes,
    render_as_template: bool = False,
) -> str:
    """
    Write a single PDF file and a vector-aware Contents.json into:
        {xcassets_path}/{asset_name}.imageset/

    Xcode uses the PDF as a universal vector asset — no scale variants needed.
    Returns the path to the created imageset folder.
    """
    imageset_dir = Path(xcassets_path).expanduser().resolve() / f"{asset_name}.imageset"
    imageset_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{asset_name}.pdf"
    (imageset_dir / filename).write_bytes(pdf_bytes)

    props: dict = {"preserves-vector-representation": True}
    if render_as_template:
        props["template-rendering-intent"] = "template"

    contents: dict = {
        "images": [{"idiom": "universal", "filename": filename}],
        "info": {"author": "xcode", "version": 1},
        "properties": props,
    }

    (imageset_dir / "Contents.json").write_text(
        json.dumps(contents, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return str(imageset_dir)


# ─── High-level orchestrators ─────────────────────────────────────────────────

def export_figma_node_to_xcassets(
    *,
    file_key: str,
    node_id: str,
    xcassets_path: str,
    asset_name: str,
    scales: list[int],
    render_as_template: bool,
    token: str,
    format: str = "png",
) -> dict:
    """
    Full pipeline: Figma API → download asset → write imageset.
    format: 'png' (default, exports 1x/2x/3x) or 'pdf' (single vector file).
    Returns a summary dict.
    """
    if format == "pdf":
        # 1. Get PDF download URL from Figma
        pdf_url = figma_export_pdf_url(file_key, node_id, token)

        # 2. Download the PDF
        pdf_bytes = download_bytes(pdf_url)

        # 3. Write to xcassets
        imageset_path = write_pdf_imageset(
            xcassets_path, asset_name, pdf_bytes, render_as_template
        )

        return {
            "status":        "ok",
            "imageset_path": imageset_path,
            "asset_name":    asset_name,
            "format":        "pdf",
            "file_written":  f"{asset_name}.pdf ({len(pdf_bytes)} bytes)",
            "storyboard_usage": f'"imageName": "{asset_name}"',
        }

    # PNG path
    # 1. Get download URLs from Figma
    scale_to_url = figma_export_urls(
        file_key=file_key,
        node_id=node_id,
        token=token,
        scales=scales,
    )

    # 2. Download each image
    scale_to_bytes: dict[int, bytes] = {}
    downloaded: dict[int, int] = {}
    for scale, url in scale_to_url.items():
        data = download_bytes(url)
        scale_to_bytes[scale] = data
        downloaded[scale] = len(data)

    # 3. Write to xcassets
    imageset_path = write_imageset(
        xcassets_path, asset_name, scale_to_bytes, render_as_template
    )

    return {
        "status":        "ok",
        "imageset_path": imageset_path,
        "asset_name":    asset_name,
        "format":        "png",
        "scales_written": [f"{s}x ({downloaded[s]} bytes)" for s in sorted(downloaded)],
        "storyboard_usage": f'"imageName": "{asset_name}"',
    }


def add_local_or_url_to_xcassets(
    *,
    image_source: str,
    xcassets_path: str,
    asset_name: str,
    scale: int,
    render_as_template: bool,
) -> dict:
    """
    Generic: take a local file path or HTTPS URL and add it to an imageset.
    PDF files (detected by extension or %PDF magic bytes) are written as a
    single vector imageset via write_pdf_imageset.
    PNG/JPG are written as a scale variant; existing scales are preserved.
    """
    # Resolve image bytes
    if image_source.startswith("http://") or image_source.startswith("https://"):
        data = download_bytes(image_source)
        is_pdf = image_source.lower().endswith(".pdf") or data[:4] == b"%PDF"
    else:
        p = Path(image_source).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Image file not found: {p}")
        data = p.read_bytes()
        is_pdf = p.suffix.lower() == ".pdf" or data[:4] == b"%PDF"

    is_svg = _is_svg(data) if not is_pdf else False

    if is_svg:
        return add_svg_to_xcassets(data, xcassets_path, asset_name, render_as_template)

    if is_pdf:
        imageset_path = write_pdf_imageset(
            xcassets_path, asset_name, data, render_as_template
        )
        return {
            "status":        "ok",
            "imageset_path": imageset_path,
            "asset_name":    asset_name,
            "format":        "pdf",
            "file_written":  f"{asset_name}.pdf ({len(data)} bytes)",
            "storyboard_usage": f'"imageName": "{asset_name}"',
        }

    # PNG / raster path — preserve existing scale variants
    imageset_dir = Path(xcassets_path).expanduser().resolve() / f"{asset_name}.imageset"
    contents_path = imageset_dir / "Contents.json"
    existing_scale_bytes: dict[int, bytes] = {}

    if contents_path.exists():
        existing = json.loads(contents_path.read_text())
        for entry in existing.get("images", []):
            fn = entry.get("filename")
            sc = entry.get("scale", "")
            if fn and sc:
                sc_int = int(sc.rstrip("x"))
                existing_file = imageset_dir / fn
                if existing_file.exists():
                    existing_scale_bytes[sc_int] = existing_file.read_bytes()

    existing_scale_bytes[scale] = data

    imageset_path = write_imageset(
        xcassets_path, asset_name, existing_scale_bytes, render_as_template
    )

    return {
        "status":        "ok",
        "imageset_path": imageset_path,
        "asset_name":    asset_name,
        "format":        "png",
        "scale_written": f"{scale}x ({len(data)} bytes)",
        "storyboard_usage": f'"imageName": "{asset_name}"',
    }
