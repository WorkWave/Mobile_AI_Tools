"""Tests for Android layout validators."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

from android.validators.layout_validator    import validate_layout
from android.validators.naming_validator    import validate_naming
from android.validators.material_validator  import validate_material
from android.validators.guidelines_validator import validate_guidelines

# ── Shared valid XML ───────────────────────────────────────────────────────────

VALID_XML = '''<?xml version="1.0" encoding="utf-8"?>
<androidx.constraintlayout.widget.ConstraintLayout
    xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:app="http://schemas.android.com/apk/res-auto"
    android:layout_width="match_parent"
    android:layout_height="match_parent">
    <com.google.android.material.button.MaterialButton
        android:id="@+id/activity_login_btn_login"
        style="@style/Widget.Material3.Button"
        android:layout_width="match_parent"
        android:layout_height="wrap_content"
        android:minHeight="@dimen/min_touch_target"
        android:minWidth="@dimen/min_touch_target"
        android:text="@string/login"
        app:layout_constraintBottom_toBottomOf="parent"
        app:layout_constraintStart_toStartOf="parent"
        app:layout_constraintEnd_toEndOf="parent" />
</androidx.constraintlayout.widget.ConstraintLayout>'''


# ── layout_validator ──────────────────────────────────────────────────────────

def test_valid_xml_passes_layout():
    r = validate_layout(VALID_XML)
    assert r["error_count"] == 0

def test_missing_layout_width_is_error():
    bad = VALID_XML.replace('android:layout_width="match_parent"\n        android:layout_height="wrap_content"',
                            'android:layout_height="wrap_content"')
    r = validate_layout(bad)
    assert r["error_count"] > 0

def test_broken_constraint_reference_is_error():
    bad = VALID_XML.replace('app:layout_constraintBottom_toBottomOf="parent"',
                            'app:layout_constraintBottom_toBottomOf="@+id/nonexistent"')
    r = validate_layout(bad)
    assert r["error_count"] > 0


# ── naming_validator ──────────────────────────────────────────────────────────

def test_valid_naming_passes():
    r = validate_naming(VALID_XML, filename="activity_login.xml")
    assert r["error_count"] == 0

def test_camelcase_id_is_error():
    bad = VALID_XML.replace("activity_login_btn_login", "activityLoginBtnLogin")
    r = validate_naming(bad, filename="activity_login.xml")
    assert r["error_count"] > 0

def test_unknown_filename_prefix_is_warning_not_error():
    r = validate_naming(VALID_XML, filename="include_header.xml")
    assert r["error_count"] == 0
    assert r["warning_count"] > 0


# ── material_validator ────────────────────────────────────────────────────────

def test_valid_material_passes():
    r = validate_material(VALID_XML)
    assert r["error_count"] == 0

def test_raw_button_is_error():
    bad = VALID_XML.replace(
        "com.google.android.material.button.MaterialButton",
        "Button"
    ).replace('style="@style/Widget.Material3.Button"\n        ', "")
    r = validate_material(bad)
    assert r["error_count"] > 0

def test_raw_edit_text_is_error():
    xml = VALID_XML.replace(
        '<com.google.android.material.button.MaterialButton',
        '<EditText'
    ).replace(
        '</androidx.constraintlayout.widget.ConstraintLayout>',
        '</androidx.constraintlayout.widget.ConstraintLayout>'
    )
    r = validate_material(xml)
    assert r["error_count"] > 0


# ── guidelines_validator ──────────────────────────────────────────────────────

def test_valid_guidelines_passes():
    r = validate_guidelines(VALID_XML)
    assert r["error_count"] == 0

def test_hardcoded_string_is_error():
    bad = VALID_XML.replace('android:text="@string/login"',
                            'android:text="Login"')
    r = validate_guidelines(bad)
    assert r["error_count"] > 0

def test_hardcoded_hex_color_is_error():
    bad = VALID_XML.replace('android:layout_height="match_parent">',
                            'android:layout_height="match_parent"\n    android:background="#FF0000">')
    r = validate_guidelines(bad)
    assert r["error_count"] > 0

def test_image_view_without_content_description_is_error():
    xml = '''<?xml version="1.0" encoding="utf-8"?>
<FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent" android:layout_height="match_parent">
    <ImageView
        android:id="@+id/fragment_test_iv_logo"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content" />
</FrameLayout>'''
    r = validate_guidelines(xml)
    assert r["error_count"] > 0

def test_missing_touch_target_is_error():
    bad = VALID_XML.replace(
        'android:minHeight="@dimen/min_touch_target"\n        android:minWidth="@dimen/min_touch_target"\n        ', ""
    )
    r = validate_guidelines(bad)
    assert r["error_count"] > 0
