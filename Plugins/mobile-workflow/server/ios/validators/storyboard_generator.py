"""
Storyboard Generator
Converts a Layout JSON (see layout_schema.md) into a valid Xcode .storyboard XML string.
"""

from __future__ import annotations
import hashlib
import json
import random
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Any

# ─── ID generation ────────────────────────────────────────────────────────────

def _xcode_id(semantic: str, cache: dict[str, str]) -> str:
    """Convert a semantic id like 'lbl-title' to an Xcode-style 'aBc-12-DeF'.

    Uses MD5 for deterministic ID generation. Collision probability is low for
    typical storyboard sizes (<100 views) but not zero — the schema validator
    will catch any duplicate IDs after generation.
    """
    if semantic in cache:
        return cache[semantic]
    h = hashlib.md5(semantic.encode()).hexdigest()
    chars = (h + semantic.replace("-", "")).encode().hex()
    pool  = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    def pick(n, offset):
        return "".join(pool[int(chars[i*2:(i*2)+2], 16) % len(pool)]
                       for i in range(offset, offset + n))
    xid = f"{pick(3,0)}-{pick(2,3)}-{pick(3,5)}"
    cache[semantic] = xid
    return xid

def _fresh_id(hint: str, cache: dict[str, str]) -> str:
    raw = hint + str(random.randint(0, 0xFFFFFFFF))
    return _xcode_id(raw, cache)


# ─── Type maps ────────────────────────────────────────────────────────────────

UI_TYPE_TO_TAG: dict[str, str] = {
    "UILabel":                  "label",
    "UIButton":                 "button",
    "UITextField":              "textField",
    "UITextView":               "textView",
    "UIImageView":              "imageView",
    "UIView":                   "view",
    "UIStackView":              "stackView",
    "UITableView":              "tableView",
    "UICollectionView":         "collectionView",
    "UIScrollView":             "scrollView",
    "UISwitch":                 "switch",
    "UISlider":                 "slider",
    "UISegmentedControl":       "segmentedControl",
    "UIActivityIndicatorView":  "activityIndicatorView",
    "UIProgressView":           "progressView",
}

VC_TYPE_TO_TAG: dict[str, str] = {
    "UIViewController":             "viewController",
    "UITableViewController":        "tableViewController",
    "UICollectionViewController":   "collectionViewController",
    "UINavigationController":       "navigationController",
    "UITabBarController":           "tabBarController",
}

ATTR_MAP: dict[str, str] = {
    "leading":              "leading",
    "trailing":             "trailing",
    "top":                  "top",
    "bottom":               "bottom",
    "width":                "width",
    "height":               "height",
    "centerX":              "centerX",
    "centerY":              "centerY",
    "firstBaseline":        "firstBaseline",
    "lastBaseline":         "lastBaseline",
}


# ─── Public entry point ───────────────────────────────────────────────────────

