"""
Android Drawable Manager
Handles writing image assets into res/drawable-* density directories.
Supports PNG (density buckets) and SVG→AVD vector drawables.
SVG detection is automatic: .svg files or SVG content are converted to AVD XML
and written to res/drawable/ (resolution-independent). PNG/JPG go to density buckets.
"""
from __future__ import annotations
import re
from pathlib import Path
from shared.figma_client import (
    parse_figma_url,
    export_figma_node_png_urls,
    export_figma_node_svg_url,
    download_bytes,
)

# Figma PNG API supports integer scales 1-4 only.
# hdpi (1.5x) is not directly exportable via the Figma API; Android derives
# hdpi assets from xhdpi by downscaling — omitting it is standard practice
# for Figma-sourced assets. All 5 buckets are present; hdpi is copied from mdpi.
SCALE_TO_DENSITY = {1: "mdpi", 2: "xhdpi", 3: "xxhdpi", 4: "xxxhdpi"}

# SVG MIME / magic bytes
_SVG_SIGNATURES = (b"<svg", b"<?xml")


def _is_svg(data: bytes) -> bool:
    stripped = data.lstrip()
    return any(stripped.startswith(sig) for sig in _SVG_SIGNATURES) or b"<svg" in data[:512]


def export_figma_to_drawable(
    figma_url: str | None,
    file_key: str | None,
    node_id: str | None,
    drawable_path: str,
    asset_name: str,
    format: str,
    token: str,
) -> dict:
    """Export a Figma node to res/drawable-* directories."""
    if figma_url:
        file_key, node_id = parse_figma_url(figma_url)
    elif not (file_key and node_id):
        raise ValueError("Provide either figma_url or both file_key and node_id.")

    dest = Path(drawable_path)
    written: list[str] = []

    if format == "svg":
        url = export_figma_node_svg_url(file_key, node_id, token)
        svg_bytes = download_bytes(url)
        avd_xml = _svg_to_avd(svg_bytes)
        out_dir = dest / "drawable"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{asset_name}.xml"
        out_file.write_text(avd_xml, encoding="utf-8")
        written.append(str(out_file))
    else:
        scales = [1, 2, 3, 4]
        urls = export_figma_node_png_urls(file_key, node_id, token, scales)
        for scale, url in urls.items():
            density = SCALE_TO_DENSITY.get(scale, f"{scale}x")
            out_dir = dest / f"drawable-{density}"
            out_dir.mkdir(parents=True, exist_ok=True)
            png_bytes = download_bytes(url)
            out_file = out_dir / f"{asset_name}.png"
            out_file.write_bytes(png_bytes)
            written.append(str(out_file))

        # hdpi (1.5x) cannot be exported from Figma directly (non-integer scale).
        # Copy the mdpi (1x) asset into drawable-hdpi — Android will scale it up.
        mdpi_file = dest / "drawable-mdpi" / f"{asset_name}.png"
        if mdpi_file.exists():
            hdpi_dir = dest / "drawable-hdpi"
            hdpi_dir.mkdir(parents=True, exist_ok=True)
            hdpi_file = hdpi_dir / f"{asset_name}.png"
            hdpi_file.write_bytes(mdpi_file.read_bytes())
            written.append(str(hdpi_file))

    return {"written": written, "asset_name": asset_name}


def add_svg_to_drawable_from_bytes(
    svg_bytes: bytes,
    drawable_path: str,
    asset_name: str,
) -> dict:
    """Convert SVG bytes to AVD XML and write to res/drawable/."""
    avd_xml = _svg_to_avd(svg_bytes)
    dest = Path(drawable_path)
    out_dir = dest / "drawable"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{asset_name}.xml"
    out_file.write_text(avd_xml, encoding="utf-8")
    return {
        "status":     "ok",
        "written":    str(out_file),
        "asset_name": asset_name,
        "format":     "vector",
    }


