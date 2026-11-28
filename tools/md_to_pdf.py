"""Convert a Markdown doc (e.g. docs/founder-questions.md) to a printable A4 PDF.

Rebuild from the repo root:
    uv run --no-project --with "reportlab>=4.2" python tools/md_to_pdf.py docs/founder-questions.md docs/founder-questions.pdf
Windows only as written (uses the Segoe UI fonts, which include the ₹ sign).

Usage: python md_to_pdf.py <input.md> <output.pdf>
Handles the subset of Markdown used in that file: headings, paragraphs, bullets
(2 levels), numbered lists, tables, "> Answer:" lines (rendered as write-in boxes),
bold/italic/code, horizontal rules. Emoji are replaced by coloured text labels,
because PDF fonts can't draw emoji.
"""

import re
import sys
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONTS = "C:/Windows/Fonts/"
pdfmetrics.registerFont(TTFont("Segoe", FONTS + "segoeui.ttf"))
pdfmetrics.registerFont(TTFont("Segoe-Bold", FONTS + "segoeuib.ttf"))
pdfmetrics.registerFont(TTFont("Segoe-Italic", FONTS + "segoeuii.ttf"))
pdfmetrics.registerFont(TTFont("Segoe-BoldItalic", FONTS + "segoeuiz.ttf"))
pdfmetrics.registerFontFamily(
    "Segoe", normal="Segoe", bold="Segoe-Bold", italic="Segoe-Italic", boldItalic="Segoe-BoldItalic"
)

INK = colors.HexColor("#1f2328")
MUTED = colors.HexColor("#57606a")
LINE = colors.HexColor("#d0d7de")
HEAD_BG = colors.HexColor("#f2f4f7")
RED, AMBER, GREEN = (colors.HexColor(c) for c in ("#c62828", "#b26a00", "#2e7d32"))


def tag(text: str, color: colors.Color) -> str:
    return f'<font color="{color.hexval()}"><b>{text}</b></font>'


EMOJI = {
    "🔴": tag("NOW", RED),
    "🟡": tag("SOON", AMBER),
    "🟢": tag("LATER", GREEN),
    "✅": tag("YES", GREEN),
    "❌": tag("NO", RED),
}
TABLE_EMOJI = {
    "🔴": tag("NOW", RED),
    "🟡": tag("MAYBE", AMBER),
    "🟢": tag("LATER", GREEN),
    "✅": tag("YES", GREEN),
    "❌": tag("NO", RED),
}
HEADING_EMOJI = {
    "🔴": tag("[NOW]", RED),
    "🟡": tag("[SOON]", AMBER),
    "🟢": tag("[LATER]", GREEN),
    "✅": tag("[DONE]", GREEN),
}

base = ParagraphStyle("base", fontName="Segoe", fontSize=10, leading=14, textColor=INK)
S = {
    "title": ParagraphStyle("t", parent=base, fontName="Segoe-Bold", fontSize=20, leading=26,
                            spaceAfter=6),
    "h2": ParagraphStyle("h2", parent=base, fontName="Segoe-Bold", fontSize=13.5, leading=18,
                         spaceBefore=10, spaceAfter=5),
    "p": ParagraphStyle("p", parent=base, spaceAfter=5, alignment=TA_LEFT),
    "small": ParagraphStyle("s", parent=base, fontSize=8, leading=11, textColor=MUTED),
    "cell": ParagraphStyle("c", parent=base, fontSize=8.5, leading=11.5),
    "cellh": ParagraphStyle("ch", parent=base, fontName="Segoe-Bold", fontSize=8.5, leading=11.5),
    "answer": ParagraphStyle("a", parent=base, fontSize=8.5, textColor=MUTED),
}


def inline(text: str, emoji: dict[str, str] = EMOJI) -> str:
    """Markdown inline -> ReportLab mini-HTML."""
    text = escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", text)
    text = text.replace("[ ]", "\u25a1")  # empty checkbox square
    for e, rep in emoji.items():
        text = text.replace(e, rep)
    return text


