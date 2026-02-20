"""
PDF Export Module for MedeX
===========================
Generates professional medical PDF documents using ReportLab.
"""

from io import BytesIO
from datetime import datetime
import re

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT


# =============================================================================
# PROFESSIONAL COLOR PALETTE
# =============================================================================
MEDEX_PRIMARY = HexColor("#1e3a5f")  # Deep navy - professional
MEDEX_PRIMARY_LIGHT = HexColor("#2563eb")  # Bright blue - accents
MEDEX_SECONDARY = HexColor("#0f766e")  # Teal - sections
MEDEX_ACCENT = HexColor("#7c3aed")  # Purple - highlights

# Severity colors (medical standard)
SEVERITY_HIGH = HexColor("#dc2626")  # Red
SEVERITY_MODERATE = HexColor("#ea580c")  # Orange
SEVERITY_LOW = HexColor("#eab308")  # Yellow
SEVERITY_NONE = HexColor("#16a34a")  # Green

# Neutral colors
MEDEX_GRAY_900 = HexColor("#111827")
MEDEX_GRAY_700 = HexColor("#374151")
MEDEX_GRAY_500 = HexColor("#6b7280")
MEDEX_GRAY_300 = HexColor("#d1d5db")
MEDEX_GRAY_100 = HexColor("#f3f4f6")
MEDEX_GRAY_50 = HexColor("#f9fafb")

# Warning/Disclaimer
MEDEX_WARNING = HexColor("#b45309")
MEDEX_WARNING_BG = HexColor("#fef3c7")


def get_professional_styles():
    """Get professional medical document styles."""
    styles = getSampleStyleSheet()

    # Document title - large, prominent
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            textColor=MEDEX_PRIMARY,
            spaceAfter=4,
            spaceBefore=0,
            alignment=TA_LEFT,
            fontName="Helvetica-Bold",
        )
    )

    # Document subtitle/metadata
    styles.add(
        ParagraphStyle(
            name="DocMeta",
            parent=styles["Normal"],
            fontSize=9,
            textColor=MEDEX_GRAY_500,
            spaceAfter=16,
            fontName="Helvetica",
        )
    )

    # Section header - level 1
    styles.add(
        ParagraphStyle(
            name="SectionH1",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=MEDEX_PRIMARY,
            spaceBefore=18,
            spaceAfter=8,
            fontName="Helvetica-Bold",
            borderPadding=4,
        )
    )

    # Section header - level 2
    styles.add(
        ParagraphStyle(
            name="SectionH2",
            parent=styles["Heading3"],
            fontSize=12,
            textColor=MEDEX_SECONDARY,
            spaceBefore=14,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        )
    )

    # Section header - level 3 (inline emphasis)
    styles.add(
        ParagraphStyle(
            name="SectionH3",
            parent=styles["Normal"],
            fontSize=10,
            textColor=MEDEX_GRAY_700,
            spaceBefore=10,
            spaceAfter=4,
            fontName="Helvetica-Bold",
        )
    )

    # Override BodyText style (already exists in getSampleStyleSheet)
    # We modify the existing style instead of adding a new one
    styles["BodyText"].fontSize = 10
    styles["BodyText"].textColor = MEDEX_GRAY_900
    styles["BodyText"].alignment = TA_JUSTIFY
    styles["BodyText"].spaceAfter = 6
    styles["BodyText"].leading = 14
    styles["BodyText"].fontName = "Helvetica"

    # Bullet point
    styles.add(
        ParagraphStyle(
            name="BulletText",
            parent=styles["Normal"],
            fontSize=10,
            textColor=MEDEX_GRAY_700,
            leftIndent=15,
            spaceAfter=3,
            leading=13,
            fontName="Helvetica",
        )
    )

    # Table header
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontSize=9,
            textColor=white,
            alignment=TA_LEFT,
            fontName="Helvetica-Bold",
        )
    )

    # Table cell
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontSize=9,
            textColor=MEDEX_GRAY_700,
            alignment=TA_LEFT,
            leading=12,
            fontName="Helvetica",
        )
    )

    # Severity badge text
    styles.add(
        ParagraphStyle(
            name="SeverityText",
            parent=styles["Normal"],
            fontSize=9,
            textColor=white,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )
    )

    # Disclaimer style
    styles.add(
        ParagraphStyle(
            name="Disclaimer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=MEDEX_WARNING,
            alignment=TA_LEFT,
            leftIndent=8,
            rightIndent=8,
            spaceAfter=8,
            leading=11,
            fontName="Helvetica-Oblique",
        )
    )

    # Footer style
    styles.add(
        ParagraphStyle(
            name="Footer",
            parent=styles["Normal"],
            fontSize=8,
            textColor=MEDEX_GRAY_500,
            alignment=TA_CENTER,
            spaceBefore=16,
            fontName="Helvetica",
        )
    )

    # Source item style
    styles.add(
        ParagraphStyle(
            name="SourceItem",
            parent=styles["Normal"],
            fontSize=9,
            textColor=MEDEX_GRAY_700,
            leftIndent=10,
            spaceAfter=4,
            leading=12,
            fontName="Helvetica",
        )
    )

    # Highlight box text
    styles.add(
        ParagraphStyle(
            name="HighlightText",
            parent=styles["Normal"],
            fontSize=10,
            textColor=MEDEX_GRAY_900,
            alignment=TA_LEFT,
            spaceAfter=4,
            leading=13,
            fontName="Helvetica",
            backColor=MEDEX_GRAY_50,
        )
    )

    return styles


