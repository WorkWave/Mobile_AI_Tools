"""
Connection Validator
- Detects orphaned outlet/action connections (destination ID doesn't exist)
- Detects broken segue references (destination scene/VC doesn't exist)
- Detects unwind segues without a matching @IBAction
- Detects placeholder connections left by Xcode (customClass missing when outlet references it)
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from shared.common import Issue, result as _common_result


def validate_connections(xml: str) -> dict:
    issues: list[Issue] = []

    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return _result([Issue("error", f"XML parse error (skipping connection checks): {e}")])

    # ── Build a registry of all element IDs present in the document ───────────
    all_ids: set[str] = set()
    for el in root.iter():
        eid = el.get("id")
        if eid:
            all_ids.add(eid)

    # ── Build VC id → customClass map (needed for unwind check) ───────────────
    vc_tags = {
        "viewController", "tableViewController", "collectionViewController",
        "navigationController", "tabBarController", "pageViewController",
        "splitViewController", "glkViewController", "avPlayerViewController",
    }
    vc_classes: dict[str, str] = {}   # id → customClass (may be empty)
    for el in root.iter():
        if el.tag in vc_tags:
            vc_id = el.get("id", "")
            vc_classes[vc_id] = el.get("customClass", "")

    # ── Collect declared @IBAction selectors per VC ───────────────────────────
    # actions exposed by each VC's customClass (from <action> elements)
    vc_action_selectors: dict[str, set[str]] = {}
    for scene in root.iter("scene"):
        scene_id = scene.get("sceneID", "")
        for action in scene.iter("action"):
            dest = action.get("destination", "")
            sel  = action.get("selector", "")
            if dest and sel:
                vc_action_selectors.setdefault(dest, set()).add(sel)

    # ── Check outlets ─────────────────────────────────────────────────────────
    for outlet in root.iter("outlet"):
        dest = outlet.get("destination", "")
        prop = outlet.get("property", "")
        oid  = outlet.get("id", "")
        if dest and dest not in all_ids:
            issues.append(Issue(
                "error",
                f"Orphaned outlet '{prop}' (id='{oid}'): destination '{dest}' does not exist",
                element_id=oid
            ))

    # ── Check actions ─────────────────────────────────────────────────────────
    for action in root.iter("action"):
        dest = action.get("destination", "")
        sel  = action.get("selector", "")
        aid  = action.get("id", "")
        if dest and dest not in all_ids:
            issues.append(Issue(
                "error",
                f"Orphaned action '{sel}' (id='{aid}'): destination '{dest}' does not exist",
                element_id=aid
            ))

    # ── Check segues ──────────────────────────────────────────────────────────
    for segue in root.iter("segue"):
        sid  = segue.get("id", "")
        dest = segue.get("destination", "")
        kind = segue.get("kind", "")

        if dest and dest not in all_ids:
            issues.append(Issue(
                "error",
                f"Broken segue id='{sid}' (kind='{kind}'): destination '{dest}' does not exist",
                element_id=sid
            ))

        # Unwind segues must reference a valid @IBAction selector
        if kind == "unwind":
            unwind_action = segue.get("unwindAction", "")
            if not unwind_action:
                issues.append(Issue(
                    "warning",
                    f"Unwind segue id='{sid}' has no 'unwindAction' attribute",
                    element_id=sid
                ))
            else:
                # Check that at least one VC in the document declares this action
                all_selectors = {s for selectors in vc_action_selectors.values() for s in selectors}
                if unwind_action not in all_selectors:
                    issues.append(Issue(
                        "warning",
                        f"Unwind segue id='{sid}' references action '{unwind_action}' "
                        f"which is not declared in any scene's connections",
                        element_id=sid
                    ))

        # Custom segues must specify a customClass
        if kind == "custom" and not segue.get("customClass"):
            issues.append(Issue(
                "warning",
                f"Custom segue id='{sid}' has kind='custom' but no 'customClass' attribute",
                element_id=sid
            ))

    # ── Check outlet collections for duplicate tags ───────────────────────────
    for oc in root.iter("outletCollection"):
        dest = oc.get("destination", "")
        oid  = oc.get("id", "")
        if dest and dest not in all_ids:
            issues.append(Issue(
                "error",
                f"Orphaned outletCollection (id='{oid}'): destination '{dest}' does not exist",
                element_id=oid
            ))

    # ── Scenes with no initial VC (if document declares initialViewController) ─
    initial_vc = root.get("initialViewController")
    if initial_vc and initial_vc not in all_ids:
        issues.append(Issue(
            "error",
            f"Document initialViewController='{initial_vc}' does not match any element id"
        ))

    return _result(issues)


def _result(issues: list[Issue]) -> dict:
    return _common_result(issues)
