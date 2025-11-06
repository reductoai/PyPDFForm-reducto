# -*- coding: utf-8 -*-
"""
Tests for the bulk_watermarks function.

These tests verify that the batch watermark copying function produces
the same results as calling copy_watermark_widgets multiple times,
but with better performance.
"""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from PyPDFForm import PdfWrapper
from PyPDFForm.widgets.base import Widget
from PyPDFForm.widgets.text import TextField, TextWidget


def create_blank_pdf(num_pages=1):
    """Create a blank PDF with the specified number of pages."""
    pdf_writer = PdfWriter()
    for _ in range(num_pages):
        pdf_writer.add_blank_page(width=612, height=792)  # Letter size

    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output.read()


def test_batch_single_widget():
    """Test batch function with a single widget."""
    blank_pdf = create_blank_pdf(1)

    # Create a single widget
    widget = TextWidget(name="field1", page_number=1, x=10, y=10, width=100, height=20)

    # Test bulk_watermarks function
    watermarks_bulk = Widget.bulk_watermarks([widget], blank_pdf)

    # Test regular watermarks function
    watermarks_single = widget.watermarks(blank_pdf)

    # Both should produce the same number of watermarks (one per page)
    assert len(watermarks_bulk) == len(watermarks_single)

    # Both should have watermark data for page 0
    assert len(watermarks_bulk[0]) > 0
    assert len(watermarks_single[0]) > 0


def test_batch_multiple_widgets():
    """Test batch function with multiple widgets."""
    blank_pdf = create_blank_pdf(1)

    # Create multiple widgets
    widgets = []
    for i in range(5):
        widget = TextWidget(
            name=f"field{i}",
            page_number=1,
            x=10 + i * 50,
            y=10,
            width=40,
            height=20
        )
        widgets.append(widget)

    # Use bulk watermarks function
    watermarks_bulk = Widget.bulk_watermarks(widgets, blank_pdf)

    # Should have watermarks for each page (1 page in this case)
    assert len(watermarks_bulk) == 1

    # The watermark for page 0 should have content
    assert len(watermarks_bulk[0]) > 0

    # Verify it's larger than a single widget watermark (since it contains 5 widgets)
    single_widget_watermarks = widgets[0].watermarks(blank_pdf)
    assert len(watermarks_bulk[0]) > len(single_widget_watermarks[0])


def test_batch_empty_list():
    """Test batch function with empty list of widgets."""
    blank_pdf = create_blank_pdf(1)

    watermarks = Widget.bulk_watermarks([], blank_pdf)

    # Should return a list with one empty watermark (for the single page)
    assert len(watermarks) == 1
    assert watermarks[0] == b""


def test_batch_multiple_pages():
    """Test batch function with widgets on multiple pages."""
    blank_pdf = create_blank_pdf(3)

    widgets = []
    for page in range(1, 4):
        widget = TextWidget(
            name=f"page{page}_field",
            page_number=page,
            x=10,
            y=10,
            width=100,
            height=20
        )
        widgets.append(widget)

    watermarks = Widget.bulk_watermarks(widgets, blank_pdf)

    # Should have watermarks for all 3 pages
    assert len(watermarks) == 3

    # Each page should have watermark content
    for i in range(3):
        assert len(watermarks[i]) > 0


def test_batch_vs_sequential_functional_equivalence():
    """
    Comprehensive test that batch and sequential methods produce
    functionally equivalent results.
    """
    blank_pdf = create_blank_pdf(1)

    # Create widgets using sequential method (old way)
    obj_sequential = PdfWrapper(blank_pdf)
    for i in range(10):
        field = TextField(
            name=f"field{i}",
            page_number=1,
            x=10 + (i % 5) * 100,
            y=10 + (i // 5) * 50
        )
        obj_sequential.create_field(field)

    # Create widgets using batch method (new way)
    obj_batch = PdfWrapper(blank_pdf)
    fields = [
        TextField(
            name=f"field{i}",
            page_number=1,
            x=10 + (i % 5) * 100,
            y=10 + (i // 5) * 50
        )
        for i in range(10)
    ]
    obj_batch.bulk_create_fields(fields)

    # Both should have the same number of widgets
    assert len(obj_sequential.widgets) == len(obj_batch.widgets) == 10

    # Widget names should match
    assert set(obj_sequential.widgets.keys()) == set(obj_batch.widgets.keys())

    # Both should be fillable
    obj_sequential.fill({f"field{i}": f"value{i}" for i in range(10)})
    obj_batch.fill({f"field{i}": f"value{i}" for i in range(10)})

    # Values should match
    for i in range(10):
        assert obj_sequential.widgets[f"field{i}"].value == f"value{i}"
        assert obj_batch.widgets[f"field{i}"].value == f"value{i}"
