"""Export SolarApp SQL tables to Google Sheets worksheets."""

import json
import os
from typing import List, Type

import gspread
from google.oauth2.service_account import Credentials
from sqlmodel import Session, SQLModel, select

from app.database import engine
from app.models import (
    Invoice,
    Material,
    Project,
    ProjectMaterial,
    Purchase,
    PurchaseItem,
    Stock,
    StockMovement,
)


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
TABLES: List[Type[SQLModel]] = [
    Material,
    Stock,
    StockMovement,
    Project,
    ProjectMaterial,
    Purchase,
    PurchaseItem,
    Invoice,
]


def _normalize_value(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def _worksheet_for(spreadsheet, title: str):
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=200, cols=26)


def export_all_tables(spreadsheet_id: str, service_account_path: str):
    creds = Credentials.from_service_account_file(service_account_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(spreadsheet_id)

    with Session(engine) as session:
        for table_model in TABLES:
            table_name = table_model.__name__
            worksheet = _worksheet_for(spreadsheet, table_name)

            headers = list(table_model.model_fields.keys())
            rows = [headers]

            records = session.exec(select(table_model)).all()
            for record in records:
                dump = record.model_dump(mode="json")
                rows.append([_normalize_value(dump.get(column)) for column in headers])

            worksheet.clear()
            worksheet.update("A1", rows)
            print(f"Exported {len(records)} rows to worksheet: {table_name}")


if __name__ == "__main__":
    spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", "").strip()
    service_account_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "").strip()

    if not spreadsheet_id:
        raise SystemExit("Missing GOOGLE_SHEETS_SPREADSHEET_ID environment variable.")
    if not service_account_path:
        raise SystemExit("Missing GOOGLE_SERVICE_ACCOUNT_FILE environment variable.")

    export_all_tables(spreadsheet_id=spreadsheet_id, service_account_path=service_account_path)
