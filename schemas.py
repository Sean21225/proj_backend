"""
Pydantic schemas for request/response validation
Ensuring type safety and data validation
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ApplicationStatus(str, Enum):
    """Enum for application status values"""
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFERED = "offered"


# User schemas
class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user creation"""
    password: str = Field(..., min_length=8, max_length=128)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class UserUpdate(BaseModel):
    """Schema for user profile updates"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """Schema for user response data"""
    user_id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str


# Resume schemas
class ResumeBase(BaseModel):
    """Base resume schema"""
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10)


class ResumeCreate(ResumeBase):
    """Schema for resume creation"""
    pass


class ResumeUpdate(BaseModel):
    """Schema for resume updates"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=10)


class ResumeResponse(ResumeBase):
    """Schema for resume response data"""
    resume_id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


# Application schemas
class ApplicationBase(BaseModel):
    """Base application schema"""
    job_title: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., min_length=1, max_length=200)
    status: ApplicationStatus = ApplicationStatus.APPLIED
    job_description: Optional[str] = None
    application_url: Optional[str] = None
    notes: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    """Schema for application creation"""
    resume_id: Optional[int] = None


class ApplicationUpdate(BaseModel):
    """Schema for application updates"""
    job_title: Optional[str] = Field(None, min_length=1, max_length=200)
    company: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[ApplicationStatus] = None
    job_description: Optional[str] = None
    application_url: Optional[str] = None
    notes: Optional[str] = None
    resume_id: Optional[int] = None


class ApplicationResponse(ApplicationBase):
    """Schema for application response data"""
    application_id: int
    user_id: int
    resume_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Authentication schemas
class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[int] = None
    username: Optional[str] = None


# External service schemas
class ResumeOptimizationRequest(BaseModel):
    """Schema for resume optimization service request"""
    resume_content: str
    job_description: Optional[str] = None
    optimization_type: str = "general"


class ResumeOptimizationResponse(BaseModel):
    """Schema for resume optimization service response"""
    optimized_content: str
    suggestions: List[str]
    score: Optional[float] = None


class LinkedInJobRequest(BaseModel):
    """Schema for LinkedIn job scraping request"""
    keywords: str
    location: Optional[str] = None
    experience_level: Optional[str] = None
    limit: int = Field(10, ge=1, le=50)


class LinkedInJobResponse(BaseModel):
    """Schema for LinkedIn job data"""
    title: str
    company: str
    location: str
    description: str
    url: str
    posted_date: Optional[str] = None


class LinkedInCompanyRequest(BaseModel):
    """Schema for LinkedIn company scraping request"""
    company_name: str


class LinkedInCompanyResponse(BaseModel):
    """Schema for LinkedIn company data"""
    name: str
    industry: str
    size: Optional[str] = None
    description: str
    website: Optional[str] = None
    headquarters: Optional[str] = None


# API Response schemas
class APIResponse(BaseModel):
    """Generic API response schema"""
    success: bool
    message: str
    data: Optional[dict] = None


class ListResponse(BaseModel):
    """Schema for paginated list responses"""
    items: List[dict]
    total: int
    page: int = 1
    per_page: int = 10
    has_next: bool = False
    has_prev: bool = False
