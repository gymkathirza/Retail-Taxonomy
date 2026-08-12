"""PDF seed CSV reconstruction helpers."""

from __future__ import annotations


def _is_data_row(line: str) -> bool:
    return line.startswith("Center,") or line.startswith("Perimeter,")


def _is_page_marker(line: str) -> bool:
    stripped = line.strip()
    return stripped.endswith(".") and stripped[:-1].isdigit()


def join_wrapped_seed_lines(lines: list[str]) -> list[str]:
    """
    Reconstruct taxonomy CSV rows from PDF-extracted lines.

    A data row starts with Center, or Perimeter,. Continuation lines that do not
    start a new row are joined onto the previous subcategory with a single space.
    Page markers like '3.' are dropped.
    """
    rows: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Location,"):
            continue
        if _is_page_marker(line):
            continue
        if _is_data_row(line):
            rows.append(line)
            continue
        if not rows:
            continue
        rows[-1] = f"{rows[-1]} {line}"
    return rows