def generate_storyboard(layout: dict | str) -> str:
    """
    Given a Layout JSON dict (or JSON string), return a storyboard XML string.
    Raises ValueError on structural problems.
    """
    cache: dict[str, str] = {}

    if isinstance(layout, str):
        try:
            layout = json.loads(layout)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"layout must be a valid JSON object or JSON string. "
                f"JSON parse error at line {e.lineno}, col {e.colno}: {e.msg}"
            ) from e
    if not isinstance(layout, dict):
        raise ValueError(
            f"layout must be a dict or a JSON string, got {type(layout).__name__}"
        )

    # Support both single-VC and multi-scene formats
    if "scenes" in layout:
        scenes_data = layout["scenes"]
    else:
        scenes_data = [{"id": layout.get("name", "root-vc"), "viewController": layout["viewController"]}]

    # Identify initial VC
    initial_vc_semantic = None
    for s in scenes_data:
        vc = s.get("viewController", {})
        if vc.get("isInitial"):
            initial_vc_semantic = s["id"]
            break
    if initial_vc_semantic is None and scenes_data:
        initial_vc_semantic = scenes_data[0]["id"]

    initial_vc_xid = _xcode_id(initial_vc_semantic, cache) if initial_vc_semantic else None

    # Build document root
    doc = ET.Element("document", {
        "type":              "com.apple.InterfaceBuilder3.CocoaTouch.Storyboard.XIB",
        "version":           "3.0",
        "toolsVersion":      "21701",
        "targetRuntime":     "iOS.CocoaTouch",
        "propertyAccessControl": "none",
        "useAutolayout":     "YES",
        "useTraitCollections": "YES",
        "useSafeAreas":      "YES",
        "colorMatched":      "YES",
    })
    if initial_vc_xid:
        doc.set("initialViewController", initial_vc_xid)

    ET.SubElement(doc, "dependencies")  # placeholder; IB fills this
    scenes_el = ET.SubElement(doc, "scenes")

    # All view outlet/constraint cross-refs need IDs resolved before we write XML,
    # so we do a two-pass: first register all semantic IDs, then write.
    for s in scenes_data:
        _preregister_ids(s, cache)

    for s in scenes_data:
        _build_scene(scenes_el, s, cache)

    # Serialise
    raw = ET.tostring(doc, encoding="unicode")
    pretty = minidom.parseString(raw).toprettyxml(indent="    ")
    # Remove the extra XML declaration minidom adds
    lines = pretty.split("\n")
    if lines[0].startswith("<?xml"):
        lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
    return "\n".join(lines)


# ─── Pre-registration pass ────────────────────────────────────────────────────

def _preregister_ids(scene: dict, cache: dict[str, str]) -> None:
    """Walk the scene tree and prime cache for all semantic IDs."""
    _xcode_id(scene["id"], cache)
    vc = scene.get("viewController", {})
    _walk_views_for_ids(vc.get("views", []), cache)
    for seg in vc.get("segues", []):
        _xcode_id(seg["id"], cache)

def _walk_views_for_ids(views: list, cache: dict[str, str]) -> None:
    for v in views:
        _xcode_id(v["id"], cache)
        _walk_views_for_ids(v.get("subviews", []), cache)


# ─── Scene builder ────────────────────────────────────────────────────────────

