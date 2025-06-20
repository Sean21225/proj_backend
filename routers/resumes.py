"""
Resume management router
Handles CRUD operations for user resumes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import User, Resume
from schemas import ResumeCreate, ResumeUpdate, ResumeResponse
from auth import get_current_active_user

router = APIRouter()


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    resume_data: ResumeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new resume for the current user
    Validates resume data and stores in database
    """
    try:
        db_resume = Resume(
            user_id=current_user.user_id,
            title=resume_data.title,
            content=resume_data.content
        )
        
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        return ResumeResponse.from_orm(db_resume)
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume creation failed: {str(e)}"
        )


@router.get("", response_model=List[ResumeResponse])
async def get_user_resumes(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    active_only: bool = Query(True)
):
    """
    Get all resumes for the current user
    Supports pagination and filtering
    """
    try:
        query = db.query(Resume).filter(Resume.user_id == current_user.user_id)
        
        if active_only:
            query = query.filter(Resume.is_active == True)
        
        resumes = query.order_by(Resume.created_at.desc()).offset(skip).limit(limit).all()
        
        return [ResumeResponse.from_orm(resume) for resume in resumes]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resumes: {str(e)}"
        )


@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific resume by ID
    Ensures user can only access their own resumes
    """
    try:
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        return ResumeResponse.from_orm(resume)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resume: {str(e)}"
        )


@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: int,
    resume_update: ResumeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific resume
    Only allows updating title and content
    """
    try:
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        # Update fields if provided
        if resume_update.title is not None:
            resume.title = resume_update.title
        
        if resume_update.content is not None:
            resume.content = resume_update.content
        
        db.commit()
        db.refresh(resume)
        
        return ResumeResponse.from_orm(resume)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume update failed: {str(e)}"
        )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    permanent: bool = Query(False, description="Permanently delete resume")
):
    """
    Delete a resume (soft delete by default)
    Can permanently delete if permanent=True
    """
    try:
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        if permanent:
            # Permanent deletion
            db.delete(resume)
        else:
            # Soft deletion
            resume.is_active = False
        
        db.commit()
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume deletion failed: {str(e)}"
        )


@router.post("/{resume_id}/restore", response_model=ResumeResponse)
async def restore_resume(
    resume_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted resume
    Sets is_active back to True
    """
    try:
        resume = db.query(Resume).filter(
            Resume.resume_id == resume_id,
            Resume.user_id == current_user.user_id,
            Resume.is_active == False  # Only restore inactive resumes
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inactive resume not found"
            )
        
        resume.is_active = True
        db.commit()
        db.refresh(resume)
        
        return ResumeResponse.from_orm(resume)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume restoration failed: {str(e)}"
        )
