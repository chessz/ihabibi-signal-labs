"""Unit tests for context export."""

from __future__ import annotations

from pathlib import Path

import pytest

from signals_lab.utils.context_export import (
    build_perplexity_context,
    export_context,
    export_context_pdf,
)


@pytest.mark.unit
def test_build_perplexity_context_contains_key_sections() -> None:
    text = build_perplexity_context()
    assert "Perplexity Pro" in text
    assert "No live trading" in text or "no live trading" in text.lower()
    assert "HIGH / EXTREME" in text or "HIGH/EXTREME" in text
    assert "FeatureEngine" in text or "feature" in text.lower()


@pytest.mark.unit
def test_export_context_writes_file(tmp_path: Path) -> None:
    # Minimal pyproject so _find_project_root works if called from tmp
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    out = tmp_path / "docs" / "PERPLEXITY_CONTEXT.md"
    path = export_context(output_path=out, root=tmp_path)
    assert path.exists()
    assert path.read_text(encoding="utf-8").startswith("# signals-lab")


@pytest.mark.unit
def test_export_context_pdf_writes_file(tmp_path: Path) -> None:
    fpdf = pytest.importorskip("fpdf")
    _ = fpdf  # used only to skip when missing

    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Test\n", encoding="utf-8")
    (tmp_path / "SPECS.md").write_text("# Spec\n" + "\n".join(f"line {i}" for i in range(50)), encoding="utf-8")
    (tmp_path / "ARCHITECTURE.md").write_text("# Arch\n", encoding="utf-8")
    (tmp_path / "config").mkdir(exist_ok=True)

    out = tmp_path / "docs" / "PERPLEXITY_CONTEXT.pdf"
    path = export_context_pdf(output_path=out, root=tmp_path)
    assert path.exists()
    assert path.stat().st_size > 1000
    assert path.read_bytes()[:4] == b"%PDF"
