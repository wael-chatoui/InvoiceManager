from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import os

def create_invoice(invoice_data, file_path, mode="Invoice", currency_symbol="€", logo_path=None, headers=None, labels=None):
    """
    Creates a PDF invoice or estimate from the given data.

    Args:
        invoice_data (dict): A dictionary containing the invoice data.
        file_path (str): The path to save the PDF file.
        mode (str): "Invoice" or "Estimate" (or translated versions like "Facture" or "Devis").
        currency_symbol (str): The currency symbol to use.
        logo_path (str, optional): Path to a logo image file. Defaults to None.
        headers (dict, optional): A dictionary of translated headers for the items table.
        labels (dict, optional): A dictionary with 'from' and 'to' labels. Defaults to English.
    """
    if headers is None:
        headers = {
            'description': 'Description',
            'quantity': 'Quantity',
            'unit_price': f'Unit Price ({currency_symbol})',
            'total': f'Total ({currency_symbol})'
        }
    else:
        # Ensure unit_price and total headers don't already have currency if we're adding it
        if 'unit_price' in headers and currency_symbol not in headers['unit_price']:
            headers['unit_price'] = f"{headers['unit_price'].rstrip(':')} ({currency_symbol})"
        if 'total' in headers and currency_symbol not in headers['total']:
            headers['total'] = f"{headers['total'].rstrip(':')} ({currency_symbol})"

    if labels is None:
        labels = {
            'from': 'From:',
            'to': 'To:'
        }

    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    # Logo
    if logo_path and os.path.exists(logo_path):
        try:
            img = ImageReader(logo_path)
            # Draw image at top left with margin
            c.drawImage(img, 6, height - 80, width=100, height=50, preserveAspectRatio=True, mask='auto')
        except Exception as e:
            print(f"Error drawing logo: {e}")

    # Title
    c.setFont("Helvetica-Bold", 24)
    # Position title to the right of the logo
    c.drawString(150, height - 65, mode.upper())

    # Invoice Info
    c.setFont("Helvetica", 12)
    text = c.beginText(width - 180, height - 40)
    text.textLine(f"{mode} #: {invoice_data['invoice_number']}")
    text.textLine(f"Date: {invoice_data['date']}")
    c.drawText(text)

    # From
    c.setFont("Helvetica-Bold", 12)
    c.drawString(30, height - 120, labels['from'])
    c.setFont("Helvetica", 12)
    from_text = c.beginText(30, height - 140)
    for line in invoice_data['from_address'].replace('\\n', '\n').split('\n'):
        from_text.textLine(line)
    c.drawText(from_text)

    # To
    c.setFont("Helvetica-Bold", 12)
    c.drawString(300, height - 120, labels['to'])
    c.setFont("Helvetica", 12)
    to_text = c.beginText(300, height - 140)
    for line in invoice_data['to_address'].replace('\\n', '\n').split('\n'):
        to_text.textLine(line)
    c.drawText(to_text)

    # Items
    c.setFont("Helvetica-Bold", 12)
    y_header = height - 220
    c.drawString(30, y_header, headers['description'])
    c.drawString(300, y_header, headers['quantity'])
    c.drawString(400, y_header, headers['unit_price'])
    c.drawString(500, y_header, headers['total'])
    c.line(30, y_header - 5, width - 30, y_header - 5)

    c.setFont("Helvetica", 12)
    y = y_header - 25
    total = 0
    for item in invoice_data['items']:
        c.drawString(30, y, item['description'])
        c.drawString(300, y, str(item['quantity']))
        c.drawString(400, y, f"{item['price']:.2f}")
        item_total = item['quantity'] * item['price']
        c.drawString(500, y, f"{item_total:.2f}")
        total += item_total
        y -= 20

    # Total
    c.line(480, y + 5, width - 30, y + 5)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(400, y - 15, "Total:")
    c.drawString(500, y - 15, f"{currency_symbol}{total:.2f}")

    c.save()

if __name__ == "__main__":
    sample_invoice = {
        "invoice_number": "12345",
        "date": "2025-11-28",
        "from_address": "9 rue Olympe de Gouges\\n92600, Asnières-sur-Seine",
        "to_address": "Restaurant BP Halal\\n 103B Bd Besszières, 75017 Paris",
        "items": [],
    }

    fr_headers = {
        'description': 'Description',
        'quantity': 'Quantité',
        'unit_price': 'Prix Unitaire (€)',
        'total': 'Total (€)'
    }

    # Example for Invoice
    invoice_file = "invoices/invoice_12345.pdf"
    create_invoice(sample_invoice, invoice_file, mode="Invoice", currency_symbol="€", logo_path="favicon.png", headers=fr_headers)
    print(f"Invoice saved to {invoice_file}")

    # Example for Estimate
    estimate_file = "invoices/estimate_67890.pdf"
    sample_invoice["invoice_number"] = "67890"
    create_invoice(sample_invoice, estimate_file, mode="Estimate", currency_symbol="$", logo_path="favicon.png")
    print(f"Estimate saved to {estimate_file}")
