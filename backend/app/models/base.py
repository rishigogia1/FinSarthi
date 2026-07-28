"""
models/base.py — Shared SQLAlchemy DeclarativeBase.

All models in app/models/ inherit from this Base.
Alembic's env.py imports Base.metadata to detect schema changes.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
