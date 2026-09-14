import io
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

from app.models.entities import Document, Finding, ActionPlan, Question, SeverityLevel


def _draw_page_decorations(canvas, doc):
    """Draw header line and persistent footer disclaimer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#64748b"))

    # Top thin line and running header
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.setLineWidth(0.5)
    canvas.line(54, 750, 558, 750)
    canvas.drawString(54, 755, "ClauseLens — Legal Consultation Preparation Packet")

    # Bottom running footer
    canvas.line(54, 45, 558, 45)
    canvas.drawString(
        54, 32,
        "ClauseLens provides information, not legal advice. Prepared for tenant legal consultation."
    )
    canvas.drawRightString(558, 32, f"Page {doc.page}")
    canvas.restoreState()


def generate_lawyer_prep_pdf(document_id: str, db: Session) -> bytes:
    """
    Generate a branded, multi-page PDF preparation packet for tenant lawyer consultation.
    Includes lease summary, situation context, prioritized findings with citations,
    action plan checklist, and topic-grouped lawyer questions.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise ValueError(f"Document with id {document_id} not found")

    findings = db.query(Finding).filter(Finding.document_id == document_id).order_by(
        Finding.severity.desc(), Finding.page_number.asc()
    ).all()

    action_plan = db.query(ActionPlan).filter(ActionPlan.document_id == document_id).first()
    questions = db.query(Question).filter(Question.document_id == document_id).order_by(
        Question.priority.desc()
    ).all()

    buffer = io.BytesIO()
    doc_template = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=60,
        bottomMargin=55,
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
    )
    bold_body = ParagraphStyle(
        "BoldBodyCustom",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0f172a"),
    )
    citation_style = ParagraphStyle(
        "CitationText",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1e40af"),
    )
    callout_style = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
    )

    story = []

    # 1. Header & Title Block
    story.append(Paragraph("ClauseLens", ParagraphStyle(
        "Brand", fontName="Helvetica-Bold", fontSize=12, textColor=colors.HexColor("#2563eb")
    )))
    story.append(Paragraph("Lawyer Consultation Preparation Packet", title_style))
    story.append(Paragraph("Evidence-First Lease Analysis & Tenant Rights Map", subtitle_style))
    story.append(Spacer(1, 10))

    # Meta Table
    export_time = datetime.now(timezone.utc).strftime("%B %d, %Y - %H:%M UTC")
    meta_data = [
        [
            Paragraph(f"<b>Document:</b> {doc.filename}", body_style),
            Paragraph(f"<b>Pages:</b> {doc.page_count}", body_style),
            Paragraph(f"<b>Generated:</b> {export_time}", body_style),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[240, 90, 174])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # 2. Situation Context Banner (if available)
    if action_plan and (action_plan.situation_context_text or action_plan.situation_type):
        sit_type_formatted = (action_plan.situation_type or "General").replace("_", " ").title()
        urgency_val = action_plan.urgency.value if hasattr(action_plan.urgency, "value") else str(action_plan.urgency)
        urgency_formatted = urgency_val.upper()

        urgency_bg = "#fee2e2" if urgency_formatted == "HIGH" else ("#fef3c7" if urgency_formatted == "MEDIUM" else "#f1f5f9")
        urgency_color = "#991b1b" if urgency_formatted == "HIGH" else ("#92400e" if urgency_formatted == "MEDIUM" else "#334155")

        sit_banner_data = [
            [
                Paragraph(f"<b>Tenant Situation:</b> {sit_type_formatted} &nbsp;|&nbsp; <b>Urgency:</b> <font color='{urgency_color}'><b>{urgency_formatted}</b></font>", bold_body),
            ],
            [
                Paragraph(f"<i>\"{action_plan.situation_context_text or 'No free-text context specified.'}\"</i>", callout_style)
            ]
        ]
        sit_table = Table(sit_banner_data, colWidths=[504])
        sit_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(sit_table)
        story.append(Spacer(1, 12))

    # 3. Document Summary & Key Terms
    if doc.summary:
        story.append(Paragraph("1. Executive Lease Summary", section_heading))
        story.append(Paragraph(doc.summary, body_style))
        story.append(Spacer(1, 8))

    if doc.key_terms and isinstance(doc.key_terms, list):
        terms_text = " • ".join([str(t) for t in doc.key_terms])
        story.append(Paragraph(f"<b>Key Identified Terms:</b> {terms_text}", body_style))
        story.append(Spacer(1, 10))

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # 4. Prioritized Risk Radar Findings
    story.append(Paragraph("2. Prioritized Risk Radar & Problematic Clauses", section_heading))
    if not findings:
        story.append(Paragraph("No high-risk findings detected in this agreement.", body_style))
    else:
        for idx, f in enumerate(findings):
            sev = f.severity.value if hasattr(f.severity, "value") else str(f.severity)
            sev_badge = sev.upper()
            badge_color = "#dc2626" if sev_badge == "HIGH" else ("#d97706" if sev_badge == "MEDIUM" else "#16a34a")

            finding_flowables = [
                Paragraph(
                    f"<b>{idx+1}. {f.title}</b> &nbsp;&nbsp;[<font color='{badge_color}'><b>{sev_badge} RISK</b></font>]",
                    bold_body
                ),
                Spacer(1, 3),
                Paragraph(f.plain_explanation, body_style),
            ]
            if f.quote:
                finding_flowables.append(Spacer(1, 3))
                finding_flowables.append(Paragraph(
                    f"<b>Verified Source:</b> Page {f.page_number} — <i>\"{f.quote[:200]}\"</i>",
                    citation_style
                ))

            finding_box = Table([[finding_flowables]], colWidths=[504])
            finding_box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(KeepTogether([finding_box, Spacer(1, 6)]))

    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # 5. Ordered Action Plan Checklist
    story.append(Paragraph("3. Recommended Action Plan Checklist", section_heading))
    steps = action_plan.steps if action_plan and action_plan.steps else []
    if not steps:
        story.append(Paragraph("No action plan steps currently configured.", body_style))
    else:
        step_rows = []
        for step in steps:
            order = step.get("order", "•")
            action = step.get("action", "")
            rationale = step.get("rationale", "")
            cit = step.get("citation")

            step_content = [
                Paragraph(f"[  ] <b>Step {order}:</b> {action}", bold_body),
                Spacer(1, 2),
                Paragraph(f"<b>Rationale:</b> {rationale}", body_style),
            ]
            if cit and isinstance(cit, dict) and cit.get("quote"):
                step_content.append(Spacer(1, 2))
                step_content.append(Paragraph(
                    f"<b>Document Anchor:</b> Page {cit.get('page')}, Clause {cit.get('clause_id') or 'N/A'}: <i>\"{cit.get('quote')[:160]}\"</i>",
                    citation_style
                ))

            step_rows.append([step_content])

        action_table = Table(step_rows, colWidths=[504])
        action_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(KeepTogether([action_table]))

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # 6. Specific Lawyer Questions
    story.append(Paragraph("4. Targeted Consultation Questions for Legal Counsel", section_heading))
    story.append(Paragraph(
        "Take these prioritized, non-generic questions to your tenant attorney or legal clinic consultation:",
        body_style
    ))
    story.append(Spacer(1, 6))

    if not questions:
        story.append(Paragraph("No specific consultation questions generated.", body_style))
    else:
        q_rows = []
        for idx, q in enumerate(questions):
            pri = q.priority.value if hasattr(q.priority, "value") else str(q.priority)
            pri_upper = pri.upper()
            pri_color = "#dc2626" if pri_upper == "HIGH" else "#475569"

            q_flowables = [
                Paragraph(
                    f"<b>Q{idx+1} ({q.topic}):</b> {q.question_text} &nbsp;[<font color='{pri_color}'><b>{pri_upper} PRIORITY</b></font>]",
                    body_style
                ),
            ]
            q_rows.append([q_flowables])

        q_table = Table(q_rows, colWidths=[504])
        q_table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(KeepTogether([q_table]))

    # Build document
    doc_template.build(story, onFirstPage=_draw_page_decorations, onLaterPages=_draw_page_decorations)
    return buffer.getvalue()
