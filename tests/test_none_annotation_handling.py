"""
Tests for handling None annotations in PDF processing.

These tests verify that PyPDFForm can gracefully handle PDFs where
annot.get_object() returns None (corrupted annotations or missing references).
This was the cause of the bug:
    AttributeError: 'NoneType' object has no attribute 'items'
"""

import warnings
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfWriter
from pypdf.generic import (
    ArrayObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    TextStringObject,
)

from PyPDFForm import PdfWrapper


def create_pdf_with_text_widget(name: str = "test_field") -> bytes:
    """Helper to create a simple PDF with a text widget."""
    writer = PdfWriter()
    writer.add_blank_page(612, 792)

    widget = DictionaryObject()
    widget[NameObject("/Type")] = NameObject("/Annot")
    widget[NameObject("/Subtype")] = NameObject("/Widget")
    widget[NameObject("/FT")] = NameObject("/Tx")
    widget[NameObject("/T")] = TextStringObject(name)
    widget[NameObject("/Rect")] = ArrayObject([
        NumberObject(100), NumberObject(100),
        NumberObject(200), NumberObject(120)
    ])

    writer.pages[0][NameObject("/Annots")] = ArrayObject()
    writer.pages[0][NameObject("/Annots")].append(writer._add_object(widget))

    pdf_bytes = BytesIO()
    writer.write(pdf_bytes)
    pdf_bytes.seek(0)
    return pdf_bytes.read()


class TestTraversePatternNoneHandling:
    """Tests showing traverse_pattern doesn't handle None - callers must check."""

    def test_traverse_pattern_with_none_raises_attribute_error(self):
        """
        traverse_pattern raises AttributeError when widget is None.
        This documents WHY we need the None checks in the calling code.
        """
        from PyPDFForm.utils import traverse_pattern

        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'items'"):
            traverse_pattern({"/T": True}, None)


class TestNoneAnnotationFix:
    """
    Tests that verify the None annotation fix works and emits warnings.

    The fix adds this pattern before calling get_widget_key:
        annot_obj = annot.get_object()
        if annot_obj is None:
            warn(...)
            continue
    """

    def test_filler_handles_none_annotation_with_warning(self):
        """Test filler.py skips None annotations and emits warning."""
        from PyPDFForm.filler import fill

        pdf_bytes = create_pdf_with_text_widget("test")
        wrapper = PdfWrapper(pdf_bytes)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            with patch('PyPDFForm.filler.PdfWriter') as MockWriter:
                mock_writer = MagicMock()
                MockWriter.return_value = mock_writer

                # Create mock page with one None annotation
                mock_none_annot = MagicMock()
                mock_none_annot.get_object.return_value = None

                mock_page = MagicMock()
                mock_page.get.return_value = [mock_none_annot]
                mock_writer.pages = [mock_page]

                def mock_write(f):
                    f.write(pdf_bytes)

                mock_writer.write.side_effect = mock_write

                result, _ = fill(
                    pdf_bytes,
                    wrapper.widgets,
                    need_appearances=False,
                    use_full_widget_name=False,
                    flatten=False,
                )

                assert isinstance(result, bytes)

                # Should have emitted a warning
                warning_messages = [str(warning.message) for warning in w]
                assert any("annotation object is None" in msg for msg in warning_messages)
                assert any("page 1" in msg for msg in warning_messages)

    def test_hooks_handles_none_annotation_with_warning(self):
        """Test hooks.py skips None annotations and emits warning."""
        from PyPDFForm.hooks import trigger_widget_hooks

        pdf_bytes = create_pdf_with_text_widget("test")
        wrapper = PdfWrapper(pdf_bytes)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            with patch('PyPDFForm.hooks.PdfWriter') as MockWriter:
                mock_writer = MagicMock()
                MockWriter.return_value = mock_writer

                mock_none_annot = MagicMock()
                mock_none_annot.get_object.return_value = None

                mock_page = MagicMock()
                mock_page.get.return_value = [mock_none_annot]
                mock_writer.pages = [mock_page]

                def mock_write(f):
                    f.write(pdf_bytes)

                mock_writer.write.side_effect = mock_write

                result = trigger_widget_hooks(pdf_bytes, wrapper.widgets, False)
                assert isinstance(result, bytes)

                # Should have emitted a warning
                warning_messages = [str(warning.message) for warning in w]
                assert any("annotation object is None" in msg for msg in warning_messages)

    def test_update_widget_keys_handles_none_annotation_with_warning(self):
        """Test template.py update_widget_keys skips None annotations and warns."""
        from PyPDFForm.template import update_widget_keys

        pdf_bytes = create_pdf_with_text_widget("test")
        wrapper = PdfWrapper(pdf_bytes)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            with patch('PyPDFForm.template.PdfWriter') as MockWriter:
                mock_writer = MagicMock()
                MockWriter.return_value = mock_writer

                mock_none_annot = MagicMock()
                mock_none_annot.get_object.return_value = None

                mock_page = MagicMock()
                mock_page.get.return_value = [mock_none_annot]
                mock_writer.pages = [mock_page]

                def mock_write(f):
                    f.write(pdf_bytes)

                mock_writer.write.side_effect = mock_write

                result = update_widget_keys(
                    pdf_bytes,
                    wrapper.widgets,
                    ["test"],
                    ["renamed"],
                    [0],
                )
                assert isinstance(result, bytes)

                # Should have emitted a warning
                warning_messages = [str(warning.message) for warning in w]
                assert any("annotation object is None" in msg for msg in warning_messages)