def answer_box(label: str = "Answer:") -> Table:
    rows = [[Paragraph(label, S["answer"])], [""], [""]]
    t = Table(rows, colWidths=[170 * mm], rowHeights=[5 * mm, 7 * mm, 7 * mm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, LINE),
        ("LINEBELOW", (0, 1), (-1, 1), 0.4, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def make_table(rows: list[list[str]]) -> Table:
    ncols = len(rows[0])
    data = [[Paragraph(inline(c, TABLE_EMOJI), S["cellh" if i == 0 else "cell"]) for c in r] for i, r in
            enumerate(rows)]
    # Width: proportional to the longest text in each column, with sensible limits
    total = 180 * mm
    lengths = [max(len(r[c]) for r in rows) for c in range(ncols)]
    lengths = [min(max(n, 6), 70) for n in lengths]
    widths = [total * n / sum(lengths) for n in lengths]
    empty_rows = all(not c.strip() for r in rows[1:] for c in r)
    t = Table(data, colWidths=widths, repeatRows=1,
              rowHeights=[None] + [9 * mm] * (len(rows) - 1) if empty_rows else None)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def convert(md: str) -> list:
    story: list = []
    lines = md.splitlines()
    i = 0
    bullets: list = []

    def flush_bullets() -> None:
        nonlocal bullets
        if bullets:
            story.append(ListFlowable(bullets, bulletType="bullet", start="\u2022",
                                      leftIndent=12, bulletFontName="Segoe"))
            bullets = []

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if stripped.startswith("|"):
            flush_bullets()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                is_sep = any(c for c in cells) and all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c)
                if not is_sep:
                    rows.append(cells)
                i += 1
            story.append(make_table(rows))
            story.append(Spacer(1, 6))
            continue

        if stripped.startswith("> "):
            flush_bullets()
            content = stripped[2:]
            if content.lower().startswith("answer:") or content.startswith("Swiggy:"):
                story.append(answer_box(inline(content)))
                story.append(Spacer(1, 4))
            else:
                story.append(Paragraph(inline(content), S["p"]))
            i += 1
            continue

        if not stripped:
            flush_bullets()
            i += 1
            continue

        if stripped == "---":
            flush_bullets()
            story.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=4,
                                    spaceAfter=4))
            i += 1
            continue

        if line.startswith("# "):
            story.append(Paragraph(inline(line[2:]), S["title"]))
            i += 1
            continue

        if line.startswith("## "):
            flush_bullets()
            story.append(Paragraph(inline(line[3:], HEADING_EMOJI), S["h2"]))
            i += 1
            continue

        m = re.match(r"^(\s*)(- |\d+\. )(.*)", line)
        if m:
            indent, marker, content = len(m.group(1)), m.group(2).strip(), m.group(3)
            para = Paragraph(inline(content), S["p"])
            if indent >= 2 and bullets:
                bullets.append(ListItem(para, leftIndent=26, bulletColor=MUTED, value="\u2013"))
            else:
                if marker != "-":
                    bullets.append(ListItem(para, leftIndent=16, value=marker))
                else:
                    bullets.append(ListItem(para, leftIndent=12))
            i += 1
            continue

        flush_bullets()
        is_italic_note = stripped.startswith("*") and not stripped.startswith("**") and stripped.endswith("*")
        style = S["small"] if is_italic_note else S["p"]
        story.append(Paragraph(inline(stripped), style))
        i += 1

    flush_bullets()
    return story


def footer(canvas, doc) -> None:  # noqa: ANN001
    canvas.saveState()
    canvas.setFont("Segoe", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(15 * mm, 10 * mm, "Chopstop: questions for the founders")
    canvas.drawRightString(195 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def main() -> None:
    src, out = sys.argv[1], sys.argv[2]
    md = open(src, encoding="utf-8").read()
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=17 * mm,
                            title="Chopstop: questions for the founders", author="Chopstop")
    story = convert(md)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("wrote", out)


if __name__ == "__main__":
    main()
