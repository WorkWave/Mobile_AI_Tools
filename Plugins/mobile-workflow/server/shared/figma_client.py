"""
Figma REST API client — shared between iOS xcassets and Android drawable managers.
Extracted from validators/xcassets_manager.py.
"""
from __future__ import annotations
import json
import re
import urllib.request
import urllib.parse
import urllib.error

FIGMA_API_BASE = "https://api.figma.com/v1"


def parse_figma_url(url: str) -> tuple[str, str]:
    """
    Extract (file_key, node_id) from a Figma share/copy-link URL.
    Supports /file/{key}/ and /design/{key}/ formats.
    """
    parsed = urllib.parse.urlparse(url)
    m = re.search(r"/(?:file|design)/([^/?#]+)", parsed.path)
    if not m:
        raise ValueError(f"Cannot parse Figma file key from URL: {url}")
    file_key = m.group(1)

    params = urllib.parse.parse_qs(parsed.query)
    raw = params.get("node-id", [None])[0]
    if not raw:
        raise ValueError(
            f"No node-id found in URL: {url}\n"
            "In Figma, right-click the component → 'Copy link'. "
            "The URL must include ?node-id=…"
        )
    node_id = urllib.parse.unquote(raw).replace("-", ":")
    return file_key, node_id


def export_figma_node_png_urls(
    file_key: str,
    node_id: str,
    token: str,
    scales: list[int],
) -> dict[int, str]:
    """
    Returns {scale: download_url} for PNG exports.
    Makes one API call per scale — the Figma Images API `scale` parameter
    is scalar (a single integer), so separate requests are required per density.
    """
    result: dict[int, str] = {}
    for scale in scales:
        api_url = (
            f"{FIGMA_API_BASE}/images/{file_key}"
            f"?ids={urllib.parse.quote(node_id, safe=':')}"
            f"&format=png&scale={scale}"
        )
        req = urllib.request.Request(
            api_url,
            headers={"X-Figma-Token": token, "User-Agent": "mobile-ui-builder/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")
            raise ValueError(f"Figma API HTTP {e.code}: {body}") from e
        if data.get("err"):
            raise ValueError(f"Figma API error: {data['err']}")
        images: dict = data.get("images", {})
        img_url = images.get(node_id) or images.get(node_id.replace(":", "-"))
        if not img_url:
            raise ValueError(
                f"No image URL returned for node '{node_id}' at scale {scale}x.\n"
                f"Figma returned: {list(images.keys())}"
            )
        result[scale] = img_url
    return result


def export_figma_node_svg_url(
    file_key: str,
    node_id: str,
    token: str,
) -> str:
    """Returns download URL for an SVG export."""
    api_url = (
        f"{FIGMA_API_BASE}/images/{file_key}"
        f"?ids={urllib.parse.quote(node_id, safe=':')}&format=svg"
    )
    req = urllib.request.Request(
        api_url,
        headers={"X-Figma-Token": token, "User-Agent": "mobile-ui-builder/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise ValueError(f"Figma API HTTP {e.code}: {body}") from e
    if data.get("err"):
        raise ValueError(f"Figma API error: {data['err']}")
    images: dict = data.get("images", {})
    svg_url = images.get(node_id) or images.get(node_id.replace(":", "-"))
    if not svg_url:
        raise ValueError(f"No SVG URL returned for node '{node_id}'.")
    return svg_url


def export_figma_node_pdf_url(
    file_key: str,
    node_id: str,
    token: str,
) -> str:
    """Returns download URL for a PDF export."""
    api_url = (
        f"{FIGMA_API_BASE}/images/{file_key}"
        f"?ids={urllib.parse.quote(node_id, safe=':')}&format=pdf"
    )
    req = urllib.request.Request(
        api_url,
        headers={"X-Figma-Token": token, "User-Agent": "mobile-ui-builder/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise ValueError(f"Figma API HTTP {e.code}: {body}") from e
    if data.get("err"):
        raise ValueError(f"Figma API error: {data['err']}")
    images: dict = data.get("images", {})
    pdf_url = images.get(node_id) or images.get(node_id.replace(":", "-"))
    if not pdf_url:
        raise ValueError(f"No PDF URL returned for node '{node_id}'.")
    return pdf_url


def download_bytes(url: str) -> bytes:
    """Download from an HTTPS URL. Enforces HTTPS-only."""
    if not url.startswith("https://"):
        raise ValueError(f"Only HTTPS downloads are allowed. Got: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "mobile-ui-builder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except urllib.error.URLError as e:
        raise ValueError(f"Failed to download {url}: {e.reason}") from e
