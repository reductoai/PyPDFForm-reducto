# -*- coding: utf-8 -*-
"""
Tests for the create_fields batch method.

These tests verify that create_fields efficiently creates multiple widgets
in a single operation, and that the resulting widgets behave identically
to those created individually with create_field.
"""

from io import BytesIO

import pytest
from pypdf import PdfWriter

from PyPDFForm import PdfWrapper
from PyPDFForm.widgets.checkbox import CheckBoxField
from PyPDFForm.widgets.dropdown import DropdownField
from PyPDFForm.widgets.text import TextField


def create_blank_pdf(num_pages=1):
    """Create a blank PDF with the specified number of pages."""
    pdf_writer = PdfWriter()
    for _ in range(num_pages):
        pdf_writer.add_blank_page(width=612, height=792)  # Letter size

    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output.read()


def test_create_fields_single_text_field():
    """Test creating a single text field using bulk_create_fields."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = [
        TextField(name="field1", page_number=1, x=10, y=10, width=100, height=20)
    ]

    result = obj.bulk_create_fields(fields)

    # Should return the wrapper object
    assert result is obj
    # Should have the widget
    assert "field1" in obj.widgets
    assert obj.widgets["field1"].name == "field1"


def test_create_fields_multiple_text_fields():
    """Test creating multiple text fields using bulk_create_fields."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = [
        TextField(name=f"field{i}", page_number=1, x=10 + i * 50, y=10)
        for i in range(10)
    ]

    obj.bulk_create_fields(fields)

    # Should have all widgets
    assert len(obj.widgets) == 10
    for i in range(10):
        assert f"field{i}" in obj.widgets


def test_create_fields_mixed_widget_types():
    """Test creating different types of widgets in a batch."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = [
        TextField(name="text1", page_number=1, x=10, y=10),
        TextField(name="text2", page_number=1, x=10, y=50),
        CheckBoxField(name="check1", page_number=1, x=10, y=90),
        CheckBoxField(name="check2", page_number=1, x=10, y=130),
        DropdownField(
            name="dropdown1", page_number=1, x=10, y=170, options=["A", "B", "C"]
        ),
    ]

    obj.bulk_create_fields(fields)

    # Should have all widgets
    assert len(obj.widgets) == 5
    assert "text1" in obj.widgets
    assert "text2" in obj.widgets
    assert "check1" in obj.widgets
    assert "check2" in obj.widgets
    assert "dropdown1" in obj.widgets


def test_create_fields_across_multiple_pages():
    """Test creating widgets across multiple pages."""
    blank_pdf = create_blank_pdf(3)
    obj = PdfWrapper(blank_pdf)

    fields = [
        TextField(name="page1_field", page_number=1, x=10, y=10),
        TextField(name="page2_field", page_number=2, x=10, y=10),
        TextField(name="page3_field", page_number=3, x=10, y=10),
    ]

    obj.bulk_create_fields(fields)

    assert len(obj.widgets) == 3
    assert "page1_field" in obj.widgets
    assert "page2_field" in obj.widgets
    assert "page3_field" in obj.widgets


def test_create_fields_with_widget_properties():
    """Test that widget properties are correctly set."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = [
        TextField(
            name="styled_field",
            page_number=1,
            x=10,
            y=10,
            width=200,
            height=30,
            font_size=14,
            max_length=50,
        )
    ]

    obj.bulk_create_fields(fields)

    # Should have the widget with correct name
    widget = obj.widgets["styled_field"]
    assert widget.name == "styled_field"
    # max_length is set correctly
    assert widget.max_length == 50


def test_create_fields_then_fill():
    """Test that widgets created with bulk_create_fields can be filled."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = [
        TextField(name="field1", page_number=1, x=10, y=10),
        TextField(name="field2", page_number=1, x=10, y=50),
        CheckBoxField(name="check1", page_number=1, x=10, y=90),
    ]

    obj.bulk_create_fields(fields)

    # Fill the created widgets
    obj.fill({"field1": "Test1", "field2": "Test2", "check1": True})

    # Verify values
    assert obj.widgets["field1"].value == "Test1"
    assert obj.widgets["field2"].value == "Test2"
    assert obj.widgets["check1"].value is True


def test_create_fields_empty_list():
    """Test bulk_create_fields with an empty list."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    result = obj.bulk_create_fields([])

    # Should return the wrapper
    assert result is obj
    # Should have no widgets
    assert len(obj.widgets) == 0


def test_create_fields_method_chaining():
    """Test that bulk_create_fields supports method chaining."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = [TextField(name="field1", page_number=1, x=10, y=10)]

    result = obj.bulk_create_fields(fields).fill({"field1": "test"})

    assert result is obj
    assert obj.widgets["field1"].value == "test"


def test_create_fields_equivalence_with_create_field():
    """
    Test that bulk_create_fields produces the same result as multiple create_field calls.

    This verifies functional equivalence between the batch and single methods.
    """
    blank_pdf = create_blank_pdf(1)

    # Create using individual create_field calls
    obj1 = PdfWrapper(blank_pdf)
    for i in range(5):
        obj1.create_field(TextField(name=f"field{i}", page_number=1, x=10 + i * 50, y=10))

    # Create using batch bulk_create_fields
    obj2 = PdfWrapper(blank_pdf)
    fields = [
        TextField(name=f"field{i}", page_number=1, x=10 + i * 50, y=10) for i in range(5)
    ]
    obj2.bulk_create_fields(fields)

    # Both should have the same widgets
    assert len(obj1.widgets) == len(obj2.widgets) == 5
    assert set(obj1.widgets.keys()) == set(obj2.widgets.keys())

    # Widget names should match
    for key in obj1.widgets:
        assert obj1.widgets[key].name == obj2.widgets[key].name


def test_create_fields_with_dropdown_options():
    """Test creating dropdown fields with options."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = [
        DropdownField(
            name="dropdown1", page_number=1, x=10, y=10, options=["Option 1", "Option 2"]
        ),
        DropdownField(
            name="dropdown2", page_number=1, x=10, y=50, options=["A", "B", "C", "D"]
        ),
    ]

    obj.bulk_create_fields(fields)

    assert "dropdown1" in obj.widgets
    assert "dropdown2" in obj.widgets
    # The choices property is set after creation
    assert obj.widgets["dropdown1"].choices is not None
    assert obj.widgets["dropdown2"].choices is not None


def test_create_fields_large_batch():
    """Test creating a large batch of widgets efficiently."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    # Create 100 fields
    fields = [
        TextField(
            name=f"field{i}",
            page_number=1,
            x=10 + (i % 10) * 50,
            y=10 + (i // 10) * 30,
        )
        for i in range(100)
    ]

    obj.bulk_create_fields(fields)

    # All fields should be created
    assert len(obj.widgets) == 100
    for i in range(100):
        assert f"field{i}" in obj.widgets


def test_create_fields_read_output():
    """Test that the PDF output is valid after bulk_create_fields."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = [
        TextField(name="field1", page_number=1, x=10, y=10),
        TextField(name="field2", page_number=1, x=10, y=50),
    ]

    obj.bulk_create_fields(fields)

    # Should be able to read the PDF
    pdf_bytes = obj.read()
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
