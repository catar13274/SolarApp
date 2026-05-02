"""Database connection, registry, and per-tenant SQLite files (multitenant)."""

import os
import re
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlmodel import Session, create_engine, select
from sqlalchemy import event
from sqlalchemy.engine import Engine

from .registry_models import TenantRegistry
from .tenant_metadata import REGISTRY_METADATA, TENANT_METADATA

# Multitenant: one central registry + one SQLite file per firm under SOLARAPP_TENANT_ROOT.
MULTITENANT_ENABLED = os.getenv("SOLARAPP_MULTITENANT", "false").lower() in (
    "1",
    "true",
    "yes",
)

REGISTRY_URL = os.getenv("SOLARAPP_REGISTRY_URL", "sqlite:///./data/registry.db")
DATABASE_URL = os.getenv("SOLARAPP_DB_URL", "sqlite:///./data/solarapp.db")
TENANT_ROOT = Path(os.getenv("SOLARAPP_TENANT_ROOT", "./data/tenants")).resolve()

_tenant_engines: dict[str, Engine] = {}

sqlite_connect_args = {"check_same_thread": False}


def _normalize_code(code: str) -> str:
    c = (code or "").strip().lower()
    c = re.sub(r"\s+", "-", c)
    return c


def tenant_db_path(code: str) -> Path:
    safe = _normalize_code(code)
    return TENANT_ROOT / safe / "solarapp.db"


def _sqlite_file_from_url(url: str) -> Optional[Path]:
    if "sqlite:///" not in url:
        return None
    db_path = url.replace("sqlite:///", "")
    if db_path.startswith("./"):
        return (Path.cwd() / db_path[2:]).resolve()
    return Path(db_path).resolve()


def _ensure_parent_dir_for_sqlite_url(url: str) -> None:
    p = _sqlite_file_from_url(url)
    if p:
        p.parent.mkdir(parents=True, exist_ok=True)


if "sqlite" in REGISTRY_URL:
    _ensure_parent_dir_for_sqlite_url(REGISTRY_URL)
if not MULTITENANT_ENABLED and "sqlite" in DATABASE_URL:
    _ensure_parent_dir_for_sqlite_url(DATABASE_URL)

registry_engine = create_engine(
    REGISTRY_URL,
    echo=False,
    connect_args=sqlite_connect_args if "sqlite" in REGISTRY_URL else {},
    pool_pre_ping=True,
    pool_recycle=3600,
)

engine: Optional[Engine] = None
if not MULTITENANT_ENABLED:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        connect_args=sqlite_connect_args if "sqlite" in DATABASE_URL else {},
        pool_pre_ping=True,
        pool_recycle=3600,
    )


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    if connection_record.dialect.name == "sqlite":
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-32000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


def get_sqlite_file_path(tenant_code: Optional[str] = None) -> Optional[Path]:
    """Absolute path to SQLite file for backup (file must exist)."""
    if MULTITENANT_ENABLED:
        if not tenant_code:
            return None
        p = tenant_db_path(tenant_code)
        return p if p.is_file() else None
    p = _sqlite_file_from_url(DATABASE_URL)
    return p if p and p.is_file() else None


def get_sqlite_restore_path(tenant_code: Optional[str] = None) -> Optional[Path]:
    """Target path for restore (parents created for multitenant)."""
    if MULTITENANT_ENABLED:
        if not tenant_code:
            return None
        p = tenant_db_path(tenant_code)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    if "sqlite" not in DATABASE_URL:
        return None
    p = _sqlite_file_from_url(DATABASE_URL)
    if p:
        p.parent.mkdir(parents=True, exist_ok=True)
    return p


def create_registry_tables() -> None:
    REGISTRY_METADATA.create_all(registry_engine)


