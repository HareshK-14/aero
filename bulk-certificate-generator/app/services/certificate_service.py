from pathlib import Path
from datetime import date
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER
from app.config import settings
from app.utils.file_utils import get_certificate_path


def generate_certificate(
    recipient_name: str,
    event_name: str,
    certificate_title: str,
    issue_date: date,
    certificate_id: str,
) -> str:
    """
    Generate a PDF certificate using ReportLab.

    Returns:
        str: The absolute path to the generated PDF file.

    Raises:
        Exception: If PDF generation fails.
    """
    output_path = get_certificate_path(certificate_id)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=landscape(A4),
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    org_style = ParagraphStyle(
        "OrgStyle",
        parent=styles["Normal"],
        fontSize=13,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        fontSize=36,
        textColor=colors.HexColor("#1a1a2e"),
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        fontSize=14,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    presented_style = ParagraphStyle(
        "PresentedStyle",
        parent=styles["Normal"],
        fontSize=13,
        textColor=colors.HexColor("#777777"),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    name_style = ParagraphStyle(
        "NameStyle",
        parent=styles["Normal"],
        fontSize=30,
        textColor=colors.HexColor("#16213e"),
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontSize=13,
        textColor=colors.HexColor("#444444"),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    )

    issue_date_str = issue_date.strftime("%B %d, %Y") if isinstance(issue_date, date) else str(issue_date)

    story = [
        Spacer(1, 0.3 * inch),
        Paragraph(settings.organization_name.upper(), org_style),
        HRFlowable(width="80%", thickness=2, color=colors.HexColor("#c9a84c"), spaceAfter=12),
        Paragraph(certificate_title, title_style),
        HRFlowable(width="80%", thickness=2, color=colors.HexColor("#c9a84c"), spaceBefore=8, spaceAfter=16),
        Paragraph("This certificate is proudly presented to", presented_style),
        Spacer(1, 0.1 * inch),
        Paragraph(recipient_name, name_style),
        Spacer(1, 0.1 * inch),
        Paragraph("for successful participation in", body_style),
        Paragraph(f"<b>{event_name}</b>", body_style),
        Spacer(1, 0.25 * inch),
        Paragraph(f"Issue Date: {issue_date_str}", body_style),
        Spacer(1, 0.2 * inch),
        HRFlowable(width="60%", thickness=1, color=colors.HexColor("#cccccc"), spaceAfter=6),
        Paragraph(f"Certificate ID: {certificate_id}", small_style),
    ]

    doc.build(story)
    return str(output_path)
