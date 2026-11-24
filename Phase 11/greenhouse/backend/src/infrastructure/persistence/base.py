"""Shared SQLAlchemy declarative base for infrastructure ORM models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
