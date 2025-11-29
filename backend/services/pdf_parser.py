"""
PDF Parser service for extracting invoice/estimate data from uploaded PDFs.
Extracts: mode (invoice/estimate), language, from address, to address, items, total
"""
import fitz  # PyMuPDF
import re
from typing import List, Tuple, Optional


def extract_invoice_data(pdf_bytes: bytes) -> dict:
    """
    Extract structured invoice data from a PDF file.
    Returns a dictionary with:
    - mode: 'invoice' or 'estimate'
    - language: 'fr' or 'en'
    - from_address: sender address
    - to_address: recipient address
    - items: list of {description, quantity, price}
    - total: calculated total
    - doc_title: document reference/title
    - raw_text: full extracted text for debugging
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        full_text = ""
        for page_num in range(min(10, doc.page_count)):
            page = doc[page_num]
            full_text += page.get_text() + "\n"

        doc.close()
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return _empty_result(f"Error opening PDF: {str(e)}")

    # Clean and prepare text
    lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    text_lower = full_text.lower()

    # Extract all data
    mode = _detect_mode(text_lower)
    language = _detect_language(text_lower)
    from_address, to_address = _extract_addresses(lines, full_text)
    items = _extract_items(lines)
    total = _calculate_total(items, full_text)
    doc_title = _extract_title(lines, text_lower)

    return {
        "mode": mode,
        "language": language,
        "from_address": from_address,
        "to_address": to_address,
        "items": items,
        "total": total,
        "doc_title": doc_title,
        "raw_text": full_text
    }


def _empty_result(error_msg: str = "") -> dict:
    """Return empty result structure."""
    return {
        "mode": "invoice",
        "language": "fr",
        "from_address": "",
        "to_address": "",
        "items": [],
        "total": 0.0,
        "doc_title": "",
        "raw_text": error_msg
    }


def _detect_mode(text_lower: str) -> str:
    """Detect if document is invoice or estimate."""
    estimate_keywords = ['devis', 'estimate', 'quotation', 'quote', 'proforma']
    invoice_keywords = ['facture', 'invoice', 'bill', 'receipt']

    # Count occurrences
    estimate_count = sum(text_lower.count(kw) for kw in estimate_keywords)
    invoice_count = sum(text_lower.count(kw) for kw in invoice_keywords)

    return 'estimate' if estimate_count > invoice_count else 'invoice'


def _detect_language(text_lower: str) -> str:
    """Detect document language (fr or en)."""
    french_keywords = ['facture', 'devis', 'montant', 'total', 'prix', 'quantité',
                       'adresse', 'client', 'référence', 'émetteur', 'destinataire',
                       'rue', 'avenue', 'boulevard', 'france', 'paris', 'lyon']
    english_keywords = ['invoice', 'estimate', 'amount', 'price', 'quantity',
                        'address', 'customer', 'reference', 'from', 'bill to',
                        'street', 'road', 'avenue']

    french_count = sum(text_lower.count(kw) for kw in french_keywords)
    english_count = sum(text_lower.count(kw) for kw in english_keywords)

    return 'fr' if french_count >= english_count else 'en'


def _extract_addresses(lines: List[str], full_text: str) -> Tuple[str, str]:
    """Extract from and to addresses."""
    from_address = ""
    to_address = ""

    # Strategy 1: Look for labeled sections
    text_lower = full_text.lower()

    # Common section markers
    from_markers = [
        (r'(?:from|de|émetteur|expéditeur)\s*[:\n]', 'after'),
        (r'(?:vendeur|seller)\s*[:\n]', 'after'),
    ]
    to_markers = [
        (r'(?:to|à|destinataire|client|bill\s*to|facturer\s*à|customer)\s*[:\n]', 'after'),
        (r'(?:acheteur|buyer)\s*[:\n]', 'after'),
    ]

    # Try to find addresses using markers
    for pattern, _ in from_markers:
        match = re.search(pattern, text_lower)
        if match:
            start_idx = match.end()
            addr = _extract_address_block(full_text, start_idx)
            if addr and len(addr) > 10:
                from_address = addr
                break

    for pattern, _ in to_markers:
        match = re.search(pattern, text_lower)
        if match:
            start_idx = match.end()
            addr = _extract_address_block(full_text, start_idx)
            if addr and len(addr) > 10:
                to_address = addr
                break

    # Strategy 2: Find address-like blocks (with postal codes)
    if not from_address or not to_address:
        address_blocks = _find_address_blocks(lines)
        if len(address_blocks) >= 2:
            if not from_address:
                from_address = address_blocks[0]
            if not to_address:
                to_address = address_blocks[1] if len(address_blocks) > 1 else ""
        elif len(address_blocks) == 1:
            if not to_address:
                to_address = address_blocks[0]

    return from_address.strip(), to_address.strip()


def _extract_address_block(text: str, start_idx: int, max_lines: int = 5) -> str:
    """Extract an address block starting from a position."""
    remaining = text[start_idx:start_idx + 500]  # Look at next 500 chars
    lines = remaining.split('\n')

    address_lines = []
    for line in lines[:max_lines]:
        line = line.strip()
        if not line:
            if address_lines:  # Stop at first empty line after content
                break
            continue
        # Stop if we hit another section marker
        if re.match(r'^(from|to|de|à|client|total|montant|date|invoice|facture)', line.lower()):
            break
        address_lines.append(line)

    return '\n'.join(address_lines)


def _find_address_blocks(lines: List[str]) -> List[str]:
    """Find blocks of text that look like addresses."""
    address_blocks = []

    # Look for lines with postal codes
    postal_pattern = re.compile(r'\b\d{5}(?:-\d{4})?\b')  # French/US postal codes

    i = 0
    while i < len(lines):
        line = lines[i]
        if postal_pattern.search(line):
            # Collect surrounding lines as address block
            start = max(0, i - 2)
            end = min(len(lines), i + 1)

            block_lines = []
            for j in range(start, end + 1):
                if j < len(lines):
                    l = lines[j].strip()
                    # Skip lines that are clearly not address parts
                    if l and not re.match(r'^(total|montant|date|invoice|facture|devis|\d+[.,]\d+\s*€?$)', l.lower()):
                        block_lines.append(l)

            if block_lines:
                address_blocks.append('\n'.join(block_lines))
            i = end + 1
        else:
            i += 1

    return address_blocks


def _extract_items(lines: List[str]) -> List[dict]:
    """Extract line items (services/products) from the document."""
    items = []

    # First, try to find table-style items where each column is on a separate line
    # Pattern: Description line, then Quantity line, then Price line, then Total line
    items = _extract_table_items(lines)

    if items:
        return items

    # Fallback: try inline patterns for other PDF formats
    return _extract_inline_items(lines)


def _extract_table_items(lines: List[str]) -> List[dict]:
    """Extract items from table format where each cell is on a separate line."""
    items = []

    # Find the header row to locate where items start
    header_idx = -1
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(h in line_lower for h in ['description', 'désignation', 'libellé']):
            header_idx = i
            break

    if header_idx == -1:
        return []

    # Skip header columns (Description, Quantité, Prix, Total)
    # Find where actual data starts
    i = header_idx + 1

    # Skip remaining header cells
    while i < len(lines):
        line_lower = lines[i].lower().strip()
        if line_lower in ['quantité', 'quantity', 'qty', 'qté',
                          'prix unitaire', 'unit price', 'prix unitaire (€)', 'prix',
                          'total', 'total (€)', 'montant']:
            i += 1
        else:
            break

    # Now extract items - each item has: description, quantity, unit_price, total
    while i < len(lines):
        line = lines[i].strip()

        # Stop if we hit the final total
        if line.lower().startswith('total:') or line.lower() == 'total':
            break

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check if this looks like a description (starts with letter, not just a number)
        if re.match(r'^[A-Za-zÀ-ÿ]', line) and not _is_metadata(line):
            description = line

            # Look for the next 3 values: quantity, unit_price, line_total
            qty = None
            price = None

            # Check next lines for numbers
            j = i + 1
            numbers_found = []
            while j < len(lines) and len(numbers_found) < 3:
                next_line = lines[j].strip()

                # Stop if we hit another description or total
                if re.match(r'^[A-Za-zÀ-ÿ]', next_line) and not re.match(r'^[\d.,]+$', next_line):
                    break
                if next_line.lower().startswith('total'):
                    break

                # Try to parse as number
                num_match = re.match(r'^([\d.,]+)$', next_line)
                if num_match:
                    try:
                        num_str = num_match.group(1).replace(',', '.')
                        num = float(num_str)
                        numbers_found.append(num)
                    except ValueError:
                        pass
                j += 1

            # We expect: quantity, unit_price, line_total
            if len(numbers_found) >= 2:
                # First number is quantity (should be integer-ish)
                qty = int(numbers_found[0]) if numbers_found[0] == int(numbers_found[0]) else 1
                # Second number is unit price
                price = numbers_found[1]

                if description and qty > 0 and price >= 0:
                    items.append({
                        "description": description,
                        "quantity": qty,
                        "price": price
                    })

                i = j  # Skip past the numbers we consumed
                continue

        i += 1

    return items


def _extract_inline_items(lines: List[str]) -> List[dict]:
    """Extract items from inline format where description and price are on same line."""
    items = []

    # Words/patterns to skip
    skip_patterns = [
        r'^devis\b', r'^facture\b', r'^invoice\b', r'^estimate\b',
        r'^date\b', r'^n[°o]\.?\s*:?\s*\d', r'^ref', r'^client\b',
        r'^total\b', r'^montant\b', r'^sous-total', r'^subtotal',
        r'^tva\b', r'^tax\b', r'^\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}',
        r'^page\s+\d', r'^siret\b', r'^iban\b', r'^bic\b',
    ]

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Skip metadata
        should_skip = any(re.match(p, line_lower) for p in skip_patterns)
        if should_skip or len(line_stripped) < 5:
            continue

        # Pattern: Description followed by quantity and price
        match = re.match(
            r'^([A-Za-zÀ-ÿ][\w\s\-\(\)\'\"\.,:]+?)\s{2,}(\d+)\s+[\$€]?\s*([\d\s.,]+)',
            line_stripped
        )
        if match and not _is_metadata(match.group(1)):
            try:
                desc = match.group(1).strip()
                qty = int(match.group(2))
                price = float(match.group(3).replace(' ', '').replace(',', '.'))
                if len(desc) > 2 and qty > 0:
                    items.append({"description": desc, "quantity": qty, "price": price})
                    continue
            except (ValueError, IndexError):
                pass

        # Pattern: Description with price only
        match = re.match(
            r'^([A-Za-zÀ-ÿ][\w\s\-\(\)\'\"\.,:]{5,}?)\s{2,}[\$€]?\s*([\d.,]+)\s*€?$',
            line_stripped
        )
        if match and not _is_metadata(match.group(1)):
            try:
                desc = match.group(1).strip()
                price = float(match.group(2).replace(',', '.'))
                if len(desc) > 3 and 0 < price < 1000000:
                    items.append({"description": desc, "quantity": 1, "price": price})
            except (ValueError, IndexError):
                pass

    return items
def _is_metadata(text: str) -> bool:
    """Check if text looks like document metadata rather than a service description."""
    text_lower = text.lower().strip()

    # Metadata patterns
    metadata_patterns = [
        r'^devis\s',
        r'^facture\s',
        r'^invoice\s',
        r'^estimate\s',
        r'^n[°o]\.?\s',
        r'^ref',
        r'^date\s',
        r'^client\s',
        r'^numéro',
        r'^number',
        r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}',  # Date pattern
        r'^valide',
        r'^valid',
        r'^émis',
        r'^issued',
    ]

    for pattern in metadata_patterns:
        if re.match(pattern, text_lower):
            return True

    # If it's very short and starts with a number, likely metadata
    if len(text) < 15 and re.match(r'^\d', text):
        return True

    return False


def _calculate_total(items: List[dict], full_text: str) -> float:
    """Calculate total from items or extract from text."""
    # First try to calculate from items
    if items:
        return sum(item["quantity"] * item["price"] for item in items)

    # Otherwise try to find total in text
    total_patterns = [
        # Handle "Total:\n€110.00" format (newline between label and value)
        r'total\s*:\s*\n?\s*[€$]?\s*([\d\s.,]+)',
        r'total\s*(?:ttc|ht)?\s*[:\s]*[\$€]?\s*([\d\s.,]+)',
        r'montant\s*(?:total|ttc|ht)?\s*[:\s]*[\$€]?\s*([\d\s.,]+)',
        r'amount\s*(?:due)?\s*[:\s]*[\$€]?\s*([\d\s.,]+)',
        r'grand\s*total\s*[:\s]*[\$€]?\s*([\d\s.,]+)',
        # Currency symbol before amount
        r'total\s*:\s*\n?\s*€([\d\s.,]+)',
        r'€([\d\s.,]+)\s*$',  # Euro amount at end
    ]

    for pattern in total_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE)
        if match:
            try:
                total_str = match.group(1).replace(' ', '').replace(',', '.')
                total_val = float(total_str)
                if total_val > 0:
                    return total_val
            except ValueError:
                continue

    return 0.0


def _extract_title(lines: List[str], text_lower: str) -> str:
    """Extract document title or reference number."""
    # Look for reference patterns
    ref_patterns = [
        r'(?:facture|invoice|devis|estimate)\s*(?:n[°o]?\.?|#|number)?\s*[:\s]*([A-Z0-9\-_]+)',
        r'(?:réf(?:érence)?|ref(?:erence)?)\s*[:\s]*([A-Z0-9\-_]+)',
        r'(?:n[°o]\.?)\s*([A-Z0-9\-_]+)',
    ]

    for pattern in ref_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            ref = match.group(1).strip()
            if len(ref) >= 2:
                return ref.upper()

    return ""
