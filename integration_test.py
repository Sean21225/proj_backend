"""
Integration tests for the complete job application management system
Tests end-to-end workflows and service integrations
"""

import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from database import get_db, Base
from auth import auth_manager

# Test database URL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/test_jobapp_integration")

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def get_test_db():
    """Override database dependency for integration tests"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = get_test_db


class TestCompleteUserWorkflow:
    """Test complete user workflow from registration to job application management"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database"""
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test database"""
        Base.metadata.drop_all(bind=test_engine)
    
    def test_complete_user_journey(self):
        """Test complete user journey: signup -> login -> create resume -> create application -> manage data"""
        
        # Step 1: User registration
        user_data = {
            "username": "integrationuser",
            "email": "integration@example.com",
            "password": "integrationpass123"
        }
        
        signup_response = self.client.post("/auth/signup", json=user_data)
        assert signup_response.status_code == 201
        user_info = signup_response.json()
        user_id = user_info["user_id"]
        
        # Step 2: User login
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        login_response = self.client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        token_data = login_response.json()
        auth_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        
        # Step 3: Get user profile
        profile_response = self.client.get("/user/profile", headers=auth_headers)
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["username"] == user_data["username"]
        
        # Step 4: Create a resume
        resume_data = {
            "title": "Senior Software Engineer Resume",
            "content": """
            John Doe
            Senior Software Engineer
            
            EXPERIENCE:
            - Lead Software Engineer at TechCorp (2021-2024)
            - Built scalable microservices using Python and FastAPI
            - Managed team of 6 developers
            
            SKILLS:
            - Python, FastAPI, PostgreSQL, Docker
            - AWS, Kubernetes, CI/CD
            - Team leadership, Agile methodologies
            
            EDUCATION:
            - M.S. Computer Science, Tech University (2019)
            - B.S. Computer Science, State University (2017)
            """
        }
        
        resume_response = self.client.post("/resume", json=resume_data, headers=auth_headers)
        assert resume_response.status_code == 201
        resume_info = resume_response.json()
        resume_id = resume_info["resume_id"]
        
        # Step 5: Create job applications
        applications_data = [
            {
                "job_title": "Senior Python Developer",
                "company": "Tech Innovations Inc",
                "status": "applied",
                "job_description": "Looking for experienced Python developer...",
                "application_url": "https://techinnovations.com/jobs/123",
                "notes": "Applied through company website",
                "resume_id": resume_id
            },
            {
                "job_title": "Lead Backend Engineer",
                "company": "StartupXYZ",
                "status": "interview",
                "job_description": "Lead our backend development team...",
                "application_url": "https://startupxyz.com/careers/456",
                "notes": "Phone interview scheduled for next week",
                "resume_id": resume_id
            },
            {
                "job_title": "Software Architect",
                "company": "Enterprise Solutions",
                "status": "offered",
                "job_description": "Design and implement enterprise software...",
                "notes": "Received offer! Salary: $150k",
                "resume_id": resume_id
            }
        ]
        
        application_ids = []
        for app_data in applications_data:
            app_response = self.client.post("/applications", json=app_data, headers=auth_headers)
            assert app_response.status_code == 201
            application_ids.append(app_response.json()["application_id"])
        
        # Step 6: Get all applications
        apps_response = self.client.get("/applications", headers=auth_headers)
        assert apps_response.status_code == 200
        apps_list = apps_response.json()
        assert len(apps_list) == 3
        
        # Step 7: Update application status
        update_data = {"status": "rejected", "notes": "Position filled internally"}
        update_response = self.client.put(
            f"/applications/{application_ids[0]}", 
            json=update_data, 
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "rejected"
        
        # Step 8: Get application statistics
        stats_response = self.client.get("/applications/statistics/summary", headers=auth_headers)
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert stats_data["total_applications"] == 3
        assert "rejected" in stats_data["status_breakdown"]
        assert "interview" in stats_data["status_breakdown"]
        assert "offered" in stats_data["status_breakdown"]
        assert stats_data["success_rate"] > 0  # Should have success due to "offered" status
        
        # Step 9: Get user statistics
        user_stats_response = self.client.get("/user/stats", headers=auth_headers)
        assert user_stats_response.status_code == 200
        user_stats = user_stats_response.json()
        assert user_stats["total_resumes"] == 1
        assert user_stats["total_applications"] == 3
        
        # Step 10: Update resume
        resume_update = {"title": "Updated Senior Software Engineer Resume"}
        resume_update_response = self.client.put(
            f"/resume/{resume_id}", 
            json=resume_update, 
            headers=auth_headers
        )
        assert resume_update_response.status_code == 200
        assert resume_update_response.json()["title"] == resume_update["title"]
        
        # Step 11: Filter applications
        filtered_response = self.client.get("/applications?status_filter=offered", headers=auth_headers)
        assert filtered_response.status_code == 200
        filtered_apps = filtered_response.json()
        assert len(filtered_apps) == 1
        assert filtered_apps[0]["status"] == "offered"
        
        # Step 12: Update user profile
        profile_update = {"email": "newemail@example.com"}
        profile_update_response = self.client.put("/user/profile", json=profile_update, headers=auth_headers)
        assert profile_update_response.status_code == 200
        assert profile_update_response.json()["email"] == "newemail@example.com"
        
        # Step 13: Test token refresh
        refresh_response = self.client.post("/auth/refresh", headers=auth_headers)
        assert refresh_response.status_code == 200
        new_token_data = refresh_response.json()
        assert "access_token" in new_token_data
        
        print("✅ Complete user workflow integration test passed!")


class TestAPIEndpointsIntegration:
    """Test API endpoints integration and error handling"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database"""
        Base.metadata.create_all(bind=test_engine)
        cls.client = TestClient(app)
    
    def test_api_health_and_docs(self):
        """Test API health check and documentation endpoints"""
        # Health check
        health_response = self.client.get("/health")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
        
        # Root endpoint
        root_response = self.client.get("/")
        assert root_response.status_code == 200
        assert "Job Application Management API" in root_response.json()["message"]
        
        # OpenAPI documentation
        docs_response = self.client.get("/docs")
        assert docs_response.status_code == 200
        
        # OpenAPI JSON
        openapi_response = self.client.get("/openapi.json")
        assert openapi_response.status_code == 200
        openapi_data = openapi_response.json()
        assert openapi_data["info"]["title"] == "Job Application Management API"
        
        print("✅ API endpoints integration test passed!")
    
    def test_authentication_flow_edge_cases(self):
        """Test authentication edge cases and error scenarios"""
        
        # Test duplicate user registration
        user_data = {
            "username": "duplicateuser",
            "email": "duplicate@example.com", 
            "password": "password123"
        }
        
        # First registration should succeed
        first_signup = self.client.post("/auth/signup", json=user_data)
        assert first_signup.status_code == 201
        
        # Second registration with same username should fail
        second_signup = self.client.post("/auth/signup", json=user_data)
        assert second_signup.status_code == 400
        assert "Username already registered" in second_signup.json()["detail"]
        
        # Registration with same email but different username should fail
        user_data_2 = {
            "username": "differentuser",
            "email": "duplicate@example.com",
            "password": "password123"
        }
        third_signup = self.client.post("/auth/signup", json=user_data_2)
        assert third_signup.status_code == 400
        assert "Email already registered" in third_signup.json()["detail"]
        
        # Test login with wrong credentials
        wrong_login = {
            "username": "duplicateuser",
            "password": "wrongpassword"
        }
        login_response = self.client.post("/auth/login", json=wrong_login)
        assert login_response.status_code == 401
        
        # Test accessing protected routes without token
        no_auth_response = self.client.get("/user/profile")
        assert no_auth_response.status_code == 403
        
        # Test with invalid token
        invalid_auth_headers = {"Authorization": "Bearer invalid_token"}
        invalid_auth_response = self.client.get("/user/profile", headers=invalid_auth_headers)
        assert invalid_auth_response.status_code == 401
        
        print("✅ Authentication flow edge cases test passed!")
    
    def test_data_validation_and_constraints(self):
        """Test data validation and database constraints"""
        
        # Create user for testing
        user_data = {
            "username": "validationuser",
            "email": "validation@example.com",
            "password": "password123"
        }
        signup_response = self.client.post("/auth/signup", json=user_data)
        assert signup_response.status_code == 201
        
        # Login to get token
        login_response = self.client.post("/auth/login", json={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        auth_headers = {"Authorization": f"Bearer {login_response.json()['access_token']}"}
        
        # Test invalid resume data
        invalid_resume = {
            "title": "",  # Empty title
            "content": "abc"  # Too short
        }
        resume_response = self.client.post("/resume", json=invalid_resume, headers=auth_headers)
        assert resume_response.status_code == 422
        
        # Test invalid application data
        invalid_application = {
            "job_title": "",  # Empty title
            "company": "",    # Empty company
            "status": "invalid_status"  # Invalid enum value
        }
        app_response = self.client.post("/applications", json=invalid_application, headers=auth_headers)
        assert app_response.status_code == 422
        
        # Test invalid email update
        invalid_email_update = {"email": "not-an-email"}
        email_response = self.client.put("/user/profile", json=invalid_email_update, headers=auth_headers)
        assert email_response.status_code == 422
        
        print("✅ Data validation and constraints test passed!")


def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting integration tests...")
    
    try:
        # Test complete workflow
        workflow_test = TestCompleteUserWorkflow()
        workflow_test.setup_class()
        workflow_test.test_complete_user_journey()
        workflow_test.teardown_class()
        
        # Test API integration
        api_test = TestAPIEndpointsIntegration()
        api_test.setup_class()
        api_test.test_api_health_and_docs()
        api_test.test_authentication_flow_edge_cases()
        api_test.test_data_validation_and_constraints()
        
        print("🎉 All integration tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Integration tests failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
