"""Google Sheets integration for the live journal worksheet.

This code runs on the backend so Google credentials are never exposed to the browser.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


JOURNAL_HEADERS: List[str] = [
    "Timestamp",
    "TipTranzactie",
    "SKU",
    "Produs",
    "Cantitate",
    "PretUnit",
    "Currency",
    "Sursa",
    "RefID",
    "Note",
]


def _get_client():
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()

    if not spreadsheet_id or not service_account_file:
        raise RuntimeError(
            "Google Sheets is not configured. Set GOOGLE_SHEETS_SPREADSHEET_ID and "
            "GOOGLE_SERVICE_ACCOUNT_FILE."
        )

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    return gspread.authorize(creds), spreadsheet_id


def _get_worksheet(spreadsheet, sheet_name: str):
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        # Create with enough columns for our fixed headers.
        return spreadsheet.add_worksheet(title=sheet_name, rows=200, cols=len(JOURNAL_HEADERS))


def append_journal_row(journal: Dict[str, Any]) -> None:
    """Append a transaction row to worksheet `JURNAL_TRANZACTII`."""

    ws_name = os.getenv("GSHEETS_JURNAL_SHEET_NAME", "JURNAL_TRANZACTII").strip() or "JURNAL_TRANZACTII"

    # Build row values in the same order as JOURNAL_HEADERS.
    now_iso = datetime.now(timezone.utc).isoformat()
    raw = str(journal.get("movement_type", "")).strip().lower()
    tip_tranzactie = "Primire" if raw == "in" else ("Trimitere" if raw == "out" else raw.upper())

    quantity = journal.get("quantity", "")
    unit_price = journal.get("unit_price", "")
    currency = journal.get("currency", "") or journal.get("purchase_currency", "") or ""

    row_values = [
        journal.get("timestamp", now_iso),
        tip_tranzactie,
        journal.get("material_sku", ""),
        journal.get("material_name", ""),
        "" if quantity is None else quantity,
        "" if unit_price is None else unit_price,
        currency,
        journal.get("reference_type", ""),
        journal.get("reference_id", ""),
        journal.get("notes", ""),
    ]

    client, spreadsheet_id = _get_client()
    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = _get_worksheet(spreadsheet, ws_name)

    # If the sheet is empty, write headers first.
    try:
        existing = worksheet.get_all_values()
        if not existing:
            worksheet.append_row(JOURNAL_HEADERS, value_input_option="USER_ENTERED")
    except Exception:
        # Don't block app usage if headers check fails.
        logger.exception("Failed to validate journal worksheet headers.")

    worksheet.append_row(row_values, value_input_option="USER_ENTERED")
    logger.info("Appended journal row to %s", ws_name)

