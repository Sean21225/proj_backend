"""
User management router
Handles user profile operations and user data management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import get_db
from models import User
from schemas import UserResponse, UserUpdate
from auth import get_current_active_user

router = APIRouter()


@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile information
    Returns user details excluding sensitive data
    """
    return UserResponse.from_orm(current_user)


@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information
    Allows updating username and email with validation
    """
    try:
        # Check if new username is already taken (if provided)
        if user_update.username and user_update.username != current_user.username:
            existing_user = db.query(User).filter(
                User.username == user_update.username,
                User.user_id != current_user.user_id
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            current_user.username = user_update.username
        
        # Check if new email is already taken (if provided)
        if user_update.email and user_update.email != current_user.email:
            existing_user = db.query(User).filter(
                User.email == user_update.email,
                User.user_id != current_user.user_id
            ).first()
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            current_user.email = user_update.email
        
        db.commit()
        db.refresh(current_user)
        
        return UserResponse.from_orm(current_user)
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile update failed due to data constraints"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.delete("/profile", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate current user's account
    Soft delete by setting is_active to False
    """
    try:
        current_user.is_active = False
        db.commit()
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account deactivation failed: {str(e)}"
        )


@router.get("/stats")
async def get_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics including resume and application counts
    Provides dashboard data for the user
    """
    try:
        # Count user's resumes
        resume_count = len([r for r in current_user.resumes if r.is_active])
        
        # Count user's applications by status
        applications = current_user.applications
        total_applications = len(applications)
        
        status_counts = {}
        for app in applications:
            status = app.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "total_resumes": resume_count,
            "total_applications": total_applications,
            "application_status_breakdown": status_counts,
            "account_created": current_user.created_at.isoformat(),
            "last_updated": current_user.updated_at.isoformat() if current_user.updated_at else None
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user statistics: {str(e)}"
        )
