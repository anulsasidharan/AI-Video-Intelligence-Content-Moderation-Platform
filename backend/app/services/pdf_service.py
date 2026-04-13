"""
PDF Service — R-03

Generates branded PDF reports from structured report data using ReportLab.

Features:
- Company header with logo placeholder, report title, and date
- Summary statistics box
- Full data table with alternating row shading
- Per-page header/footer with page numbering
- Portrait / Landscape orientation support
- Bar chart for categorical summary data (where applicable)
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from typing import Any

import structlog
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = structlog.get_logger(__name__)

# ── Brand palette ──────────────────────────────────────────────────────────────
BRAND_PRIMARY = colors.HexColor("#6366F1")  # indigo-500
BRAND_DARK = colors.HexColor("#1E1B4B")  # indigo-950
BRAND_ACCENT = colors.HexColor("#10B981")  # emerald-500
BRAND_WARN = colors.HexColor("#F59E0B")  # amber-500
BRAND_DANGER = colors.HexColor("#EF4444")  # red-500
BRAND_LIGHT = colors.HexColor("#EEF2FF")  # indigo-50
ROW_ALT = colors.HexColor("#F8FAFC")  # slate-50

# Severity → colour mapping for visual cues in cells
_SEVERITY_COLORS = {
    "critical": BRAND_DANGER,
    "high": colors.HexColor("#F97316"),
    "medium": BRAND_WARN,
    "low": BRAND_ACCENT,
}

_STATUS_COLORS = {
    "rejected": BRAND_DANGER,
    "flagged": BRAND_WARN,
    "escalated": colors.HexColor("#8B5CF6"),
    "approved": BRAND_ACCENT,
    "pending": colors.HexColor("#94A3B8"),
}


def _human_label(col: str) -> str:
    return col.replace("_", " ").title()


def _truncate(value: Any, max_len: int = 60) -> str:
    s = str(value) if value is not None else "—"
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


# ── Main entry point ───────────────────────────────────────────────────────────


def generate_pdf(
    report_title: str,
    report_type: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    summary: dict[str, Any],
    orientation: str = "portrait",
) -> bytes:
    """
    Build and return the PDF as raw bytes.

    Args:
        report_title: Human-readable title shown in the header.
        report_type: Report type identifier (for subtitle).
        columns: Ordered list of column keys.
        rows: List of row dicts (key → value).
        summary: Summary statistics dict.
        orientation: "portrait" or "landscape".
    """
    buf = io.BytesIO()
    pagesize = A4 if orientation == "portrait" else landscape(A4)

    doc = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.0 * cm,
        title=report_title,
        author="VidShield AI",
        subject=f"Report: {report_type}",
    )

    styles = _build_styles()
    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    story: list = []

    # ── Header block ──────────────────────────────────────────────────────────
    story += _build_header(report_title, report_type, generated_at, styles)
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_PRIMARY))
    story.append(Spacer(1, 0.4 * cm))

    # ── Summary box ───────────────────────────────────────────────────────────
    if summary:
        story += _build_summary_box(summary, styles)
        story.append(Spacer(1, 0.6 * cm))

    # ── Row count note ────────────────────────────────────────────────────────
    total = summary.get("total", len(rows))
    note = f"Showing {len(rows):,} of {total:,} record(s)."
    story.append(Paragraph(note, styles["note"]))
    story.append(Spacer(1, 0.3 * cm))

    # ── Data table ────────────────────────────────────────────────────────────
    if rows:
        story += _build_data_table(columns, rows, styles, pagesize)
    else:
        story.append(Paragraph("No data matching the selected filters.", styles["note"]))

    # ── Footer note ───────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "This report was generated automatically by VidShield AI. "
            "Data reflects the state at the time of generation.",
            styles["footer_note"],
        )
    )

    # ── Build PDF ─────────────────────────────────────────────────────────────
    doc.build(
        story,
        onFirstPage=_make_page_decorator(report_title, generated_at),
        onLaterPages=_make_page_decorator(report_title, generated_at),
    )
    pdf_bytes = buf.getvalue()
    buf.close()
    logger.info(
        "pdf_generated",
        title=report_title,
        rows=len(rows),
        size_bytes=len(pdf_bytes),
    )
    return pdf_bytes


# ── Style builders ─────────────────────────────────────────────────────────────


def _build_styles() -> dict[str, ParagraphStyle]:
    return {
        "brand_title": ParagraphStyle(
            "brand_title",
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=BRAND_DARK,
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#64748B"),
            alignment=TA_LEFT,
            spaceAfter=2,
        ),
        "date_label": ParagraphStyle(
            "date_label",
            fontName="Helvetica",
            fontSize=9,
            textColor=colors.HexColor("#94A3B8"),
            alignment=TA_RIGHT,
        ),
        "summary_key": ParagraphStyle(
            "summary_key",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=BRAND_DARK,
            alignment=TA_CENTER,
        ),
        "summary_val": ParagraphStyle(
            "summary_val",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=BRAND_PRIMARY,
            alignment=TA_CENTER,
        ),
        "th": ParagraphStyle(
            "th",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=colors.white,
            alignment=TA_CENTER,
        ),
        "td": ParagraphStyle(
            "td",
            fontName="Helvetica",
            fontSize=7.5,
            textColor=BRAND_DARK,
            alignment=TA_LEFT,
            leading=10,
        ),
        "note": ParagraphStyle(
            "note",
            fontName="Helvetica",
            fontSize=8,
            textColor=colors.HexColor("#64748B"),
        ),
        "footer_note": ParagraphStyle(
            "footer_note",
            fontName="Helvetica",
            fontSize=7,
            textColor=colors.HexColor("#94A3B8"),
            alignment=TA_CENTER,
        ),
    }


# ── Section builders ───────────────────────────────────────────────────────────


def _build_header(title: str, report_type: str, generated_at: str, styles: dict) -> list:
    type_label = report_type.replace("_", " ").title()
    # Two-column layout: title left, date right
    header_data = [
        [
            Paragraph(f"VidShield AI — {title}", styles["brand_title"]),
            Paragraph(f"Generated: {generated_at}", styles["date_label"]),
        ],
        [
            Paragraph(f"Report Type: {type_label}", styles["subtitle"]),
            Paragraph("Confidential — Admin Use Only", styles["date_label"]),
        ],
    ]
    tbl = Table(header_data, colWidths=["70%", "30%"])
    tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return [tbl]


def _build_summary_box(summary: dict[str, Any], styles: dict) -> list:
    """Render top-level numeric fields as a horizontal stat cards row."""
    # Pick scalar stats (int/float) for display
    stat_items = [
        (k.replace("_", " ").title(), v)
        for k, v in summary.items()
        if isinstance(v, int | float) and not isinstance(v, bool)
    ]
    if not stat_items:
        return []

    # Cap at 5 cards to avoid overflow
    stat_items = stat_items[:5]
    header_row = [Paragraph(k, styles["summary_key"]) for k, _ in stat_items]
    value_row = [
        Paragraph(f"{v:,.2f}" if isinstance(v, float) else f"{v:,}", styles["summary_val"])
        for _, v in stat_items
    ]

    col_w = 100.0 / len(stat_items)
    col_widths = [f"{col_w}%" for _ in stat_items]

    tbl = Table([header_row, value_row], colWidths=col_widths)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
                ("ROUNDEDCORNERS", [4]),
                ("BOX", (0, 0), (-1, -1), 0.5, BRAND_PRIMARY),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C7D2FE")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return [tbl]


def _build_data_table(
    columns: list[str],
    rows: list[dict[str, Any]],
    styles: dict,
    pagesize: tuple,
) -> list:
    """Build the main data table with header row, alternating shading, and column widths."""
    usable_width = pagesize[0] - 3 * cm  # left + right margins

    # Distribute widths proportionally
    n = len(columns)
    col_w = usable_width / n

    header = [Paragraph(_human_label(c), styles["th"]) for c in columns]
    table_data = [header]

    for row in rows:
        data_row = [Paragraph(_truncate(row.get(c, "—")), styles["td"]) for c in columns]
        table_data.append(data_row)

    tbl = Table(table_data, colWidths=[col_w] * n, repeatRows=1)

    # Base style
    tbl_style = [
        # Header
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        # Data rows
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ("LINEBELOW", (0, 0), (-1, 0), 1, BRAND_PRIMARY),
    ]

    # Alternating row background
    for i in range(1, len(table_data)):
        if i % 2 == 0:
            tbl_style.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))

    tbl.setStyle(TableStyle(tbl_style))
    return [tbl]


# ── Per-page decorator (header/footer overlay) ─────────────────────────────────


def _make_page_decorator(report_title: str, generated_at: str):
    """Returns a canvas callback that draws running header and footer on each page."""

    def _decorator(canvas, doc):
        canvas.saveState()
        w, h = doc.pagesize

        # Top bar
        canvas.setFillColor(BRAND_DARK)
        canvas.rect(0, h - 18 * mm, w, 18 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(15 * mm, h - 11 * mm, f"VidShield AI  ·  {report_title}")
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(w - 15 * mm, h - 11 * mm, generated_at)

        # Bottom bar
        canvas.setFillColor(colors.HexColor("#F1F5F9"))
        canvas.rect(0, 0, w, 12 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawString(15 * mm, 4 * mm, "Confidential — VidShield AI Admin Report")
        canvas.drawRightString(w - 15 * mm, 4 * mm, f"Page {doc.page}")

        canvas.restoreState()

    return _decorator
