"""Desktop OAuth flow for Google Sheets on Raspberry Pi.

What this script does:
1) Runs Google OAuth desktop loopback flow on 127.0.0.1
2) Saves/refreshes token in token.json (offline access)
3) Calls Google Sheets API and lists rows from NOMENCLATOR_PRODUSE

Usage:
  python google_sheets_desktop_auth.py

Required environment variables:
  GOOGLE_OAUTH_CLIENT_SECRETS_FILE=/path/to/desktop-client-secret.json
  GOOGLE_SHEETS_SPREADSHEET_ID=<spreadsheet_id>

Optional:
  GOOGLE_SHEETS_STOCK_SHEET_NAME=NOMENCLATOR_PRODUSE
  GOOGLE_OAUTH_TOKEN_FILE=token.json
  GOOGLE_OAUTH_LOCAL_PORT=8088
"""

import json
import os
import pathlib
import socket
import sys
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


def _load_client_id(client_secret_path: str) -> str:
    with open(client_secret_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    installed = data.get("installed", {})
    client_id = installed.get("client_id", "")
    if not client_id:
        raise RuntimeError("Invalid desktop OAuth client file: missing installed.client_id")
    return client_id


def _ensure_oauth_credentials() -> Credentials:
    client_secret_file = _env_required("GOOGLE_OAUTH_CLIENT_SECRETS_FILE")
    token_file = os.getenv("GOOGLE_OAUTH_TOKEN_FILE", "token.json").strip() or "token.json"
    token_path = pathlib.Path(token_file)
    local_port = int(os.getenv("GOOGLE_OAUTH_LOCAL_PORT", "8088"))

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
        return creds

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)

    if _is_ssh_session():
        client_id = _load_client_id(client_secret_file)
        print("\nSSH session detected.")
        print("If you are connected from laptop via SSH, use local port forwarding in another terminal:")
        print(f"  ssh -L {local_port}:127.0.0.1:{local_port} <pi-user>@<pi-host>\n")
        print("Then open the auth URL from your laptop browser.")

        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        print("Authorization URL:")
        print(auth_url)
        print(
            "\nThe local callback must reach http://127.0.0.1 on Raspberry Pi.\n"
            "If you used SSH -L, callback on laptop localhost is tunneled to Pi."
        )

        # Start temporary local server (loopback flow).
        creds = flow.run_local_server(
            host="127.0.0.1",
            port=local_port,
            open_browser=False,
            authorization_prompt_message="Open this URL in your browser: {url}",
            success_message="Authentication complete. You can close this tab.",
        )
    else:
        creds = flow.run_local_server(
            host="127.0.0.1",
            port=local_port,
            open_browser=True,
            authorization_prompt_message="",
            success_message="Authentication complete. You can close this tab.",
        )

    token_path.write_text(creds.to_json(), encoding="utf-8")
    print(f"\nSaved token to: {token_path.resolve()}")
    return creds


def _list_stock_products(creds: Credentials) -> None:
    spreadsheet_id = _env_required("GOOGLE_SHEETS_SPREADSHEET_ID")
    sheet_name = os.getenv("GOOGLE_SHEETS_STOCK_SHEET_NAME", "NOMENCLATOR_PRODUSE").strip() or "NOMENCLATOR_PRODUSE"

    service = build("sheets", "v4", credentials=creds)
    read_range = f"{sheet_name}!A:Z"

    response = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=read_range)
        .execute()
    )
    rows: List[List[str]] = response.get("values", [])

    if not rows:
        print(f"No rows found in worksheet '{sheet_name}'.")
        return

    headers = rows[0]
    data_rows = rows[1:]
    print(f"\nWorksheet: {sheet_name}")
    print(f"Columns: {headers}")
    print(f"Rows found: {len(data_rows)}\n")

    for idx, row in enumerate(data_rows, start=1):
        # Print compact key/value pairs based on header positions.
        record: Dict[str, Any] = {}
        for i, header in enumerate(headers):
            record[header] = row[i] if i < len(row) else ""
        print(f"{idx}. {record}")


def main() -> int:
    try:
        creds = _ensure_oauth_credentials()
        _list_stock_products(creds)
        return 0
    except HttpError as e:
        print(f"Google API error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
