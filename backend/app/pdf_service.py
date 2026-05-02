"""PDF generation service for commercial offers."""

from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
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


def wrap_text(text, style_name='Normal', font_size=9):
    """
    Wrap text in a Paragraph for automatic text wrapping in table cells.
    
    Args:
        text: Text to wrap
        style_name: Style name to use
        font_size: Font size for the paragraph
    
    Returns:
        Paragraph object with wrapped text
    """
    styles = getSampleStyleSheet()
    style = ParagraphStyle(
        name='CellText',
        parent=styles[style_name],
        fontSize=font_size,
        leading=font_size * 1.2,
        alignment=TA_LEFT
    )
    return Paragraph(str(text), style)


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
    
    grand_total_table = Table(grand_total_data, colWidths=[110*mm, 40*mm])
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
    
    # Create the PDF document in landscape format
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
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
    
    offer_table = Table(offer_details, colWidths=[70*mm, 100*mm])
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
    
    client_table = Table(client_info, colWidths=[70*mm, 100*mm])
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
    
    project_table = Table(project_info, colWidths=[70*mm, 100*mm])
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
        
        # Materials table header with wrapped text
        materials_data = [
            [
                wrap_text(remove_diacritics('Nr.'), font_size=10),
                wrap_text(remove_diacritics('Material'), font_size=10),
                wrap_text(remove_diacritics('SKU'), font_size=10),
                wrap_text(remove_diacritics('Cantitate'), font_size=10),
                wrap_text(remove_diacritics('Preț Unitar cu Adaos (RON)'), font_size=10),
                wrap_text(remove_diacritics('Total (RON)'), font_size=10)
            ]
        ]
        
        total_cost = 0
        for idx, material in enumerate(materials_list, 1):
            material_total = material.get('quantity_planned', 0) * material.get('unit_price', 0)
            total_cost += material_total
            
            materials_data.append([
                str(idx),
                wrap_text(remove_diacritics(material.get('material_name', 'N/A')), font_size=9),
                wrap_text(remove_diacritics(material.get('material_sku', 'N/A')), font_size=9),
                f"{material.get('quantity_planned', 0):.2f}",
                f"{material.get('unit_price', 0):.2f}",
                f"{material_total:.2f}"
            ])
        
        # Add subtotal row for materials
        materials_data.append(['', '', '', '', remove_diacritics('SUBTOTAL MATERIALE (cu adaos):'), f"{total_cost:.2f}"])
        
        # Adjusted column widths for landscape format (total width 240mm for landscape A4)
        materials_table = Table(materials_data, colWidths=[15*mm, 80*mm, 40*mm, 25*mm, 45*mm, 35*mm])
        materials_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            
            # Body style
            ('FONT', (0, 1), (-1, -2), 'Helvetica', 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (3, 1), (-1, -2), 'RIGHT'),
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
        
        additional_costs_table = Table(additional_costs_data, colWidths=[110*mm, 40*mm])
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
            
            additional_costs_table = Table(additional_costs_data, colWidths=[110*mm, 40*mm])
            additional_costs_table.setStyle(get_additional_costs_table_style())
            elements.append(additional_costs_table)
            elements.append(Spacer(1, 10*mm))
        
        # Show estimated cost if provided
        if project_data.get('estimated_cost'):
            elements.append(Paragraph(remove_diacritics("Estimare Cost"), heading_style))
            cost_data = [
                [remove_diacritics('Cost estimat total:'), f"{project_data.get('estimated_cost', 0):.2f} RON"]
            ]
            cost_table = Table(cost_data, colWidths=[70*mm, 100*mm])
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


INVOICE_VAT_RATE = 0.21


def _invoice_xml_escape(text) -> str:
    if text is None:
        return ""
    s = remove_diacritics(str(text))
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _invoice_block_paragraph(title: str, rows: list[tuple[str, str]], normal_style) -> Paragraph:
    parts = [f"<b>{_invoice_xml_escape(title)}</b>"]
    for label, value in rows:
        val = value if (value is not None and str(value).strip()) else "-"
        parts.append(f"<b>{_invoice_xml_escape(label)}</b> {_invoice_xml_escape(val)}")
    inner = "<br/>".join(parts)
    return Paragraph(inner, normal_style)


