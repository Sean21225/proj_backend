"""
Unit tests for job application management functionality
Tests CRUD operations and statistics for job applications
"""

import pytest
from fastapi import status


class TestApplicationCreation:
    """Test job application creation functionality"""
    
    def test_create_application_success(self, client, auth_headers, test_application_data):
        """Test successful application creation"""
        response = client.post("/applications", json=test_application_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["job_title"] == test_application_data["job_title"]
        assert data["company"] == test_application_data["company"]
        assert data["status"] == test_application_data["status"]
        assert "application_id" in data
        assert "user_id" in data
    
    def test_create_application_with_resume(self, client, auth_headers, test_application_data, created_resume):
        """Test creating application with resume reference"""
        test_application_data["resume_id"] = created_resume.resume_id
        
        response = client.post("/applications", json=test_application_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["resume_id"] == created_resume.resume_id
    
    def test_create_application_invalid_resume(self, client, auth_headers, test_application_data):
        """Test creating application with invalid resume ID"""
        test_application_data["resume_id"] = 99999
        
        response = client.post("/applications", json=test_application_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid resume ID" in response.json()["detail"]
    
    def test_create_application_unauthorized(self, client, test_application_data):
        """Test application creation without authentication"""
        response = client.post("/applications", json=test_application_data)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_create_application_invalid_data(self, client, auth_headers):
        """Test application creation with invalid data"""
        invalid_data = {
            "job_title": "",  # Empty title
            "company": "",    # Empty company
            "status": "invalid_status"
        }
        
        response = client.post("/applications", json=invalid_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestApplicationRetrieval:
    """Test job application retrieval functionality"""
    
    def test_get_all_applications(self, client, auth_headers, created_application):
        """Test retrieving all user applications"""
        response = client.get("/applications", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["application_id"] == created_application.application_id
    
    def test_get_applications_with_pagination(self, client, auth_headers, created_application):
        """Test application retrieval with pagination"""
        response = client.get("/applications?skip=0&limit=5", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
    
    def test_get_applications_with_status_filter(self, client, auth_headers, created_application):
        """Test retrieving applications filtered by status"""
        response = client.get("/applications?status_filter=applied", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "applied"
        
        # Test with different status
        response = client.get("/applications?status_filter=interview", headers=auth_headers)
        assert len(response.json()) == 0
    
    def test_get_applications_with_company_filter(self, client, auth_headers, created_application):
        """Test retrieving applications filtered by company"""
        response = client.get("/applications?company_filter=Tech", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert "Tech" in data[0]["company"]
    
    def test_get_specific_application(self, client, auth_headers, created_application):
        """Test retrieving a specific application by ID"""
        response = client.get(f"/applications/{created_application.application_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["application_id"] == created_application.application_id
        assert data["job_title"] == created_application.job_title
    
    def test_get_nonexistent_application(self, client, auth_headers):
        """Test retrieving a non-existent application"""
        response = client.get("/applications/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Application not found" in response.json()["detail"]


class TestApplicationUpdate:
    """Test job application update functionality"""
    
    def test_update_application_status(self, client, auth_headers, created_application):
        """Test updating application status"""
        update_data = {"status": "interview"}
        
        response = client.put(f"/applications/{created_application.application_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "interview"
        assert data["application_id"] == created_application.application_id
    
    def test_update_application_notes(self, client, auth_headers, created_application):
        """Test updating application notes"""
        update_data = {"notes": "Updated notes with follow-up information"}
        
        response = client.put(f"/applications/{created_application.application_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["notes"] == "Updated notes with follow-up information"
    
    def test_update_application_resume_reference(self, client, auth_headers, created_application, created_resume):
        """Test updating application resume reference"""
        update_data = {"resume_id": created_resume.resume_id}
        
        response = client.put(f"/applications/{created_application.application_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["resume_id"] == created_resume.resume_id
    
    def test_remove_application_resume_reference(self, client, auth_headers, created_application):
        """Test removing resume reference from application"""
        update_data = {"resume_id": 0}  # 0 means remove association
        
        response = client.put(f"/applications/{created_application.application_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["resume_id"] is None
    
    def test_update_application_multiple_fields(self, client, auth_headers, created_application):
        """Test updating multiple application fields"""
        update_data = {
            "status": "offered",
            "notes": "Received job offer!",
            "application_url": "https://newurl.com/offer"
        }
        
        response = client.put(f"/applications/{created_application.application_id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "offered"
        assert data["notes"] == "Received job offer!"
        assert data["application_url"] == "https://newurl.com/offer"
    
    def test_update_nonexistent_application(self, client, auth_headers):
        """Test updating a non-existent application"""
        update_data = {"status": "interview"}
        
        response = client.put("/applications/99999", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestApplicationDeletion:
    """Test job application deletion functionality"""
    
    def test_delete_application(self, client, auth_headers, created_application, db_session):
        """Test permanent deletion of application"""
        application_id = created_application.application_id
        
        response = client.delete(f"/applications/{application_id}", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify application is permanently deleted
        from models import Application
        deleted_app = db_session.query(Application).filter(Application.application_id == application_id).first()
        assert deleted_app is None
    
    def test_delete_nonexistent_application(self, client, auth_headers):
        """Test deleting a non-existent application"""
        response = client.delete("/applications/99999", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestApplicationStatistics:
    """Test job application statistics functionality"""
    
    def test_get_statistics_no_data(self, client, auth_headers):
        """Test getting statistics with no applications"""
        response = client.get("/applications/statistics/summary", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_applications"] == 0
        assert data["status_breakdown"] == {}
        assert data["success_rate"] == 0.0
    
    def test_get_statistics_with_data(self, client, auth_headers, created_application):
        """Test getting statistics with existing applications"""
        response = client.get("/applications/statistics/summary", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_applications"] == 1
        assert "applied" in data["status_breakdown"]
        assert data["status_breakdown"]["applied"] == 1
        assert "company_breakdown" in data
        assert "monthly_applications" in data
    
    def test_get_statistics_multiple_applications(self, client, auth_headers, db_session, created_user):
        """Test statistics with multiple applications"""
        from models import Application
        
        # Create additional applications with different statuses
        applications = [
            Application(
                user_id=created_user.user_id,
                job_title="Backend Developer",
                company="Company A",
                status="interview"
            ),
            Application(
                user_id=created_user.user_id,
                job_title="Frontend Developer", 
                company="Company B",
                status="offered"
            ),
            Application(
                user_id=created_user.user_id,
                job_title="Full Stack Developer",
                company="Company A",
                status="rejected"
            )
        ]
        
        for app in applications:
            db_session.add(app)
        db_session.commit()
        
        response = client.get("/applications/statistics/summary", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_applications"] == 3
        assert "interview" in data["status_breakdown"]
        assert "offered" in data["status_breakdown"]
        assert "rejected" in data["status_breakdown"]
        assert data["success_rate"] > 0  # Should have some success rate due to "offered" status
