# -*- coding: utf-8 -*-
"""
Tests for safe fill behavior.

These tests verify that the fill() method can gracefully handle errors
when setting widget values without crashing. The core principle: skip
faulty widget fills, warn the user, and continue processing.
"""

from PyPDFForm import PdfWrapper


def test_fill_with_nonexistent_widget(template_stream):
    """Test that fill handles non-existent widget keys gracefully."""
    obj = PdfWrapper(template_stream)

    # Fill with a key that doesn't exist - should not crash
    result = obj.fill({"nonexistent_widget": "some_value"})

    # Should still return the wrapper
    assert result is not None
    assert isinstance(result, PdfWrapper)


def test_fill_with_mixed_valid_and_invalid_keys(sample_template_with_dropdown):
    """Test that fill processes valid widgets even when some keys don't exist."""
    obj = PdfWrapper(sample_template_with_dropdown)

    widget_keys = list(obj.widgets.keys())
    if widget_keys:
        valid_key = widget_keys[0]

        # Mix valid and invalid keys
        result = obj.fill({
            valid_key: "valid_value",
            "nonexistent_1": "value1",
            "nonexistent_2": "value2"
        })

        # Should complete successfully
        assert result is not None


def test_fill_with_empty_data(template_stream):
    """Test that fill handles empty data dictionary."""
    obj = PdfWrapper(template_stream)

    # Should not crash with empty data
    result = obj.fill({})

    assert result is not None


def test_fill_with_none_values(sample_template_with_dropdown):
    """Test that fill handles None values gracefully."""
    obj = PdfWrapper(sample_template_with_dropdown)

    widget_keys = list(obj.widgets.keys())
    if widget_keys:
        # Fill with None value - should not crash
        result = obj.fill({widget_keys[0]: None})

        assert result is not None
