"""Tests for server/shared modules."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from shared.common import Issue, result
from shared.figma_client import parse_figma_url
from shared.image_analyzer import load_image_for_claude


# ── common.py ────────────────────────────────────────────────────────────────

def test_result_empty():
    assert result([]) == {"error_count": 0, "warning_count": 0, "errors": [], "warnings": []}

def test_result_counts_errors_and_warnings():
    issues = [
        Issue(severity="error", message="bad"),
        Issue(severity="warning", message="meh"),
        Issue(severity="info", message="fyi"),
    ]
    r = result(issues)
    assert r["error_count"] == 1
    assert r["warning_count"] == 2   # info counted as warning

def test_issue_optional_fields_omitted():
    i = Issue(severity="error", message="oops")
    r = result([i])
    assert "element_id" not in r["errors"][0]
    assert "rule" not in r["errors"][0]


# ── figma_client.py ───────────────────────────────────────────────────────────

def test_parse_figma_url_design_format():
    url = "https://www.figma.com/design/AbCdEfGhIjKl/MyApp?node-id=12-34"
    file_key, node_id = parse_figma_url(url)
    assert file_key == "AbCdEfGhIjKl"
    assert node_id == "12:34"

def test_parse_figma_url_file_format():
    url = "https://www.figma.com/file/XyZ123/App?node-id=99%3A100"
    file_key, node_id = parse_figma_url(url)
    assert file_key == "XyZ123"
    assert node_id == "99:100"

def test_parse_figma_url_missing_node_id_raises():
    import pytest
    with pytest.raises(ValueError, match="No node-id"):
        parse_figma_url("https://www.figma.com/design/AbCdEf/App")


# ── image_analyzer.py ─────────────────────────────────────────────────────────

def test_load_image_returns_base64_and_mime(tmp_path):
    img = tmp_path / "test.png"
    # Minimal 1x1 PNG
    img.write_bytes(bytes([
        0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,
        0x00,0x00,0x00,0x0D,0x49,0x48,0x44,0x52,
        0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,
        0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,
        0xDE,0x00,0x00,0x00,0x0C,0x49,0x44,0x41,
        0x54,0x08,0xD7,0x63,0xF8,0xCF,0xC0,0x00,
        0x00,0x00,0x02,0x00,0x01,0xE2,0x21,0xBC,
        0x33,0x00,0x00,0x00,0x00,0x49,0x45,0x4E,
        0x44,0xAE,0x42,0x60,0x82,
    ]))
    r = load_image_for_claude(str(img))
    assert r["media_type"] == "image/png"
    assert isinstance(r["base64"], str)
    assert len(r["base64"]) > 0

def test_load_image_missing_file_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        load_image_for_claude(str(tmp_path / "nope.png"))

def test_download_bytes_rejects_http():
    import pytest
    with pytest.raises(ValueError, match="Only HTTPS"):
        from shared.figma_client import download_bytes
        download_bytes("http://example.com/image.png")

def test_load_image_base64_roundtrips(tmp_path):
    import base64
    img = tmp_path / "test.png"
    img.write_bytes(bytes([
        0x89,0x50,0x4E,0x47,0x0D,0x0A,0x1A,0x0A,
        0x00,0x00,0x00,0x0D,0x49,0x48,0x44,0x52,
        0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,
        0x08,0x02,0x00,0x00,0x00,0x90,0x77,0x53,
        0xDE,0x00,0x00,0x00,0x0C,0x49,0x44,0x41,
        0x54,0x08,0xD7,0x63,0xF8,0xCF,0xC0,0x00,
        0x00,0x00,0x02,0x00,0x01,0xE2,0x21,0xBC,
        0x33,0x00,0x00,0x00,0x00,0x49,0x45,0x4E,
        0x44,0xAE,0x42,0x60,0x82,
    ]))
    r = load_image_for_claude(str(img))
    assert base64.b64decode(r["base64"]) == img.read_bytes()
