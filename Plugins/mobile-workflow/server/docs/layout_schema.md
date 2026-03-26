# Layout JSON Schema Reference

This document describes the JSON input schemas accepted by the iOS and Android layout generators in this plugin.

---

## iOS Layout JSON Schema

Used by `generate_storyboard()` in `server/ios/validators/storyboard_generator.py`.

### Top-level formats

**Single-ViewController format:**
```json
{
  "name": "my-vc",
  "viewController": { ... }
}
```

**Multi-scene format:**
```json
{
  "scenes": [
    { "id": "main-vc", "viewController": { ... } },
    { "id": "detail-vc", "viewController": { ... } }
  ]
}
```

In the single-VC format, `name` becomes the scene ID. The first scene (or the one with `isInitial: true`) is set as the storyboard's initial view controller.

---

### ViewController fields

| Field | Type | Description |
|---|---|---|
| `type` | string | ViewController class. One of: `UIViewController`, `UITableViewController`, `UICollectionViewController`, `UINavigationController`, `UITabBarController`. Default: `UIViewController`. |
| `customClass` | string | Custom Swift/ObjC class name (e.g. `"MyViewController"`). |
| `customModule` | string | Swift module name for the custom class (optional). |
| `isInitial` | bool | Set to `true` to make this the initial VC for the storyboard. |
| `title` | string | Scene title shown in Interface Builder. |
| `views` | array | Array of View objects to add to the root view. |
| `constraints` | array | Cross-view constraints defined at the ViewController level. |
| `outlets` | array | IBOutlet connections. See Outlet format below. |
| `segues` | array | Segue connections to other scenes. See Segue format below. |

---

### View fields

| Field | Type | Description |
|---|---|---|
| `id` | string | **Required.** Semantic identifier (e.g. `"lbl-title"`). Used to reference the view in constraints and outlets. |
| `type` | string | UIKit type. See Supported View Types below. Default: `UIView`. |
| `text` | string | Label text or button fallback text. |
| `title` | string | Button title (preferred over `text` for UIButton). |
| `placeholder` | string | Placeholder text for UITextField. |
| `imageName` | string | Asset catalog image name for UIImageView. |
| `accessibilityLabel` | string | Accessibility label. |
| `accessibilityHint` | string | Accessibility hint. |
| `accessibilityIdentifier` | string | UI testing identifier. Defaults to the view's `id`. |
| `customClass` | string | Custom Swift/ObjC class name for the view. |
| `backgroundColor` | string or object | Background color. See Color formats below. |
| `isHidden` | bool | If `true`, sets `hidden="YES"`. |
| `alpha` | number | Opacity (0.0–1.0). Omit or set to `1.0` for fully opaque. |
| `clipsToBounds` | bool | If `true`, sets `clipsSubviews="YES"`. |
| `textAlignment` | string | Text alignment for UILabel (e.g. `"center"`, `"left"`, `"right"`). |
| `lineBreakMode` | string | Line break mode for UILabel. Default: `"middleTruncation"`. |
| `adjustsFontForContentSizeCategory` | bool | Dynamic Type scaling for UILabel. Default: `true`. |
| `borderStyle` | string | Border style for UITextField. Default: `"roundedRect"`. |
| `contentMode` | string | Content mode for UIImageView. Default: `"scaleAspectFit"`. |
| `axis` | string | Stack axis for UIStackView: `"vertical"` or `"horizontal"`. Default: `"vertical"`. |
| `spacing` | number | Spacing between arranged subviews in UIStackView. Default: `8`. |
| `distribution` | string | Distribution for UIStackView (e.g. `"fill"`, `"fillEqually"`, `"equalSpacing"`). Default: `"fill"`. |
| `alignment` | string | Alignment for UIStackView (e.g. `"fill"`, `"center"`, `"leading"`). Default: `"fill"`. |
| `font` | object | Font descriptor. See Font format below. |
| `subviews` | array | Nested child views (recursive). Preferred key for container views. |
| `views` | array | Alias for `subviews` (accepted for compatibility). |
| `constraints` | array | Constraints associated with this view. |
| `outlet` | string | Inline IBOutlet property name (shorthand wiring). |

#### Supported View Types

