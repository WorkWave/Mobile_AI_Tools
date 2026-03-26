"""
Guidelines Validator — Apple iOS HIG and Xcode storyboard best practices.

Checks enforced:
  1.  Document flags         — useAutolayout, useSafeAreas, useTraitCollections must be "YES"
  2.  Accessibility          — interactive elements must have accessibilityLabel or accessibilityIdentifier
  3.  Dynamic Type           — labels should set adjustsFontForContentSizeCategory="YES"
  4.  Semantic colors        — root-view backgroundColor should use a system semantic color for Dark Mode
  5.  Cell reuse IDs         — tableViewCell / collectionViewCell must have a reuseIdentifier
  6.  Image content mode     — imageViews should not use the default "scaleToFill" (usually unintentional)
  7.  Missing storyboard ID  — VCs without storyboardIdentifier can't be instantiated programmatically
  8.  Landscape safety       — fixed heights and unscrollable centerY layouts clip in landscape
  9.  Scroll view layout guides — scrollViewContentLayoutGuide / scrollViewFrameLayoutGuide are invalid
      element names; the correct elements are viewLayoutGuide key="contentLayoutGuide" / key="frameLayoutGuide"
  10. Scrollable root        — every viewController should have a UIScrollView (or inherently scrollable
      view) so content doesn't clip on small screens or in landscape (~320 pt available height)
  11. Scroll view constraints — content view must have width = frameLayoutGuide.width and
      height = frameLayoutGuide.height; missing these causes ambiguous layout or no scrolling

References:
  - Apple Human Interface Guidelines: https://developer.apple.com/design/human-interface-guidelines/
  - Auto Layout Guide: https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/AutolayoutPG/
  - Dynamic Type: https://developer.apple.com/documentation/uikit/uifont/scaling_fonts_automatically
  - Supporting Dark Mode: https://developer.apple.com/documentation/uikit/appearance_customization/supporting_dark_mode_in_your_ios_app
  - Accessibility: https://developer.apple.com/documentation/accessibility
"""

from __future__ import annotations
import xml.etree.ElementTree as ET
from shared.common import Issue, result as _common_result


# Interactive UI elements that must be accessible
INTERACTIVE_TAGS = {
    "button", "textField", "textView", "switch", "slider",
    "segmentedControl", "stepper", "datePicker", "searchBar",
}

# ViewController tags that own a root <view>
VC_TAGS = {
    "viewController", "tableViewController", "collectionViewController",
    "navigationController", "tabBarController", "pageViewController",
    "splitViewController",
}

# Image content modes that are appropriate for most ImageView use cases
GOOD_IMAGE_CONTENT_MODES = {
    "scaleAspectFit", "scaleAspectFill",
    "center", "top", "bottom", "left", "right",
    "topLeft", "topRight", "bottomLeft", "bottomRight",
}


# ─── Public entry point ───────────────────────────────────────────────────────

def validate_guidelines(xml: str) -> dict:
    issues: list[Issue] = []

    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return _result([Issue("error", f"XML parse error (skipping guidelines checks): {e}")])

    issues.extend(_check_document_flags(root))
    issues.extend(_check_accessibility(root))
    issues.extend(_check_dynamic_type(root))
    issues.extend(_check_hardcoded_colors(root))
    issues.extend(_check_cell_reuse_ids(root))
    issues.extend(_check_image_content_mode(root))
    issues.extend(_check_storyboard_identifiers(root))
    issues.extend(_check_landscape_safety(root))
    issues.extend(_check_scroll_view_layout_guides(root))
    issues.extend(_check_vc_scrollable_root(root))
    issues.extend(_check_scroll_view_constraints(root))

    return _result(issues)


# ─── Check 1: Document-level flags ───────────────────────────────────────────

def _check_document_flags(root: ET.Element) -> list[Issue]:
    """
    Apple requires useAutolayout, useSafeAreas, and useTraitCollections for
    modern iOS apps targeting iPhone X+ and Dynamic Type.
    """
    issues: list[Issue] = []
    if root.tag != "document":
        return issues

    if root.get("useAutolayout", "NO") != "YES":
        issues.append(Issue(
            "error",
            'Document is missing useAutolayout="YES". '
            "Auto Layout is required for adaptive layouts across all iPhone and iPad screen sizes.",
            rule="useAutolayout",
        ))

    if root.get("useSafeAreas", "NO") != "YES":
        issues.append(Issue(
            "warning",
            'Document is missing useSafeAreas="YES". '
            "Safe areas ensure content is not obscured by the notch, home indicator, or system bars (iPhone X+). "
            "See: https://developer.apple.com/documentation/uikit/uiview/positioning_content_relative_to_the_safe_area",
            rule="useSafeAreas",
        ))

    if root.get("useTraitCollections", "NO") != "YES":
        issues.append(Issue(
            "warning",
            'Document is missing useTraitCollections="YES". '
            "Trait collections are required for size-class adaptive layouts (compact/regular) on iPad and iPhone.",
            rule="useTraitCollections",
        ))

    return issues


