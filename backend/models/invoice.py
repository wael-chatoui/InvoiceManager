from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class InvoiceItem(BaseModel):
    description: str
    quantity: int
    price: float


class InvoiceCreate(BaseModel):
    from_address: str
    to_address: str
    items: List[InvoiceItem]
    mode: str = "invoice"  # "invoice" or "estimate"
    language: str = "en"  # "en" or "fr"
    doc_title: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: str
    invoice_number: str
    date: str
    from_address: str
    to_address: str
    items: List[InvoiceItem]
    mode: str
    language: str
    total: float
    created_at: datetime
    pdf_url: Optional[str] = None


class InvoiceDB(BaseModel):
    id: Optional[str] = None
    invoice_number: str
    date: str
    from_address: str
    to_address: str
    items: List[dict]
    mode: str
    language: str
    total: float
    doc_title: Optional[str] = None
    pdf_path: Optional[str] = None
    created_at: Optional[datetime] = None
    user_id: Optional[str] = None
