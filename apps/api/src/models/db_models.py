"""
SQLAlchemy ORM models for user progress, lab completions,
incident post-mortems, and technology mastery tracking.
"""

import time
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, default="sre-engineer")
    created_at = Column(Float, default=time.time)

    lab_attempts = relationship("LabAttempt", back_populates="user")
    incident_attempts = relationship("IncidentAttempt", back_populates="user")
    assessment_attempts = relationship("AssessmentAttempt", back_populates="user")


class LabAttempt(Base):
    __tablename__ = "lab_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    lab_id = Column(String(100), index=True)
    track = Column(String(50), index=True)
    status = Column(String(20), default="started")  # started, passed, partial, failed
    score = Column(Integer, default=0)
    max_score = Column(Integer, default=100)
    hints_used = Column(Integer, default=0)
    validation_report = Column(JSON, nullable=True)
    started_at = Column(Float, default=time.time)
    completed_at = Column(Float, nullable=True)

    user = relationship("User", back_populates="lab_attempts")


class IncidentAttempt(Base):
    __tablename__ = "incident_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    incident_id = Column(String(100), index=True)
    severity = Column(String(20))
    detection_score = Column(Integer, default=0)
    investigation_score = Column(Integer, default=0)
    root_cause_score = Column(Integer, default=0)
    fix_score = Column(Integer, default=0)
    verification_score = Column(Integer, default=0)
    prevention_score = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    feedback = Column(JSON, nullable=True)
    started_at = Column(Float, default=time.time)
    completed_at = Column(Float, nullable=True)

    user = relationship("User", back_populates="incident_attempts")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    track = Column(String(50), index=True)
    score_percentage = Column(Float, default=0.0)
    correct_count = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    completed_at = Column(Float, default=time.time)

    user = relationship("User", back_populates="assessment_attempts")