def _build_scene(scenes_el: ET.Element, scene: dict, cache: dict[str, str]) -> None:
    scene_sem = scene["id"]
    scene_xid = _xcode_id(scene_sem + "-scene", cache)
    vc_data   = scene.get("viewController", {})
    vc_xid    = _xcode_id(scene_sem, cache)

    scene_el = ET.SubElement(scenes_el, "scene", {"sceneID": scene_xid})
    objs_el  = ET.SubElement(scene_el, "objects")

    vc_type = vc_data.get("type", "UIViewController")
    vc_tag  = VC_TYPE_TO_TAG.get(vc_type, "viewController")

    vc_attrs: dict[str, str] = {"id": vc_xid, "sceneMemberID": "viewController"}
    if cc := vc_data.get("customClass"):
        vc_attrs["customClass"] = cc
        if cm := vc_data.get("customModule"):
            vc_attrs["customModule"] = cm
    if title := vc_data.get("title"):
        vc_attrs["title"] = title

    vc_el = ET.SubElement(objs_el, vc_tag, vc_attrs)

    # Root view
    root_view_xid = _xcode_id(scene_sem + "-root-view", cache)
    safe_area_xid = _xcode_id(scene_sem + "-safe-area", cache)
    root_view_el = ET.SubElement(vc_el, "view", {
        "key":              "view",
        "contentMode":      "scaleToFill",
        "id":               root_view_xid,
    })
    _add_rect(root_view_el, "frame", 0, 0, 390, 844)
    _add_autoresizing(root_view_el)
    _add_color(root_view_el, "backgroundColor", "systemBackground")

    # Subviews
    subviews_el  = ET.SubElement(root_view_el, "subviews")
    constraints_el = ET.SubElement(root_view_el, "constraints")
    # Map of semantic view id → xcode id (for constraint resolution)
    # "safeArea", "safeAreaLayoutGuide", "safe-area" all resolve to the safe area guide
    view_id_map: dict[str, str] = {
        scene_sem + "-root-view": root_view_xid,
        "safeArea":               safe_area_xid,
        "safeAreaLayoutGuide":    safe_area_xid,
        "safe-area":              safe_area_xid,
    }

    all_constraints: list[dict] = []

    for view_data in vc_data.get("views", []):
        _build_view(subviews_el, view_data, view_id_map, all_constraints,
                    parent_sem=scene_sem + "-root-view", cache=cache)

    # VC-level constraints (cross-view constraints defined on the viewController)
    for c in vc_data.get("constraints", []):
        all_constraints.append(c)

    # Write collected constraints
    for c in all_constraints:
        _write_constraint(constraints_el, c, view_id_map, cache)

    # Safe area layout guide — key must be "safeArea" (not "safeAreaLayoutGuide")
    ET.SubElement(root_view_el, "viewLayoutGuide", {
        "key": "safeArea",
        "id":  safe_area_xid,
    })

    # Connections (outlets + actions)
    connections_el = ET.SubElement(vc_el, "connections")
    _build_connections(connections_el, vc_xid, vc_data, view_id_map, cache)

    # Segues
    for seg in vc_data.get("segues", []):
        dest_xid = _xcode_id(seg["destination"], cache)
        seg_attrs: dict[str, str] = {
            "destination": dest_xid,
            "kind":        seg.get("kind", "show"),
            "id":          _xcode_id(seg["id"], cache),
        }
        if ident := seg.get("identifier"):
            seg_attrs["identifier"] = ident
        if cc := seg.get("customClass"):
            seg_attrs["customClass"] = cc
        if seg.get("kind") == "unwind" and (ua := seg.get("unwindAction")):
            seg_attrs["unwindAction"] = ua
        ET.SubElement(connections_el, "segue", seg_attrs)

    # Placeholder (first responder)
    ET.SubElement(objs_el, "placeholder", {
        "placeholderIdentifier": "IBFirstResponder",
        "id": _xcode_id(scene_sem + "-first-responder", cache),
        "sceneMemberID": "firstResponder"
    })

    # Scene label
    point_el = ET.SubElement(scene_el, "point")
    point_el.set("key", "canvasLocation")
    point_el.set("x", "0")
    point_el.set("y", "0")


# ─── View builder (recursive) ─────────────────────────────────────────────────

