"""Phase 6 persistence: saved strategy per location + zone thresholds as plain data."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from domain.automation.rule import StrategyRule
from domain.locations.entity import ZoneThresholds
from infrastructure.persistence.models import AutomationRuleRow, LocationRow, ZoneRow


class AutomationRuleRepository:

    def __init__(self, session: Session):
        self.session = session


    def get(self, location_id: UUID) -> StrategyRule | None:

        row = self._row(location_id)

        return self._to_domain(row) if row else None


    def upsert(self, location_id: UUID, strategy_key: str) -> StrategyRule:
        """Insert the rule, or update the existing one (location_id is unique)."""

        try:

            row = self._row(location_id)

            if row is None:
                row = AutomationRuleRow(
                    location_id=location_id,
                    strategy_key=strategy_key,
                    parameters={},
                )
                self.session.add(row)
            else:
                row.strategy_key = strategy_key
                row.updated_at = datetime.now(timezone.utc)

            self.session.commit()
            self.session.refresh(row)

            return self._to_domain(row)

        except Exception:

            self.session.rollback()
            raise


    def _row(self, location_id: UUID) -> AutomationRuleRow | None:

        return self.session.scalar(
            select(AutomationRuleRow).where(
                AutomationRuleRow.location_id == location_id
            )
        )


    def _to_domain(self, row: AutomationRuleRow) -> StrategyRule:

        return StrategyRule(
            location_id=row.location_id,
            strategy_key=row.strategy_key,
            parameters=dict(row.parameters or {}),
            updated_at=row.updated_at,
        )



class AutomationLocationRepository:
    """Reads locations and zone thresholds for automation. Returns plain data, not rows."""

    def __init__(self, session: Session):
        self.session = session


    def exists(self, location_id: UUID) -> bool:

        return self.session.get(LocationRow, location_id) is not None


    def list_zones(self, location_id: UUID) -> list[ZoneThresholds]:

        rows = self.session.scalars(
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name, ZoneRow.id)
        ).all()

        return [
            ZoneThresholds(
                zone_id=row.id,
                location_id=row.location_id,
                name=row.name,
                moisture_threshold_low=float(row.moisture_threshold_low),
                moisture_threshold_high=float(row.moisture_threshold_high),
            )
            for row in rows
        ]
