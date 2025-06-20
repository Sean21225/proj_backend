"""
Unit tests for authentication functionality
Tests user registration, login, and token management
"""

import pytest
from fastapi import status
from auth import auth_manager


class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_successful_signup(self, client, test_user_data):
        """Test successful user registration"""
        response = client.post("/auth/signup", json=test_user_data)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["username"] == test_user_data["username"]
        assert data["email"] == test_user_data["email"]
        assert "user_id" in data
        assert data["is_active"] is True
    
    def test_duplicate_username_signup(self, client, test_user_data, created_user):
        """Test registration with existing username"""
        response = client.post("/auth/signup", json=test_user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Username already registered" in response.json()["detail"]
    
    def test_duplicate_email_signup(self, client, test_user_data, created_user):
        """Test registration with existing email"""
        new_user_data = test_user_data.copy()
        new_user_data["username"] = "newuser"
        
        response = client.post("/auth/signup", json=new_user_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Email already registered" in response.json()["detail"]
    
    def test_invalid_email_signup(self, client, test_user_data):
        """Test registration with invalid email"""
        test_user_data["email"] = "invalid-email"
        
        response = client.post("/auth/signup", json=test_user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_short_password_signup(self, client, test_user_data):
        """Test registration with short password"""
        test_user_data["password"] = "short"
        
        response = client.post("/auth/signup", json=test_user_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUserLogin:
    """Test user login functionality"""
    
    def test_successful_login(self, client, test_user_data, created_user):
        """Test successful user login"""
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == created_user.user_id
        assert data["username"] == created_user.username
    
    def test_invalid_username_login(self, client, test_user_data):
        """Test login with non-existent username"""
        login_data = {
            "username": "nonexistent",
            "password": test_user_data["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_invalid_password_login(self, client, test_user_data, created_user):
        """Test login with incorrect password"""
        login_data = {
            "username": test_user_data["username"],
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_inactive_user_login(self, client, test_user_data, created_user, db_session):
        """Test login with deactivated user"""
        # Deactivate user
        created_user.is_active = False
        db_session.commit()
        
        login_data = {
            "username": test_user_data["username"],
            "password": test_user_data["password"]
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Account is deactivated" in response.json()["detail"]


class TestTokenManagement:
    """Test JWT token management"""
    
    def test_token_refresh(self, client, auth_headers):
        """Test token refresh functionality"""
        response = client.post("/auth/refresh", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_invalid_token_refresh(self, client):
        """Test token refresh with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/auth/refresh", headers=headers)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_missing_token_refresh(self, client):
        """Test token refresh without token"""
        response = client.post("/auth/refresh")
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestPasswordHashing:
    """Test password hashing utilities"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "testpassword123"
        hashed = auth_manager.get_password_hash(password)
        
        assert hashed != password
        assert auth_manager.verify_password(password, hashed) is True
        assert auth_manager.verify_password("wrongpassword", hashed) is False
    
    def test_token_creation_and_verification(self):
        """Test JWT token creation and verification"""
        data = {"sub": "testuser", "user_id": 1}
        token = auth_manager.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        
        token_data = auth_manager.verify_token(token)
        assert token_data.username == "testuser"
        assert token_data.user_id == 1
