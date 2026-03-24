"""Tests for Android layout generator."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

import xml.etree.ElementTree as ET
from android.layout_generator import generate_android_layout


MINIMAL_LAYOUT = {
    "screen_name": "LoginScreen",
    "root_layout": "ConstraintLayout",
    "views": [
        {
            "id": "activity_login_btn_login",
            "type": "MaterialButton",
            "style": "@style/Widget.Material3.Button",
            "text": "@string/login",
            "layout_width": "match_parent",
            "layout_height": "wrap_content",
            "constraints": {
                "bottom_to_bottom": "parent",
                "start_to_start": "parent",
                "end_to_end": "parent",
            },
            "margin_bottom": "16dp",
        }
    ],
    "strings": {"login": "Login"},
}


def _parse(result: dict) -> ET.Element:
    return ET.fromstring(result["layout_xml"])


def test_returns_layout_xml_and_strings_xml():
    result = generate_android_layout(MINIMAL_LAYOUT)
    assert "layout_xml" in result
    assert "strings_xml" in result


def test_root_element_is_constraint_layout():
    root = _parse(generate_android_layout(MINIMAL_LAYOUT))
    assert "ConstraintLayout" in root.tag


def test_button_id_is_set():
    root = _parse(generate_android_layout(MINIMAL_LAYOUT))
    btn = root.find(".//*[@{http://schemas.android.com/apk/res/android}id]")
    assert btn is not None
    assert "activity_login_btn_login" in btn.get(
        "{http://schemas.android.com/apk/res/android}id", ""
    )


def test_strings_xml_contains_key():
    result = generate_android_layout(MINIMAL_LAYOUT)
    assert "<string name=\"login\">" in result["strings_xml"]


def test_missing_layout_width_emits_warning():
    layout = {**MINIMAL_LAYOUT, "views": [{
        **MINIMAL_LAYOUT["views"][0],
        "layout_width": None,
    }]}
    result = generate_android_layout(layout)
    assert result.get("warnings")


def test_children_nested_correctly():
    layout = {
        "screen_name": "Test",
        "root_layout": "ConstraintLayout",
        "views": [{
            "id": "fragment_test_til_email",
            "type": "TextInputLayout",
            "layout_width": "match_parent",
            "layout_height": "wrap_content",
            "constraints": {"top_to_top": "parent", "start_to_start": "parent", "end_to_end": "parent"},
            "children": [{
                "id": "fragment_test_et_email",
                "type": "TextInputEditText",
                "layout_width": "match_parent",
                "layout_height": "wrap_content",
                "input_type": "textEmailAddress",
            }]
        }],
    }
    root = _parse(generate_android_layout(layout))
    ns = "http://schemas.android.com/apk/res/android"
    # Find TextInputLayout by searching all elements for the matching id attribute
    til_el = None
    for el in root.iter():
        if el.get(f"{{{ns}}}id") == "@+id/fragment_test_til_email":
            til_el = el
            break
    assert til_el is not None, "TextInputLayout element not found"
    # Its direct children should contain TextInputEditText
    child_ids = [c.get(f"{{{ns}}}id", "") for c in til_el]
    assert any("fragment_test_et_email" in cid for cid in child_ids), (
        f"Expected nested child not found. Children: {child_ids}"
    )


def test_min_touch_target_injected_on_button():
    root = _parse(generate_android_layout(MINIMAL_LAYOUT))
    ns = "http://schemas.android.com/apk/res/android"
    btn = root.find(f".//*[@{{{ns}}}id='@+id/activity_login_btn_login']")
    assert btn is not None
    assert btn.get(f"{{{ns}}}minHeight") == "@dimen/min_touch_target"


def test_dimens_xml_contains_min_touch_target():
    result = generate_android_layout(MINIMAL_LAYOUT)
    assert "dimens_xml" in result
    assert "min_touch_target" in result["dimens_xml"]
