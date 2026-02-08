"""Document parser service for extracting invoice materials from PDF, DOC, and TXT files."""

import re
import logging
from typing import List, Dict, Optional
from io import BytesIO

# Import PDF and DOC parsing libraries
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from PDF file."""
    if not PDF_AVAILABLE:
        raise Exception("PyPDF2 library not available. Install with: pip install PyPDF2")
    
    try:
        text = ""
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """Extract text content from DOCX file."""
    if not DOCX_AVAILABLE:
        raise Exception("python-docx library not available. Install with: pip install python-docx")
    
    try:
        doc = Document(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                text += "\n" + "\t".join([cell.text for cell in row.cells])
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from DOCX: {e}")
        raise Exception(f"Failed to extract text from DOCX: {str(e)}")


def extract_text_from_doc(file_path: str) -> str:
    """Extract text content from DOC file (legacy format).
    
    Note: python-docx doesn't support .doc files, only .docx.
    For .doc files, we return an empty string and let the user manually process.
    """
    logger.warning("Legacy .doc format not supported. Please convert to .docx or use XML format.")
    return ""


def extract_text_from_txt(file_path: str) -> str:
    """Extract text content from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with different encoding
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error reading TXT file: {e}")
            raise Exception(f"Failed to read TXT file: {str(e)}")


def parse_invoice_materials(text: str) -> Dict:
    """Parse invoice materials from extracted text.
    
    This function attempts to extract:
    - Invoice number
    - Supplier name
    - Invoice date
    - Total amount
    - Line items with description, quantity, unit price, and total
    
    The parsing uses heuristics and pattern matching since the text format
    can vary significantly between different invoice formats.
    """
    result = {
        'invoice_number': '',
        'invoice_date': '',
        'supplier_name': '',
        'currency': 'RON',
        'total_amount': 0.0,
        'items': []
    }
    
    lines = text.split('\n')
    
    # Pattern matching for common invoice fields
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        
        # Extract invoice number
        if not result['invoice_number']:
            invoice_patterns = [
                r'(?:invoice|factura|nr\.?\s*factura)[:\s#]*([A-Z0-9\-/]+)',
                r'(?:invoice\s*(?:no|number|nr)[:\s#]*([A-Z0-9\-/]+))',
                r'nr\.?\s*(\d+[A-Z0-9\-/]*)',
            ]
            for pattern in invoice_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    result['invoice_number'] = match.group(1).strip()
                    break
        
        # Extract invoice date
        if not result['invoice_date']:
            date_patterns = [
                r'(?:date|data)[:\s]*(\d{1,2}[\./-]\d{1,2}[\./-]\d{2,4})',
                r'(\d{1,2}[\./-]\d{1,2}[\./-]\d{2,4})',
                r'(\d{4}-\d{2}-\d{2})',
            ]
            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    date_str = match.group(1).strip()
                    # Convert date format if needed
                    result['invoice_date'] = normalize_date(date_str)
                    break
        
        # Extract supplier name (usually near the top)
        if not result['supplier_name'] and i < 10:
            supplier_patterns = [
                r'(?:supplier|furnizor|seller)[:\s]+(.+)',
                r'(?:s\.?c\.?)\s+([A-Z][A-Za-z\s&\.]+(?:s\.?r\.?l\.?|s\.?a\.?))',
            ]
            for pattern in supplier_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    result['supplier_name'] = match.group(1).strip()
                    break
        
        # Extract total amount
        if 'total' in line_lower or 'suma' in line_lower:
            amount_pattern = r'(\d{1,3}(?:[,\.\s]\d{3})*[,\.]\d{2}|\d+[,\.]\d{2}|\d+)'
            match = re.search(amount_pattern, line)
            if match:
                amount_str = match.group(1).replace(',', '.').replace(' ', '')
                try:
                    amount = float(amount_str)
                    if amount > result['total_amount']:
                        result['total_amount'] = amount
                except ValueError:
                    pass
    
    # Extract line items
    # Look for table-like structures with materials
    result['items'] = extract_line_items(text)
    
    return result


def extract_line_items(text: str) -> List[Dict]:
    """Extract line items from invoice text.
    
    This function looks for patterns that resemble invoice line items:
    - Description, quantity, unit price, total
    - Tab or space-separated values
    - Numeric patterns for quantities and prices
    """
    items = []
    lines = text.split('\n')
    
    # Try to identify table headers
    header_idx = -1
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Look for common table headers
        if any(keyword in line_lower for keyword in ['descriere', 'description', 'produs', 'material', 'item']):
            if any(keyword in line_lower for keyword in ['cantitate', 'quantity', 'qty', 'cant']):
                header_idx = i
                break
    
    # If we found a header, parse the following lines as table rows
    if header_idx >= 0:
        for i in range(header_idx + 1, min(header_idx + 100, len(lines))):
            line = lines[i].strip()
            if not line:
                continue
            
            # Try to extract item information using patterns
            item = parse_line_item(line)
            if item:
                items.append(item)
    
    # If no items found via table parsing, try a more aggressive approach
    if not items:
        for line in lines:
            item = parse_line_item(line)
            if item and item['quantity'] > 0 and item['unit_price'] > 0:
                items.append(item)
    
    return items


