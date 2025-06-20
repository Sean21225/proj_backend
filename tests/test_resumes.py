"""
Unit tests for resume management functionality
Tests CRUD operations for user resumes
"""

import pytest
from fastapi import status


class TestResumeCreation:
    """Test resume creation functionality"""
    
    def test_create_resume_success(self, client, auth_headers, test_resume_data):
        """Test successful resume creation"""
        response = client.post("/resume", json=test_resume_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == test_resume_data["title"]
        assert data["content"] == test_resume_data["content"]
        assert "resume_id" in data
        assert "user_id" in data
        assert data["is_active"] is True
    
    def test_create_resume_unauthorized(self, client, test_resume_data):
        """Test resume creation without authentication"""
        response = client.post("/resume", json=test_resume_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_resume_invalid_data(self, client, auth_headers):
        """Test resume creation with invalid data"""
        invalid_data = {
            "title": "",  # Empty title
            "content": "abc"  # Too short content
        }
        
        response = client.post("/resume", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_create_resume_missing_fields(self, client, auth_headers):
        """Test resume creation with missing fields"""
        incomplete_data = {"title": "Test Resume"}  # Missing content
        
        response = client.post("/resume", json=incomplete_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestResumeRetrieval:
    """Test resume retrieval functionality"""
    
    def test_get_all_resumes(self, client, auth_headers, created_resume):
        """Test retrieving all user resumes"""
        response = client.get("/resume", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["resume_id"] == created_resume.resume_id
    
    def test_get_resumes_with_pagination(self, client, auth_headers, created_resume):
        """Test resume retrieval with pagination"""
        response = client.get("/resume?skip=0&limit=5", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_resumes_active_only(self, client, auth_headers, created_resume, db_session):
        """Test retrieving only active resumes"""
        # Deactivate the resume
        created_resume.is_active = False
        db_session.commit()
        
        response = client.get("/resume?active_only=true", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0
        
        # Test getting all resumes including inactive
        response = client.get("/resume?active_only=false", headers=auth_headers)
        assert len(response.json()) == 1
    
    def test_get_specific_resume(self, client, auth_headers, created_resume):
        """Test retrieving a specific resume by ID"""
        response = client.get(f"/resume/{created_resume.resume_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["resume_id"] == created_resume.resume_id
        assert data["title"] == created_resume.title
    
    def test_get_nonexistent_resume(self, client, auth_headers):
        """Test retrieving a non-existent resume"""
        response = client.get("/resume/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Resume not found" in response.json()["detail"]
    
    def test_get_other_user_resume(self, client, auth_headers, db_session):
        """Test retrieving another user's resume"""
        # Create another user and resume
        from models import User, Resume
        from auth import auth_manager
        
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hashed=auth_manager.get_password_hash("password123")
        )
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)
        
        other_resume = Resume(
            user_id=other_user.user_id,
            title="Other User Resume",
            content="Other user's resume content"
        )
        db_session.add(other_resume)
        db_session.commit()
        
        response = client.get(f"/resume/{other_resume.resume_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestResumeUpdate:
    """Test resume update functionality"""
    
    def test_update_resume_title(self, client, auth_headers, created_resume):
        """Test updating resume title"""
        update_data = {"title": "Updated Resume Title"}
        
        response = client.put(f"/resume/{created_resume.resume_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Resume Title"
        assert data["resume_id"] == created_resume.resume_id
    
    def test_update_resume_content(self, client, auth_headers, created_resume):
        """Test updating resume content"""
        update_data = {"content": "Updated resume content with more details"}
        
        response = client.put(f"/resume/{created_resume.resume_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["content"] == "Updated resume content with more details"
    
    def test_update_resume_both_fields(self, client, auth_headers, created_resume):
        """Test updating both title and content"""
        update_data = {
            "title": "Completely New Title",
            "content": "Completely new content for the resume"
        }
        
        response = client.put(f"/resume/{created_resume.resume_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Completely New Title"
        assert data["content"] == "Completely new content for the resume"
    
    def test_update_nonexistent_resume(self, client, auth_headers):
        """Test updating a non-existent resume"""
        update_data = {"title": "New Title"}
        
        response = client.put("/resume/99999", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestResumeDeletion:
    """Test resume deletion functionality"""
    
    def test_soft_delete_resume(self, client, auth_headers, created_resume, db_session):
        """Test soft deletion of resume"""
        response = client.delete(f"/resume/{created_resume.resume_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify resume is soft deleted
        db_session.refresh(created_resume)
        assert created_resume.is_active is False
    
    def test_permanent_delete_resume(self, client, auth_headers, created_resume, db_session):
        """Test permanent deletion of resume"""
        resume_id = created_resume.resume_id
        
        response = client.delete(f"/resume/{resume_id}?permanent=true", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify resume is permanently deleted
        from models import Resume
        deleted_resume = db_session.query(Resume).filter(Resume.resume_id == resume_id).first()
        assert deleted_resume is None
    
    def test_restore_resume(self, client, auth_headers, created_resume, db_session):
        """Test restoring a soft-deleted resume"""
        # First soft delete the resume
        created_resume.is_active = False
        db_session.commit()
        
        response = client.post(f"/resume/{created_resume.resume_id}/restore", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is True
        
        # Verify in database
        db_session.refresh(created_resume)
        assert created_resume.is_active is True
    
    def test_restore_active_resume(self, client, auth_headers, created_resume):
        """Test restoring an already active resume"""
        response = client.post(f"/resume/{created_resume.resume_id}/restore", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Inactive resume not found" in response.json()["detail"]
    
    def test_delete_nonexistent_resume(self, client, auth_headers):
        """Test deleting a non-existent resume"""
        response = client.delete("/resume/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
