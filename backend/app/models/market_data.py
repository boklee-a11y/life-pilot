import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, BigInteger, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MarketData(Base):
    __tablename__ = "market_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_category: Mapped[str] = mapped_column(String(50), nullable=False)
    skill_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    demand_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_salary_min: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    avg_salary_max: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    years_range: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint("demand_level BETWEEN 1 AND 10", name="check_demand_level"),
    )
