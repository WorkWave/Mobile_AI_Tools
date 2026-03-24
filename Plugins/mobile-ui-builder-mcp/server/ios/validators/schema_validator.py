"""
Schema Validator
- Parses the XML and checks it is well-formed
- Verifies the root element is <document> with the expected Xcode storyboard attributes
- Validates required attributes on common elements (scene, viewController, view, etc.)
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from shared.common import Issue, result as _common_result

# ─── Known/required attributes per element tag ────────────────────────────────

REQUIRED_ATTRS: dict[str, list[str]] = {
    "document":              ["type", "version", "toolsVersion", "targetRuntime"],
    "scene":                 ["sceneID"],
    "viewController":        ["id"],
    "tableViewController":   ["id"],
    "collectionViewController": ["id"],
    "navigationController":  ["id"],
    "tabBarController":      ["id"],
    "view":                  ["key"],
    "outlet":                ["property", "destination", "id"],
    "action":                ["selector", "destination", "id"],
    "segue":                 ["destination", "kind", "id"],
    "constraint":            ["firstAttribute", "id"],
}

KNOWN_SEGUE_KINDS = {
    "show", "showDetail", "present", "presentAsPopover",
    "embed", "unwind", "custom", "push", "modal", "replace"
}

KNOWN_TARGET_RUNTIMES = {
    "iOS.CocoaTouch", "AppleCocoa.CocoaTouch", "AppleCocoa", "AppleWatchKit"
}

KNOWN_DOCUMENT_TYPES = {
    "com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB",
    "com.apple.InterfaceBuilder3.CocoaTouch.XIB",
    "com.apple.InterfaceBuilder.AppleCocoaXML.Storyboard.XIB",
}

def validate_schema(xml: str) -> dict:
    issues: list[Issue] = []

    # 1. Well-formedness
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return _result([Issue("error", f"XML parse error: {e}")])

    # 2. Root element
    if root.tag != "document":
        issues.append(Issue("error", f"Root element must be <document>, got <{root.tag}>"))
        return _result(issues)

    # 3. document-level attribute checks
    doc_type = root.get("type", "")
    if doc_type and doc_type not in KNOWN_DOCUMENT_TYPES:
        issues.append(Issue("warning", f"Unrecognised document type: '{doc_type}'"))

    runtime = root.get("targetRuntime", "")
    if runtime and runtime not in KNOWN_TARGET_RUNTIMES:
        issues.append(Issue("warning", f"Unrecognised targetRuntime: '{runtime}'"))

    # 4. Required attributes on all known elements
    # Build set of VC root view IDs so we only require key="view" on those
    vc_tags = {
        "viewController", "tableViewController", "collectionViewController",
        "navigationController", "tabBarController",
    }
    vc_root_view_ids: set[str] = set()
    for vc_el in root.iter():
        if vc_el.tag in vc_tags:
            root_view = vc_el.find("view")
            if root_view is not None and root_view.get("id"):
                vc_root_view_ids.add(root_view.get("id"))

    for el in root.iter():
        required = REQUIRED_ATTRS.get(el.tag)
        if not required:
            continue
        # <view> only requires key="view" when it is the root view of a ViewController
        if el.tag == "view" and el.get("id") not in vc_root_view_ids:
            required = [a for a in required if a != "key"]
        el_id = el.get("id") or el.get("sceneID") or el.get("property")
        for attr in required:
            if not el.get(attr):
                issues.append(Issue(
                    "error",
                    f"<{el.tag}> is missing required attribute '{attr}'",
                    element_id=el_id
                ))

    # 5. Segue kind validation
    for segue in root.iter("segue"):
        kind = segue.get("kind", "")
        if kind and kind not in KNOWN_SEGUE_KINDS:
            issues.append(Issue(
                "warning",
                f"Segue id='{segue.get('id')}' has unrecognised kind '{kind}'",
                element_id=segue.get("id")
            ))

    # 6. Duplicate IDs
    seen_ids: dict[str, int] = {}
    for el in root.iter():
        eid = el.get("id")
        if eid:
            seen_ids[eid] = seen_ids.get(eid, 0) + 1
    for eid, count in seen_ids.items():
        if count > 1:
            issues.append(Issue(
                "error",
                f"Duplicate id='{eid}' found {count} times"
            ))

    # 7. Version sanity
    version = root.get("version", "")
    try:
        major = int(version.split(".")[0]) if version else 0
        if major < 3:
            issues.append(Issue("warning", f"Storyboard version '{version}' is very old"))
    except ValueError:
        issues.append(Issue("warning", f"Could not parse document version '{version}'"))

    return _result(issues)


def _result(issues: list[Issue]) -> dict:
    return _common_result(issues)
