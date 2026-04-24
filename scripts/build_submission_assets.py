from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
PDF_DIR = DOCS_DIR / "pdf"
ASSETS_DIR = ROOT / "assets"


def build_pdf_from_markdown(input_path: Path, output_path: Path) -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    heading_style = styles["Heading2"]
    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )
    code_style = ParagraphStyle(
        "CodeBlock",
        parent=styles["BodyText"],
        fontName="Courier",
        fontSize=8,
        leading=10,
    )

    story = []
    in_code_block = False
    code_lines: list[str] = []

    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
            if in_code_block:
                story.append(Preformatted("\n".join(code_lines), code_style))
                story.append(Spacer(1, 0.3 * cm))
                code_lines.clear()
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if not line.strip():
            story.append(Spacer(1, 0.2 * cm))
            continue

        if line.startswith("# "):
            story.append(Paragraph(line[2:], title_style))
        elif line.startswith("## "):
            story.append(Paragraph(line[3:], heading_style))
        elif line.startswith("### "):
            story.append(Paragraph(f"<b>{line[4:]}</b>", body_style))
        elif line.startswith("- "):
            story.append(Paragraph(f"&bull; {line[2:]}", body_style))
        elif line[:2].isdigit() and line[1:3] == ". ":
            story.append(Paragraph(line, body_style))
        else:
            story.append(Paragraph(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), body_style))

    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    document.build(story)


def build_sample_kb_pdf(output_path: Path) -> None:
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    body_style = ParagraphStyle(
        "KBBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        spaceAfter=10,
    )
    sections = [
        ("Delivery Policy", "Standard delivery takes 4 to 6 business days. Express delivery takes 1 to 2 business days in serviceable locations."),
        ("Refund Policy", "Approved refunds are processed within 5 to 7 business days after the returned item passes inspection."),
        ("Cancellation Policy", "Orders can be cancelled before shipment from the My Orders section. Shipped orders must follow the return workflow."),
        ("Login Support", "If login fails after password reset, customers should clear browser cache, verify OTP-based identity checks, and retry after 15 minutes."),
        ("Billing Support", "Double charge complaints must be escalated to a human billing specialist after payment gateway verification."),
        ("Human Escalation", "If a customer requests a human agent or the system has low confidence, the conversation must be transferred to support staff."),
    ]

    story = [Paragraph("Customer Support Knowledge Base", title_style), Spacer(1, 0.4 * cm)]
    for heading, content in sections:
        story.append(Paragraph(f"<b>{heading}</b>", body_style))
        story.append(Paragraph(content, body_style))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )
    document.build(story)


def main() -> None:
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    build_pdf_from_markdown(DOCS_DIR / "HLD.md", PDF_DIR / "HLD.pdf")
    build_pdf_from_markdown(DOCS_DIR / "LLD.md", PDF_DIR / "LLD.pdf")
    build_pdf_from_markdown(
        DOCS_DIR / "TECHNICAL_DOCUMENTATION.md",
        PDF_DIR / "Technical_Documentation.pdf",
    )
    build_sample_kb_pdf(ASSETS_DIR / "customer_support_kb.pdf")

    print("Generated submission PDFs and sample knowledge-base PDF.")


if __name__ == "__main__":
    main()
