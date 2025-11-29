from fastapi import APIRouter, HTTPException, Response, UploadFile, File, Depends, Header
from datetime import datetime
import uuid
import os
from pathlib import Path
from typing import Optional

from models.invoice import InvoiceCreate, InvoiceResponse, InvoiceItem
from services.invoice_generator import create_invoice
from services.supabase_client import get_supabase
from services.pdf_parser import extract_invoice_data

router = APIRouter(prefix="/invoices", tags=["invoices"])

# Get project root directory (parent of backend)
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOGO_PATH = PROJECT_ROOT / "favicon.png"


def get_optional_user(authorization: Optional[str] = Header(None)):
    """Extract user from Authorization header if present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None

    token = authorization.replace("Bearer ", "")

    try:
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)

        if user_response and user_response.user:
            return {"user": user_response.user, "token": token}
    except Exception:
        pass

    return None


def get_required_user(authorization: str = Header(...)):
    """Require user authentication."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.replace("Bearer ", "")

    try:
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)

        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return {"user": user_response.user, "token": token}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# Translations
I18N = {
    "en": {
        "mode_invoice": "Invoice",
        "mode_estimate": "Estimate",
        "currency_symbol": "$",
        "headers": {
            "description": "Description",
            "quantity": "Quantity",
            "unit_price": "Unit Price ($)",
            "total": "Total ($)"
        },
        "labels": {
            "from": "From:",
            "to": "To:"
        }
    },
    "fr": {
        "mode_invoice": "Facture",
        "mode_estimate": "Devis",
        "currency_symbol": "€",
        "headers": {
            "description": "Description",
            "quantity": "Quantité",
            "unit_price": "Prix Unitaire (€)",
            "total": "Total (€)"
        },
        "labels": {
            "from": "De :",
            "to": "À :"
        }
    }
}


