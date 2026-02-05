import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    job_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_of_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    data_sources = relationship("DataSource", back_populates="user", cascade="all, delete-orphan")
    career_scores = relationship("CareerScore", back_populates="user", cascade="all, delete-orphan")
    action_recommendations = relationship("ActionRecommendation", back_populates="user", cascade="all, delete-orphan")
    score_histories = relationship("ScoreHistory", back_populates="user", cascade="all, delete-orphan")
