import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Text, Numeric, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ActionRecommendation(Base):
    __tablename__ = "action_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    score_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_scores.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    target_area: Mapped[str | None] = mapped_column(String(20), nullable=True)
    difficulty: Mapped[str | None] = mapped_column(String(10), nullable=True)
    estimated_duration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[list | None] = mapped_column(ARRAY(Text), nullable=True)
    cta_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cta_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_bookmarked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="action_recommendations")
    career_score = relationship("CareerScore", back_populates="action_recommendations")
