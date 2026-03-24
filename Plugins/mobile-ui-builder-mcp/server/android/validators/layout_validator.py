"""Android layout XML — structural and constraint checks."""
from __future__ import annotations
import xml.etree.ElementTree as ET
from shared.common import Issue, result

ANDROID_NS = "http://schemas.android.com/apk/res/android"
APP_NS     = "http://schemas.android.com/apk/res-auto"
CONSTRAINT_ATTRS = [
    f"{{{APP_NS}}}layout_constraintTop_toTopOf",
    f"{{{APP_NS}}}layout_constraintTop_toBottomOf",
    f"{{{APP_NS}}}layout_constraintBottom_toBottomOf",
    f"{{{APP_NS}}}layout_constraintBottom_toTopOf",
    f"{{{APP_NS}}}layout_constraintStart_toStartOf",
    f"{{{APP_NS}}}layout_constraintStart_toEndOf",
    f"{{{APP_NS}}}layout_constraintEnd_toEndOf",
    f"{{{APP_NS}}}layout_constraintEnd_toStartOf",
]


def validate_layout(xml: str) -> dict:
    issues: list[Issue] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return result([Issue("error", f"XML parse error: {e}", rule="schema")])

    all_ids: set[str] = set()
    _collect_ids(root, all_ids)

    is_constraint = "ConstraintLayout" in root.tag
    _check_views(root, all_ids, is_constraint, issues, depth=0, is_root=True)
    return result(issues)


def _collect_ids(el: ET.Element, ids: set[str]) -> None:
    vid = el.get(f"{{{ANDROID_NS}}}id", "")
    if vid:
        ids.add(vid.replace("@+id/", "").replace("@id/", ""))
    for child in el:
        _collect_ids(child, ids)


NON_CONSTRAINT_CONTAINERS = {
    "LinearLayout", "FrameLayout", "RelativeLayout",
    "androidx.coordinatorlayout.widget.CoordinatorLayout",
    "com.google.android.material.card.MaterialCardView",
    "ScrollView", "HorizontalScrollView",
}


def _is_constraint_layout(tag: str) -> bool:
    return "ConstraintLayout" in tag


def _check_views(
    el: ET.Element, all_ids: set[str], parent_is_cl: bool, issues: list[Issue],
    depth: int, is_root: bool,
) -> None:
    if depth > 4:
        issues.append(Issue("error", "View hierarchy depth exceeds 4 levels", rule="nesting"))

    vid = el.get(f"{{{ANDROID_NS}}}id", "?")

    if not is_root:
        if not el.get(f"{{{ANDROID_NS}}}layout_width"):
            issues.append(Issue("error", f"Missing layout_width on '{vid}'",
                                element_id=vid, rule="layout_width"))
        if not el.get(f"{{{ANDROID_NS}}}layout_height"):
            issues.append(Issue("error", f"Missing layout_height on '{vid}'",
                                element_id=vid, rule="layout_height"))

        # Only check ConstraintLayout constraints when the DIRECT parent is a ConstraintLayout
        if parent_is_cl:
            horiz = any(el.get(a) for a in CONSTRAINT_ATTRS if "Start" in a or "End" in a)
            vert  = any(el.get(a) for a in CONSTRAINT_ATTRS if "Top" in a or "Bottom" in a)
            if not horiz:
                issues.append(Issue("warning",
                    f"'{vid}' has no horizontal constraint", element_id=vid, rule="constraint"))
            if not vert:
                issues.append(Issue("warning",
                    f"'{vid}' has no vertical constraint", element_id=vid, rule="constraint"))

            for attr in CONSTRAINT_ATTRS:
                ref = el.get(attr, "")
                if ref and ref != "parent":
                    ref_id = ref.replace("@+id/", "").replace("@id/", "")
                    if ref_id not in all_ids:
                        issues.append(Issue("error",
                            f"'{vid}' references unknown id '{ref_id}'",
                            element_id=vid, rule="broken_reference"))

    # Children inherit constraint-check only if THIS element is a ConstraintLayout
    child_parent_is_cl = _is_constraint_layout(el.tag)
    for child in el:
        _check_views(child, all_ids, child_parent_is_cl, issues, depth + 1, is_root=False)
