"""
Job application management router
Handles CRUD operations for job applications
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import User, Application, Resume
from schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse, ApplicationStatus
from auth import get_current_active_user

router = APIRouter()


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application_data: ApplicationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new job application
    Validates resume ownership if resume_id is provided
    """
    try:
        # Validate resume ownership if provided
        if application_data.resume_id:
            resume = db.query(Resume).filter(
                Resume.resume_id == application_data.resume_id,
                Resume.user_id == current_user.user_id,
                Resume.is_active == True
            ).first()
            
            if not resume:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid resume ID or resume not found"
                )
        
        db_application = Application(
            user_id=current_user.user_id,
            resume_id=application_data.resume_id,
            job_title=application_data.job_title,
            company=application_data.company,
            status=application_data.status,
            job_description=application_data.job_description,
            application_url=application_data.application_url,
            notes=application_data.notes
        )
        
        db.add(db_application)
        db.commit()
        db.refresh(db_application)
        
        return ApplicationResponse.from_orm(db_application)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application creation failed: {str(e)}"
        )


@router.get("", response_model=List[ApplicationResponse])
async def get_user_applications(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[ApplicationStatus] = Query(None),
    company_filter: Optional[str] = Query(None)
):
    """
    Get all job applications for the current user
    Supports pagination and filtering by status and company
    """
    try:
        query = db.query(Application).filter(Application.user_id == current_user.user_id)
        
        if status_filter:
            query = query.filter(Application.status == status_filter.value)
        
        if company_filter:
            query = query.filter(Application.company.ilike(f"%{company_filter}%"))
        
        applications = query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
        
        return [ApplicationResponse.from_orm(app) for app in applications]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific job application by ID
    Ensures user can only access their own applications
    """
    try:
        application = db.query(Application).filter(
            Application.application_id == application_id,
            Application.user_id == current_user.user_id
        ).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        return ApplicationResponse.from_orm(application)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve application: {str(e)}"
        )


@router.put("/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: int,
    application_update: ApplicationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific job application
    Validates resume ownership if resume_id is being updated
    """
    try:
        application = db.query(Application).filter(
            Application.application_id == application_id,
            Application.user_id == current_user.user_id
        ).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        # Validate resume ownership if resume_id is being updated
        if application_update.resume_id is not None:
            if application_update.resume_id != 0:  # 0 means remove resume association
                resume = db.query(Resume).filter(
                    Resume.resume_id == application_update.resume_id,
                    Resume.user_id == current_user.user_id,
                    Resume.is_active == True
                ).first()
                
                if not resume:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid resume ID or resume not found"
                    )
            else:
                application_update.resume_id = None
        
        # Update fields if provided
        update_data = application_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)
        
        db.commit()
        db.refresh(application)
        
        return ApplicationResponse.from_orm(application)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application update failed: {str(e)}"
        )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a job application permanently
    """
    try:
        application = db.query(Application).filter(
            Application.application_id == application_id,
            Application.user_id == current_user.user_id
        ).first()
        
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Application not found"
            )
        
        db.delete(application)
        db.commit()
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Application deletion failed: {str(e)}"
        )


@router.get("/statistics/summary")
async def get_application_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get application statistics and analytics for the current user
    Provides insights into application patterns and success rates
    """
    try:
        applications = db.query(Application).filter(Application.user_id == current_user.user_id).all()
        
        if not applications:
            return {
                "total_applications": 0,
                "status_breakdown": {},
                "company_breakdown": {},
                "monthly_applications": {},
                "success_rate": 0.0
            }
        
        # Status breakdown
        status_counts = {}
        for app in applications:
            status = app.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Company breakdown (top 10)
        company_counts = {}
        for app in applications:
            company = app.company
            company_counts[company] = company_counts.get(company, 0) + 1
        
        top_companies = dict(sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Monthly breakdown (last 12 months)
        from collections import defaultdict
        monthly_counts = defaultdict(int)
        for app in applications:
            month_key = app.created_at.strftime("%Y-%m")
            monthly_counts[month_key] += 1
        
        # Success rate calculation (offers / total applications)
        offers = status_counts.get("offered", 0)
        success_rate = (offers / len(applications)) * 100 if applications else 0.0
        
        return {
            "total_applications": len(applications),
            "status_breakdown": status_counts,
            "company_breakdown": top_companies,
            "monthly_applications": dict(monthly_counts),
            "success_rate": round(success_rate, 2),
            "average_applications_per_month": round(len(applications) / 12, 2) if applications else 0
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve application statistics: {str(e)}"
        )
