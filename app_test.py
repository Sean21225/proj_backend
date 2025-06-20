#!/usr/bin/env python3
"""
Comprehensive application test script
Tests all major functionality of the Job Application Management API
"""

import requests
import json
import time
from typing import Dict, Any

# API Base URL
BASE_URL = "http://localhost:5000"

def test_api_health():
    """Test API health check"""
    print("Testing API health...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ API health check passed")

def test_user_registration():
    """Test user registration"""
    print("Testing user registration...")
    user_data = {
        "username": f"testuser_{int(time.time())}",
        "email": f"test_{int(time.time())}@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/signup", json=user_data)
    assert response.status_code == 201
    
    user_info = response.json()
    assert user_info["username"] == user_data["username"]
    assert user_info["email"] == user_data["email"]
    assert "user_id" in user_info
    
    print("✅ User registration passed")
    return user_data, user_info

def test_user_login(user_data: Dict[str, str]):
    """Test user login"""
    print("Testing user login...")
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    print("✅ User login passed")
    return token_data["access_token"]

def get_auth_headers(token: str) -> Dict[str, str]:
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def test_user_profile(token: str):
    """Test user profile operations"""
    print("Testing user profile...")
    headers = get_auth_headers(token)
    
    # Get profile
    response = requests.get(f"{BASE_URL}/user/profile", headers=headers)
    assert response.status_code == 200
    
    profile = response.json()
    assert "username" in profile
    assert "email" in profile
    
    print("✅ User profile test passed")
    return profile

def test_resume_operations(token: str):
    """Test resume CRUD operations"""
    print("Testing resume operations...")
    headers = get_auth_headers(token)
    
    # Create resume
    resume_data = {
        "title": "Software Engineer Resume",
        "content": """
        John Doe
        Software Engineer
        
        EXPERIENCE:
        - Senior Software Engineer at TechCorp (2021-2024)
        - Built scalable web applications using Python and FastAPI
        - Led team of 5 developers
        
        SKILLS:
        - Python, FastAPI, PostgreSQL, Docker
        - AWS, Kubernetes, CI/CD
        - Team leadership, Agile methodologies
        
        EDUCATION:
        - M.S. Computer Science, Tech University (2019)
        """
    }
    
    response = requests.post(f"{BASE_URL}/resume", json=resume_data, headers=headers)
    assert response.status_code == 201
    
    resume = response.json()
    assert resume["title"] == resume_data["title"]
    assert "resume_id" in resume
    
    resume_id = resume["resume_id"]
    
    # Get resumes
    response = requests.get(f"{BASE_URL}/resume", headers=headers)
    assert response.status_code == 200
    resumes = response.json()
    assert len(resumes) >= 1
    
    # Get specific resume
    response = requests.get(f"{BASE_URL}/resume/{resume_id}", headers=headers)
    assert response.status_code == 200
    
    print("✅ Resume operations passed")
    return resume_id

def test_application_operations(token: str, resume_id: int):
    """Test job application CRUD operations"""
    print("Testing application operations...")
    headers = get_auth_headers(token)
    
    # Create application
    app_data = {
        "job_title": "Senior Python Developer",
        "company": "Tech Innovation Inc",
        "status": "applied",
        "job_description": "Looking for experienced Python developer...",
        "application_url": "https://techinnovations.com/jobs/123",
        "notes": "Applied through company website",
        "resume_id": resume_id
    }
    
    response = requests.post(f"{BASE_URL}/applications", json=app_data, headers=headers)
    assert response.status_code == 201
    
    application = response.json()
    assert application["job_title"] == app_data["job_title"]
    assert "application_id" in application
    
    app_id = application["application_id"]
    
    # Get applications
    response = requests.get(f"{BASE_URL}/applications", headers=headers)
    assert response.status_code == 200
    applications = response.json()
    assert len(applications) >= 1
    
    # Update application
    update_data = {"status": "interview", "notes": "Phone interview scheduled"}
    response = requests.put(f"{BASE_URL}/applications/{app_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    
    updated_app = response.json()
    assert updated_app["status"] == "interview"
    
    print("✅ Application operations passed")
    return app_id

def test_statistics(token: str):
    """Test statistics endpoints"""
    print("Testing statistics...")
    headers = get_auth_headers(token)
    
    # User stats
    response = requests.get(f"{BASE_URL}/user/stats", headers=headers)
    assert response.status_code == 200
    
    stats = response.json()
    assert "total_resumes" in stats
    assert "total_applications" in stats
    
    # Application statistics
    response = requests.get(f"{BASE_URL}/applications/statistics/summary", headers=headers)
    assert response.status_code == 200
    
    app_stats = response.json()
    assert "total_applications" in app_stats
    assert "status_breakdown" in app_stats
    
    print("✅ Statistics test passed")

def test_api_documentation():
    """Test API documentation endpoints"""
    print("Testing API documentation...")
    
    # Root endpoint
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    root_data = response.json()
    assert "Job Application Management API" in root_data["message"]
    
    # OpenAPI JSON
    response = requests.get(f"{BASE_URL}/openapi.json")
    assert response.status_code == 200
    openapi_data = response.json()
    assert "info" in openapi_data
    
    print("✅ API documentation test passed")

def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 Starting comprehensive API test...")
    print("=" * 50)
    
    try:
        # Test API availability
        test_api_health()
        
        # Test authentication flow
        user_data, user_info = test_user_registration()
        token = test_user_login(user_data)
        
        # Test user operations
        profile = test_user_profile(token)
        
        # Test resume operations
        resume_id = test_resume_operations(token)
        
        # Test application operations
        app_id = test_application_operations(token, resume_id)
        
        # Test statistics
        test_statistics(token)
        
        # Test documentation
        test_api_documentation()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed successfully!")
        print("\n📊 Test Summary:")
        print(f"   - User created: {user_info['username']}")
        print(f"   - Resume created: ID {resume_id}")
        print(f"   - Application created: ID {app_id}")
        print(f"   - API is fully functional")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    exit(0 if success else 1)