"""PDF generation service for commercial offers."""

from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generate_commercial_offer_pdf(project_data, materials_list=None):
    """
    Generate a commercial offer PDF for a project.
    
    Args:
        project_data: Dictionary containing project information
        materials_list: List of materials with quantities and prices
    
    Returns:
        BytesIO: PDF file as bytes
    """
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    normal_style.leading = 14
    
    # Add Title
    elements.append(Paragraph("OFERTĂ COMERCIALĂ", title_style))
    elements.append(Spacer(1, 10*mm))
    
    # Add Offer Details Section
    elements.append(Paragraph("Detalii Ofertă", heading_style))
    
    offer_date = datetime.now().strftime("%d.%m.%Y")
    offer_details = [
        ['Data ofertei:', offer_date],
        ['Nr. ofertă:', f"OF-{project_data.get('id', 'N/A')}-{datetime.now().strftime('%Y%m%d')}"],
        ['Valabilitate:', '30 zile'],
    ]
    
    offer_table = Table(offer_details, colWidths=[60*mm, 80*mm])
    offer_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(offer_table)
    elements.append(Spacer(1, 10*mm))
    
    # Add Client Information
    elements.append(Paragraph("Date Client", heading_style))
    
    client_info = [
        ['Nume client:', project_data.get('client_name', 'N/A')],
        ['Contact:', project_data.get('client_contact', 'N/A')],
        ['Locație:', project_data.get('location', 'N/A')],
    ]
    
    client_table = Table(client_info, colWidths=[60*mm, 80*mm])
    client_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 10*mm))
    
    # Add Project Information
    elements.append(Paragraph("Detalii Proiect", heading_style))
    
    project_info = [
        ['Nume proiect:', project_data.get('name', 'N/A')],
        ['Capacitate sistem:', f"{project_data.get('capacity_kw', 0)} kW" if project_data.get('capacity_kw') else 'N/A'],
        ['Status:', project_data.get('status', 'N/A').replace('_', ' ').title()],
    ]
    
    if project_data.get('start_date'):
        project_info.append(['Data start estimată:', str(project_data.get('start_date'))])
    
    project_table = Table(project_info, colWidths=[60*mm, 80*mm])
    project_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(project_table)
    elements.append(Spacer(1, 10*mm))
    
    # Add Materials List (if provided)
    if materials_list and len(materials_list) > 0:
        elements.append(Paragraph("Materiale și Costuri", heading_style))
        
        # Materials table header
        materials_data = [
            ['Nr.', 'Material', 'SKU', 'Cantitate', 'Preț Unitar (RON)', 'Total (RON)']
        ]
        
        total_cost = 0
        for idx, material in enumerate(materials_list, 1):
            material_total = material.get('quantity_planned', 0) * material.get('unit_price', 0)
            total_cost += material_total
            
            materials_data.append([
                str(idx),
                material.get('material_name', 'N/A'),
                material.get('material_sku', 'N/A'),
                f"{material.get('quantity_planned', 0):.2f}",
                f"{material.get('unit_price', 0):.2f}",
                f"{material_total:.2f}"
            ])
        
        # Add total row
        materials_data.append(['', '', '', '', 'TOTAL:', f"{total_cost:.2f}"])
        
        materials_table = Table(materials_data, colWidths=[10*mm, 60*mm, 30*mm, 20*mm, 30*mm, 30*mm])
        materials_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Body style
            ('FONT', (0, 1), (-1, -2), 'Helvetica', 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -2), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -2), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -2), 6),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f3f4f6')]),
            
            # Total row style
            ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 11),
            ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
            ('TOPPADDING', (0, -1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(materials_table)
        elements.append(Spacer(1, 10*mm))
    
    # Add pricing section (if no materials provided, use estimated cost)
    if not materials_list or len(materials_list) == 0:
        if project_data.get('estimated_cost'):
            elements.append(Paragraph("Estimare Cost", heading_style))
            cost_data = [
                ['Cost estimat total:', f"{project_data.get('estimated_cost', 0):.2f} RON"]
            ]
            cost_table = Table(cost_data, colWidths=[60*mm, 80*mm])
            cost_table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 12),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(cost_table)
            elements.append(Spacer(1, 10*mm))
    
    # Add Notes
    if project_data.get('notes'):
        elements.append(Paragraph("Note", heading_style))
        elements.append(Paragraph(project_data.get('notes'), normal_style))
        elements.append(Spacer(1, 10*mm))
    
    # Add Footer with Terms
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph("Termeni și Condiții", heading_style))
    
    terms = [
        "• Prețurile sunt exprimate în RON și nu includ TVA.",
        "• Oferta este valabilă 30 de zile de la data emiterii.",
        "• Timpul de livrare va fi confirmat la plasarea comenzii.",
        "• Montajul și punerea în funcțiune sunt incluse în preț.",
        "• Garanție conform specificațiilor producătorilor."
    ]
    
    for term in terms:
        elements.append(Paragraph(term, normal_style))
        elements.append(Spacer(1, 2*mm))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf
