# -*- coding: utf-8 -*-
"""
Tests for handling faulty widgets during PDF initialization.

These tests verify that PdfWrapper can gracefully handle PDFs with malformed
or faulty widgets without crashing. The core principle: skip faulty widgets,
warn the user, and continue processing.
"""

import warnings
from unittest.mock import patch

from PyPDFForm import PdfWrapper
from PyPDFForm.template import get_dropdown_choices


def test_faulty_widget_skipped_and_continues(template_stream):
    """Test that a faulty widget is skipped and processing continues."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Simulate an error in widget key extraction (affects all widget types)
        call_count = [0]

        def mock_get_widget_key(widget, use_full_name):
            call_count[0] += 1
            # Fail on first widget, succeed on others
            if call_count[0] == 1:
                raise ValueError("Simulated widget processing error")
            return f"widget_{call_count[0]}"

        with patch('PyPDFForm.template.get_widget_key', side_effect=mock_get_widget_key):
            obj = PdfWrapper(template_stream)

            # PdfWrapper should still be created successfully
            assert obj is not None

            # Should have issued at least one warning
            assert len(w) > 0
            warning_messages = [str(warning.message) for warning in w]
            assert any("Failed to process widget" in msg for msg in warning_messages)


def test_exception_during_widget_construction(template_stream):
    """Test that exceptions during widget construction are caught."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Mock construct_widget to fail
        def mock_construct_widget(widget, key):
            raise RuntimeError("Widget construction failed")

        with patch('PyPDFForm.template.construct_widget', side_effect=mock_construct_widget):
            obj = PdfWrapper(template_stream)

            # Should not crash
            assert obj is not None
            # Should have warnings
            assert len(w) > 0


def test_dropdown_with_none_choices_warns(sample_template_with_dropdown):
    """Test that dropdowns with None choices issue a warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Mock get_dropdown_choices to return None
        with patch('PyPDFForm.template.get_dropdown_choices', return_value=None):
            obj = PdfWrapper(sample_template_with_dropdown)

            # Should still create wrapper
            assert obj is not None

            # Should warn about missing choices
            assert len(w) > 0
            warning_messages = [str(warning.message) for warning in w]
            assert any("has no choices defined" in msg for msg in warning_messages)


def test_multiple_faulty_widgets_all_skipped(template_stream):
    """Test that multiple faulty widgets are all skipped."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Fail all widgets
        def mock_get_widget_key(widget, use_full_name):
            raise ValueError("All widgets are faulty")

        with patch('PyPDFForm.template.get_widget_key', side_effect=mock_get_widget_key):
            obj = PdfWrapper(template_stream)

            # Should still create wrapper (with no widgets)
            assert obj is not None
            assert len(obj.widgets) == 0

            # Should have warnings for each failed widget
            assert len(w) > 0


def test_error_types_reported_correctly(sample_template_with_dropdown):
    """Test that different error types are reported in warnings."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Simulate a TypeError
        with patch('PyPDFForm.template.get_dropdown_choices', side_effect=TypeError("test error")):
            obj = PdfWrapper(sample_template_with_dropdown)

            assert obj is not None
            warning_messages = [str(warning.message) for warning in w]
            # Should mention the error type in the warning
            assert any("TypeError" in msg for msg in warning_messages)
            assert any("test error" in msg for msg in warning_messages)


def test_get_dropdown_choices_none_handling():
    """Test that get_dropdown_choices handles None from extract_widget_property."""
    # Empty widget should return None
    result = get_dropdown_choices({})
    assert result is None


def test_dropdown_nonetype_not_iterable_error(sample_template_with_dropdown):
    """
    Test that dropdown widgets with None choices don't crash with:
    TypeError: 'NoneType' object is not iterable

    This was the original bug reported by the user.
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Simulate the exact condition that caused the original error:
        # extract_widget_property returns None for dropdown choices
        def mock_extract_widget_property(widget, patterns, default, cast_type):
            # Return None for dropdown choice patterns
            from PyPDFForm.patterns import DROPDOWN_CHOICE_PATTERNS
            if patterns == DROPDOWN_CHOICE_PATTERNS:
                return None
            # For other patterns, use a safe default
            return default

        with patch('PyPDFForm.template.extract_widget_property', side_effect=mock_extract_widget_property):
            # This should NOT raise TypeError anymore
            obj = PdfWrapper(sample_template_with_dropdown, adobe_mode=True)

            # Should successfully create wrapper
            assert obj is not None

            # Should have issued warnings about missing choices
            assert len(w) > 0
            warning_messages = [str(warning.message) for warning in w]
            assert any("has no choices defined" in msg for msg in warning_messages)