# ─── Check 2: Accessibility ───────────────────────────────────────────────────

def _check_accessibility(root: ET.Element) -> list[Issue]:
    """
    Per Apple HIG: all interactive controls must be accessible.
    At minimum they need an accessibilityLabel (for VoiceOver) or
    accessibilityIdentifier (for UI testing and assistive tech).
    https://developer.apple.com/design/human-interface-guidelines/accessibility
    """
    issues: list[Issue] = []

    for el in root.iter():
        if el.tag not in INTERACTIVE_TAGS:
            continue
        eid = el.get("id", "")
        has_label      = bool(el.get("accessibilityLabel"))
        has_identifier = bool(el.get("accessibilityIdentifier"))

        if not has_label and not has_identifier:
            issues.append(Issue(
                "warning",
                f"<{el.tag}> id='{eid}' is missing both accessibilityLabel and accessibilityIdentifier. "
                "Interactive elements must be accessible (VoiceOver) and identifiable (UI tests). "
                "Add accessibilityLabel for screen-reader support.",
                element_id=eid,
                rule="accessibility",
            ))

    return issues


# ─── Check 3: Dynamic Type ────────────────────────────────────────────────────

def _check_dynamic_type(root: ET.Element) -> list[Issue]:
    """
    Apple HIG mandates Dynamic Type support: labels must set
    adjustsFontForContentSizeCategory="YES" so text scales with the user's
    preferred text size in Settings > Display & Brightness > Text Size.
    https://developer.apple.com/documentation/uikit/uifont/scaling_fonts_automatically
    """
    issues: list[Issue] = []

    for label in root.iter("label"):
        eid = label.get("id", "")

        if label.get("adjustsFontForContentSizeCategory") == "YES":
            continue

        # Custom fonts (e.g. brand fonts) can't automatically scale → skip
        font_el = label.find("fontDescription")
        if font_el is not None and font_el.get("type") == "custom":
            continue

        issues.append(Issue(
            "warning",
            f"<label> id='{eid}' is missing adjustsFontForContentSizeCategory=\"YES\". "
            "Labels should scale with Dynamic Type to honour the user's preferred text size. "
            "Enable 'Automatically Adjusts Font' in Xcode's Attributes inspector or set "
            "adjustsFontForContentSizeCategory=\"YES\" in the storyboard XML.",
            element_id=eid,
            rule="dynamicType",
        ))

    return issues


# ─── Check 4: Semantic colors (Dark Mode) ─────────────────────────────────────

def _check_hardcoded_colors(root: ET.Element) -> list[Issue]:
    """
    Apple requires apps to support Dark Mode (iOS 13+).
    Root view backgroundColor should use a system semantic color such as
    'systemBackground' rather than a hard-coded RGB value that won't adapt.
    https://developer.apple.com/documentation/uikit/appearance_customization/supporting_dark_mode_in_your_ios_app
    """
    issues: list[Issue] = []

    for vc in root.iter():
        if vc.tag not in VC_TAGS:
            continue
        root_view = vc.find("view")
        if root_view is None:
            continue
        for child in root_view:
            if child.tag == "color" and child.get("key") == "backgroundColor":
                # Hard-coded: has red/green/blue attributes or colorSpace="custom"
                if child.get("red") is not None or child.get("colorSpace") == "custom":
                    vc_id = vc.get("id", "")
                    issues.append(Issue(
                        "warning",
                        f"ViewController id='{vc_id}': root view uses a hard-coded RGB backgroundColor. "
                        "Use a system semantic color (e.g. systemBackground, secondarySystemBackground) "
                        "so the view adapts automatically to Dark Mode.",
                        element_id=vc_id,
                        rule="semanticColors",
                    ))

    return issues


# ─── Check 5: Cell reuse identifiers ─────────────────────────────────────────

