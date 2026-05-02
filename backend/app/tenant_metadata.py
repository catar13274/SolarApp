"""Separate SQLAlchemy MetaData for tenant DBs vs central registry."""

from sqlalchemy import MetaData

TENANT_METADATA = MetaData()
REGISTRY_METADATA = MetaData()
