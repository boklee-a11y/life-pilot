import uuid
from datetime import datetime, timezone

from sqlalchemy import Numeric, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CareerScore(Base):
    __tablename__ = "career_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    expertise_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    influence_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    consistency_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    marketability_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    potential_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    total_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    estimated_salary_min: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    estimated_salary_max: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    analysis_accuracy: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    ai_insights: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    scored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    user = relationship("User", back_populates="career_scores")
    action_recommendations = relationship("ActionRecommendation", back_populates="career_score")
    score_histories = relationship("ScoreHistory", back_populates="career_score")