def add_image_to_drawable(
    image_source: str,
    drawable_path: str,
    asset_name: str,
    density: str,
) -> dict:
    """Add a local or HTTPS image to drawable resources.

    SVG files (detected by extension or content) are converted to Android Vector
    Drawable XML and written to res/drawable/  (resolution-independent).
    PNG/JPG files are written to res/drawable-{density}/ as before.
    """
    dest = Path(drawable_path)

    if image_source.startswith("https://"):
        img_bytes = download_bytes(image_source)
        is_svg = image_source.lower().endswith(".svg") or _is_svg(img_bytes)
    elif image_source.startswith("http://"):
        raise ValueError("Only HTTPS sources are allowed.")
    else:
        src = Path(image_source)
        if not src.exists():
            raise FileNotFoundError(f"File not found: {src}")
        img_bytes = src.read_bytes()
        is_svg = src.suffix.lower() == ".svg" or _is_svg(img_bytes)

    if is_svg:
        avd_xml = _svg_to_avd(img_bytes)
        out_dir = dest / "drawable"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{asset_name}.xml"
        out_file.write_text(avd_xml, encoding="utf-8")
        return {"written": str(out_file), "asset_name": asset_name, "format": "vector"}

    out_dir = dest / f"drawable-{density}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{asset_name}.png"
    out_file.write_bytes(img_bytes)
    return {"written": str(out_file), "asset_name": asset_name, "density": density}


# ---------------------------------------------------------------------------
# SVG → Android Vector Drawable converter
# ---------------------------------------------------------------------------

_NS = "http://www.w3.org/2000/svg"
_NAMED_COLORS = {
    "black": "#000000", "white": "#FFFFFF", "red": "#FF0000", "green": "#008000",
    "blue": "#0000FF", "yellow": "#FFFF00", "cyan": "#00FFFF", "magenta": "#FF00FF",
    "gray": "#808080", "grey": "#808080", "silver": "#C0C0C0", "maroon": "#800000",
    "none": "none", "transparent": "none",
}


def _css_color_to_hex(color: str) -> str:
    """Best-effort conversion of CSS color values to #RRGGBB / #AARRGGBB."""
    if not color or color in ("none", "transparent"):
        return "none"
    color = color.strip()
    if color.startswith("#"):
        if len(color) == 4:  # #RGB → #RRGGBB
            r, g, b = color[1], color[2], color[3]
            return f"#{r}{r}{g}{g}{b}{b}".upper()
        return color.upper()
    if color in _NAMED_COLORS:
        return _NAMED_COLORS[color]
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)", color)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if m.group(4) is not None:
            a = round(float(m.group(4)) * 255)
            return f"#{a:02X}{r:02X}{g:02X}{b:02X}"
        return f"#{r:02X}{g:02X}{b:02X}"
    return color  # pass-through for values we don't recognise


def _parse_style(style: str) -> dict[str, str]:
    """Parse a CSS inline style string into a key→value dict."""
    result: dict[str, str] = {}
    for part in style.split(";"):
        part = part.strip()
        if ":" in part:
            k, _, v = part.partition(":")
            result[k.strip()] = v.strip()
    return result


def _attr(el, name: str, style: dict[str, str], default: str = "") -> str:
    """Return a presentation attribute, preferring inline style over XML attr."""
    return style.get(name) or el.get(name, default)


