# -*- coding: utf-8 -*-
"""
Tests for the copy_watermark_widgets_batch function.

These tests verify that the batch watermark copying function produces
the same results as calling copy_watermark_widgets multiple times,
but with better performance.
"""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from PyPDFForm import PdfWrapper
from PyPDFForm.watermark import copy_watermark_widgets, copy_watermark_widgets_batch
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

    # Create watermark for a single widget
    widget = TextWidget(name="field1", page_number=1, x=10, y=10, width=100, height=20)
    watermarks = widget.watermarks(blank_pdf)

    # Test batch function
    result_batch = copy_watermark_widgets_batch(
        blank_pdf,
        [watermarks],
        [["field1"]],
        [None]
    )

    # Test regular function
    result_single = copy_watermark_widgets(blank_pdf, watermarks, ["field1"], None)

    # Both should produce valid PDFs
    assert result_batch.startswith(b"%PDF")
    assert result_single.startswith(b"%PDF")

    # Both should have similar sizes (within 10% - may vary due to PDF internals)
    size_ratio = len(result_batch) / len(result_single)
    assert 0.9 <= size_ratio <= 1.1


def test_batch_multiple_widgets():
    """Test batch function with multiple widgets."""
    blank_pdf = create_blank_pdf(1)

    # Create watermarks for multiple widgets
    all_watermarks = []
    all_keys = []
    all_page_nums = []

    for i in range(5):
        widget = TextWidget(
            name=f"field{i}",
            page_number=1,
            x=10 + i * 50,
            y=10,
            width=40,
            height=20
        )
        watermarks = widget.watermarks(blank_pdf)
        all_watermarks.append(watermarks)
        all_keys.append([f"field{i}"])
        all_page_nums.append(None)

    # Use batch function
    result_batch = copy_watermark_widgets_batch(
        blank_pdf,
        all_watermarks,
        all_keys,
        all_page_nums
    )

    # Use sequential calls (simulating the old behavior)
    result_sequential = blank_pdf
    for watermarks, keys in zip(all_watermarks, all_keys):
        result_sequential = copy_watermark_widgets(
            result_sequential,
            watermarks,
            keys,
            None
        )

    # Both should produce valid PDFs
    assert result_batch.startswith(b"%PDF")
    assert result_sequential.startswith(b"%PDF")

    # Verify both have widgets by creating PdfWrapper instances
    wrapper_batch = PdfWrapper(result_batch)
    wrapper_sequential = PdfWrapper(result_sequential)

    # Both should have all 5 widgets
    assert len(wrapper_batch.widgets) == 5
    assert len(wrapper_sequential.widgets) == 5

    # Widget names should match
    assert set(wrapper_batch.widgets.keys()) == set(wrapper_sequential.widgets.keys())
    for i in range(5):
        assert f"field{i}" in wrapper_batch.widgets
        assert f"field{i}" in wrapper_sequential.widgets


def test_batch_empty_list():
    """Test batch function with empty lists."""
    blank_pdf = create_blank_pdf(1)

    result = copy_watermark_widgets_batch(
        blank_pdf,
        [],
        [],
        []
    )

    # Should return a valid PDF
    assert result.startswith(b"%PDF")

    # Should have no widgets
    wrapper = PdfWrapper(result)
    assert len(wrapper.widgets) == 0


def test_batch_multiple_pages():
    """Test batch function with widgets on multiple pages."""
    blank_pdf = create_blank_pdf(3)

    all_watermarks = []
    all_keys = []
    all_page_nums = []

    for page in range(1, 4):
        widget = TextWidget(
            name=f"page{page}_field",
            page_number=page,
            x=10,
            y=10,
            width=100,
            height=20
        )
        watermarks = widget.watermarks(blank_pdf)
        all_watermarks.append(watermarks)
        all_keys.append([f"page{page}_field"])
        all_page_nums.append(None)

    result = copy_watermark_widgets_batch(
        blank_pdf,
        all_watermarks,
        all_keys,
        all_page_nums
    )

    # Should produce valid PDF
    assert result.startswith(b"%PDF")

    # Should have all widgets
    wrapper = PdfWrapper(result)
    assert len(wrapper.widgets) == 3
    assert "page1_field" in wrapper.widgets
    assert "page2_field" in wrapper.widgets
    assert "page3_field" in wrapper.widgets


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
    obj_batch.create_fields(fields)

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
