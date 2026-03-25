"""Android naming convention checks."""
from __future__ import annotations
import re
import xml.etree.ElementTree as ET
from shared.common import Issue, result

ANDROID_NS = "http://schemas.android.com/apk/res/android"
KNOWN_PREFIXES = {"activity_", "fragment_", "row_", "dialog_"}
INTERACTIVE_TAGS = {
    "Button", "EditText", "CheckBox", "RadioButton", "Spinner", "Switch",
    "com.google.android.material.button.MaterialButton",
    "com.google.android.material.textfield.TextInputEditText",
}
SNAKE_RE = re.compile(r'^[a-z][a-z0-9_]*$')


def validate_naming(xml: str, filename: str = "") -> dict:
    issues: list[Issue] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return result([Issue("error", f"XML parse error: {e}", rule="schema")])

    if filename:
        base = filename.replace(".xml", "")
        if not any(base.startswith(p) for p in KNOWN_PREFIXES):
            issues.append(Issue("warning",
                f"Filename '{filename}' does not match a known prefix "
                f"({', '.join(sorted(KNOWN_PREFIXES))}). "
                "If this is an include or custom layout, this warning can be ignored.",
                rule="filename_prefix"))

    _check_element(root, issues)
    return result(issues)


def _check_element(el: ET.Element, issues: list[Issue]) -> None:
    vid_raw = el.get(f"{{{ANDROID_NS}}}id", "")
    vid = vid_raw.replace("@+id/", "").replace("@id/", "")

    if vid:
        if not SNAKE_RE.match(vid):
            issues.append(Issue("error",
                f"ID '{vid}' must be snake_case",
                element_id=vid, rule="snake_case"))
    else:
        tag_short = el.tag.split(".")[-1] if "." in el.tag else el.tag
        if tag_short in INTERACTIVE_TAGS:
            issues.append(Issue("error",
                f"Interactive element <{tag_short}> is missing android:id",
                rule="missing_id"))

    for child in el:
        _check_element(child, issues)