def _migrate_tenant_engine(eng: Engine) -> None:
    """Incremental SQLite migrations for tenant DBs."""
    url = str(eng.url)
    if "sqlite" not in url:
        return

    path = _sqlite_file_from_url(url.replace("+aiosqlite", ""))
    if not path:
        return

    with eng.connect() as conn:
        columns = conn.exec_driver_sql("PRAGMA table_info(material)").fetchall()
        column_names = {col[1] for col in columns} if columns else set()
        if columns and "company" in column_names:
            conn.exec_driver_sql(
                "UPDATE material SET category='other' WHERE category IS NULL OR category=''"
            )
        proj_cols = conn.exec_driver_sql("PRAGMA table_info(project)").fetchall()
        proj_names = {col[1] for col in proj_cols} if proj_cols else set()
        alters = []
        if proj_cols and "client_id" not in proj_names:
            alters.append("ALTER TABLE project ADD COLUMN client_id INTEGER")
        if proj_cols and "client_tax_id" not in proj_names:
            alters.append("ALTER TABLE project ADD COLUMN client_tax_id VARCHAR")
        if proj_cols and "client_registration" not in proj_names:
            alters.append("ALTER TABLE project ADD COLUMN client_registration VARCHAR")
        if proj_cols and "client_billing_address" not in proj_names:
            alters.append("ALTER TABLE project ADD COLUMN client_billing_address VARCHAR")
        for stmt in alters:
            conn.exec_driver_sql(stmt)
        if alters:
            conn.commit()


def create_db_and_tables() -> None:
    """Legacy single-database initialization."""
    if MULTITENANT_ENABLED or engine is None:
        return
    TENANT_METADATA.create_all(engine)
    _migrate_tenant_engine(engine)


def sqlite_url_from_path(path: Path) -> str:
    return "sqlite:///" + path.resolve().as_posix()


def provision_tenant_database(code: str) -> Path:
    """Create empty tenant SQLite with schema; return path."""
    path = tenant_db_path(code)
    path.parent.mkdir(parents=True, exist_ok=True)
    url = sqlite_url_from_path(path)
    eng = create_engine(
        url,
        echo=False,
        connect_args=sqlite_connect_args,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    TENANT_METADATA.create_all(eng)
    _migrate_tenant_engine(eng)
    eng.dispose(close=True)
    invalidate_tenant_engine(code)
    return path


def invalidate_tenant_engine(code: str) -> None:
    eng = _tenant_engines.pop(_normalize_code(code), None)
    if eng is not None:
        eng.dispose(close=True)


def refresh_tenant_after_restore(code: str) -> None:
    """Re-open tenant engine and apply SQLite migrations after file replace."""
    invalidate_tenant_engine(code)
    eng = get_tenant_engine(code)
    _migrate_tenant_engine(eng)


def get_tenant_engine(code: str) -> Engine:
    """Cached engine for tenant SQLite; validates registry row exists."""
    norm = _normalize_code(code)
    if norm in _tenant_engines:
        return _tenant_engines[norm]

    with Session(registry_engine) as session:
        row = session.exec(select(TenantRegistry).where(TenantRegistry.code == norm)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Firma (tenant) necunoscuta in registru.")

    path = tenant_db_path(norm)
    if not path.is_file():
        raise HTTPException(
            status_code=503,
            detail=f"Baza pentru firma '{norm}' nu este provisionata. Reporniti API-ul sau recreati firma.",
        )

    url = sqlite_url_from_path(path)
    eng = create_engine(
        url,
        echo=False,
        connect_args=sqlite_connect_args,
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    _tenant_engines[norm] = eng
    return eng


def normalize_tenant_code(code: str) -> str:
    return _normalize_code(code)


def ensure_registry_seed() -> None:
    """Central firm list (always used by /companies). Seeds defaults once."""
    create_registry_tables()
    with Session(registry_engine) as session:
        if session.exec(select(TenantRegistry)).first():
            return
        defaults = [
            ("freevoltsrl.ro", "Freevolt SRL", "Freevolt SRL"),
            ("energoteamconect.ro", "Energoteam Conect", "Energoteam Conect"),
        ]
        for code, name, legal in defaults:
            session.add(
                TenantRegistry(
                    code=code,
                    name=name,
                    legal_name=legal,
                )
            )
        session.commit()


def provision_missing_tenant_files() -> None:
    """Create SQLite files for each registry row when multitenant mode is on."""
    if not MULTITENANT_ENABLED:
        return
    with Session(registry_engine) as session:
        rows = session.exec(select(TenantRegistry)).all()
        for row in rows:
            p = tenant_db_path(row.code)
            if not p.is_file():
                provision_tenant_database(row.code)


def tenant_has_any_material(code: str) -> bool:
    eng = get_tenant_engine(code)
    from .models import Material

    with Session(eng) as session:
        return session.exec(select(Material)).first() is not None


def get_tenant_display_name(code: str) -> str:
    """Resolve short name for a firm code from the central registry."""
    norm = _normalize_code(code)
    with Session(registry_engine) as session:
        row = session.exec(select(TenantRegistry).where(TenantRegistry.code == norm)).first()
        return row.name if row else norm
