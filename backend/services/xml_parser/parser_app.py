"""XML Invoice Parser Service for UBL/e-Factura format."""

import os
import logging
from flask import Flask, request, jsonify
from defusedxml import ElementTree as ET
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
API_TOKEN = os.getenv('XML_PARSER_TOKEN', 'dev-token-12345')

# Security warning for default token
if API_TOKEN == 'dev-token-12345':
    logging.warning(
        "⚠️  WARNING: Using default XML_PARSER_TOKEN='dev-token-12345'. "
        "This is insecure for production! Set XML_PARSER_TOKEN environment variable to a secure token."
    )

# Namespaces for UBL XML invoices
NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'invoice': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'
}


def check_auth():
    """Check API token authentication."""
    token = request.headers.get('X-API-Token')
    if API_TOKEN and token != API_TOKEN:
        return False
    return True


def parse_ubl_invoice(xml_file):
    """Parse UBL format invoice XML."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Extract invoice data
        invoice_data = {
            'invoice_number': '',
            'invoice_date': '',
            'supplier_name': '',
            'supplier_tax_id': '',
            'customer_name': '',
            'customer_tax_id': '',
            'currency': 'RON',
            'total_amount': 0.0,
            'tax_amount': 0.0,
            'items': []
        }
        
        # Invoice number
        invoice_num = root.find('.//cbc:ID', NAMESPACES)
        if invoice_num is not None:
            invoice_data['invoice_number'] = invoice_num.text
        
        # Invoice date
        invoice_date = root.find('.//cbc:IssueDate', NAMESPACES)
        if invoice_date is not None:
            invoice_data['invoice_date'] = invoice_date.text
        
        # Supplier info
        supplier_party = root.find('.//cac:AccountingSupplierParty/cac:Party', NAMESPACES)
        if supplier_party is not None:
            supplier_name = supplier_party.find('.//cac:PartyName/cbc:Name', NAMESPACES)
            if supplier_name is not None:
                invoice_data['supplier_name'] = supplier_name.text
            
            supplier_tax = supplier_party.find('.//cac:PartyTaxScheme/cbc:CompanyID', NAMESPACES)
            if supplier_tax is not None:
                invoice_data['supplier_tax_id'] = supplier_tax.text
        
        # Customer info
        customer_party = root.find('.//cac:AccountingCustomerParty/cac:Party', NAMESPACES)
        if customer_party is not None:
            customer_name = customer_party.find('.//cac:PartyName/cbc:Name', NAMESPACES)
            if customer_name is not None:
                invoice_data['customer_name'] = customer_name.text
            
            customer_tax = customer_party.find('.//cac:PartyTaxScheme/cbc:CompanyID', NAMESPACES)
            if customer_tax is not None:
                invoice_data['customer_tax_id'] = customer_tax.text
        
        # Currency
        currency_code = root.find('.//cbc:DocumentCurrencyCode', NAMESPACES)
        if currency_code is not None:
            invoice_data['currency'] = currency_code.text
        
        # Total amount
        total_amount = root.find('.//cac:LegalMonetaryTotal/cbc:PayableAmount', NAMESPACES)
        if total_amount is not None:
            invoice_data['total_amount'] = float(total_amount.text)
        
        # Tax amount
        tax_amount = root.find('.//cac:TaxTotal/cbc:TaxAmount', NAMESPACES)
        if tax_amount is not None:
            invoice_data['tax_amount'] = float(tax_amount.text)
        
        # Line items
        items = root.findall('.//cac:InvoiceLine', NAMESPACES)
        for item in items:
            line_item = {
                'description': '',
                'quantity': 0.0,
                'unit_price': 0.0,
                'total_price': 0.0,
                'sku': ''
            }
            
            # Item description
            item_name = item.find('.//cac:Item/cbc:Name', NAMESPACES)
            if item_name is not None:
                line_item['description'] = item_name.text
            
            # SKU / Seller Item ID
            seller_id = item.find('.//cac:Item/cac:SellersItemIdentification/cbc:ID', NAMESPACES)
            if seller_id is not None:
                line_item['sku'] = seller_id.text
            
            # Quantity
            quantity = item.find('.//cbc:InvoicedQuantity', NAMESPACES)
            if quantity is not None:
                line_item['quantity'] = float(quantity.text)
            
            # Unit price
            unit_price = item.find('.//cac:Price/cbc:PriceAmount', NAMESPACES)
            if unit_price is not None:
                line_item['unit_price'] = float(unit_price.text)
            
            # Line total
            line_total = item.find('.//cbc:LineExtensionAmount', NAMESPACES)
            if line_total is not None:
                line_item['total_price'] = float(line_total.text)
            
            invoice_data['items'].append(line_item)
        
        return invoice_data
    
    except Exception as e:
        raise Exception(f"Error parsing XML: {str(e)}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'xml-parser'})


@app.route('/parse', methods=['POST'])
def parse_invoice():
    """Parse uploaded XML invoice file."""
    # Check authentication
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.xml'):
        return jsonify({'error': 'Only XML files are allowed'}), 400
    
    try:
        # Parse the invoice
        invoice_data = parse_ubl_invoice(file)
        
        return jsonify(invoice_data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/', methods=['GET'])
def index():
    """Root endpoint."""
    return jsonify({
        'service': 'XML Invoice Parser',
        'version': '1.0.0',
        'endpoints': {
            'parse': '/parse (POST)',
            'health': '/health (GET)'
        }
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
