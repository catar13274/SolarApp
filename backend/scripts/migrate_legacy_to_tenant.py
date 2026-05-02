"""
Migrate a single legacy SQLite database (SOLARAPP_DB_URL) into multitenant layout:

  data/tenants/<tenant_code>/solarapp.db

Also ensures a row exists in the central registry (registry.db).

Usage (from the backend folder, with venv activated):

  python scripts/migrate_legacy_to_tenant.py --tenant-code freevoltsrl.ro --tenant-name "Freevolt SRL"

  python scripts/migrate_legacy_to_tenant.py --tenant-code freevoltsrl.ro --dry-run

Environment (optional, same as the API):

  SOLARAPP_DB_URL=sqlite:///./data/solarapp.db
  SOLARAPP_REGISTRY_URL=sqlite:///./data/registry.db
  SOLARAPP_TENANT_ROOT=./data/tenants

After migration, set SOLARAPP_MULTITENANT=true and restart the API.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Run from backend/: `python scripts/migrate_legacy_to_tenant.py`
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from dotenv import load_dotenv

load_dotenv(_BACKEND_ROOT / ".env")


def _normalize_code(code: str) -> str:
    c = (code or "").strip().lower()
    c = re.sub(r"\s+", "-", c)
    return c


def _sqlite_path_from_url(url: str) -> Path | None:
    if "sqlite:///" not in url:
        return None
    db_path = url.replace("sqlite:///", "")
    if db_path.startswith("./"):
        return (_BACKEND_ROOT / db_path[2:]).resolve()
    return Path(db_path).resolve()


def _checkpoint(path: Path) -> None:
    conn = sqlite3.connect(path)
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
            raise SystemExit(f"Integrity check failed: {row[0] if row else 'unknown'}")
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            ).fetchall()
        }
        if not tables.intersection({"material", "stock", "project"}):
            raise SystemExit(
                "Fișierul nu pare o bază SolarApp (lipsesc tabele așteptate: material, stock, project)."
            )
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrare bază unică → tenant multitenant.")
    parser.add_argument(
        "--tenant-code",
        required=True,
        help="Cod firmă (ex: freevoltsrl.ro), ca în registru.",
    )
    parser.add_argument(
        "--tenant-name",
        default="",
        help="Nume afișat în registru (implicit: același cu codul sau din env MIGRATE_TENANT_NAME).",
    )
    parser.add_argument(
        "--legacy-path",
        default="",
        help="Cale explicită către solarapp.db vechi (altfel se folosește SOLARAPP_DB_URL).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Doar afișează pașii, nu scrie fișiere.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Dacă există deja solarapp.db pentru tenant, face backup .bak și înlocuiește.",
    )
    parser.add_argument(
        "--remove-legacy",
        action="store_true",
        help="După copiere reușită, șterge fișierul sursă legacy (periculos).",
    )

    args = parser.parse_args()
    code = _normalize_code(args.tenant_code)
    if not code:
        raise SystemExit("Cod tenant invalid.")

    tenant_name = (
        args.tenant_name.strip()
        or os.getenv("MIGRATE_TENANT_NAME", "").strip()
        or code
    )

    if args.legacy_path:
        legacy_path = Path(args.legacy_path).resolve()
    else:
        db_url = os.getenv("SOLARAPP_DB_URL", "sqlite:///./data/solarapp.db")
        p = _sqlite_path_from_url(db_url)
        if not p:
            raise SystemExit("SOLARAPP_DB_URL trebuie să fie SQLite (sqlite:///...).")
        legacy_path = p

    if not legacy_path.is_file():
        raise SystemExit(f"Sursa nu există: {legacy_path}")

    tenant_root = Path(os.getenv("SOLARAPP_TENANT_ROOT", "./data/tenants")).resolve()
    if not tenant_root.is_absolute():
        tenant_root = (_BACKEND_ROOT / tenant_root).resolve()

    dest_dir = tenant_root / code
    dest_db = dest_dir / "solarapp.db"

    print(f"Sursă legacy:     {legacy_path}")
    print(f"Destinație tenant:{dest_db}")
    print(f"Cod / nume:       {code} / {tenant_name}")

    _checkpoint(legacy_path)
    _verify_solarapp_sqlite(legacy_path)

    if dest_db.is_file() and not args.overwrite:
        raise SystemExit(
            f"Există deja {dest_db}. Folosiți --overwrite pentru backup + înlocuire, sau ștergeți manual."
        )

    if args.dry_run:
        print("[dry-run] Oprit înainte de copiere.")
        return

    dest_dir.mkdir(parents=True, exist_ok=True)

    if dest_db.is_file():
        stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        bak = dest_db.with_name(f"{dest_db.name}.pre-migrate.{stamp}.bak")
        shutil.copy2(dest_db, bak)
        print(f"Backup tenant existent: {bak}")
        for extra in (Path(str(dest_db) + "-wal"), Path(str(dest_db) + "-shm")):
            if extra.is_file():
                extra.unlink()

    for extra in (Path(str(dest_db) + "-wal"), Path(str(dest_db) + "-shm")):
        if extra.is_file():
            extra.unlink()

    shutil.copy2(legacy_path, dest_db)
    _checkpoint(dest_db)
    _verify_solarapp_sqlite(dest_db)
    print(f"Copiere OK → {dest_db}")

    # Registry row
    os.chdir(_BACKEND_ROOT)
    from sqlmodel import Session, create_engine, select

    from app.database import REGISTRY_URL, create_registry_tables, sqlite_connect_args
    from app.registry_models import TenantRegistry

    reg_engine = create_engine(
        REGISTRY_URL,
        echo=False,
        connect_args=sqlite_connect_args if "sqlite" in REGISTRY_URL else {},
    )
    create_registry_tables()

    with Session(reg_engine) as session:
        existing = session.exec(select(TenantRegistry).where(TenantRegistry.code == code)).first()
        if existing:
            existing.name = tenant_name
            existing.updated_at = datetime.utcnow()
            session.add(existing)
            print(f"Actualizat rând registru pentru {code!r}.")
        else:
            session.add(
                TenantRegistry(
                    code=code,
                    name=tenant_name,
                    legal_name=tenant_name,
                )
            )
            print(f"Adăugat rând registru pentru {code!r}.")
        session.commit()

    reg_engine.dispose(close=True)

    if args.remove_legacy:
        try:
            for extra in (Path(str(legacy_path) + "-wal"), Path(str(legacy_path) + "-shm")):
                if extra.is_file():
                    extra.unlink()
            legacy_path.unlink()
            print(f"Șters sursa legacy: {legacy_path}")
        except OSError as exc:
            raise SystemExit(f"Nu s-a putut șterge sursa: {exc}") from exc

    print()
    print("Următorii pași:")
    print("  1. Setați SOLARAPP_MULTITENANT=true în .env")
    print("  2. Reporniți API-ul")
    print("  3. În UI, selectați firma cu codul:", code)


if __name__ == "__main__":
    main()