| JSON type | Storyboard element |
|---|---|
| `UILabel` | `<label>` |
| `UIButton` | `<button>` |
| `UITextField` | `<textField>` |
| `UITextView` | `<textView>` |
| `UIImageView` | `<imageView>` |
| `UIView` | `<view>` |
| `UIStackView` | `<stackView>` |
| `UITableView` | `<tableView>` |
| `UICollectionView` | `<collectionView>` |
| `UIScrollView` | `<scrollView>` |
| `UISwitch` | `<switch>` |
| `UISlider` | `<slider>` |
| `UISegmentedControl` | `<segmentedControl>` |
| `UIActivityIndicatorView` | `<activityIndicatorView>` |
| `UIProgressView` | `<progressView>` |

---

### Font format

Use `textStyle` for Dynamic Type (preferred — scales with user's text size setting):

```json
{ "textStyle": "body" }
```

Supported `textStyle` values: `largeTitle`, `title1`, `title2`, `title3`, `headline`, `subheadline`, `body`, `callout`, `footnote`, `caption1`, `caption2`.

For fixed-size fonts, use `style` and `size`:

```json
{ "style": "system",  "size": 17 }
{ "style": "bold",    "size": 14 }
{ "style": "italic",  "size": 13 }
{ "style": "custom",  "name": "HelveticaNeue-Medium", "size": 16 }
```

---

### Color formats

System color (string):
```json
"backgroundColor": "systemBackground"
```
The `Color` suffix is optional — `"systemBackground"` and `"systemBackgroundColor"` are both accepted.

Hex string:
```json
"backgroundColor": "#FF5733"
```

sRGB dict:
```json
"backgroundColor": { "red": 0.2, "green": 0.4, "blue": 0.8, "alpha": 1.0 }
```

Grayscale dict:
```json
"backgroundColor": { "white": 0.95, "alpha": 1.0 }
```

---

### Constraint formats

**Shorthand format** — anchor the view to its superview or another named view:
```json
{
  "item":      "lbl-title",
  "attribute": "leading",
  "to":        "safeArea",
  "toAttribute": "leading",
  "constant":  16
}
```

**Explicit format** — full first/second item specification:
```json
{
  "firstItem":      "lbl-title",
  "firstAttribute": "leading",
  "secondItem":     "safeArea",
  "secondAttribute": "leading",
  "constant":       16
}
```

Both formats support an optional `id` field (string). If omitted, an ID is generated deterministically from the constraint's properties.

Additional optional fields:
- `relation`: `"equal"` (default), `"lessThanOrEqual"`, `"greaterThanOrEqual"`
- `multiplier`: number, default `1.0`
- `priority`: number (1–1000), default `1000`

#### Supported constraint attributes

`leading`, `trailing`, `top`, `bottom`, `width`, `height`, `centerX`, `centerY`, `firstBaseline`, `lastBaseline`

#### Safe area reference

To anchor to the safe area layout guide, use any of these as `to` / `secondItem`:
- `"safeArea"`
- `"safeAreaLayoutGuide"`
- `"safe-area"`

---

### Outlet format

**Explicit outlet** (in the ViewController's `outlets` array):
```json
{ "property": "closeButton", "destination": "btn-close" }
```

**Inline outlet** (on the view itself):
```json
{ "id": "btn-close", "type": "UIButton", "outlet": "closeButton", ... }
```

Declaration-only outlets (with `name` but no `destination`) are silently skipped by the generator — wire them via the inline `outlet` field on the view instead.

---

### Segue format

```json
{
  "id":          "segue-to-detail",
  "destination": "detail-vc",
  "kind":        "show",
  "identifier":  "showDetail",
  "customClass": "MyCustomSegue",
  "unwindAction": "unwindToMain:"
}
```

| Field | Required | Description |
|---|---|---|
| `id` | yes | Semantic ID for the segue. |
| `destination` | yes | Scene ID of the destination ViewController. |
| `kind` | no | Segue kind: `"show"` (default), `"modal"`, `"unwind"`, etc. |
| `identifier` | no | String identifier for `prepare(for:sender:)`. |
| `customClass` | no | Custom segue class. |
| `unwindAction` | no | Unwind action selector (only for `kind: "unwind"`). |

---

### Full iOS example

```json
{
  "name": "login-vc",
  "viewController": {
    "customClass": "LoginViewController",
    "isInitial": true,
    "views": [
      {
        "id": "lbl-title",
        "type": "UILabel",
        "text": "Sign In",
        "font": { "textStyle": "title1" },
        "textAlignment": "center",
        "outlet": "titleLabel",
        "constraints": [
          {
            "firstAttribute": "top",
            "secondItem": "safeArea",
            "secondAttribute": "top",
            "constant": 40
          },
          {
            "firstAttribute": "leading",
            "secondItem": "safeArea",
            "secondAttribute": "leading",
            "constant": 16
          },
          {
            "firstAttribute": "trailing",
            "secondItem": "safeArea",
            "secondAttribute": "trailing",
            "constant": -16
          }
        ]
      },
      {
        "id": "btn-submit",
        "type": "UIButton",
        "title": "Log In",
        "outlet": "submitButton",
        "constraints": [
          {
            "firstAttribute": "top",
            "secondItem": "lbl-title",
            "secondAttribute": "bottom",
            "constant": 24
          },
          { "firstAttribute": "centerX", "secondItem": "safeArea", "secondAttribute": "centerX" }
        ]
      }
    ]
  }
}
```

---

## Android Layout JSON Schema

Used by `generate_android_layout()` in `server/android/layout_generator.py`.

The generator returns:
```json
{
  "layout_xml":  "<string — Android XML>",
  "strings":     { "key": "value" },
  "dimens_xml":  "<string — dimens resource XML>",
  "warnings":    ["<string>"]
}
```

The `strings` dict contains key→value pairs to be added to `AppStrings.resx` (the shared .NET resource file), NOT to Android's `res/values/strings.xml`.

---

### Top-level formats

**Flat format:**
```json
{
  "screen_name": "appointment_detail",
  "root_layout": "LinearLayout",
  "views": [ ... ],
  "strings": { "btn_save": "Save" }
}
```

**Nested format:**
```json
{
  "rootView": {
    "type": "LinearLayout",
    "id":   "root_container",
    "children": [ ... ]
  },
  "strings": { "btn_save": "Save" }
}
```

| Field | Description |
|---|---|
| `screen_name` | Human-readable screen name (informational only). |
| `root_layout` | Root layout type for flat format. Default: `RelativeLayout`. |
| `views` | Array of View objects (flat format). |
| `rootView` | Root view object with `type`, `id`, and `children` (nested format). |
| `strings` | Map of string key → English value for `AppStrings.resx`. |

---

### View fields

| Field | Type | Description |
|---|---|---|
| `id` | string | View ID in `snake_case` (e.g. `"btn_save"`). Becomes `@+id/btn_save` in XML. |
| `type` | string | View type. See Allowed Types below. |
| `layout_width` | string | **Required.** `"match_parent"`, `"wrap_content"`, or a dimension (e.g. `"48dp"`). Defaults to `match_parent` with a warning if omitted. |
| `layout_height` | string | **Required.** `"match_parent"`, `"wrap_content"`, or a dimension. Defaults to `wrap_content` with a warning if omitted. |
| `text` | string | `android:text` value. Use a string reference (e.g. `"@string/btn_save"`) or a literal. |
| `hint` | string | `android:hint` for EditText. |
| `input_type` | string | `android:inputType` (e.g. `"text"`, `"textPassword"`, `"number"`). |
| `text_style` | string | Text appearance shorthand. See Text Style values below. |
| `content_description` | string | `android:contentDescription` for accessibility. |
| `style` | string | XML `style` attribute value. |
| `orientation` | string | `android:orientation` for LinearLayout: `"vertical"` or `"horizontal"`. |
| `gravity` | string | `android:gravity` (e.g. `"center"`, `"center_horizontal"`). |
| `layout_weight` | string | `android:layout_weight` for LinearLayout children. |
| `margin_top` | string | `android:layout_marginTop` (e.g. `"8dp"`). |
| `margin_bottom` | string | `android:layout_marginBottom`. |
| `margin_start` | string | `android:layout_marginStart`. |
| `margin_end` | string | `android:layout_marginEnd`. |
| `padding` | string | `android:padding`. |
| `on_click` | string | Method name for `android:onClick`. Also triggers 48dp minimum touch target. |
| `children` | array | Nested child views (for container types). |

#### Allowed View Types

| Type | XML tag | Notes |
|---|---|---|
| `androidx.constraintlayout.widget.ConstraintLayout` | `ConstraintLayout` | **Preferred** for complex layouts and chat screens |
| `androidx.recyclerview.widget.RecyclerView` | `RecyclerView` | **Preferred** over ListView for all scrollable lists |
| `LinearLayout` | `LinearLayout` | Use for simple linear flows |
| `RelativeLayout` | `RelativeLayout` | Use when ConstraintLayout is overkill |
| `FrameLayout` | `FrameLayout` | Use for overlays and stacked views |
| `ScrollView` / `HorizontalScrollView` | — | Wraps a single child |
| `Button` | `Button` | Plain button (prefer `MaterialButton` for styled) |
| `com.google.android.material.button.MaterialButton` | `MaterialButton` | Preferred for styled/chip buttons |
| `EditText` | `EditText` | Plain input (prefer `TextInputLayout` for styled) |
| `com.google.android.material.textfield.TextInputLayout` | `TextInputLayout` | Preferred for styled inputs |
| `com.google.android.material.textfield.TextInputEditText` | `TextInputEditText` | Use inside TextInputLayout |
| `com.google.android.material.chip.Chip` | `Chip` | Use for suggestion/filter chips |
| `TextView` | `TextView` | — |
| `ImageView` | `ImageView` | — |
| `androidx.cardview.widget.CardView` | `CardView` | — |
| `ListView` | `ListView` | Legacy — use RecyclerView instead |

The generator emits a warning for types requiring external dependencies (ConstraintLayout, RecyclerView, Material). These warnings are informational — verify the dependency is present in the project before using. In this project all of the above are available.

---

### Text Style values

The `text_style` field maps to Material text appearance attributes:

| Value | Attribute |
|---|---|
| `headline1` | `?attr/textAppearanceHeadline1` |
| `headline2` | `?attr/textAppearanceHeadline2` |
| `headline3` | `?attr/textAppearanceHeadline3` |
| `headline4` | `?attr/textAppearanceHeadline4` |
| `headline5` | `?attr/textAppearanceHeadline5` |
| `headline6` | `?attr/textAppearanceHeadline6` |
| `subtitle1` | `?attr/textAppearanceSubtitle1` |
| `subtitle2` | `?attr/textAppearanceSubtitle2` |
| `body1` | `?attr/textAppearanceBody1` |
| `body2` | `?attr/textAppearanceBody2` |
| `caption` | `?attr/textAppearanceCaption` |
| `button` | `?attr/textAppearanceButton` |

---

### String resources

Strings defined in the `strings` map at the top level are returned as a `dict` in the generator's output. The caller is responsible for adding them to `PP.Mobile.Common/Resources/AppStrings.resx` (the shared .NET resource file). They must NOT be added to `res/values/strings.xml`.

---

### Landscape safety

- A view with a fixed `layout_height` greater than 200dp that is not inside a `ScrollView` or `HorizontalScrollView` will trigger a warning. Available height in landscape can be as low as ~320dp.
- Interactive views (`Button`, `EditText`, `ImageButton`) automatically get a minimum touch target of 48dp via `@dimen/min_touch_target`.

---

### Full Android example

```json
{
  "screen_name": "login_screen",
  "root_layout": "LinearLayout",
  "strings": {
    "lbl_sign_in":   "Sign In",
    "hint_username": "Username",
    "hint_password": "Password",
    "btn_login":     "Log In"
  },
  "views": [
    {
      "id":            "lbl_sign_in",
      "type":          "TextView",
      "layout_width":  "match_parent",
      "layout_height": "wrap_content",
      "text":          "@string/lbl_sign_in",
      "text_style":    "headline5",
      "gravity":       "center",
      "margin_top":    "40dp"
    },
    {
      "id":            "et_username",
      "type":          "EditText",
      "layout_width":  "match_parent",
      "layout_height": "wrap_content",
      "hint":          "@string/hint_username",
      "input_type":    "text",
      "margin_top":    "24dp",
      "margin_start":  "16dp",
      "margin_end":    "16dp"
    },
    {
      "id":            "et_password",
      "type":          "EditText",
      "layout_width":  "match_parent",
      "layout_height": "wrap_content",
      "hint":          "@string/hint_password",
      "input_type":    "textPassword",
      "margin_top":    "8dp",
      "margin_start":  "16dp",
      "margin_end":    "16dp"
    },
    {
      "id":            "btn_login",
      "type":          "Button",
      "layout_width":  "wrap_content",
      "layout_height": "wrap_content",
      "text":          "@string/btn_login",
      "gravity":       "center",
      "margin_top":    "24dp"
    }
  ]
}
```