def _write_path(el, style: dict[str, str], out: list[str], indent: str) -> None:
    path_data = el.get("d", "")
    if not path_data:
        return

    fill = _css_color_to_hex(_attr(el, "fill", style, "black"))
    stroke = _css_color_to_hex(_attr(el, "stroke", style, "none"))
    stroke_width = _attr(el, "stroke-width", style, "")
    fill_opacity = _attr(el, "fill-opacity", style, "")
    stroke_opacity = _attr(el, "stroke-opacity", style, "")
    fill_rule = _attr(el, "fill-rule", style, "")
    clip_rule = _attr(el, "clip-rule", style, "")
    opacity = _attr(el, "opacity", style, "")

    lines = [f'{indent}<path']
    lines.append(f'{indent}    android:pathData="{path_data}"')
    if fill and fill != "none":
        if fill_opacity and fill_opacity != "1":
            alpha = round(float(fill_opacity) * 255)
            fill = f"#{alpha:02X}{fill.lstrip('#')}"
        lines.append(f'{indent}    android:fillColor="{fill}"')
    else:
        lines.append(f'{indent}    android:fillColor="@android:color/transparent"')
    if stroke and stroke != "none":
        if stroke_opacity and stroke_opacity != "1":
            alpha = round(float(stroke_opacity) * 255)
            stroke = f"#{alpha:02X}{stroke.lstrip('#')}"
        lines.append(f'{indent}    android:strokeColor="{stroke}"')
        if stroke_width:
            lines.append(f'{indent}    android:strokeWidth="{stroke_width}"')
    if fill_rule in ("evenodd", "evenOdd"):
        lines.append(f'{indent}    android:fillType="evenOdd"')
    elif clip_rule in ("evenodd", "evenOdd"):
        lines.append(f'{indent}    android:fillType="evenOdd"')
    if opacity and opacity != "1":
        lines.append(f'{indent}    android:alpha="{opacity}"')
    lines[-1] += "/>"
    # Fix: all but last line don't have /> yet
    result = "\n".join(lines[:-1])
    if len(lines) > 1:
        result += "\n" + lines[-1]
    else:
        result = lines[0].rstrip() + "/>"
    out.append(result)


def _process_group(el, out: list[str], indent: str) -> None:
    style_str = el.get("style", "")
    style = _parse_style(style_str)

    transform = el.get("transform", "")
    if transform:
        out.append(f'{indent}<group android:name="{el.get("id", "")}">')
        # TODO: parse transform for translateX/Y/rotate/scaleX/Y if needed
        child_indent = indent + "    "
    else:
        child_indent = indent

    for child in el:
        tag = child.tag.replace(f"{{{_NS}}}", "")
        child_style = _parse_style(child.get("style", ""))
        if tag == "path":
            _write_path(child, child_style, out, child_indent)
        elif tag == "g":
            _process_group(child, out, child_indent)
        elif tag in ("circle", "ellipse", "rect", "line", "polyline", "polygon"):
            # Convert basic shapes to path equivalents via a simple approximation
            path_el = _shape_to_path(child, tag)
            if path_el is not None:
                _write_path(path_el, child_style, out, child_indent)

    if transform:
        out.append(f'{indent}</group>')