def _build_view(
    parent_el: ET.Element,
    vdata: dict,
    view_id_map: dict[str, str],
    all_constraints: list[dict],
    parent_sem: str,
    cache: dict[str, str],
) -> None:
    sem_id  = vdata["id"]
    xid     = _xcode_id(sem_id, cache)
    view_id_map[sem_id] = xid

    ui_type = vdata.get("type", "UIView")
    tag     = UI_TYPE_TO_TAG.get(ui_type, "view")

    attrs: dict[str, str] = {
        "contentMode": "scaleToFill",
        "translatesAutoresizingMaskIntoConstraints": "NO",
        "id":          xid,
    }

    # Type-specific attributes
    if tag == "label":
        if txt := vdata.get("text"):
            attrs["text"] = txt
        if al := vdata.get("textAlignment"):
            attrs["textAlignment"] = al
        attrs["lineBreakMode"] = vdata.get("lineBreakMode", "middleTruncation")
        # Apple HIG: labels must support Dynamic Type (adjustsFontForContentSizeCategory)
        attrs["adjustsFontForContentSizeCategory"] = vdata.get("adjustsFontForContentSizeCategory", "YES")
    elif tag == "button":
        attrs["buttonType"] = "system"
    elif tag == "textField":
        if ph := vdata.get("placeholder"):
            attrs["placeholder"] = ph
        attrs["borderStyle"] = vdata.get("borderStyle", "roundedRect")
    elif tag == "imageView":
        if img := vdata.get("imageName"):
            attrs["image"] = img
        attrs["contentMode"] = vdata.get("contentMode", "scaleAspectFit")
    elif tag == "stackView":
        attrs["axis"]         = vdata.get("axis", "vertical")
        attrs["spacing"]      = str(vdata.get("spacing", 8))
        attrs["distribution"] = vdata.get("distribution", "fill")
        attrs["alignment"]    = vdata.get("alignment", "fill")

    if vdata.get("isHidden"):
        attrs["hidden"] = "YES"
    if (alpha := vdata.get("alpha")) is not None and alpha != 1.0:
        attrs["alpha"] = str(alpha)
    if vdata.get("clipsToBounds"):
        attrs["clipsSubviews"] = "YES"
    if al := vdata.get("accessibilityLabel"):
        attrs["accessibilityLabel"] = al
    if ah := vdata.get("accessibilityHint"):
        attrs["accessibilityHint"] = ah
    # Apple HIG: provide accessibilityIdentifier for UI testing (defaults to semantic id)
    attrs["accessibilityIdentifier"] = vdata.get("accessibilityIdentifier", sem_id)
    if cc := vdata.get("customClass"):
        attrs["customClass"] = cc

    view_el = ET.SubElement(parent_el, tag, attrs)

    # Frame placeholder
    _add_rect(view_el, "frame", 0, 0, 100, 44)

    # Background color
    if (bg := vdata.get("backgroundColor")) is not None:
        _add_color(view_el, "backgroundColor", bg)

    # Font
    if font := vdata.get("font"):
        _add_font(view_el, font)

    # Button title — accept either "title" (preferred) or "text"
    if tag == "button" and (txt := vdata.get("title") or vdata.get("text")):
        ET.SubElement(view_el, "state", {"key": "normal", "title": txt})

    # Subviews (recursive)
    if subviews := vdata.get("subviews"):
        sub_el = ET.SubElement(view_el, "subviews")
        sub_constraints: list[dict] = []
        for sv in subviews:
            _build_view(sub_el, sv, view_id_map, sub_constraints, parent_sem=sem_id, cache=cache)
        if sub_constraints:
            sc_el = ET.SubElement(view_el, "constraints")
            for c in sub_constraints:
                _write_constraint(sc_el, c, view_id_map, cache)

    # Collect constraints (will be written at root-view level for cross-view constraints)
    for c in vdata.get("constraints", []):
        all_constraints.append({**c, "_first_sem": sem_id, "_parent_sem": parent_sem, "_view_type": tag})

    _add_autoresizing(view_el)


# ─── Constraint writer ────────────────────────────────────────────────────────

