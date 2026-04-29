"""Build docs/user-guide.pdf from docs/user-guide.md using ReportLab.

ReportLab is already a runtime dependency of kim_app so no extra install is
needed. Run from the repo root:

    python scripts/build_docs_pdf.py [--version v0.1.0]

The optional --version flag overrides the version string stamped in the
document header (defaults to "dev" when not supplied).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Minimal markdown → ReportLab flowables converter
# Handles: ATX headings, paragraphs, fenced code blocks, pipe tables,
#          blockquotes, unordered/ordered lists, inline `code`, **bold**, *italic*
# ---------------------------------------------------------------------------

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

_styles = getSampleStyleSheet()

_H1 = ParagraphStyle(
    "H1", parent=_styles["Heading1"],
    fontSize=18, spaceAfter=3 * mm, spaceBefore=6 * mm,
    textColor=colors.HexColor("#1F2937"),
    borderPad=0, borderWidth=0,
)
_H2 = ParagraphStyle(
    "H2", parent=_styles["Heading2"],
    fontSize=13, spaceAfter=2 * mm, spaceBefore=5 * mm,
    textColor=colors.HexColor("#374151"),
)
_H3 = ParagraphStyle(
    "H3", parent=_styles["Heading3"],
    fontSize=11, spaceAfter=1.5 * mm, spaceBefore=3 * mm,
    textColor=colors.HexColor("#4B5563"),
)
_BODY = ParagraphStyle(
    "Body", parent=_styles["BodyText"],
    fontSize=10, leading=15, spaceAfter=2 * mm,
)
_CODE_BLOCK = ParagraphStyle(
    "CodeBlock", parent=_styles["Code"],
    fontSize=8, leading=12, leftIndent=6 * mm,
    backColor=colors.HexColor("#F3F4F6"),
    borderColor=colors.HexColor("#D1D5DB"),
    borderWidth=0.5, borderPad=3 * mm,
    spaceAfter=3 * mm, spaceBefore=1 * mm,
    fontName="Courier",
)
_QUOTE = ParagraphStyle(
    "Quote", parent=_BODY,
    leftIndent=8 * mm,
    textColor=colors.HexColor("#6B7280"),
    borderLeftColor=colors.HexColor("#9CA3AF"),
    borderLeftWidth=2,
    borderLeftPadding=4,
)
_LIST = ParagraphStyle(
    "List", parent=_BODY,
    leftIndent=6 * mm, bulletIndent=3 * mm,
    spaceAfter=1 * mm,
)
_FOOTER = ParagraphStyle(
    "Footer", parent=_styles["BodyText"],
    fontSize=7, textColor=colors.HexColor("#9CA3AF"),
)


def _inline(text: str) -> str:
    """Convert inline markdown (bold, italic, backtick code) to ReportLab XML."""
    # Escape ampersands first to avoid double-encoding later.
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # Backtick inline code.
    text = re.sub(
        r"`([^`]+)`",
        r'<font name="Courier" size="9" backColor="#F3F4F6">\1</font>',
        text,
    )
    # Bold.
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # Italic.
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return text


def _parse_table(header_line: str, sep_line: str, rows: list[str]) -> Table:
    """Build a ReportLab Table from a GFM pipe-table fragment."""
    def split_row(line: str) -> list[str]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        return cells

    aligns = []
    for cell in split_row(sep_line):
        if cell.startswith(":") and cell.endswith(":"):
            aligns.append("CENTER")
        elif cell.endswith(":"):
            aligns.append("RIGHT")
        else:
            aligns.append("LEFT")

    header_cells = [Paragraph(_inline(c), ParagraphStyle(
        "TH", parent=_BODY, fontName="Helvetica-Bold", fontSize=9, leading=12,
    )) for c in split_row(header_line)]

    data = [header_cells]
    for row_line in rows:
        data.append([
            Paragraph(_inline(c), ParagraphStyle(
                "TD", parent=_BODY, fontSize=9, leading=12,
            ))
            for c in split_row(row_line)
        ])

    tbl = Table(data, hAlign="LEFT", repeatRows=1)
    style_cmds: list = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3F4F6")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    for col_idx, align in enumerate(aligns):
        if align != "LEFT":
            style_cmds.append(("ALIGN", (col_idx, 1), (col_idx, -1), align))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def parse_markdown(text: str) -> list:
    """Convert markdown text to a list of ReportLab flowables."""
    flowables = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]

        # --- Horizontal rule (---, ***, ___)
        if re.match(r"^[-*_]{3,}\s*$", line):
            flowables.append(HRFlowable(width="100%", thickness=0.5,
                                        color=colors.HexColor("#D1D5DB"),
                                        spaceAfter=3 * mm, spaceBefore=2 * mm))
            i += 1
            continue

        # --- ATX heading
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            text_content = _inline(m.group(2).strip())
            style = {1: _H1, 2: _H2, 3: _H3}[level]
            flowables.append(Paragraph(text_content, style))
            if level == 1:
                flowables.append(HRFlowable(
                    width="100%", thickness=1,
                    color=colors.HexColor("#D1D5DB"),
                    spaceAfter=2 * mm,
                ))
            i += 1
            continue

        # --- Fenced code block
        if line.startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            code_text = "\n".join(code_lines)
            # Escape XML special chars in code.
            code_text = (code_text.replace("&", "&amp;")
                                  .replace("<", "&lt;")
                                  .replace(">", "&gt;"))
            flowables.append(Paragraph(
                code_text.replace("\n", "<br/>"),
                _CODE_BLOCK,
            ))
            continue

        # --- Table: detect header | sep | rows block
        if "|" in line and i + 1 < len(lines) and re.match(r"^[|\s:|-]+$", lines[i + 1]):
            header_line = line
            sep_line = lines[i + 1]
            i += 2
            row_lines = []
            while i < len(lines) and "|" in lines[i]:
                row_lines.append(lines[i])
                i += 1
            flowables.append(_parse_table(header_line, sep_line, row_lines))
            flowables.append(Spacer(1, 2 * mm))
            continue

        # --- Blockquote
        if line.startswith("> "):
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:])
                i += 1
            flowables.append(Paragraph(_inline(" ".join(quote_lines)), _QUOTE))
            continue

        # --- Unordered list item
        m = re.match(r"^[-*+]\s+(.*)", line)
        if m:
            flowables.append(Paragraph(
                f"• {_inline(m.group(1))}",
                _LIST,
            ))
            i += 1
            continue

        # --- Ordered list item
        m = re.match(r"^\d+\.\s+(.*)", line)
        if m:
            # Collect the number for display.
            num = re.match(r"^(\d+)\.", line).group(1)
            flowables.append(Paragraph(
                f"{num}. {_inline(m.group(1))}",
                _LIST,
            ))
            i += 1
            continue

        # --- Empty line → small spacer
        if not line.strip():
            flowables.append(Spacer(1, 1 * mm))
            i += 1
            continue

        # --- Default: paragraph. Collect continued lines.
        para_lines = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{1,3}\s|```|[-*+]\s|\d+\.\s|>|\||[-*_]{3,})", lines[i]
        ):
            para_lines.append(lines[i])
            i += 1
        flowables.append(Paragraph(_inline(" ".join(para_lines)), _BODY))

    return flowables


def build_pdf(source: Path, output: Path, version: str) -> None:
    md_text = source.read_text(encoding="utf-8")

    def draw_header_footer(canvas, doc):
        canvas.saveState()
        # Header bar.
        canvas.setFillColor(colors.HexColor("#1F2937"))
        canvas.rect(MARGIN, PAGE_H - 14 * mm, PAGE_W - 2 * MARGIN, 10 * mm, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN + 3 * mm, PAGE_H - 9 * mm, "KIM-QA Reporter")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(PAGE_W - MARGIN - 3 * mm, PAGE_H - 9 * mm, f"User Guide  {version}")
        # Footer.
        canvas.setFillColor(colors.HexColor("#9CA3AF"))
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MARGIN, 8 * mm, "KIM-QA Reporter — Clinical Use. Verify results against source data.")
        canvas.drawRightString(PAGE_W - MARGIN, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=20 * mm,
        bottomMargin=18 * mm,
        title=f"KIM-QA Reporter {version} — User Guide",
        author="KIM-QA Reporter",
    )

    story = parse_markdown(md_text)
    doc.build(story, onFirstPage=draw_header_footer, onLaterPages=draw_header_footer)
    print(f"Written: {output}  ({output.stat().st_size // 1024} KB)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build user-guide PDF from markdown.")
    ap.add_argument("--version", default="dev", help="Version string to stamp in the PDF header.")
    ap.add_argument("--input", default="docs/user-guide.md", help="Source markdown file.")
    ap.add_argument("--output", default="docs/user-guide.pdf", help="Output PDF path.")
    args = ap.parse_args()

    source = Path(args.input)
    output = Path(args.output)
    if not source.is_file():
        print(f"ERROR: source not found: {source}", file=sys.stderr)
        sys.exit(1)
    output.parent.mkdir(parents=True, exist_ok=True)
    build_pdf(source, output, args.version)


if __name__ == "__main__":
    main()
