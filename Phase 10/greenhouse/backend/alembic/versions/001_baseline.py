"""Baseline revision.

Creates no business tables. It exists only to prove that the migration
toolchain runs against PostgreSQL. Phase 2 adds the first real table
(`devices`) on top of this baseline.

Revision ID: 001
Revises:
Create Date: 2026-09-05
"""

from collections.abc import Sequence

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Baseline: intentionally empty."""


def downgrade() -> None:
    """Baseline: nothing to undo."""
