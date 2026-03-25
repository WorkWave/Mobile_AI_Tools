"""
External-dependency component checks.

Warns when layouts use components that require libraries not present in every
Android project: ConstraintLayout, RecyclerView, and Material Components.
These all need explicit NuGet (Xamarin) or Gradle dependencies.
"""
from __future__ import annotations
import xml.etree.ElementTree as ET
from shared.common import Issue, result

ANDROID_NS = "http://schemas.android.com/apk/res/android"

# Components that require an external library/NuGet package.
# Key = XML tag (or prefix), Value = required dependency name.
EXTERNAL_DEP_COMPONENTS: dict[str, str] = {
    "androidx.constraintlayout.widget.ConstraintLayout": "Xamarin.AndroidX.ConstraintLayout (or androidx.constraintlayout)",
    "androidx.recyclerview.widget.RecyclerView":         "Xamarin.AndroidX.RecyclerView (or androidx.recyclerview)",
    "androidx.coordinatorlayout.widget.CoordinatorLayout": "Xamarin.AndroidX.CoordinatorLayout (or androidx.coordinatorlayout)",
    "com.google.android.material.button.MaterialButton":           "Xamarin.Google.Android.Material (or com.google.android.material)",
    "com.google.android.material.textfield.TextInputLayout":       "Xamarin.Google.Android.Material (or com.google.android.material)",
    "com.google.android.material.textfield.TextInputEditText":     "Xamarin.Google.Android.Material (or com.google.android.material)",
    "com.google.android.material.card.MaterialCardView":           "Xamarin.Google.Android.Material (or com.google.android.material)",
    "com.google.android.material.appbar.MaterialToolbar":          "Xamarin.Google.Android.Material (or com.google.android.material)",
    "com.google.android.material.chip.Chip":                       "Xamarin.Google.Android.Material (or com.google.android.material)",
    "com.google.android.material.chip.ChipGroup":                  "Xamarin.Google.Android.Material (or com.google.android.material)",
    "com.google.android.material.floatingactionbutton.FloatingActionButton": "Xamarin.Google.Android.Material (or com.google.android.material)",
}


def validate_material(xml: str) -> dict:
    issues: list[Issue] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as e:
        return result([Issue("error", f"XML parse error: {e}", rule="schema")])

    _check_element(root, issues)
    return result(issues)


def _check_element(el: ET.Element, issues: list[Issue]) -> None:
    tag = el.tag
    vid = el.get(f"{{{ANDROID_NS}}}id", tag)

    dep = EXTERNAL_DEP_COMPONENTS.get(tag)
    if dep:
        issues.append(Issue(
            "warning",
            f"<{tag}> (id='{vid}') requires the '{dep}' library. "
            "Verify this dependency is present in the project before using this component. "
            "If not available, use a standard alternative: "
            "ConstraintLayout → RelativeLayout/LinearLayout, "
            "RecyclerView → ListView, "
            "MaterialButton → Button, "
            "TextInputEditText/TextInputLayout → EditText.",
            element_id=vid,
            rule="external_dependency",
        ))

    for child in el:
        _check_element(child, issues)