def markdown_to_paragraphs(text: str, styles) -> list:
    """Convert markdown-like text to ReportLab paragraphs with professional styles."""
    elements = []

    # Clean up the text
    text = text.strip()

    # Split into lines
    lines = text.split("\n")
    current_paragraph = []

    for line in lines:
        line = line.strip()

        if not line:
            # Empty line - flush current paragraph
            if current_paragraph:
                para_text = " ".join(current_paragraph)
                para_text = format_inline_styles(para_text)
                elements.append(Paragraph(para_text, styles["BodyText"]))
                current_paragraph = []
            continue

        # Check for headers - level 1
        if line.startswith("## "):
            if current_paragraph:
                para_text = " ".join(current_paragraph)
                para_text = format_inline_styles(para_text)
                elements.append(Paragraph(para_text, styles["BodyText"]))
                current_paragraph = []
            header_text = line[3:].strip()
            header_text = format_inline_styles(header_text)
            elements.append(Paragraph(header_text, styles["SectionH1"]))
            continue

        # Check for headers - level 2
        if line.startswith("### "):
            if current_paragraph:
                para_text = " ".join(current_paragraph)
                para_text = format_inline_styles(para_text)
                elements.append(Paragraph(para_text, styles["BodyText"]))
                current_paragraph = []
            header_text = line[4:].strip()
            header_text = format_inline_styles(header_text)
            elements.append(Paragraph(header_text, styles["SectionH2"]))
            continue

        # Check for headers - level 3
        if line.startswith("#### "):
            if current_paragraph:
                para_text = " ".join(current_paragraph)
                para_text = format_inline_styles(para_text)
                elements.append(Paragraph(para_text, styles["BodyText"]))
                current_paragraph = []
            header_text = line[5:].strip()
            header_text = format_inline_styles(header_text)
            elements.append(Paragraph(header_text, styles["SectionH3"]))
            continue

        # Check for bullet points
        if line.startswith("- ") or line.startswith("* "):
            if current_paragraph:
                para_text = " ".join(current_paragraph)
                para_text = format_inline_styles(para_text)
                elements.append(Paragraph(para_text, styles["BodyText"]))
                current_paragraph = []
            bullet_text = line[2:].strip()
            bullet_text = format_inline_styles(bullet_text)
            elements.append(Paragraph(f"• {bullet_text}", styles["BulletText"]))
            continue

        # Check for numbered list
        if re.match(r"^\d+\.\s", line):
            if current_paragraph:
                para_text = " ".join(current_paragraph)
                para_text = format_inline_styles(para_text)
                elements.append(Paragraph(para_text, styles["BodyText"]))
                current_paragraph = []
            list_text = format_inline_styles(line)
            elements.append(Paragraph(list_text, styles["BulletText"]))
            continue

        # Regular text - add to current paragraph
        current_paragraph.append(line)

    # Flush remaining paragraph
    if current_paragraph:
        para_text = " ".join(current_paragraph)
        para_text = format_inline_styles(para_text)
        elements.append(Paragraph(para_text, styles["BodyText"]))

    return elements