def _check_cell_reuse_ids(root: ET.Element) -> list[Issue]:
    """
    UITableViewCell and UICollectionViewCell must have a reuseIdentifier.
    Without one, dequeueReusableCell(withIdentifier:) will always return nil,
    causing a crash or forcing the app to allocate new cells on every scroll.
    """
    issues: list[Issue] = []

    for cell in root.iter():
        if cell.tag not in ("tableViewCell", "collectionViewCell"):
            continue
        eid = cell.get("id", "")
        if not cell.get("reuseIdentifier"):
            issues.append(Issue(
                "warning",
                f"<{cell.tag}> id='{eid}' is missing a reuseIdentifier. "
                "All prototype cells must declare a reuseIdentifier so UITableView / "
                "UICollectionView can dequeue them correctly.",
                element_id=eid,
                rule="reuseIdentifier",
            ))

    return issues


# ─── Check 6: Image content mode ─────────────────────────────────────────────

def _check_image_content_mode(root: ET.Element) -> list[Issue]:
    """
    UIImageView with contentMode="scaleToFill" distorts images unless the image
    is exactly the same aspect ratio as the view — which is rarely true.
    Apple recommends scaleAspectFit or scaleAspectFill in almost all cases.
    """
    issues: list[Issue] = []

    for img in root.iter("imageView"):
        eid  = img.get("id", "")
        mode = img.get("contentMode", "scaleToFill")
        if mode == "scaleToFill":
            issues.append(Issue(
                "info",
                f"<imageView> id='{eid}' uses contentMode='scaleToFill', which distorts images "
                "when the view's aspect ratio doesn't match the image. "
                "Consider scaleAspectFit (letterboxed) or scaleAspectFill (cropped) instead.",
                element_id=eid,
                rule="imageContentMode",
            ))

    return issues


# ─── Check 7: Storyboard identifiers ─────────────────────────────────────────

def _check_storyboard_identifiers(root: ET.Element) -> list[Issue]:
    """
    ViewControllers without a storyboardIdentifier cannot be instantiated
    programmatically via UIStoryboard.instantiateViewController(withIdentifier:).
    This is an info-level hint, not a hard error.
    """
    issues: list[Issue] = []

    for vc in root.iter():
        if vc.tag not in VC_TAGS:
            continue
        eid = vc.get("id", "")
        if not vc.get("storyboardIdentifier"):
            # Skip container VCs that are rarely instantiated directly
            if vc.tag in ("navigationController", "tabBarController",
                          "pageViewController", "splitViewController"):
                continue
            issues.append(Issue(
                "info",
                f"<{vc.tag}> id='{eid}' has no storyboardIdentifier. "
                "Without a storyboard ID it cannot be instantiated programmatically "
                "via UIStoryboard.instantiateViewController(withIdentifier:).",
                element_id=eid,
                rule="storyboardIdentifier",
            ))

    return issues


# ─── Check 8: Landscape safety ────────────────────────────────────────────────

