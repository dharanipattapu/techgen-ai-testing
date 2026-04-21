import io
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
 
 
# ─────────────────────────────────────────────
# EXISTING: Test Cases Report (generation only)
# ─────────────────────────────────────────────
 
def create_pdf(test_cases: list) -> bytes:
    """
    Generate a PDF report from test cases and return it as bytes.
    (No file is written to disk.)
    """
    buffer = io.BytesIO()
 
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
 
    styles = getSampleStyleSheet()
 
    title_style = ParagraphStyle(
        'ReportTitle', parent=styles['Title'],
        fontSize=18, textColor=colors.HexColor('#0f172a'), spaceAfter=6
    )
    heading_style = ParagraphStyle(
        'TestHeading', parent=styles['Heading2'],
        fontSize=12, textColor=colors.HexColor('#1e40af'), spaceBefore=10, spaceAfter=4
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#475569'), spaceBefore=2
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#1e293b'), spaceAfter=4, leading=14
    )
 
    priority_text = {"High": "HIGH", "Medium": "MEDIUM", "Low": "LOW"}
 
    content = []
    content.append(Paragraph("AI Generated Test Cases Report", title_style))
    content.append(Paragraph(f"Total Test Cases: {len(test_cases)}", body_style))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1')))
    content.append(Spacer(1, 6))
 
    for i, t in enumerate(test_cases, 1):
        priority = t.get('priority', 'Medium')
        tc_type  = t.get('type', 'Functional')
 
        content.append(Paragraph(f"TC-{i:02d}: {t.get('title', 'N/A')}", heading_style))
        content.append(Paragraph(
            f"Priority: <b>{priority_text.get(priority, priority)}</b>"
            f"&nbsp;&nbsp;|&nbsp;&nbsp;Type: <b>{tc_type}</b>",
            label_style
        ))
 
        content.append(Paragraph("<b>Steps:</b>", label_style))
        steps_text = t.get('steps', 'N/A').replace('\n', '<br/>')
        content.append(Paragraph(steps_text, body_style))
 
        content.append(Paragraph("<b>Expected Result:</b>", label_style))
        content.append(Paragraph(t.get('expected', 'N/A'), body_style))
 
        content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
        content.append(Spacer(1, 4))
 
    doc.build(content)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
 
 
# ─────────────────────────────────────────────
# NEW: Execution Results Report
# ─────────────────────────────────────────────
 