def format_inline_styles(text: str) -> str:
    """Convert markdown inline styles to ReportLab XML tags."""
    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

    # Italic: *text* or _text_
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)

    # Remove markdown links but keep text
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)

    # Remove any emojis for clean PDF
    emoji_pattern = re.compile(
        "["
        "\U0001f600-\U0001f64f"
        "\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff"
        "\U0001f700-\U0001f77f"
        "\U0001f780-\U0001f7ff"
        "\U0001f800-\U0001f8ff"
        "\U0001f900-\U0001f9ff"
        "\U0001fa00-\U0001fa6f"
        "\U0001fa70-\U0001faff"
        "\U00002702-\U000027b0"
        "\U000024c2-\U0001f251"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)

    return text


def parse_markdown_table(text: str) -> list:
    """Extract tables from markdown text."""
    tables = []
    lines = text.split("\n")
    current_table = []
    in_table = False

    for line in lines:
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            # Skip separator lines
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            # Parse table row
            cells = [cell.strip() for cell in line.split("|")[1:-1]]
            current_table.append(cells)
            in_table = True
        else:
            if in_table and current_table:
                tables.append(current_table)
                current_table = []
            in_table = False

    if current_table:
        tables.append(current_table)

    return tables


def create_pdf_table(data: list, styles, has_header: bool = True) -> Table:
    """Create a professionally formatted ReportLab table with alternating rows."""
    if not data:
        return None

    # Format cells as paragraphs using new styles
    formatted_data = []
    for i, row in enumerate(data):
        style_name = "TableHeader" if (i == 0 and has_header) else "TableCell"
        formatted_row = [
            Paragraph(format_inline_styles(str(cell)), styles[style_name])
            for cell in row
        ]
        formatted_data.append(formatted_row)

    # Calculate column widths based on content
    available_width = 17 * cm
    num_cols = len(data[0]) if data else 1
    col_width = available_width / num_cols

    table = Table(formatted_data, colWidths=[col_width] * num_cols)

    # Professional table styling
    table_style = [
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), MEDEX_PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        # All cells
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        # Borders
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, MEDEX_PRIMARY),
        ("LINEBELOW", (0, 1), (-1, -1), 0.5, MEDEX_GRAY_300),
        ("LINEBEFORE", (0, 0), (0, -1), 0.5, MEDEX_GRAY_300),
        ("LINEAFTER", (-1, 0), (-1, -1), 0.5, MEDEX_GRAY_300),
    ]

    # Add alternating row colors for data rows
    for i in range(1, len(data)):
        if i % 2 == 0:
            table_style.append(("BACKGROUND", (0, i), (-1, i), MEDEX_GRAY_50))

    table.setStyle(TableStyle(table_style))

    return table


