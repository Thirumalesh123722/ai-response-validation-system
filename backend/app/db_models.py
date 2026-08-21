"""
SQLAlchemy models for the multi-tenant, Postgres-backed data layer.

Every piece of data that belongs to a customer is scoped to an
Organization. Users belong to exactly one Organization. Evaluations
belong to both an Organization (for isolation) and the User who ran
them (for auditing).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, Boolean, ForeignKey, DateTime, Text, JSON, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _uuid():
    return str(uuid.uuid4())


def _now():
    return datetime.now(timezone.utc)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    plan = Column(String, nullable=False, default="free")  # free | pro | enterprise — for future billing
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    evaluations = relationship("Evaluation", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="admin")  # admin | member
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    organization = relationship("Organization", back_populates="users")


class RefreshToken(Base):
    """Stored so refresh tokens can be revoked (logout, security incident)
    rather than just relying on expiry."""
    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    organization_id = Column(UUID(as_uuid=False), ForeignKey("organizations.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)  # nullable: system/API-key-run evals
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False, index=True)

    mode = Column(String, nullable=False)  # 'single' | 'batch'
    batch_job_id = Column(String, nullable=True)
    system_name = Column(String, nullable=False, default="Unspecified")
    dataset_name = Column(String, nullable=True)

    question = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    reference_answer = Column(Text, nullable=True)

    relevance_score = Column(Float, nullable=False)
    accuracy_score = Column(Float, nullable=False)
    hallucination_score = Column(Float, nullable=False)
    completeness_score = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False)

    verdict_label = Column(String, nullable=False, index=True)
    verdict_reasoning = Column(Text, nullable=False)
    relevance_reasoning = Column(Text, nullable=False)
    accuracy_reasoning = Column(Text, nullable=False)
    hallucination_reasoning = Column(Text, nullable=False)
    completeness_reasoning = Column(Text, nullable=False)
    hallucination_flags = Column(JSON, nullable=False, default=list)

    model_used = Column(String, nullable=False)

    organization = relationship("Organization", back_populates="evaluations")

    __table_args__ = (
        Index("ix_eval_org_created", "organization_id", "created_at"),
        Index("ix_eval_org_verdict", "organization_id", "verdict_label"),
    )