def _check_landscape_safety(root: ET.Element) -> list[Issue]:
    """
    Views with large fixed heights clip in landscape where vertical space is ~320 pt.
    ImageViews with a fixed height > 80 pt outside a UIScrollView are flagged.
    Centered containers (centerY constraint) without a scrollable ancestor are flagged.

    Fix: use relation="lessThanOrEqual" for image heights + add an aspect-ratio constraint.
    Wrap welcome/content areas in UIScrollView so they scroll when content overflows.
    """
    issues: list[Issue] = []

    def _has_scroll_ancestor(el: ET.Element, all_elements: dict) -> bool:
        """Not easily traversable bottom-up in ElementTree; we use a pre-built parent map."""
        return False  # conservative — evaluated via parent_map below

    # Build parent map for bottom-up traversal
    parent_map: dict[ET.Element, ET.Element] = {}
    for parent in root.iter():
        for child in parent:
            parent_map[child] = parent

    def _inside_scroll_view(el: ET.Element) -> bool:
        node = el
        while node in parent_map:
            node = parent_map[node]
            if node.tag == "scrollView":
                return True
        return False

    # Check imageViews with fixed large heights not inside a scrollView
    for img in root.iter("imageView"):
        if _inside_scroll_view(img):
            continue
        eid = img.get("id", "")
        # Look for fixed height constraints on this imageView (child constraints)
        for constraint in img.iter("constraint"):
            first_attr = constraint.get("firstAttribute", "")
            relation   = constraint.get("relation", "equal")  # absent = equal
            constant   = float(constraint.get("constant", "0") or "0")
            if first_attr == "height" and relation == "equal" and constant > 80:
                issues.append(Issue(
                    "warning",
                    f"<imageView> id='{eid}' has a fixed height={constant:.0f}pt that may clip "
                    "in landscape (available height ~320 pt on iPhone). "
                    "Use relation=\"lessThanOrEqual\" for the height constraint and add an "
                    "aspect-ratio constraint (width = height * multiplier) so the image "
                    "scales down gracefully. If the parent container is not scrollable, "
                    "consider wrapping it in a UIScrollView.",
                    element_id=eid,
                    rule="landscapeSafety",
                ))

    # Check UIViews that use centerY anchoring without a scrollable ancestor —
    # these will be clipped rather than scrollable when content is taller than the viewport.
    for view in root.iter("view"):
        if _inside_scroll_view(view):
            continue
        vid = view.get("id", "")
        # Find root-level constraints that reference this view's centerY
        for constraint in root.iter("constraint"):
            if (constraint.get("firstItem") == vid and
                    constraint.get("firstAttribute") == "centerY" and
                    constraint.get("relation", "equal") == "equal"):
                issues.append(Issue(
                    "info",
                    f"<view> id='{vid}' is vertically centred (centerY constraint) but is not "
                    "inside a UIScrollView. In landscape, if its content height exceeds the "
                    "available space the content will be clipped rather than scrollable. "
                    "Wrap the view in a UIScrollView and use a lower-priority centerY "
                    "(priority='500') so it centres when there is room but scrolls when needed.",
                    element_id=vid,
                    rule="landscapeSafety",
                ))
                break  # one warning per view is enough

    return issues


# ─── Check 8: Scroll view layout guide element names ─────────────────────────

def _check_scroll_view_layout_guides(root: ET.Element) -> list[Issue]:
    """
    Xcode storyboards use <viewLayoutGuide key="contentLayoutGuide"> and
    <viewLayoutGuide key="frameLayoutGuide"> as child elements of a scrollView.

    The element names scrollViewContentLayoutGuide and scrollViewFrameLayoutGuide
    are NOT valid and cause Xcode to refuse to open the storyboard with:
      "Failed to unarchive element named 'scrollViewContentLayoutGuide'"

    Every existing storyboard in this project (LocationDocumentList, ActivitiesContainerVC,
    Main) uses the correct <viewLayoutGuide key="contentLayoutGuide"> form.
    """
    issues: list[Issue] = []
    for bad_tag in ("scrollViewContentLayoutGuide", "scrollViewFrameLayoutGuide"):
        for el in root.iter(bad_tag):
            parent_id = el.get("id", "unknown")
            issues.append(Issue(
                "error",
                f"Invalid storyboard element <{bad_tag}> (id='{parent_id}'). "
                "Xcode cannot unarchive this element and will refuse to open the storyboard. "
                "Replace with the correct form: "
                '<viewLayoutGuide key="contentLayoutGuide" id="..."/> and '
                '<viewLayoutGuide key="frameLayoutGuide" id="..."/> '
                "as direct children of the <scrollView> element.",
                element_id=parent_id,
                rule="scrollViewLayoutGuides",
            ))
    return issues


# ─── Check 10: Every ViewController needs a scrollable root ──────────────────

def _check_vc_scrollable_root(root: ET.Element) -> list[Issue]:
    """
    In landscape on iPhone SE the available height is only ~320 pt. A screen with
    fixed-position content and no scroll view will clip anything that doesn't fit.

    Every viewController should have at least one UIScrollView, UITableView, or
    UICollectionView somewhere in its hierarchy. tableViewController and
    collectionViewController are inherently scrollable — skip them.
    navigationController / tabBarController are containers — skip them too.
    """
    SKIP_VC_TAGS = {
        "tableViewController", "collectionViewController",
        "navigationController", "tabBarController",
        "pageViewController",   "splitViewController",
    }
    SCROLLABLE_TAGS = {"scrollView", "tableView", "collectionView", "textView"}

    issues: list[Issue] = []

    for vc in root.iter():
        if vc.tag not in VC_TAGS or vc.tag in SKIP_VC_TAGS:
            continue
        vc_id    = vc.get("id", "")
        vc_class = vc.get("customClass") or vc_id

        if not any(el.tag in SCROLLABLE_TAGS for el in vc.iter()):
            issues.append(Issue(
                "warning",
                f"<viewController> id='{vc_id}' (class: {vc_class}) has no UIScrollView, "
                "UITableView, or UICollectionView in its view hierarchy. "
                "In landscape mode the available vertical height is ~320 pt on iPhone SE — "
                "any content taller than that will be clipped. "
                "Wrap the main content in a UIScrollView so it scrolls when the viewport is small.",
                element_id=vc_id,
                rule="scrollableRoot",
            ))

    return issues