def test_indirect_object_max_length():
    """
    Test that text widgets with IndirectObject MaxLen that fail to dereference
    are still created successfully with max_length=None.

    This tests the fix for the bug where malformed PDFs with invalid
    IndirectObject references in MaxLen would cause the entire widget to be
    skipped. Now only the max_length attribute is set to None.
    """
    from io import BytesIO
    from pypdf import PdfWriter
    from pypdf.generic import (
        IndirectObject,
        DictionaryObject,
        NameObject,
        TextStringObject,
        ArrayObject,
        NumberObject,
    )

    # Create a PDF with a text widget that has an invalid IndirectObject MaxLen
    writer = PdfWriter()
    writer.add_blank_page(612, 792)

    # Widget with bad IndirectObject MaxLen
    bad_widget = DictionaryObject()
    bad_widget[NameObject("/Type")] = NameObject("/Annot")
    bad_widget[NameObject("/Subtype")] = NameObject("/Widget")
    bad_widget[NameObject("/FT")] = NameObject("/Tx")
    bad_widget[NameObject("/T")] = TextStringObject("field_with_bad_maxlen")
    bad_widget[NameObject("/Rect")] = ArrayObject([
        NumberObject(100), NumberObject(100),
        NumberObject(200), NumberObject(120)
    ])
    # Invalid IndirectObject reference (object 999 doesn't exist)
    bad_widget[NameObject("/MaxLen")] = IndirectObject(idnum=999, generation=0, pdf=None)

    # Widget with valid MaxLen for comparison
    good_widget = DictionaryObject()
    good_widget[NameObject("/Type")] = NameObject("/Annot")
    good_widget[NameObject("/Subtype")] = NameObject("/Widget")
    good_widget[NameObject("/FT")] = NameObject("/Tx")
    good_widget[NameObject("/T")] = TextStringObject("field_with_good_maxlen")
    good_widget[NameObject("/Rect")] = ArrayObject([
        NumberObject(300), NumberObject(100),
        NumberObject(400), NumberObject(120)
    ])
    good_widget[NameObject("/MaxLen")] = NumberObject(10)

    # Add widgets to page
    writer.pages[0][NameObject("/Annots")] = ArrayObject()
    writer.pages[0][NameObject("/Annots")].append(writer._add_object(bad_widget))
    writer.pages[0][NameObject("/Annots")].append(writer._add_object(good_widget))

    # Write PDF to bytes
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    # Test with PyPDFForm
    obj = PdfWrapper(pdf_bytes)

    # Both widgets should be created (not skipped)
    assert len(obj.widgets) == 2
    assert "field_with_bad_maxlen" in obj.widgets
    assert "field_with_good_maxlen" in obj.widgets

    # Widget with bad MaxLen should have max_length=None
    assert obj.widgets["field_with_bad_maxlen"].max_length is None

    # Widget with good MaxLen should have max_length=10
    assert obj.widgets["field_with_good_maxlen"].max_length == 10

    # Both widgets should be usable for filling
    filled = obj.fill(
        {
            "field_with_bad_maxlen": "test value 1",
            "field_with_good_maxlen": "test",
        }
    )
    assert filled.read() is not None


def test_indirect_object_field_flags_multiline():
    """
    Test that text widgets with IndirectObject Ff (field flags) that fail to
    dereference are still created successfully with multiline=False.

    This tests the fix for the bug where malformed PDFs with invalid
    IndirectObject references in Ff would cause the entire widget to be
    skipped. Now only the multiline attribute defaults to False.
    """
    from io import BytesIO
    from pypdf import PdfWriter
    from pypdf.generic import (
        IndirectObject,
        DictionaryObject,
        NameObject,
        TextStringObject,
        ArrayObject,
        NumberObject,
    )

    # Create a PDF with a text widget that has an invalid IndirectObject Ff
    writer = PdfWriter()
    writer.add_blank_page(612, 792)

    # Widget with bad IndirectObject Ff (field flags)
    bad_widget = DictionaryObject()
    bad_widget[NameObject("/Type")] = NameObject("/Annot")
    bad_widget[NameObject("/Subtype")] = NameObject("/Widget")
    bad_widget[NameObject("/FT")] = NameObject("/Tx")
    bad_widget[NameObject("/T")] = TextStringObject("field_with_bad_ff")
    bad_widget[NameObject("/Rect")] = ArrayObject([
        NumberObject(100), NumberObject(100),
        NumberObject(200), NumberObject(120)
    ])
    # Invalid IndirectObject reference for field flags
    bad_widget[NameObject("/Ff")] = IndirectObject(idnum=888, generation=0, pdf=None)

    # Widget with valid Ff for comparison (4096 = 0x1000 = multiline flag)
    good_widget = DictionaryObject()
    good_widget[NameObject("/Type")] = NameObject("/Annot")
    good_widget[NameObject("/Subtype")] = NameObject("/Widget")
    good_widget[NameObject("/FT")] = NameObject("/Tx")
    good_widget[NameObject("/T")] = TextStringObject("field_with_good_ff")
    good_widget[NameObject("/Rect")] = ArrayObject([
        NumberObject(300), NumberObject(100),
        NumberObject(400), NumberObject(120)
    ])
    good_widget[NameObject("/Ff")] = NumberObject(4096)  # Multiline flag

    # Add widgets to page
    writer.pages[0][NameObject("/Annots")] = ArrayObject()
    writer.pages[0][NameObject("/Annots")].append(writer._add_object(bad_widget))
    writer.pages[0][NameObject("/Annots")].append(writer._add_object(good_widget))

    # Write PDF to bytes
    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)

    # Test with PyPDFForm
    obj = PdfWrapper(pdf_bytes)

    # Both widgets should be created (not skipped)
    assert len(obj.widgets) == 2
    assert "field_with_bad_ff" in obj.widgets
    assert "field_with_good_ff" in obj.widgets

    # Widget with bad Ff should have multiline=False (safe default)
    assert obj.widgets["field_with_bad_ff"].multiline is False

    # Widget with good Ff should have multiline=True
    assert obj.widgets["field_with_good_ff"].multiline is True

    # Both widgets should be usable for filling
    filled = obj.fill(
        {
            "field_with_bad_ff": "test value 1",
            "field_with_good_ff": "test value 2",
        }
    )
    assert filled.read() is not None
