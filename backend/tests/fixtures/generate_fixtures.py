import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def create_lease_pdf(filename: str, title: str, rent: str, notice_days: str, termination_fee: str):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        alignment=1,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=10,
        spaceAfter=4,
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    story = []
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 10))

    clauses = [
        ("Clause 1. Parties and Premises",
         "This Residential Lease Agreement is entered into between Apex Living LLC ('Landlord') and Priya Sharma ('Tenant') for the premises located at 742 Evergreen Terrace, Apt 4B. The premises shall be occupied solely by Tenant as a private residence."),

        ("Clause 2. Term and Duration",
         "The initial term of this lease shall commence on August 1, 2026, and shall terminate on July 31, 2027. Any holding over after expiration without renewal shall constitute a month-to-month tenancy."),

        ("Clause 3. Rent and Fees",
         f"Tenant agrees to pay monthly rent in the amount of {rent}, payable in advance on the first (1st) day of each calendar month. A late fee of $150.00 shall be assessed if payment is not received within five (5) days of the due date."),

        ("Clause 4. Security Deposit",
         "Tenant shall deposit with Landlord the sum of $2,400.00 as security for performance of lease obligations. Landlord shall return the deposit within thirty (30) days of move-out inspection less lawful deductions."),

        ("Clause 5. Restrictions and Subletting",
         "Subletting or assignment without Landlord's prior written consent is strictly prohibited. Unauthorized guests staying longer than fourteen (14) consecutive days require prior registration. Quiet hours are observed between 10:00 PM and 8:00 AM daily."),

        ("Clause 6. Repairs and Habitability",
         "Landlord shall maintain heating, electrical, plumbing, and structural components in habitable condition. Tenant shall promptly report needed repairs in writing. Tenant is responsible for minor repairs under $100 not caused by normal wear and tear."),

        ("Clause 7. Landlord Access and Privacy",
         "Landlord may enter the premises for inspection, repairs, or showing with at least twenty-four (24) hours' prior written notice, except in emergencies where immediate access is necessary."),

        ("Clause 8. Notice of Termination or Renewal",
         f"Either party must provide at least {notice_days} written notice prior to the end of the term regarding intent to vacate or renew."),

        ("Clause 9(a). Early Termination and Penalties",
         f"In the event Tenant elects to terminate this Agreement prior to the expiration of the full term, Tenant shall provide sixty (60) days' written notice and pay an early termination fee equivalent to {termination_fee}. Tenant remains liable for rent during the 60-day notice period."),

        ("Clause 10. Governing Law",
         "This agreement shall be interpreted in accordance with applicable residential landlord-tenant regulations. If any provision is held invalid, remaining provisions continue in full force.")
    ]

    for heading, text in clauses:
        story.append(Paragraph(heading, heading_style))
        story.append(Paragraph(text, body_style))

    doc.build(story)


if __name__ == "__main__":
    fixtures_dir = os.path.dirname(__file__)
    p1 = os.path.join(fixtures_dir, "sample_lease.pdf")
    p2 = os.path.join(fixtures_dir, "sample_lease_renewal.pdf")

    create_lease_pdf(
        p1,
        title="RESIDENTIAL LEASE AGREEMENT (2026)",
        rent="$2,400.00",
        notice_days="sixty (60) days'",
        termination_fee="two (2) months' rent ($4,800.00)",
    )
    create_lease_pdf(
        p2,
        title="RENEWAL LEASE OFFER (2027)",
        rent="$2,650.00",
        notice_days="sixty (60) days'",
        termination_fee="three (3) months' rent ($7,950.00)",
    )
    print(f"Created {p1} ({os.path.getsize(p1)} bytes)")
    print(f"Created {p2} ({os.path.getsize(p2)} bytes)")
