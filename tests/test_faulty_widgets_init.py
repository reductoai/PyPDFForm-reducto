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
