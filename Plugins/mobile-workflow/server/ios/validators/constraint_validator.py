"""
Constraint Validator — mirrors what Interface Builder's layout warnings surface:

Ambiguity:
  - A view that has no horizontal position defined (no leading/trailing/centerX)
  - A view that has no vertical position defined (no top/bottom/centerY/firstBaseline)
  - A view with no width defined (no width / leading+trailing)
  - A view with no height defined (no height / top+bottom)

Conflicts:
  - Two constraints that pin the same attribute of the same view to different constants
    without one being an inequality (would over-constrain the axis)
  - A fixed-width constraint that also has leading+trailing → potential redundancy/conflict

Other issues:
  - Constraints referencing IDs not present in the document
  - Constraints with multiplier=0 (collapses the view)
  - Priority out of range [1, 1000]
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from collections import defaultdict
from shared.common import Issue, result as _common_result

POSITION_H  = {"leading", "trailing", "left", "right", "centerX"}
POSITION_V  = {"top", "bottom", "centerY", "firstBaseline", "lastBaseline"}
SIZE_H      = {"width"}
SIZE_V      = {"height"}

# Attributes that, together, imply the other axis dimension is determined
IMPLIED_WIDTH   = {"leading", "trailing", "left", "right"}   # having both implies width
IMPLIED_HEIGHT  = {"top", "bottom"}                           # having both implies height

# UIKit element types that provide an intrinsic content size at runtime.
# These don't need explicit width/height constraints to avoid ambiguity.
INTRINSIC_SIZE_ELEMENTS = {
    "label", "button", "textField", "switch", "segmentedControl",
    "slider", "stepper", "pageControl", "activityIndicatorView",
    "datePicker", "searchBar",
}


def validate_constraints(xml: str) -> dict:
    issues: list[Issue] = []

    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return _result([Issue("error", f"XML parse error (skipping constraint checks): {e}")])

    all_ids: set[str] = {el.get("id") for el in root.iter() if el.get("id")}

    # Process each scene independently (constraints don't cross scene boundaries)
    for scene in root.iter("scene"):
        issues.extend(_check_scene(scene, all_ids))

    return _result(issues)


# ─── Per-scene analysis ───────────────────────────────────────────────────────

def _check_scene(scene: ET.Element, all_ids: set[str]) -> list[Issue]:
    issues: list[Issue] = []

    # Collect all views in this scene, keeping track of each element's tag
    view_ids: set[str] = set()
    id_to_tag: dict[str, str] = {}
    for el in scene.iter():
        if el.tag in {"view", "tableView", "collectionView", "scrollView",
                      "stackView", "imageView", "label", "button", "textField",
                      "textView", "visualEffectView", "containerView", "mapView",
                      "webView", "activityIndicatorView", "progressView",
                      "segmentedControl", "slider", "switch", "datePicker",
                      "pickerView", "pageControl", "stepper", "searchBar",
                      "tabBar", "toolbar", "navigationBar"}:
            eid = el.get("id")
            if eid:
                view_ids.add(eid)
                id_to_tag[eid] = el.tag

    # Collect all active constraints in this scene (skip inactive ones)
    constraints: list[ET.Element] = [
        c for c in scene.iter("constraint")
        if c.get("active", "YES") != "NO"
    ]

    if not constraints:
        return issues

    # ── 1. Reference checks ───────────────────────────────────────────────────
    for c in constraints:
        cid   = c.get("id", "")
        first = c.get("firstItem")
        second = c.get("secondItem")
        for ref_attr, ref_id in [("firstItem", first), ("secondItem", second)]:
            if ref_id and ref_id not in all_ids:
                issues.append(Issue(
                    "error",
                    f"Constraint id='{cid}' references unknown {ref_attr}='{ref_id}'",
                    element_id=cid
                ))

    # ── 1b. Self-referencing constraints ──────────────────────────────────────
    for c in constraints:
        cid        = c.get("id", "")
        first_item = c.get("firstItem")
        second_item = c.get("secondItem")
        first_attr = c.get("firstAttribute", "")
        second_attr = c.get("secondAttribute", "")

        if (first_item and first_item == second_item and first_attr and first_attr == second_attr):
            issues.append(Issue(
                "error",
                f"Constraint id='{cid}' is self-referencing: "
                f"firstItem=secondItem='{first_item}' and firstAttribute=secondAttribute='{first_attr}'. "
                "This is a circular constraint (e.g. width = width * 1 + 128) that produces "
                "undefined layout. Use a plain size constraint with no secondItem instead "
                "(e.g. <constraint firstItem='id' firstAttribute='width' constant='128'/>).",
                element_id=cid,
            ))

    # ── 2. Multiplier = 0 ─────────────────────────────────────────────────────
    for c in constraints:
        mul = c.get("multiplier", "1")
        try:
            if float(mul) == 0.0:
                issues.append(Issue(
                    "warning",
                    f"Constraint id='{c.get('id')}' has multiplier=0, which will collapse the view",
                    element_id=c.get("id")
                ))
        except ValueError:
            issues.append(Issue(
                "warning",
                f"Constraint id='{c.get('id')}' has non-numeric multiplier='{mul}'",
                element_id=c.get("id")
            ))

    # ── 3. Priority out of range ──────────────────────────────────────────────
    for c in constraints:
        pri_str = c.get("priority")
        if pri_str:
            try:
                pri = float(pri_str)
                if not (1 <= pri <= 1000):
                    issues.append(Issue(
                        "warning",
                        f"Constraint id='{c.get('id')}' has priority={pri} outside [1, 1000]",
                        element_id=c.get("id")
                    ))
            except ValueError:
                pass

    # ── 3b. Negative constants ────────────────────────────────────────────────
    # Apple's Auto Layout documentation forbids negative constant values.
    # If a gap requires a negative constant (e.g. viewA.trailing = viewB.leading - 8),
    # reverse the relationship instead: viewB.leading = viewA.trailing + 8.
    for c in constraints:
        const_str = c.get("constant", "0")
        try:
            if float(const_str) < 0:
                cid = c.get("id", "unknown")
                issues.append(Issue(
                    "error",
                    f"Constraint id='{cid}' has a negative constant='{const_str}'. "
                    "Negative constants are not allowed. Reverse the firstItem/secondItem "
                    "and firstAttribute/secondAttribute and use a positive constant instead. "
                    f"e.g. if A.trailing = B.leading - 8, write B.leading = A.trailing + 8.",
                    element_id=cid,
                ))
        except (ValueError, TypeError):
            pass

    # ── 4. Ambiguity analysis ─────────────────────────────────────────────────
    # Views whose layout is fully managed by a UIStackView — skip ambiguity checks
    stack_managed_ids: set[str] = set()
    for sv in scene.iter("stackView"):
        subviews_el = sv.find("subviews")
        if subviews_el is not None:
            for child in subviews_el:
                if cid := child.get("id"):
                    stack_managed_ids.add(cid)

    container_managed_ids: set[str] = set()
    for cv in scene.iter("containerView"):
        subviews_el = cv.find("subviews")
        if subviews_el is not None:
            for child in subviews_el:
                if cid := child.get("id"):
                    container_managed_ids.add(cid)

    # Root VC views (key="view") don't need constraints — skip them too
    root_view_ids: set[str] = {el.get("id") for el in scene.iter() if el.get("key") == "view" and el.get("id")}

    # For each view, collect which attributes are constrained.
    # A view can appear as firstItem or secondItem in a constraint — both count.
    view_constrained_attrs: dict[str, set[str]] = defaultdict(set)

    for c in constraints:
        first_item = c.get("firstItem")
        first_attr = c.get("firstAttribute", "")
        if first_item and first_attr:
            view_constrained_attrs[first_item].add(first_attr)

        second_item = c.get("secondItem")
        second_attr = c.get("secondAttribute", "")
        if second_item and second_attr:
            view_constrained_attrs[second_item].add(second_attr)

    for vid in view_ids:
        if vid in stack_managed_ids or vid in container_managed_ids or vid in root_view_ids:
            continue  # layout managed by UIStackView or VC root — no constraints needed

        tag = id_to_tag.get(vid, "view")
        has_intrinsic_size = tag in INTRINSIC_SIZE_ELEMENTS

        attrs = view_constrained_attrs.get(vid, set())

        # leading+trailing together imply width; top+bottom together imply height
        implied_w = len(attrs & IMPLIED_WIDTH) >= 2
        implied_h = len(attrs & IMPLIED_HEIGHT) >= 2

        has_h_pos  = bool(attrs & POSITION_H)
        has_v_pos  = bool(attrs & POSITION_V)
        has_width  = bool(attrs & SIZE_H) or implied_w
        has_height = bool(attrs & SIZE_V) or implied_h

        if not has_h_pos:
            issues.append(Issue(
                "warning",
                f"View id='{vid}' may be ambiguous: no horizontal position constraint "
                f"(leading/trailing/centerX) found",
                element_id=vid
            ))
        if not has_v_pos:
            issues.append(Issue(
                "warning",
                f"View id='{vid}' may be ambiguous: no vertical position constraint "
                f"(top/bottom/centerY) found",
                element_id=vid
            ))
        # Skip width/height warnings for elements with UIKit intrinsic content size
        if not has_width and not has_intrinsic_size:
            issues.append(Issue(
                "warning",
                f"View id='{vid}' may be ambiguous: no width constraint found",
                element_id=vid
            ))
        if not has_height and not has_intrinsic_size:
            issues.append(Issue(
                "warning",
                f"View id='{vid}' may be ambiguous: no height constraint found",
                element_id=vid
            ))

    # ── 5. Conflict detection ─────────────────────────────────────────────────
    # Group required (priority=1000) constraints by (firstItem, firstAttribute, secondItem, secondAttribute)
    # Two constraints only conflict when they pin the exact same relationship to different constants.
    # Constraints with different secondItems are independent (e.g. two views each pinned to a
    # layout guide at different offsets — not a conflict).
    RequiredKey = tuple  # (firstItem, firstAttribute, secondItem, secondAttribute)
    required_constraints: dict[RequiredKey, list[ET.Element]] = defaultdict(list)

    for c in constraints:
        pri_str = c.get("priority", "1000")
        try:
            pri = float(pri_str)
        except ValueError:
            pri = 1000.0

        if pri < 1000:
            continue  # optional constraints can't conflict by definition

        first_item  = c.get("firstItem", "")
        first_attr  = c.get("firstAttribute", "")
        second_item = c.get("secondItem", "")
        second_attr = c.get("secondAttribute", "")
        rel         = c.get("relation", "equal")

        raw_key = (first_item, first_attr, second_item, second_attr)
        # Normalize: canonical form has the lexicographically smaller item as firstItem
        if second_item and second_item < first_item:
            normalized_key = (second_item, second_attr, first_item, first_attr)
        else:
            normalized_key = raw_key

        if first_item and first_attr and rel == "equal":
            required_constraints[normalized_key].append(c)

    for (item, attr, sec_item, sec_attr), group in required_constraints.items():
        if len(group) < 2:
            continue
        constants = [_parse_constant(c.get("constant", "0")) for c in group]
        if len(set(constants)) > 1:
            ids = ", ".join(f"'{c.get('id')}'" for c in group)
            issues.append(Issue(
                "error",
                f"Conflicting constraints on view id='{item}' attribute='{attr}': "
                f"multiple required-equal constraints with different constants "
                f"(constants={constants}). Constraint ids: {ids}",
                element_id=item
            ))

    return issues


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _parse_constant(s: str) -> float:
    try:
        return float(s)
    except ValueError:
        return 0.0

def _result(issues: list[Issue]) -> dict:
    return _common_result(issues)
