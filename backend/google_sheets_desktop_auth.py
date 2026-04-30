"""Desktop OAuth flow for Google Sheets on Raspberry Pi.

What this script does:
1) Uses InstalledAppFlow (Desktop App OAuth)
2) Runs run_local_server on localhost (SSH-friendly with tunnel)
3) Saves/refreshes token.json for offline access
4) Tests connection by reading stock worksheet title
"""

import json
import os
import pathlib
from typing import Any, Dict, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def _is_ssh_session() -> bool:
    return bool(os.getenv("SSH_CONNECTION") or os.getenv("SSH_TTY"))


def _env_required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _save_token(token_path: pathlib.Path, creds: Credentials) -> None:
    token_path.write_text(creds.to_json(), encoding="utf-8")


def get_valid_credentials() -> Credentials:
    """Load token.json, refresh if needed, else run desktop OAuth flow."""
    client_secret_file = _env_required("GOOGLE_OAUTH_CLIENT_SECRETS_FILE")
    token_file = os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "token.json").strip() or "token.json"
    token_path = pathlib.Path(token_file)
    local_port = int(os.getenv("GOOGLE_OAUTH_LOCAL_PORT", "8080"))

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_token(token_path, creds)
        print(f"Refreshed and saved token: {token_path.resolve()}")
        return creds

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)

    if _is_ssh_session():
        print("\nSSH session detected.")
        print("If you are connected from laptop via SSH, use local port forwarding in another terminal:")
        print(f"  ssh -L {local_port}:127.0.0.1:{local_port} <pi-user>@<pi-host>\n")
        print("Then open the URL shown below in your laptop browser.")
        print("Callback will be received on Raspberry localhost via SSH tunnel.")

        # Desktop OAuth loopback flow on localhost:8080 (tunnel-friendly)
        creds = flow.run_local_server(
            host="localhost",
            port=local_port,
            open_browser=False,
            authorization_prompt_message="Open this URL in your browser: {url}",
            success_message="Authentication complete. You can close this tab.",
            access_type="offline",
            prompt="consent",
        )
    else:
        creds = flow.run_local_server(
            host="localhost",
            port=local_port,
            open_browser=True,
            authorization_prompt_message="",
            success_message="Authentication complete. You can close this tab.",
            access_type="offline",
            prompt="consent",
        )

    _save_token(token_path, creds)
    print(f"\nSaved token to: {token_path.resolve()}")
    return creds


def _test_stock_sheet_connection(creds: Credentials) -> None:
    """Test Google Sheets connection by reading stock sheet title."""
    spreadsheet_id = _env_required("GOOGLE_SHEETS_SPREADSHEET_ID")
    sheet_name = os.getenv("GOOGLE_SHEETS_STOCK_SHEET_NAME", "NOMENCLATOR_PRODUSE").strip() or "NOMENCLATOR_PRODUSE"

    service = build("sheets", "v4", credentials=creds)
    spreadsheet = (
        service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id)
        .execute()
    )
    all_sheets = spreadsheet.get("sheets", [])
    target = None
    for sheet in all_sheets:
        props = sheet.get("properties", {})
        if props.get("title") == sheet_name:
            target = props
            break

    if not target:
        available = [s.get("properties", {}).get("title", "") for s in all_sheets]
        raise RuntimeError(
            f"Worksheet '{sheet_name}' not found. Available sheets: {available}"
        )

    print(f"Connected successfully. Stock worksheet title: {target.get('title')}")

    # Optional: show first rows as proof of access.
    read_range = f"{sheet_name}!A:Z"
    response = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=read_range
    ).execute()
    rows: List[List[str]] = response.get("values", [])

    if not rows:
        print("No data rows found in stock worksheet.")
        return

    headers = rows[0]
    preview_rows = rows[1:6]
    print(f"Columns: {headers}")
    print(f"Preview rows: {len(preview_rows)}")
    for idx, row in enumerate(preview_rows, start=1):
        record: Dict[str, Any] = {}
        for i, header in enumerate(headers):
            record[header] = row[i] if i < len(row) else ""
        print(f"{idx}. {record}")


def main() -> int:
    try:
        creds = get_valid_credentials()
        _test_stock_sheet_connection(creds)
        return 0
    except HttpError as e:
        print(f"Google API error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
