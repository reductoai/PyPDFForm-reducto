#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple benchmark for filling fields performance.
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


def benchmark_fill_sequential(n_fields):
    """Benchmark filling fields one at a time (sequential fill calls)."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    # Create fields using bulk_create_fields
    fields = []
    fill_data = {}

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
            fill_data[f"checkbox_{i}"] = True
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
            fill_data[f"field_{i}"] = f"Value {i}"

        fields.append(field)

    # Create all fields (not timed)
    obj.bulk_create_fields(fields)

    # Time filling fields one at a time
    start_time = time.perf_counter()
    for field_name, value in fill_data.items():
        obj.fill({field_name: value})
    elapsed = time.perf_counter() - start_time

    return elapsed


def benchmark_fill_batch(n_fields):
    """Benchmark filling all fields in a single call (batch fill)."""
    blank_pdf = create_blank_pdf(1)
    obj = PdfWrapper(blank_pdf)

    # Create fields using bulk_create_fields
    fields = []
    fill_data = {}

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
            fill_data[f"checkbox_{i}"] = True
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
            fill_data[f"field_{i}"] = f"Value {i}"

        fields.append(field)

    # Create all fields (not timed)
    obj.bulk_create_fields(fields)

    # Time filling all fields at once
    start_time = time.perf_counter()
    obj.fill(fill_data)
    elapsed = time.perf_counter() - start_time

    return elapsed


def main():
    print("=" * 80)
    print("PyPDFForm Performance Benchmark: Sequential vs Batch Fill")
    print("=" * 80)
    print()

    test_cases = [1, 10, 100]

    print(f"{'Fields':<10} {'Sequential (s)':<17} {'Batch (s)':<15} {'Speedup':<10}")
    print("-" * 80)

    for n in test_cases:
        print(f"{n:<10}", end=" ", flush=True)

        # Benchmark sequential fill
        sequential_time = benchmark_fill_sequential(n)
        print(f"{sequential_time:<17.4f}", end=" ", flush=True)

        # Benchmark batch fill
        batch_time = benchmark_fill_batch(n)
        print(f"{batch_time:<15.4f}", end=" ", flush=True)

        # Calculate speedup
        speedup = sequential_time / batch_time if batch_time > 0 else 0
        print(f"{speedup:<10.1f}x")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
