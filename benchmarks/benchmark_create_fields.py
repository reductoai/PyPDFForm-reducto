#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple benchmark comparing create_field vs create_fields performance.
"""

import time
from io import BytesIO

from pypdf import PdfWriter
from PyPDFForm import PdfWrapper
from PyPDFForm.widgets.text import TextField
from PyPDFForm.widgets.checkbox import CheckBoxField


def create_blank_pdf(num_pages=1):
    """Create a blank PDF with the specified number of pages."""
    pdf_writer = PdfWriter()
    for _ in range(num_pages):
        pdf_writer.add_blank_page(width=612, height=792)  # Letter size

    output = BytesIO()
    pdf_writer.write(output)
    output.seek(0)
    return output.read()


def benchmark_single(n_fields):
    """Benchmark using create_widget for each field individually."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    translucent_bg = (0.95, 0.95, 0.95)
    border_width = 1

    start_time = time.perf_counter()

    for i in range(n_fields):
        is_checkbox = (i % 4 == 0)

        if is_checkbox:
            obj = obj.create_widget(
                widget_type="checkbox",
                name=f"checkbox_{i}",
                page_number=1,
                x=10 + (i % 5) * 100,
                y=10 + (i // 5) * 50,
                size=15,
                bg_color=translucent_bg,
                border_width=border_width,
                suppress_deprecation_notice=True,
            )
        else:
            width = 80
            height = 20
            font_size = min(12, height * 0.6)
            max_length = int(width / (font_size * 0.5))

            obj = obj.create_widget(
                widget_type="text",
                name=f"field_{i}",
                page_number=1,
                x=10 + (i % 5) * 100,
                y=10 + (i // 5) * 50,
                width=max(5, width),
                height=max(5, height),
                bg_color=translucent_bg,
                border_width=border_width,
                max_length=max_length,
                multiline=True,
                font_size=font_size,
                suppress_deprecation_notice=True,
            )

    elapsed = time.perf_counter() - start_time
    return elapsed


def benchmark_batch(n_fields):
    """Benchmark using bulk_create_fields for batch creation."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    fields = []
    for i in range(n_fields):
        is_checkbox = (i % 4 == 0)

        if is_checkbox:
            field = CheckBoxField(
                name=f"checkbox_{i}",
                page_number=1,
                x=10 + (i % 5) * 100,
                y=10 + (i // 5) * 50,
                size=15,
            )
        else:
            width = 80
            height = 20
            font_size = min(12, height * 0.6)
            max_length = int(width / (font_size * 0.5))

            field = TextField(
                name=f"field_{i}",
                page_number=1,
                x=10 + (i % 5) * 100,
                y=10 + (i // 5) * 50,
                width=width,
                height=height,
                font_size=font_size,
                max_length=max_length,
            )

        fields.append(field)

    start_time = time.perf_counter()
    obj.bulk_create_fields(fields)
    elapsed = time.perf_counter() - start_time

    return elapsed


def main():
    print("=" * 80)
    print("PyPDFForm Performance Benchmark: create_widget vs bulk_create_fields")
    print("=" * 80)
    print()

    test_cases = [1, 10, 50, 100]

    print(f"{'Fields':<10} {'Single (s)':<15} {'Batch (s)':<15} {'Speedup':<10}")
    print("-" * 80)

    for n in test_cases:
        print(f"{n:<10}", end=" ", flush=True)

        # Benchmark single method
        single_time = benchmark_single(n)
        print(f"{single_time:<15.4f}", end=" ", flush=True)

        # Benchmark batch method
        batch_time = benchmark_batch(n)
        print(f"{batch_time:<15.4f}", end=" ", flush=True)

        # Calculate speedup
        speedup = single_time / batch_time if batch_time > 0 else 0
        print(f"{speedup:<10.1f}x")

    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