@router.post("/", response_model=InvoiceResponse)
async def create_new_invoice(
    invoice: InvoiceCreate,
    current_user: dict = Depends(get_required_user)
):
    """Create a new invoice and save it to the database."""
    try:
        supabase = get_supabase()

        # Generate invoice number and date
        invoice_number = datetime.now().strftime("%Y%m%d-%H%M%S")
        invoice_date = datetime.now().strftime("%Y-%m-%d")
        invoice_id = str(uuid.uuid4())

        # Calculate total
        total = sum(item.quantity * item.price for item in invoice.items)

        # Prepare invoice data for database
        invoice_db = {
            "id": invoice_id,
            "invoice_number": invoice_number,
            "date": invoice_date,
            "from_address": invoice.from_address,
            "to_address": invoice.to_address,
            "items": [item.model_dump() for item in invoice.items],
            "mode": invoice.mode,
            "language": invoice.language,
            "total": total,
            "doc_title": invoice.doc_title,
            "user_id": str(current_user["user"].id),
            "created_at": datetime.now().isoformat()
        }

        # Save to Supabase
        result = supabase.table("invoices").insert(invoice_db).execute()

        return InvoiceResponse(
            id=invoice_id,
            invoice_number=invoice_number,
            date=invoice_date,
            from_address=invoice.from_address,
            to_address=invoice.to_address,
            items=invoice.items,
            mode=invoice.mode,
            language=invoice.language,
            total=total,
            created_at=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: str):
    """Generate and return the PDF for an invoice."""
    try:
        supabase = get_supabase()

        # Fetch invoice from database
        result = supabase.table("invoices").select("*").eq("id", invoice_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")

        invoice_data = result.data[0]
        lang = invoice_data.get("language", "en")
        lang_dict = I18N.get(lang, I18N["en"])

        # Get mode label
        mode_key = f"mode_{invoice_data['mode']}"
        mode_label = lang_dict.get(mode_key, invoice_data['mode'].capitalize())

        # Generate PDF
        pdf_bytes = create_invoice(
            invoice_data=invoice_data,
            mode=mode_label,
            currency_symbol=lang_dict["currency_symbol"],
            logo_path=str(LOGO_PATH) if LOGO_PATH.exists() else None,
            headers=lang_dict["headers"],
            labels=lang_dict["labels"],
            return_bytes=True
        )

        # Generate filename
        if invoice_data.get("doc_title"):
            safe_title = "".join(c for c in invoice_data["doc_title"] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            date_yymmdd = datetime.now().strftime("%y%m%d")
            filename = f"{safe_title}_{date_yymmdd}.pdf"
        else:
            filename = f"{invoice_data['mode']}_{invoice_data['invoice_number']}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_invoices(current_user: dict = Depends(get_required_user)):
    """List all invoices for the current user."""
    try:
        supabase = get_supabase()

        query = supabase.table("invoices").select("*").eq("user_id", str(current_user["user"].id))

        result = query.order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str):
    """Get a specific invoice by ID."""
    try:
        supabase = get_supabase()
        result = supabase.table("invoices").select("*").eq("id", invoice_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Invoice not found")

        return result.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str):
    """Delete an invoice."""
    try:
        supabase = get_supabase()
        result = supabase.table("invoices").delete().eq("id", invoice_id).execute()
        return {"message": "Invoice deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-pdf")
async def generate_pdf_only(invoice: InvoiceCreate):
    """Generate a PDF without saving to database (for preview)."""
    try:
        invoice_number = datetime.now().strftime("%Y%m%d-%H%M%S")
        invoice_date = datetime.now().strftime("%Y-%m-%d")

        lang_dict = I18N.get(invoice.language, I18N["en"])
        mode_label = lang_dict.get(f"mode_{invoice.mode}", invoice.mode.capitalize())

        invoice_data = {
            "invoice_number": invoice_number,
            "date": invoice_date,
            "from_address": invoice.from_address,
            "to_address": invoice.to_address,
            "items": [item.model_dump() for item in invoice.items]
        }

        pdf_bytes = create_invoice(
            invoice_data=invoice_data,
            mode=mode_label,
            currency_symbol=lang_dict["currency_symbol"],
            logo_path=str(LOGO_PATH) if LOGO_PATH.exists() else None,
            headers=lang_dict["headers"],
            labels=lang_dict["labels"],
            return_bytes=True
        )

        # Generate filename
        if invoice.doc_title:
            safe_title = "".join(c for c in invoice.doc_title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            date_yymmdd = datetime.now().strftime("%y%m%d")
            filename = f"{safe_title}_{date_yymmdd}.pdf"
        else:
            filename = f"{invoice.mode}_{invoice_number}.pdf"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_invoice(file: UploadFile = File(...)):
    """
    Upload a PDF invoice/estimate and extract structured data.
    Returns extracted fields for user confirmation before saving.
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are accepted")

        # Read file content
        pdf_bytes = await file.read()

        if len(pdf_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty file")

        # Limit file size (10MB)
        if len(pdf_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # Save the PDF to the uploads directory
        uploads_dir = PROJECT_ROOT / "uploads"
        uploads_dir.mkdir(exist_ok=True)

        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = "".join(c for c in file.filename if c.isalnum() or c in ('_', '-', '.')).strip()
        saved_filename = f"{file_id}_{safe_filename}"
        file_path = uploads_dir / saved_filename

        with open(file_path, "wb") as f:
            f.write(pdf_bytes)

        # Extract structured data from PDF
        try:
            extracted_data = extract_invoice_data(pdf_bytes)
        except Exception as parse_error:
            print(f"PDF parsing error: {parse_error}")
            extracted_data = {
                "mode": "invoice",
                "language": "fr",
                "from_address": "",
                "to_address": "",
                "items": [],
                "total": 0.0,
                "doc_title": "",
                "raw_text": f"Failed to parse: {str(parse_error)}"
            }

        # Return extracted data for confirmation
        return {
            "success": True,
            "filename": file.filename,
            "file_id": file_id,
            "saved_path": saved_filename,
            "extracted": {
                "mode": extracted_data.get("mode", "invoice"),
                "language": extracted_data.get("language", "fr"),
                "from_address": extracted_data.get("from_address", ""),
                "to_address": extracted_data.get("to_address", ""),
                "items": extracted_data.get("items", []),
                "total": extracted_data.get("total", 0.0),
                "doc_title": extracted_data.get("doc_title", ""),
            },
            "raw_text": extracted_data.get("raw_text", "")[:3000]  # Limit for display
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")
