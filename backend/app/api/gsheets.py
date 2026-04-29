"""Google Sheets API endpoints (backend-to-Google)."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import get_current_user
from ..gsheets_journal import append_journal_row

router = APIRouter(prefix="/api/v1/gsheets", tags=["gsheets"])


class AppendJournalRowRequest(BaseModel):
    movement_type: str  # "in" / "out"
    material_sku: str
    material_name: str
    quantity: float
    unit_price: Optional[float] = None
    currency: Optional[str] = None
    reference_type: Optional[str] = None  # "purchase" / "project"
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    timestamp: Optional[str] = None  # ISO 8601 string (optional)


@router.post("/journal/append")
def append_journal(request: AppendJournalRowRequest, _user=Depends(get_current_user)):
    try:
        append_journal_row(request.model_dump())
        return {"message": "Journal row appended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to append to Google Sheets: {str(e)}")

