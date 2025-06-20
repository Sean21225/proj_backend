"""
Database models for the Job Application Management system
Following SOLID principles with proper relationships
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hashed = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}', email='{self.email}')>"


class Resume(Base):
    """Resume model for storing user resume data"""
    __tablename__ = "resumes"

    resume_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    title = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="resumes")
    applications = relationship("Application", back_populates="resume")

    def __repr__(self):
        return f"<Resume(id={self.resume_id}, user_id={self.user_id}, title='{self.title}')>"


class Application(Base):
    """Application model for job application tracking"""
    __tablename__ = "applications"

    application_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.resume_id"), nullable=True)
    job_title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    status = Column(String(50), nullable=False, default="applied")  # applied, interview, rejected, offered
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    job_description = Column(Text, nullable=True)
    application_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="applications")
    resume = relationship("Resume", back_populates="applications")

    def __repr__(self):
        return f"<Application(id={self.application_id}, job_title='{self.job_title}', company='{self.company}', status='{self.status}')>"