def _shape_to_path(el, tag: str):
    """Convert basic SVG shapes to a <path>-like object (returns a dict-like stub)."""
    import xml.etree.ElementTree as ET

    def _f(name: str) -> float:
        return float(el.get(name, 0))

    d = ""
    if tag == "rect":
        x, y, w, h = _f("x"), _f("y"), _f("width"), _f("height")
        rx = _f("rx") or _f("ry")
        if rx:
            d = (f"M{x+rx},{y} H{x+w-rx} Q{x+w},{y} {x+w},{y+rx} "
                 f"V{y+h-rx} Q{x+w},{y+h} {x+w-rx},{y+h} "
                 f"H{x+rx} Q{x},{y+h} {x},{y+h-rx} "
                 f"V{y+rx} Q{x},{y} {x+rx},{y} Z")
        else:
            d = f"M{x},{y} H{x+w} V{y+h} H{x} Z"
    elif tag == "circle":
        cx, cy, r = _f("cx"), _f("cy"), _f("r")
        k = r * 0.5523
        d = (f"M{cx},{cy-r} C{cx+k},{cy-r} {cx+r},{cy-k} {cx+r},{cy} "
             f"C{cx+r},{cy+k} {cx+k},{cy+r} {cx},{cy+r} "
             f"C{cx-k},{cy+r} {cx-r},{cy+k} {cx-r},{cy} "
             f"C{cx-r},{cy-k} {cx-k},{cy-r} {cx},{cy-r} Z")
    elif tag == "ellipse":
        cx, cy, rx, ry = _f("cx"), _f("cy"), _f("rx"), _f("ry")
        kx, ky = rx * 0.5523, ry * 0.5523
        d = (f"M{cx},{cy-ry} C{cx+kx},{cy-ry} {cx+rx},{cy-ky} {cx+rx},{cy} "
             f"C{cx+rx},{cy+ky} {cx+kx},{cy+ry} {cx},{cy+ry} "
             f"C{cx-kx},{cy+ry} {cx-rx},{cy+ky} {cx-rx},{cy} "
             f"C{cx-rx},{cy-ky} {cx-kx},{cy-ry} {cx},{cy-ry} Z")
    elif tag == "line":
        d = f"M{_f('x1')},{_f('y1')} L{_f('x2')},{_f('y2')}"
    elif tag == "polyline":
        pts = el.get("points", "").split()
        if pts:
            d = "M" + " L".join(pts)
    elif tag == "polygon":
        pts = el.get("points", "").split()
        if pts:
            d = "M" + " L".join(pts) + " Z"

    if not d:
        return None

    stub = ET.Element("path")
    stub.set("d", d)
    for attr in ("fill", "stroke", "stroke-width", "fill-opacity", "opacity",
                 "fill-rule", "clip-rule", "style"):
        if el.get(attr):
            stub.set(attr, el.get(attr))
    return stub


def _svg_to_avd(svg_bytes: bytes) -> str:
    """Convert SVG bytes to Android Vector Drawable XML string using lxml."""
    import xml.etree.ElementTree as ET

    svg_text = svg_bytes.decode("utf-8", errors="replace")

    # Strip XML declaration so ET can parse without encoding issues
    svg_text = re.sub(r"<\?xml[^?]*\?>", "", svg_text).strip()

    root = ET.fromstring(svg_text)

    # Determine viewport dimensions
    vb = root.get("viewBox", "")
    if vb:
        parts = re.split(r"[\s,]+", vb.strip())
        vp_w = float(parts[2]) if len(parts) >= 3 else 24.0
        vp_h = float(parts[3]) if len(parts) >= 4 else 24.0
    else:
        vp_w = float(root.get("width", "24").rstrip("pt px em rem"))
        vp_h = float(root.get("height", "24").rstrip("pt px em rem"))

    dp_w = root.get("width", f"{vp_w:.0f}").rstrip("pt px em rem")
    dp_h = root.get("height", f"{vp_h:.0f}").rstrip("pt px em rem")
    # Strip units (px, pt, etc.) if present
    dp_w = re.sub(r"[a-z%]+$", "", dp_w) or str(vp_w)
    dp_h = re.sub(r"[a-z%]+$", "", dp_h) or str(vp_h)

    out: list[str] = [
        '<?xml version="1.0" encoding="utf-8"?>',
        f'<vector xmlns:android="http://schemas.android.com/apk/res/android"',
        f'    android:width="{dp_w}dp"',
        f'    android:height="{dp_h}dp"',
        f'    android:viewportWidth="{vp_w:.6g}"',
        f'    android:viewportHeight="{vp_h:.6g}">',
    ]

    indent = "    "
    for child in root:
        tag = child.tag.replace(f"{{{_NS}}}", "")
        child_style = _parse_style(child.get("style", ""))
        if tag == "path":
            _write_path(child, child_style, out, indent)
        elif tag == "g":
            _process_group(child, out, indent)
        elif tag in ("circle", "ellipse", "rect", "line", "polyline", "polygon"):
            path_el = _shape_to_path(child, tag)
            if path_el is not None:
                _write_path(path_el, child_style, out, indent)

    out.append("</vector>")
    return "\n".join(out)