def parse_line_item(line: str) -> Optional[Dict]:
    """Parse a single line item from invoice text.
    
    Expects patterns like:
    - "Product name    10    100.00    1000.00"
    - "Product name | 10 | 100.00 | 1000.00"
    - "Product name, 10 buc, 100.00 RON, 1000.00 RON"
    """
    # Skip lines that are likely headers or totals
    # Only skip if these keywords appear without other content (likely a header row)
    line_lower = line.lower().strip()
    line_words = line_lower.split()
    
    # Check if line is primarily a header (contains header keywords and few other words)
    header_keywords = ['total', 'subtotal', 'tva', 'tax', 'discount']
    table_header_keywords = ['descriere', 'description', 'cantitate', 'quantity', 'pret', 'price', 'produs', 'product']
    
    # Skip if it's a total/subtotal line
    if any(keyword in line_lower for keyword in header_keywords):
        return None
    
    # Skip if it appears to be a table header (has multiple header keywords and no numbers)
    header_count = sum(1 for kw in table_header_keywords if kw in line_lower)
    if header_count >= 2 and len(re.findall(r'\d', line)) < 3:
        return None
    
    # Extract numbers from the line
    numbers = re.findall(r'\d+(?:[,\.]\d+)?', line)
    if len(numbers) < 2:
        return None
    
    # Convert to floats
    try:
        numeric_values = [float(n.replace(',', '.')) for n in numbers]
    except ValueError:
        return None
    
    # Heuristic: If we have 3 or more numbers, the pattern is likely: quantity, unit_price, total_price
    # If we have exactly 2 numbers, assume quantity and price (calculate total)
    if len(numeric_values) >= 3:
        # Take the last 3 numbers as quantity, unit_price, total_price
        quantity = numeric_values[-3]
        unit_price = numeric_values[-2]
        total_price = numeric_values[-1]
    elif len(numeric_values) == 2:
        quantity = numeric_values[0]
        unit_price = numeric_values[1]
        total_price = quantity * unit_price
    else:
        return None
    
    # Extract description (text before numbers start)
    # Find position of first number
    first_num_match = re.search(r'\d', line)
    if first_num_match:
        description = line[:first_num_match.start()].strip()
    else:
        description = line[:50].strip()
    
    # Skip if description is too short or looks like a number
    if len(description) < 3 or description.replace(' ', '').isdigit():
        return None
    
    return {
        'description': description,
        'sku': '',
        'quantity': quantity,
        'unit_price': unit_price,
        'total_price': total_price
    }


def normalize_date(date_str: str) -> str:
    """Normalize date string to ISO format (YYYY-MM-DD)."""
    # Try different date formats
    patterns = [
        (r'(\d{1,2})[\./-](\d{1,2})[\./-](\d{4})', lambda m: f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"),
        (r'(\d{4})-(\d{2})-(\d{2})', lambda m: f"{m.group(1)}-{m.group(2)}-{m.group(3)}"),
    ]
    
    for pattern, formatter in patterns:
        match = re.match(pattern, date_str)
        if match:
            return formatter(match)
    
    return date_str


def parse_document(file_path: str, file_extension: str) -> Dict:
    """Parse document and extract invoice data.
    
    Args:
        file_path: Path to the document file
        file_extension: File extension (pdf, doc, docx, txt)
    
    Returns:
        Dictionary with invoice data including items
    """
    text = ""
    
    # Extract text based on file type
    if file_extension == 'pdf':
        text = extract_text_from_pdf(file_path)
    elif file_extension == 'docx':
        text = extract_text_from_docx(file_path)
    elif file_extension == 'doc':
        text = extract_text_from_doc(file_path)
    elif file_extension == 'txt':
        text = extract_text_from_txt(file_path)
    else:
        raise Exception(f"Unsupported file format: {file_extension}")
    
    if not text:
        logger.warning(f"No text extracted from {file_extension} file")
        return {
            'invoice_number': '',
            'invoice_date': '',
            'supplier_name': '',
            'currency': 'RON',
            'total_amount': 0.0,
            'items': []
        }
    
    # Parse the extracted text
    return parse_invoice_materials(text)
