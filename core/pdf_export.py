import io
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_brief_pdf(ticker: str, brief: str, metrics: dict, sentiment: dict, confidence: int, sector_data: dict = None) -> bytes:
    """Generates a formatted PDF report of the analyst brief.

    Args:
        ticker: The stock ticker.
        brief: The Gemini-generated analyst brief text.
        metrics: The stock financial metrics dictionary.
        sentiment: The news sentiment analysis dictionary.
        confidence: The confidence score (0-100).
        sector_data: Optional sector relative strength dictionary.

    Returns:
        Bytes containing the PDF document.
    """
    buffer = io.BytesIO()
    
    # Page setup - 0.75 margin
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Define custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0F172A'), # Charcoal / Slate
        spaceAfter=15
    )
    
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor('#334155'),
        spaceAfter=8
    )
    
    meta_label_style = ParagraphStyle(
        'MetaLabel',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#475569')
    )
    
    meta_val_style = ParagraphStyle(
        'MetaValue',
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor('#0F172A')
    )
    
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#94A3B8'),
        alignment=1 # Center aligned
    )

    # 1. Document Title
    story.append(Paragraph("FinSight Equity Research Brief", title_style))
    story.append(Spacer(1, 8))
    
    # 2. Metadata Grid Table
    company_name = metrics.get("company_name", ticker)
    price_val = f"${metrics.get('current_price', 0.0):.2f}" if metrics.get('current_price') else "N/A"
    pe_val = f"{metrics.get('pe_ratio'):.2f}" if metrics.get('pe_ratio') else "N/A"
    
    raw_cap = metrics.get('market_cap')
    cap_val = "N/A"
    if raw_cap:
        if raw_cap >= 1e12:
            cap_val = f"${raw_cap/1e12:.2f}T"
        elif raw_cap >= 1e9:
            cap_val = f"${raw_cap/1e9:.2f}B"
        elif raw_cap >= 1e6:
            cap_val = f"${raw_cap/1e6:.2f}M"
            
    change_raw = metrics.get('thirty_day_change_percent', 0.0)
    change_val = f"{change_raw:+.2f}%"
    
    # Sentiment and Confidence Info
    sent_sig = sentiment.get("aggregate_signal", "Mixed")
    if isinstance(sentiment, str):
        sent_sig = sentiment
        
    meta_data = [
        [
            Paragraph("Ticker", meta_label_style), Paragraph(ticker.upper(), meta_val_style),
            Paragraph("Current Price", meta_label_style), Paragraph(price_val, meta_val_style)
        ],
        [
            Paragraph("Company", meta_label_style), Paragraph(company_name, meta_val_style),
            Paragraph("P/E Ratio", meta_label_style), Paragraph(pe_val, meta_val_style)
        ],
        [
            Paragraph("Sector", meta_label_style), Paragraph(metrics.get("sector", "N/A"), meta_val_style),
            Paragraph("Market Cap", meta_label_style), Paragraph(cap_val, meta_val_style)
        ],
        [
            Paragraph("Analysis Date", meta_label_style), Paragraph(datetime.datetime.now().strftime("%Y-%m-%d"), meta_val_style),
            Paragraph("30-Day Return", meta_label_style), Paragraph(change_val, meta_val_style)
        ],
        [
            Paragraph("News Sentiment", meta_label_style), Paragraph(sent_sig, meta_val_style),
            Paragraph("Confidence Score", meta_label_style), Paragraph(f"{confidence}/100", meta_val_style)
        ]
    ]
    
    meta_table = Table(meta_data, colWidths=[1.25*inch, 2.25*inch, 1.25*inch, 2.25*inch])
    meta_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # 3. Analyst Brief Section
    story.append(Paragraph("Analyst Brief", section_heading))
    
    # Split brief into paragraphs and add them
    brief_paragraphs = brief.strip().split("\n\n")
    for para in brief_paragraphs:
        if para.strip():
            # Clean double stars/markdown bold tags, converting to HTML <b> tags
            clean_para = para.replace("**", "<b>", 1).replace("**", "</b>", 1)
            # Repeat to catch all occurrences
            while "**" in clean_para:
                clean_para = clean_para.replace("**", "<b>", 1).replace("**", "</b>", 1)
            story.append(Paragraph(clean_para, body_style))
            
    story.append(Spacer(1, 10))
    
    # 4. Sector Relative Strength Table (if available)
    if sector_data and "comparison_metrics" in sector_data:
        story.append(Paragraph("Sector Comparison", section_heading))
        
        comp_headers = [
            Paragraph("Ticker", meta_label_style),
            Paragraph("Company Name", meta_label_style),
            Paragraph("P/E Ratio", meta_label_style),
            Paragraph("30-Day Return", meta_label_style)
        ]
        
        comp_rows = [comp_headers]
        for m in sector_data["comparison_metrics"]:
            ticker_name = m.get("ticker", "")
            # Add (Target) to the row of the analyzed stock
            if ticker_name.upper() == ticker.upper():
                ticker_name = f"<b>{ticker_name} (Target)</b>"
                
            pe_row = f"{m.get('pe_ratio'):.2f}" if m.get("pe_ratio") is not None else "N/A"
            ret_row = f"{m.get('thirty_day_change_percent', 0.0):+.2f}%"
            
            comp_rows.append([
                Paragraph(ticker_name, meta_val_style),
                Paragraph(m.get("company_name", ""), meta_val_style),
                Paragraph(pe_row, meta_val_style),
                Paragraph(ret_row, meta_val_style)
            ])
            
        comp_table = Table(comp_rows, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1.5*inch])
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ]))
        story.append(comp_table)
        story.append(Spacer(1, 15))
        
    # 5. Footer / Disclaimer
    story.append(Spacer(1, 20))
    story.append(Paragraph("FinSight is an educational project. This is not financial advice.", disclaimer_style))
    
    # Build Document
    doc.build(story)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
