"""
Unit tests for user management functionality
Tests user profile operations and user data management
"""

import pytest
from fastapi import status


class TestUserProfile:
    """Test user profile management"""
    
    def test_get_user_profile(self, client, auth_headers, created_user):
        """Test retrieving user profile"""
        response = client.get("/user/profile", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == created_user.user_id
        assert data["username"] == created_user.username
        assert data["email"] == created_user.email
        assert data["is_active"] is True
    
    def test_get_profile_unauthorized(self, client):
        """Test getting profile without authentication"""
        response = client.get("/user/profile")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_profile_invalid_token(self, client):
        """Test getting profile with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/user/profile", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserProfileUpdate:
    """Test user profile update functionality"""
    
    def test_update_username(self, client, auth_headers, created_user):
        """Test updating username"""
        update_data = {"username": "newusername"}
        
        response = client.put("/user/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "newusername"
        assert data["user_id"] == created_user.user_id
    
    def test_update_email(self, client, auth_headers, created_user):
        """Test updating email"""
        update_data = {"email": "newemail@example.com"}
        
        response = client.put("/user/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "newemail@example.com"
    
    def test_update_both_fields(self, client, auth_headers):
        """Test updating both username and email"""
        update_data = {
            "username": "updateduser",
            "email": "updated@example.com"
        }
        
        response = client.put("/user/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "updateduser"
        assert data["email"] == "updated@example.com"
    
    def test_update_to_existing_username(self, client, auth_headers, db_session, created_user):
        """Test updating to an existing username"""
        # Create another user
        from models import User
        from auth import auth_manager
        
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hashed=auth_manager.get_password_hash("password123")
        )
        db_session.add(other_user)
        db_session.commit()
        
        update_data = {"username": "otheruser"}
        
        response = client.put("/user/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already taken" in response.json()["detail"]
    
    def test_update_to_existing_email(self, client, auth_headers, db_session):
        """Test updating to an existing email"""
        # Create another user
        from models import User
        from auth import auth_manager
        
        other_user = User(
            username="otheruser",
            email="other@example.com",
            password_hashed=auth_manager.get_password_hash("password123")
        )
        db_session.add(other_user)
        db_session.commit()
        
        update_data = {"email": "other@example.com"}
        
        response = client.put("/user/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_update_invalid_email(self, client, auth_headers):
        """Test updating with invalid email format"""
        update_data = {"email": "invalid-email"}
        
        response = client.put("/user/profile", json=update_data, headers=auth_headers)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserAccountDeactivation:
    """Test user account deactivation"""
    
    def test_deactivate_account(self, client, auth_headers, created_user, db_session):
        """Test account deactivation"""
        response = client.delete("/user/profile", headers=auth_headers)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify user is deactivated
        db_session.refresh(created_user)
        assert created_user.is_active is False
    
    def test_deactivate_unauthorized(self, client):
        """Test account deactivation without authentication"""
        response = client.delete("/user/profile")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestUserStatistics:
    """Test user statistics functionality"""
    
    def test_get_user_stats_no_data(self, client, auth_headers, created_user):
        """Test getting user stats with no resumes or applications"""
        response = client.get("/user/stats", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["user_id"] == created_user.user_id
        assert data["username"] == created_user.username
        assert data["total_resumes"] == 0
        assert data["total_applications"] == 0
        assert data["application_status_breakdown"] == {}
    
    def test_get_user_stats_with_data(self, client, auth_headers, created_user, created_resume, created_application):
        """Test getting user stats with existing data"""
        response = client.get("/user/stats", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total_resumes"] == 1
        assert data["total_applications"] == 1
        assert "applied" in data["application_status_breakdown"]
        assert data["application_status_breakdown"]["applied"] == 1
    
    def test_get_stats_unauthorized(self, client):
        """Test getting stats without authentication"""
        response = client.get("/user/stats")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
