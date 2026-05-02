"""SQLite database backup and restore (admin)."""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile
from fastapi.responses import Response

from ..database import create_db_and_tables, engine, get_sqlite_file_path

router = APIRouter(prefix="/api/v1/admin/database", tags=["database-admin"])

TOKEN_HEADER = "X-Solarapp-Backup-Token"


def _require_backup_token(
    x_solarapp_backup_token: Annotated[Optional[str], Header(alias=TOKEN_HEADER)] = None,
):
    expected = os.getenv("SOLARAPP_BACKUP_TOKEN", "").strip()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="Backup API is disabled. Set SOLARAPP_BACKUP_TOKEN in the server environment.",
        )
    if not x_solarapp_backup_token or x_solarapp_backup_token.strip() != expected:
        raise HTTPException(status_code=403, detail="Invalid or missing backup token")


def _checkpoint_sqlite(db_path: Path) -> None:
    """Flush WAL into the main database file for a consistent copy."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA wal_checkpoint(FULL)")
        conn.commit()
    finally:
        conn.close()


def _verify_solarapp_sqlite(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        if not row or row[0] != "ok":
            raise HTTPException(
                status_code=400,
                detail=f"SQLite integrity check failed: {row[0] if row else 'unknown'}",
            )
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        if not tables.intersection({"material", "stock", "project", "company"}):
            raise HTTPException(
                status_code=400,
                detail="File does not look like a SolarApp database (missing expected tables).",
            )
    finally:
        conn.close()


@router.get("/backup")
def download_database_backup(_token_ok: None = Depends(_require_backup_token)):
    """Download a snapshot of the SQLite database file."""
    db_path = get_sqlite_file_path()
    if not db_path or not db_path.is_file():
        raise HTTPException(status_code=501, detail="Backup is only supported for SQLite file databases.")

    try:
        _checkpoint_sqlite(db_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not prepare database file: {exc}") from exc

    data = db_path.read_bytes()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"solarapp_backup_{stamp}.db"
    return Response(
        content=data,
        media_type="application/x-sqlite3",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore")
async def restore_database_upload(
    _token_ok: None = Depends(_require_backup_token),
    file: UploadFile = File(...),
):
    """
    Replace the SQLite database with an uploaded .db file.
    The current database is copied aside as solarapp.db.pre-restore.<timestamp>.bak before overwrite.
    """
    db_path = get_sqlite_file_path()
    if not db_path:
        raise HTTPException(status_code=501, detail="Restore is only supported for SQLite file databases.")

    if not file.filename or not file.filename.lower().endswith(".db"):
        raise HTTPException(status_code=400, detail="Upload a .db SQLite file.")

    raw = await file.read()
    if len(raw) < 512:
        raise HTTPException(status_code=400, detail="Uploaded file is too small to be a valid database.")

    suffix = Path(file.filename).suffix or ".db"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(raw)
        tmp_path = Path(tmp.name)

    try:
        _verify_solarapp_sqlite(tmp_path)
    except HTTPException:
        tmp_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Invalid database file: {exc}") from exc

    db_path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    pre_restore = db_path.with_name(f"{db_path.name}.pre-restore.{stamp}.bak")

    engine.dispose(close=True)

    try:
        if db_path.is_file():
            shutil.copy2(db_path, pre_restore)
        for extra in (Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")):
            if extra.is_file():
                extra.unlink()

        shutil.move(str(tmp_path), str(db_path))
    except OSError as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Could not replace database file: {exc}") from exc

    try:
        create_db_and_tables()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Database replaced but migration step failed: {exc}. Check backup file {pre_restore.name}.",
        ) from exc

    return {
        "message": "Database restored successfully.",
        "previous_saved_as": pre_restore.name if pre_restore.is_file() else None,
    }
