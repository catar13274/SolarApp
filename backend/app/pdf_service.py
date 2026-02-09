"""PDF generation service for commercial offers."""

from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def remove_diacritics(text):
    """
    Remove Romanian diacritics from text.
    Converts: ă→a, â→a, î→i, ș→s, ț→t (both uppercase and lowercase)
    """
    if not text:
        return text
    
    if not isinstance(text, str):
        text = str(text)
    
    diacritics_map = {
        'ă': 'a', 'Ă': 'A',
        'â': 'a', 'Â': 'A',
        'î': 'i', 'Î': 'I',
        'ș': 's', 'Ș': 'S',
        'ț': 't', 'Ț': 'T'
    }
    
    for diacritic, replacement in diacritics_map.items():
        text = text.replace(diacritic, replacement)
    
    return text


def create_additional_costs_table_data(labor_cost, transport_cost, other_costs, subtotal_label):
    """
    Create table data for additional costs section.
    
    Args:
        labor_cost: Labor cost amount
        transport_cost: Transport cost amount
        other_costs: Other costs amount
        subtotal_label: Label for the subtotal row
    
    Returns:
        List of lists containing table data
    """
    additional_costs_data = [
        [remove_diacritics('Tip Cost'), remove_diacritics('Valoare (RON)')]
    ]
    
    # Always show all cost types, even if 0
    additional_costs_data.append([
        remove_diacritics('Manoperă'),
        f"{labor_cost:.2f}"
    ])
    
    additional_costs_data.append([
        remove_diacritics('Transport'),
        f"{transport_cost:.2f}"
    ])
    
    additional_costs_data.append([
        remove_diacritics('Alte costuri'),
        f"{other_costs:.2f}"
    ])
    
    # Add subtotal for additional costs
    subtotal_additional = labor_cost + transport_cost + other_costs
    additional_costs_data.append([
        remove_diacritics(subtotal_label),
        f"{subtotal_additional:.2f}"
    ])
    
    return additional_costs_data


def get_additional_costs_table_style():
    """
    Get the standard table style for additional costs tables.
    
    Returns:
        TableStyle object
    """
    return TableStyle([
        # Header style
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        
        # Body style
        ('FONT', (0, 1), (-1, -2), 'Helvetica', 10),
        ('ALIGN', (0, 1), (0, -2), 'LEFT'),
        ('ALIGN', (1, 1), (1, -2), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -2), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -2), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f3f4f6')]),
        
        # Subtotal row style
        ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 11),
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
        ('TOPPADDING', (0, -1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])