def create_results_pdf(results: list, summary: dict) -> bytes:
    """
    Generate a rich PDF execution report from run results.
 
    Args:
        results: List of result dicts — title, status, priority, type, message,
                 and optionally steps + expected from the original test case.
        summary: Dict with total, passed, failed, pass_rate.
 
    Returns:
        PDF as bytes (no file written to disk).
    """
    buffer = io.BytesIO()
 
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
 
    styles = getSampleStyleSheet()
 
    # ── Custom Styles ────────────────────────────────────────
    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        fontSize=20, textColor=colors.HexColor('#0f172a'),
        spaceAfter=4, fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#64748b'),
        spaceAfter=16, fontName='Helvetica'
    )
    section_style = ParagraphStyle(
        'Section', parent=styles['Heading2'],
        fontSize=13, textColor=colors.HexColor('#1e40af'),
        spaceBefore=16, spaceAfter=8, fontName='Helvetica-Bold'
    )
    label_style = ParagraphStyle(
        'Label', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#64748b'),
        spaceBefore=2, fontName='Helvetica'
    )
    body_style = ParagraphStyle(
        'Body', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#1e293b'),
        spaceAfter=3, leading=13, fontName='Helvetica'
    )
    pass_style = ParagraphStyle(
        'Pass', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#15803d'),
        fontName='Helvetica-Bold'
    )
    fail_style = ParagraphStyle(
        'Fail', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#b91c1c'),
        fontName='Helvetica-Bold'
    )
    msg_style = ParagraphStyle(
        'Msg', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#334155'),
        leading=12, fontName='Helvetica'
    )
 
    content = []
    generated_at = datetime.now().strftime("%d %B %Y, %I:%M %p")
 
    # ── Header ───────────────────────────────────────────────
    content.append(Paragraph("Test Execution Report", title_style))
    content.append(Paragraph(f"AI-Powered Code Analysis &nbsp;·&nbsp; Generated: {generated_at}", subtitle_style))
    content.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1e40af')))
    content.append(Spacer(1, 10))
 
    # ── Summary Table ────────────────────────────────────────
    content.append(Paragraph("Execution Summary", section_style))
 
    total    = summary.get('total', len(results))
    passed   = summary.get('passed', 0)
    failed   = summary.get('failed', 0)
    rate     = summary.get('pass_rate', 0)
 
    # Coloured summary boxes as a table
    summary_data = [
        [
            Paragraph(f"<b>TOTAL</b><br/><font size=18>{total}</font>", _centred(styles, '#1e40af')),
            Paragraph(f"<b>PASSED</b><br/><font size=18>{passed}</font>", _centred(styles, '#15803d')),
            Paragraph(f"<b>FAILED</b><br/><font size=18>{failed}</font>", _centred(styles, '#b91c1c')),
            Paragraph(f"<b>PASS RATE</b><br/><font size=18>{rate}%</font>", _centred(styles, '#92400e')),
        ]
    ]
 
    summary_table = Table(summary_data, colWidths=[40*mm, 40*mm, 40*mm, 40*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND',  (0,0), (0,0), colors.HexColor('#eff6ff')),
        ('BACKGROUND',  (1,0), (1,0), colors.HexColor('#f0fdf4')),
        ('BACKGROUND',  (2,0), (2,0), colors.HexColor('#fef2f2')),
        ('BACKGROUND',  (3,0), (3,0), colors.HexColor('#fffbeb')),
        ('BOX',         (0,0), (0,0), 1, colors.HexColor('#bfdbfe')),
        ('BOX',         (1,0), (1,0), 1, colors.HexColor('#bbf7d0')),
        ('BOX',         (2,0), (2,0), 1, colors.HexColor('#fecaca')),
        ('BOX',         (3,0), (3,0), 1, colors.HexColor('#fde68a')),
        ('ALIGN',       (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',  (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0), (-1,-1), 10),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING',(0,0), (-1,-1), 8),
        ('ROUNDEDCORNERS', [4]),
    ]))
    content.append(summary_table)
    content.append(Spacer(1, 14))
 
    # ── Priority Breakdown ───────────────────────────────────
    priority_counts = {'High': 0, 'Medium': 0, 'Low': 0}
    type_counts = {}
    for r in results:
        p = r.get('priority', 'Medium')
        priority_counts[p] = priority_counts.get(p, 0) + 1
        t = r.get('type', 'Functional')
        type_counts[t] = type_counts.get(t, 0) + 1
 
    content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
    content.append(Spacer(1, 6))
 
    # Breakdown row
    breakdown_data = [[
        Paragraph(
            f"<b>Priority Breakdown</b><br/>"
            f"<font color='#b91c1c'>High: {priority_counts.get('High',0)}</font>  "
            f"<font color='#92400e'>Medium: {priority_counts.get('Medium',0)}</font>  "
            f"<font color='#15803d'>Low: {priority_counts.get('Low',0)}</font>",
            body_style
        ),
        Paragraph(
            "<b>Types Covered</b><br/>" +
            "  ".join(f"{k}: {v}" for k, v in sorted(type_counts.items())),
            body_style
        ),
    ]]
    bd_table = Table(breakdown_data, colWidths=[85*mm, 85*mm])
    bd_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('BOX',        (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('INNERGRID',  (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0),(-1,-1), 8),
        ('LEFTPADDING',(0,0),(-1,-1), 10),
    ]))
    content.append(bd_table)
    content.append(Spacer(1, 16))
 
    # ── Individual Results ───────────────────────────────────
    content.append(Paragraph("Detailed Test Results", section_style))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1e40af')))
    content.append(Spacer(1, 6))
 
    for i, r in enumerate(results, 1):
        status   = r.get('status', 'Failed')
        priority = r.get('priority', 'Medium')
        tc_type  = r.get('type', 'Functional')
        title    = r.get('title', 'N/A')
        message  = r.get('message', '')
        steps    = r.get('steps', '')
        expected = r.get('expected', '')
 
        # Status colours
        status_color = '#15803d' if status == 'Passed' else '#b91c1c'
        status_bg    = '#f0fdf4' if status == 'Passed' else '#fef2f2'
        status_border= '#bbf7d0' if status == 'Passed' else '#fecaca'
        priority_color = {'High': '#b91c1c', 'Medium': '#92400e', 'Low': '#15803d'}.get(priority, '#475569')
 
        # Row header
        header_data = [[
            Paragraph(
                f"<b>TC-{i:02d}: {title}</b>",
                ParagraphStyle('H', parent=styles['Normal'], fontSize=10,
                               textColor=colors.HexColor('#0f172a'), fontName='Helvetica-Bold')
            ),
            Paragraph(
                f"<b>{status.upper()}</b>",
                ParagraphStyle('S', parent=styles['Normal'], fontSize=10,
                               textColor=colors.HexColor(status_color),
                               fontName='Helvetica-Bold', alignment=2)
            ),
        ]]
        hdr_table = Table(header_data, colWidths=[130*mm, 40*mm])
        hdr_table.setStyle(TableStyle([
            ('BACKGROUND',  (0,0), (-1,-1), colors.HexColor(status_bg)),
            ('BOX',         (0,0), (-1,-1), 1,   colors.HexColor(status_border)),
            ('TOPPADDING',  (0,0), (-1,-1), 7),
            ('BOTTOMPADDING',(0,0),(-1,-1), 7),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING',(0,0),(-1,-1), 10),
            ('VALIGN',      (0,0), (-1,-1), 'MIDDLE'),
        ]))
        content.append(hdr_table)
 
        # Meta row
        content.append(Paragraph(
            f"Priority: <font color='{priority_color}'><b>{priority}</b></font>"
            f"&nbsp;&nbsp;|&nbsp;&nbsp;Type: <b>{tc_type}</b>",
            ParagraphStyle('Meta', parent=styles['Normal'], fontSize=8,
                           textColor=colors.HexColor('#475569'),
                           leftIndent=4, spaceBefore=3)
        ))
 
        # Steps
        if steps:
            content.append(Paragraph("<b>Steps:</b>", label_style))
            content.append(Paragraph(steps.replace('\n', '<br/>'), body_style))
 
        # Expected
        if expected:
            content.append(Paragraph("<b>Expected Result:</b>", label_style))
            content.append(Paragraph(expected, body_style))
 
        # AI Analysis message
        if message:
            content.append(Paragraph("<b>AI Analysis:</b>", label_style))
            content.append(Paragraph(message, msg_style))
 
        content.append(Spacer(1, 8))
        content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
        content.append(Spacer(1, 6))
 
    # ── Footer ───────────────────────────────────────────────
    content.append(Spacer(1, 10))
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cbd5e1')))
    content.append(Paragraph(
        f"Generated by TECHGEN AI Testing System &nbsp;·&nbsp; {generated_at}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8,
                       textColor=colors.HexColor('#94a3b8'), alignment=1, spaceBefore=6)
    ))
 
    doc.build(content)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
 
 
def _centred(styles, hex_color: str):
    """Helper — centred paragraph style with given text colour."""
    return ParagraphStyle(
        f'C_{hex_color}', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor(hex_color),
        alignment=1, fontName='Helvetica-Bold', leading=16
    )
 