def _write_constraint(parent_el: ET.Element, c: dict, view_id_map: dict[str, str], cache: dict[str, str]) -> None:
    # Support two formats:
    # 1. Shorthand:  { attribute, to, toAttribute, constant, ... }
    # 2. Explicit:   { firstItem, firstAttribute, secondItem, secondAttribute, constant, ... }
    if "firstAttribute" in c:
        # Explicit format — resolve semantic IDs if needed
        first_sem  = c.get("firstItem", c.get("_first_sem", ""))
        first_attr = ATTR_MAP.get(c["firstAttribute"], c["firstAttribute"])
        second_sem = c.get("secondItem")
        second_attr = ATTR_MAP.get(c.get("secondAttribute", ""), c.get("secondAttribute", ""))
    else:
        # Shorthand format — "item" specifies the view, anchors to superview
        first_sem  = c.get("item") or c.get("_first_sem", "")
        first_attr = ATTR_MAP.get(c.get("attribute", ""), c.get("attribute", ""))
        second_sem = c.get("to")
        second_attr = ATTR_MAP.get(c.get("toAttribute", ""), c.get("toAttribute", ""))

    first_xid  = view_id_map.get(first_sem, first_sem)
    second_xid = view_id_map.get(second_sem, second_sem) if second_sem else None

    cid = _xcode_id(c["id"], cache) if "id" in c else _xcode_id(f"c-{first_sem}-{first_attr}-{second_sem or 'superview'}-{c.get('constant', 0)}", cache)

    # Landscape-safe image heights: use <= and aspect ratio instead of fixed =
    relation = c.get("relation", "equal")
    constant = c.get("constant", 0)
    is_image_height = (
        first_attr == "height"
        and relation == "equal"
        and isinstance(constant, (int, float))
        and float(constant) > 80
        and c.get("_view_type") == "imageView"
    )
    if is_image_height:
        relation = "lessThanOrEqual"

    attrs: dict[str, str] = {
        "firstItem":      first_xid,
        "firstAttribute": first_attr,
        "relation":       relation,
        "id":             cid,
    }
    if second_xid:
        attrs["secondItem"]      = second_xid
        attrs["secondAttribute"] = second_attr
    if (const := c.get("constant", 0)) != 0:
        attrs["constant"] = str(const)
    if (mul := c.get("multiplier", 1.0)) != 1.0:
        attrs["multiplier"] = str(mul)
    if (pri := c.get("priority", 1000)) != 1000:
        attrs["priority"] = str(pri)

    ET.SubElement(parent_el, "constraint", attrs)

    # Emit companion aspect-ratio constraint for landscape-safe image heights
    if is_image_height:
        ar_cid = _xcode_id(f"c-ar-{first_sem}-width-height", cache)
        ET.SubElement(parent_el, "constraint", {
            "firstItem":      first_xid,
            "firstAttribute": "width",
            "secondItem":     first_xid,
            "secondAttribute": "height",
            "multiplier":     "1",
            "relation":       "equal",
            "id":             ar_cid,
        })


# ─── Connection builder ───────────────────────────────────────────────────────

def _build_connections(
    conn_el: ET.Element,
    owner_xid: str,
    vc_data: dict,
    view_id_map: dict[str, str],
    cache: dict[str, str],
) -> None:
    # VC-level outlets array.
    # Supported formats:
    #   { "property": "closeButton", "destination": "view-sem-id" }  — explicit wiring
    #   { "name": "closeButton", "type": "UIButton" }                — declaration only (skipped; wired via inline outlet on view)
    for o in vc_data.get("outlets", []):
        prop = o.get("property") or o.get("name")
        dest_sem = o.get("destination")
        if not prop:
            continue  # malformed entry — skip silently
        if not dest_sem:
            continue  # declaration-only outlet (no destination) — wired via view's inline "outlet" field
        dest_xid = view_id_map.get(dest_sem, dest_sem)
        ET.SubElement(conn_el, "outlet", {
            "property":    prop,
            "destination": dest_xid,
            "id":          _xcode_id(f"outlet-{prop}-{dest_sem}", cache),
        })

    # Inline outlet property on individual view objects (legacy / shorthand)
    def walk(vlist: list) -> None:
        for v in vlist:
            xid = view_id_map.get(v["id"], v["id"])
            if outlet := v.get("outlet"):
                ET.SubElement(conn_el, "outlet", {
                    "property":    outlet,
                    "destination": xid,
                    "id":          _xcode_id(f"outlet-{outlet}-{v['id']}", cache),
                })
            walk(v.get("subviews", []))
    walk(vc_data.get("views", []))


# ─── XML helpers ──────────────────────────────────────────────────────────────

def _add_rect(parent: ET.Element, key: str, x: int, y: int, w: int, h: int) -> None:
    ET.SubElement(parent, "rect", {
        "key": key, "x": str(x), "y": str(y), "width": str(w), "height": str(h)
    })

def _add_autoresizing(parent: ET.Element) -> None:
    ET.SubElement(parent, "autoresizingMask", {
        "key": "autoresizingMask",
        "flexibleMaxX": "YES",
        "flexibleMaxY": "YES",
    })

def _add_color(parent: ET.Element, key: str, value) -> None:
    if isinstance(value, dict):
        if sc := value.get("systemColor"):
            ET.SubElement(parent, "color", {"key": key, "systemColor": sc})
        elif "white" in value:
            ET.SubElement(parent, "color", {
                "key": key, "white": str(value["white"]), "alpha": str(value.get("alpha", 1)),
                "colorSpace": "custom", "customColorSpace": "genericGamma22GrayColorSpace",
            })
        else:
            ET.SubElement(parent, "color", {
                "key": key,
                "red": str(value.get("red", 0)), "green": str(value.get("green", 0)),
                "blue": str(value.get("blue", 0)), "alpha": str(value.get("alpha", 1)),
                "colorSpace": "custom", "customColorSpace": "sRGB",
            })
        return

    if not isinstance(value, str):
        # Silently skip non-string, non-dict values (e.g. null, boolean from AI output)
        return

    if value.startswith("#"):
        hex_c = value.lstrip("#")
        r = int(hex_c[0:2], 16) / 255
        g = int(hex_c[2:4], 16) / 255
        b = int(hex_c[4:6], 16) / 255
        ET.SubElement(parent, "color", {
            "key": key, "red": f"{r:.3f}", "green": f"{g:.3f}",
            "blue": f"{b:.3f}", "alpha": "1", "colorSpace": "custom",
            "customColorSpace": "sRGB",
        })
    else:
        # System color name. Accept both short form ("systemBackground") and
        # full Xcode form ("systemBackgroundColor") — normalize to full form.
        if not value.endswith("Color"):
            value = value + "Color"
        ET.SubElement(parent, "color", {"key": key, "systemColor": value})


# Mapping from short names to Xcode's UICTFontTextStyle values for Dynamic Type.
# Usage in Layout JSON:  "font": {"textStyle": "body"}
_TEXT_STYLE_MAP: dict[str, str] = {
    "largeTitle":   "UICTFontTextStyleLargeTitle",
    "title1":       "UICTFontTextStyleTitle1",
    "title2":       "UICTFontTextStyleTitle2",
    "title3":       "UICTFontTextStyleTitle3",
    "headline":     "UICTFontTextStyleHeadline",
    "subheadline":  "UICTFontTextStyleSubheadline",
    "body":         "UICTFontTextStyleBody",
    "callout":      "UICTFontTextStyleCallout",
    "footnote":     "UICTFontTextStyleFootnote",
    "caption1":     "UICTFontTextStyleCaption1",
    "caption2":     "UICTFontTextStyleCaption2",
}


def _add_font(parent: ET.Element, font: dict) -> None:
    # Dynamic Type text style (preferred — scales automatically with user text size)
    if text_style := font.get("textStyle"):
        xcode_style = _TEXT_STYLE_MAP.get(text_style, text_style)
        ET.SubElement(parent, "fontDescription", {
            "key":   "fontDescription",
            "style": xcode_style,
        })
        return

    style = font.get("style", "system")
    size  = str(font.get("size", 17))
    if style == "system":
        ET.SubElement(parent, "fontDescription", {"key": "fontDescription", "type": "system", "pointSize": size})
    elif style == "bold":
        ET.SubElement(parent, "fontDescription", {"key": "fontDescription", "type": "boldSystem", "pointSize": size})
    elif style == "italic":
        ET.SubElement(parent, "fontDescription", {"key": "fontDescription", "type": "italicSystem", "pointSize": size})
    elif style == "custom" and (name := font.get("name")):
        ET.SubElement(parent, "fontDescription", {"key": "fontDescription", "type": "custom", "customFontName": name, "pointSize": size})