def create_grand_total_table(total_amount):
    """
    Create a grand total table.
    
    Args:
        total_amount: The total amount to display
    
    Returns:
        Table object
    """
    grand_total_data = [
        [remove_diacritics('TOTAL GENERAL:'), f"{total_amount:.2f} RON"]
    ]
    
    grand_total_table = Table(grand_total_data, colWidths=[90*mm, 30*mm])
    grand_total_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica-Bold', 14),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#1e40af')),
    ]))
    
    return grand_total_table


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
    elements.append(Paragraph(remove_diacritics("OFERTĂ COMERCIALĂ"), title_style))
    elements.append(Spacer(1, 10*mm))
    
    # Add Offer Details Section
    elements.append(Paragraph(remove_diacritics("Detalii Ofertă"), heading_style))
    
    offer_date = datetime.now().strftime("%d.%m.%Y")
    offer_details = [
        [remove_diacritics('Data ofertei:'), offer_date],
        [remove_diacritics('Nr. ofertă:'), f"OF-{project_data.get('id', 'N/A')}-{datetime.now().strftime('%Y%m%d')}"],
        [remove_diacritics('Valabilitate:'), remove_diacritics('30 zile')],
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
    elements.append(Paragraph(remove_diacritics("Date Client"), heading_style))
    
    client_info = [
        [remove_diacritics('Nume client:'), remove_diacritics(project_data.get('client_name', 'N/A'))],
        [remove_diacritics('Contact:'), remove_diacritics(project_data.get('client_contact', 'N/A'))],
        [remove_diacritics('Locație:'), remove_diacritics(project_data.get('location', 'N/A'))],
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
    elements.append(Paragraph(remove_diacritics("Detalii Proiect"), heading_style))
    
    project_info = [
        [remove_diacritics('Nume proiect:'), remove_diacritics(project_data.get('name', 'N/A'))],
        [remove_diacritics('Capacitate sistem:'), f"{project_data.get('capacity_kw', 0)} kW" if project_data.get('capacity_kw') else 'N/A'],
        [remove_diacritics('Status:'), remove_diacritics(project_data.get('status', 'N/A').replace('_', ' ').title())],
    ]
    
    if project_data.get('start_date'):
        project_info.append([remove_diacritics('Data start estimată:'), str(project_data.get('start_date'))])
    
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
        elements.append(Paragraph(remove_diacritics("Materiale și Costuri"), heading_style))
        
        # Materials table header
        materials_data = [
            [remove_diacritics('Nr.'), remove_diacritics('Material'), 
             remove_diacritics('SKU'), remove_diacritics('Cantitate'), 
             remove_diacritics('Preț Unitar cu Adaos (RON)'), remove_diacritics('Total (RON)')]
        ]
        
        total_cost = 0
        for idx, material in enumerate(materials_list, 1):
            material_total = material.get('quantity_planned', 0) * material.get('unit_price', 0)
            total_cost += material_total
            
            materials_data.append([
                str(idx),
                remove_diacritics(material.get('material_name', 'N/A')),
                remove_diacritics(material.get('material_sku', 'N/A')),
                f"{material.get('quantity_planned', 0):.2f}",
                f"{material.get('unit_price', 0):.2f}",
                f"{material_total:.2f}"
            ])
        
        # Add subtotal row for materials
        materials_data.append(['', '', '', '', remove_diacritics('SUBTOTAL MATERIALE (cu adaos):'), f"{total_cost:.2f}"])
        
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
            
            # Subtotal row style
            ('FONT', (0, -1), (-1, -1), 'Helvetica-Bold', 11),
            ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
            ('TOPPADDING', (0, -1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(materials_table)
        elements.append(Spacer(1, 5*mm))
        
        # Add Additional Costs Section (always show when materials exist)
        labor_cost = project_data.get('labor_cost_estimated', 0) or 0
        transport_cost = project_data.get('transport_cost_estimated', 0) or 0
        other_costs = project_data.get('other_costs_estimated', 0) or 0
        
        elements.append(Paragraph(remove_diacritics("Costuri Adiționale"), heading_style))
        
        # Create additional costs table using helper function
        additional_costs_data = create_additional_costs_table_data(
            labor_cost, transport_cost, other_costs, 
            'SUBTOTAL COSTURI ADIȚIONALE:'
        )
        
        additional_costs_table = Table(additional_costs_data, colWidths=[90*mm, 30*mm])
        additional_costs_table.setStyle(get_additional_costs_table_style())
        elements.append(additional_costs_table)
        elements.append(Spacer(1, 5*mm))
        
        # Add Grand Total
        subtotal_additional = labor_cost + transport_cost + other_costs
        grand_total = total_cost + subtotal_additional
        elements.append(create_grand_total_table(grand_total))
        elements.append(Spacer(1, 10*mm))
    
    # Add pricing section (if no materials provided, show additional costs and estimated cost)
    if not materials_list or len(materials_list) == 0:
        labor_cost = project_data.get('labor_cost_estimated', 0) or 0
        transport_cost = project_data.get('transport_cost_estimated', 0) or 0
        other_costs = project_data.get('other_costs_estimated', 0) or 0
        
        # Show additional costs if any exist
        if labor_cost > 0 or transport_cost > 0 or other_costs > 0:
            elements.append(Paragraph(remove_diacritics("Costuri Adiționale"), heading_style))
            
            # Create additional costs table using helper function (use consistent label)
            additional_costs_data = create_additional_costs_table_data(
                labor_cost, transport_cost, other_costs, 
                'SUBTOTAL COSTURI ADIȚIONALE:'
            )
            
            additional_costs_table = Table(additional_costs_data, colWidths=[90*mm, 30*mm])
            additional_costs_table.setStyle(get_additional_costs_table_style())
            elements.append(additional_costs_table)
            elements.append(Spacer(1, 10*mm))
        
        # Show estimated cost if provided
        if project_data.get('estimated_cost'):
            elements.append(Paragraph(remove_diacritics("Estimare Cost"), heading_style))
            cost_data = [
                [remove_diacritics('Cost estimat total:'), f"{project_data.get('estimated_cost', 0):.2f} RON"]
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
        elements.append(Paragraph(remove_diacritics("Note"), heading_style))
        elements.append(Paragraph(remove_diacritics(project_data.get('notes')), normal_style))
        elements.append(Spacer(1, 10*mm))
    
    # Add Footer with Terms
    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(remove_diacritics("Termeni și Condiții"), heading_style))
    
    terms = [
        remove_diacritics("• Prețurile sunt exprimate în RON și nu includ TVA."),
        remove_diacritics("• Oferta este valabilă 30 de zile de la data emiterii."),
        remove_diacritics("• Timpul de livrare va fi confirmat la plasarea comenzii."),
        remove_diacritics("• Montajul și punerea în funcțiune sunt incluse în preț."),
        remove_diacritics("• Garanție conform specificațiilor producătorilor.")
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
