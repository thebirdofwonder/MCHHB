"""接種記録表の PDF 出力（セル自動折り返し・行高調整）。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .excel_export import _format_date
from .schema import ExtractionResult
from .table_rows import build_output_rows, disease_merge_spans, vaccine_merge_spans

FONT_NAME = "HeiseiKakuGo-W5"
pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))

COL_RATIOS = [0.11, 0.11, 0.09, 0.05, 0.11, 0.17, 0.10, 0.26]
FONT_SIZE = 8
LEADING = 11


def _para(text: Optional[str], *, bold: bool = False) -> Paragraph:
    style = ParagraphStyle(
        "cell",
        fontName=FONT_NAME,
        fontSize=FONT_SIZE,
        leading=LEADING,
        wordWrap="CJK",
    )
    safe = (text or " ").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Paragraph(safe, style)


def _column_widths(usable_width: float) -> list[float]:
    return [usable_width * ratio for ratio in COL_RATIOS]


def export_to_pdf(
    result: ExtractionResult,
    output_path: Path,
    *,
    child_name: Optional[str] = None,
) -> Path:
    """抽出結果を接種記録表 PDF として出力する。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=page_size,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
    )
    usable_width = page_size[0] - doc.leftMargin - doc.rightMargin
    col_widths = _column_widths(usable_width)

    name = child_name or result.child_name or ""
    output_rows = build_output_rows(result)
    templates = [r.template for r in output_rows]

    story = []
    story.append(_para("Vaccination Record", bold=True))
    story.append(Spacer(1, 4 * mm))
    story.append(_para(f"Name: {name}" if name else "Name:"))
    story.append(Spacer(1, 4 * mm))

    headers = [
        "Disease",
        "Vaccine",
        "Dose",
        "No.",
        "Date of Vaccination",
        "Manufacturer / Product",
        "Lot Number",
        "Medical Institution / Doctor",
    ]
    table_data: list[list[Paragraph]] = [[_para(h, bold=True) for h in headers]]

    merge_spans: list[tuple] = []
    sheet_start = 1

    for out_row in output_rows:
        t = out_row.template
        entry = out_row.entry
        table_data.append(
            [
                _para(t.disease_en),
                _para(t.vaccine_ja),
                _para(t.dose_category),
                _para(str(t.dose_number)),
                _para(_format_date(entry.date)),
                _para(entry.manufacturer),
                _para(entry.lot_number),
                _para(entry.institution),
            ]
        )

    for row_start, row_end in disease_merge_spans(templates, start_index=sheet_start):
        merge_spans.append(("SPAN", (0, row_start), (0, row_end)))
    for row_start, row_end in vaccine_merge_spans(templates, start_index=sheet_start):
        merge_spans.append(("SPAN", (1, row_start), (1, row_end)))

    table = Table(table_data, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAD3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    style_commands.extend(merge_spans)
    table.setStyle(TableStyle(style_commands))

    story.append(table)
    doc.build(story)
    return output_path