def generate_project_invoice_pdf(project_data, materials_list=None, company_billing=None):
    """Generate a sales invoice PDF with supplier and client billing blocks."""
    materials_list = materials_list or []
    company_billing = company_billing or {}

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=14,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "InvoiceHeading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=8,
        spaceBefore=10,
    )
    normal_style = ParagraphStyle(
        "InvoiceNormal",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        alignment=TA_LEFT,
    )

    elements.append(Paragraph(remove_diacritics("FACTURA"), title_style))

    issue_date = datetime.now().strftime("%d.%m.%Y")
    inv_no = f"FAC-P{project_data.get('id', 'N/A')}-{datetime.now().strftime('%Y%m%d')}"
    meta_rows = [
        [remove_diacritics("Nr. factura:"), inv_no],
        [remove_diacritics("Data emiterii:"), issue_date],
        [remove_diacritics("Referinta proiect:"), project_data.get("name", "-")],
    ]
    meta_table = Table(meta_rows, colWidths=[45 * mm, 115 * mm])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
                ("FONT", (1, 0), (1, -1), "Helvetica", 9),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(meta_table)
    elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph(remove_diacritics("Date de facturare"), heading_style))

    company_rows = [
        ("Denumire:", company_billing.get("legal_name")),
        ("CUI / CIF:", company_billing.get("tax_id")),
        ("Nr. Reg. Com.:", company_billing.get("registration")),
        ("Adresa:", company_billing.get("address")),
        ("Banca:", company_billing.get("bank_name")),
        ("IBAN:", company_billing.get("iban")),
        ("Telefon:", company_billing.get("phone")),
        ("Email:", company_billing.get("email")),
    ]
    client_rows = [
        ("Denumire:", project_data.get("client_name")),
        ("CUI / CIF:", project_data.get("client_tax_id")),
        ("Nr. Reg. Com.:", project_data.get("client_registration")),
        ("Adresa facturare:", project_data.get("client_billing_address")),
        ("Contact:", project_data.get("client_contact")),
        ("Locatie montaj:", project_data.get("location")),
    ]

    left_para = _invoice_block_paragraph("Furnizor", company_rows, normal_style)
    right_para = _invoice_block_paragraph("Cumparator", client_rows, normal_style)
    billing_table = Table([[left_para, right_para]], colWidths=[82 * mm, 82 * mm])
    billing_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(billing_table)
    elements.append(Spacer(1, 8 * mm))

    elements.append(Paragraph(remove_diacritics("Detaliere (valori fara TVA)"), heading_style))

    table_header = [
        wrap_text(remove_diacritics("Nr."), font_size=9),
        wrap_text(remove_diacritics("Denumire"), font_size=9),
        wrap_text(remove_diacritics("UM"), font_size=9),
        wrap_text(remove_diacritics("Cant."), font_size=9),
        wrap_text(remove_diacritics("Pret unitar"), font_size=9),
        wrap_text(remove_diacritics("Valoare"), font_size=9),
    ]
    lines_data = [table_header]

    net_total = 0.0
    idx = 0
    for material in materials_list:
        qty = float(material.get("quantity_planned") or 0)
        price = float(material.get("unit_price") or 0)
        line_net = qty * price
        net_total += line_net
        idx += 1
        um = material.get("material_unit") or "buc"
        lines_data.append(
            [
                str(idx),
                wrap_text(_invoice_xml_escape(material.get("material_name", "-")), font_size=8),
                wrap_text(_invoice_xml_escape(um), font_size=8),
                f"{qty:.2f}",
                f"{price:.2f}",
                f"{line_net:.2f}",
            ]
        )

    labor = float(project_data.get("labor_cost_estimated") or 0)
    transport = float(project_data.get("transport_cost_estimated") or 0)
    other = float(project_data.get("other_costs_estimated") or 0)

    for label, amount in (
        (remove_diacritics("Manopera"), labor),
        (remove_diacritics("Transport"), transport),
        (remove_diacritics("Alte costuri"), other),
    ):
        if amount > 0:
            idx += 1
            net_total += amount
            lines_data.append(
                [
                    str(idx),
                    wrap_text(label, font_size=8),
                    wrap_text(remove_diacritics("serviciu"), font_size=8),
                    "1.00",
                    f"{amount:.2f}",
                    f"{amount:.2f}",
                ]
            )

    if not materials_list and labor == 0 and transport == 0 and other == 0:
        est = project_data.get("estimated_cost")
        if est:
            net_total = float(est)
            lines_data.append(
                [
                    "1",
                    wrap_text(remove_diacritics("Servicii / proiect (estimare)"), font_size=8),
                    wrap_text(remove_diacritics("set"), font_size=8),
                    "1.00",
                    f"{net_total:.2f}",
                    f"{net_total:.2f}",
                ]
            )

    col_widths = [12 * mm, 62 * mm, 18 * mm, 22 * mm, 28 * mm, 28 * mm]
    lines_table = Table(lines_data, colWidths=col_widths)
    lines_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
                ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(lines_table)
    elements.append(Spacer(1, 6 * mm))

    vat_amount = net_total * INVOICE_VAT_RATE
    gross_total = net_total + vat_amount

    totals_data = [
        [remove_diacritics("Total fara TVA:"), f"{net_total:.2f} RON"],
        [remove_diacritics("TVA (21%):"), f"{vat_amount:.2f} RON"],
        [remove_diacritics("Total de plata:"), f"{gross_total:.2f} RON"],
    ]
    totals_table = Table(totals_data, colWidths=[120 * mm, 50 * mm])
    totals_table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -2), "Helvetica", 10),
                ("FONT", (0, -1), (-1, -1), "Helvetica-Bold", 11),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#dbeafe")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(totals_table)

    if project_data.get("notes"):
        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph(remove_diacritics("Observatii"), heading_style))
        elements.append(
            Paragraph(_invoice_xml_escape(project_data.get("notes")), normal_style)
        )

    elements.append(Spacer(1, 10 * mm))
    footer_note = remove_diacritics(
        "Document informational generat din aplicatie. Verificati conformitatea cu legislatia "
        "fiscala in vigoare inainte de transmiterea catre client."
    )
    elements.append(Paragraph(f"<i>{footer_note}</i>", normal_style))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