# ─── Check 11: Scroll view content constraints ────────────────────────────────

def _check_scroll_view_constraints(root: ET.Element) -> list[Issue]:
    """
    For Auto Layout to determine a scroll view's content size, its content view must:
      1. Pin all 4 edges to contentLayoutGuide (defines the scrollable area).
      2. Have width  = frameLayoutGuide.width  → prevents unintended horizontal scrolling.
      3. Have height >= frameLayoutGuide.height → content centres in portrait and scrolls
         in landscape instead of being clipped (greaterThanOrEqual relation).

    A scroll view that is missing rules 2 or 3 will either scroll in both axes
    or show an ambiguous layout warning in Xcode.
    """
    issues: list[Issue] = []

    for sv in root.iter("scrollView"):
        sv_id = sv.get("id", "")

        # Collect the two layout guide IDs declared directly on this scrollView
        content_guide_id: str | None = None
        frame_guide_id:   str | None = None
        for lg in sv:
            if lg.tag == "viewLayoutGuide":
                key = lg.get("key", "")
                if key == "contentLayoutGuide":
                    content_guide_id = lg.get("id")
                elif key == "frameLayoutGuide":
                    frame_guide_id = lg.get("id")

        # No layout guides at all → older-style scroll view; skip constraint checks
        # but remind the developer to add them.
        if content_guide_id is None and frame_guide_id is None:
            issues.append(Issue(
                "warning",
                f"<scrollView> id='{sv_id}' has no viewLayoutGuide children. "
                "Add <viewLayoutGuide key=\"contentLayoutGuide\" id=\"...\"/> and "
                "<viewLayoutGuide key=\"frameLayoutGuide\" id=\"...\"/> as direct children "
                "so Auto Layout can determine the scroll content size. "
                "Without them the scroll view's content size is ambiguous.",
                element_id=sv_id,
                rule="scrollViewConstraints",
            ))
            continue

        # All constraints reachable from this scrollView element
        sv_constraints = list(sv.iter("constraint"))

        def _refs(c: ET.Element, guide_id: str | None, attr: str) -> bool:
            """True if constraint c links `attr` to `guide_id`."""
            if guide_id is None:
                return False
            return (
                (c.get("firstItem")  == guide_id and c.get("firstAttribute")  == attr) or
                (c.get("secondItem") == guide_id and c.get("secondAttribute") == attr)
            )

        # Rule 2: content view width = frameLayoutGuide.width
        if frame_guide_id and not any(_refs(c, frame_guide_id, "width") for c in sv_constraints):
            issues.append(Issue(
                "warning",
                f"<scrollView> id='{sv_id}' content view is missing "
                "width = frameLayoutGuide.width constraint. "
                "Without it the scroll view may scroll horizontally. "
                f"Add: <constraint firstItem=\"[contentView]\" firstAttribute=\"width\" "
                f"secondItem=\"{frame_guide_id}\" secondAttribute=\"width\"/>",
                element_id=sv_id,
                rule="scrollViewConstraints",
            ))

        # Rule 3: content view height >= frameLayoutGuide.height
        has_height_ge = any(
            c.get("relation") == "greaterThanOrEqual" and _refs(c, frame_guide_id, "height")
            for c in sv_constraints
        )
        if frame_guide_id and not has_height_ge:
            issues.append(Issue(
                "info",
                f"<scrollView> id='{sv_id}' content view is missing "
                "height >= frameLayoutGuide.height constraint. "
                "Without it the content view won't centre vertically in portrait when shorter "
                "than the viewport, and may not scroll correctly in landscape. "
                f"Add: <constraint firstItem=\"[contentView]\" firstAttribute=\"height\" "
                f"relation=\"greaterThanOrEqual\" secondItem=\"{frame_guide_id}\" secondAttribute=\"height\"/>",
                element_id=sv_id,
                rule="scrollViewConstraints",
            ))

    return issues


# ─── Result builder ───────────────────────────────────────────────────────────

def _result(issues: list[Issue]) -> dict:
    return _common_result(issues)
