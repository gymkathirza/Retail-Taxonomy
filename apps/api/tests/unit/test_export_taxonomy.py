"""Unit: Excel/Word taxonomy export builders."""

from __future__ import annotations

from types import SimpleNamespace

from app.services.export_taxonomy import build_excel, build_word


def _sample() -> list:
    return [
        SimpleNamespace(
            zone="Z",
            department="D",
            category="C",
            subcategory="S",
            full_path="Z > D > C > S",
            is_active=True,
        )
    ]


def test_build_excel_is_xlsx_zip() -> None:
    data = build_excel(_sample())
    assert data[:2] == b"PK"
    assert len(data) > 100


def test_build_word_is_docx_zip() -> None:
    data = build_word(_sample())
    assert data[:2] == b"PK"
    assert len(data) > 100
