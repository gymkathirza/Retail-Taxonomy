"""PDF seed CSV reconstruction helpers."""

from __future__ import annotations


def join_wrapped_seed_lines(lines: list[str]) -> list[str]:
    """
    Reconstruct taxonomy CSV rows from PDF-extracted lines.

    A data row starts with Center, or Perimeter,. Continuation lines that do not
    start a new row are joined onto the previous subcategory with a single space.
    Page markers like '3.' are dropped.
    """
    raise NotImplementedError