def generate_pdf(title: str, content: str, user_mode: str = "Professional") -> bytes:
    """
    Generate a professional medical PDF document.

    Args:
        title: Document title
        content: Markdown-formatted content
        user_mode: User mode (Educational/Professional)

    Returns:
        PDF file as bytes
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = get_professional_styles()
    elements = []

    # Header - professional layout
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
    elements.append(Paragraph(f"MedeX - {title}", styles["DocTitle"]))
    elements.append(
        Paragraph(
            f"Generado: {timestamp}  •  Modo: {user_mode}  •  Documento Médico",
            styles["DocMeta"],
        )
    )

    # Horizontal line
    elements.append(
        HRFlowable(
            width="100%", thickness=2, color=MEDEX_PRIMARY, spaceBefore=0, spaceAfter=16
        )
    )

    # Process content - improved table handling
    # Split content into segments (text blocks and table blocks)
    lines = content.split("\n")
    current_segment = []
    current_is_table = False

    for line in lines:
        stripped = line.strip()
        is_table_line = stripped.startswith("|") and stripped.endswith("|")
        is_separator = bool(re.match(r"^\|[\s\-:|]+\|$", stripped))

        if is_table_line:
            # This line is part of a table
            if not current_is_table and current_segment:
                # Flush previous text segment
                text_content = "\n".join(current_segment)
                paragraphs = markdown_to_paragraphs(text_content, styles)
                elements.extend(paragraphs)
                current_segment = []

            current_is_table = True
            if not is_separator:  # Skip separator lines
                # Parse table row
                cells = [cell.strip() for cell in stripped.split("|")[1:-1]]
                current_segment.append(cells)
        else:
            # This line is regular text
            if current_is_table and current_segment:
                # Flush previous table segment
                table = create_pdf_table(current_segment, styles)
                if table:
                    elements.append(Spacer(1, 8))
                    elements.append(table)
                    elements.append(Spacer(1, 8))
                current_segment = []

            current_is_table = False
            current_segment.append(line)

    # Flush final segment
    if current_segment:
        if current_is_table:
            table = create_pdf_table(current_segment, styles)
            if table:
                elements.append(Spacer(1, 8))
                elements.append(table)
                elements.append(Spacer(1, 8))
        else:
            text_content = "\n".join(current_segment)
            paragraphs = markdown_to_paragraphs(text_content, styles)
            elements.extend(paragraphs)

    # Spacer before disclaimer
    elements.append(Spacer(1, 30))

    # Disclaimer box
    elements.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=MEDEX_WARNING,
            spaceBefore=10,
            spaceAfter=5,
        )
    )

    disclaimer_text = (
        "<b>⚕ AVISO IMPORTANTE:</b> Esta información es de soporte clínico educacional. "
        "No sustituye la evaluación médica presencial ni el juicio clínico profesional. "
        "Validar siempre con guías clínicas locales y protocolos institucionales."
    )
    elements.append(Paragraph(disclaimer_text, styles["Disclaimer"]))

    # Footer
    elements.append(Spacer(1, 20))
    elements.append(
        Paragraph("MedeX Alpha — Sistema de Soporte Clínico con IA", styles["Footer"])
    )

    # Build PDF
    doc.build(elements)

    return buffer.getvalue()


def generate_interactions_pdf(
    drugs: list, interactions_data: list, user_mode: str = "Professional"
) -> bytes:
    """
    Generate PDF for drug interactions.

    Args:
        drugs: List of drug names
        interactions_data: List of interaction dictionaries
        user_mode: User mode

    Returns:
        PDF bytes
    """
    content = f"## Medicamentos Analizados\n{', '.join(drugs)}\n\n"

    if interactions_data:
        for inter in interactions_data:
            content += f"### {inter.get('drug_a', '')} + {inter.get('drug_b', '')}\n"
            content += f"**Severidad:** {inter.get('severity', 'No especificada')}\n\n"
            content += f"**Mecanismo:** {inter.get('mechanism', 'No especificado')}\n\n"
            content += f"**Efecto Clínico:** {inter.get('clinical_effect', 'No especificado')}\n\n"
            content += f"**Manejo:** {inter.get('management', 'No especificado')}\n\n"
            content += "---\n\n"
    else:
        content += "No se encontraron interacciones significativas entre los medicamentos analizados.\n"

    return generate_pdf("Interacciones Medicamentosas", content, user_mode)


def generate_research_pdf(
    query: str, result: str, sources: list, steps: list, user_mode: str = "Professional"
) -> bytes:
    """
    Generate PDF for deep research results.

    Args:
        query: Research query
        result: Research result content
        sources: List of sources used
        steps: Research steps taken
        user_mode: User mode

    Returns:
        PDF bytes
    """
    content = f"## Consulta de Investigación\n{query}\n\n"

    if steps:
        content += "## Metodología\n"
        for step in steps:
            status = "✓" if step.get("status") == "completed" else "○"
            content += f"- {status} {step.get('title', '')}\n"
        content += "\n"

    if sources:
        content += "## Fuentes Consultadas\n"
        for source in sources:
            source_type = source.get("type", "Web")
            source_title = source.get("title", source.get("url", "Fuente desconocida"))
            content += f"- [{source_type}] {source_title}\n"
        content += "\n"

    content += "## Resultados de la Investigación\n\n"
    content += result

    return generate_pdf("Investigación Médica Profunda", content, user_mode)
