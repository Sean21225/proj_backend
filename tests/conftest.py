"""
Pytest configuration and fixtures for testing
Provides database setup and common test utilities
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from main import app
from database import get_db, Base
from auth import auth_manager
from models import User, Resume, Application

# Test database URL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://test:test@localhost:5432/test_jobapp")

# Create test engine
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create test database session"""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """Test user data fixture"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def created_user(db_session, test_user_data):
    """Create a test user in the database"""
    hashed_password = auth_manager.get_password_hash(test_user_data["password"])
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        password_hashed=hashed_password
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(created_user):
    """Generate authentication headers for test requests"""
    token = auth_manager.create_access_token(
        data={"sub": created_user.username, "user_id": created_user.user_id}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_resume_data():
    """Test resume data fixture"""
    return {
        "title": "Software Engineer Resume",
        "content": """
        John Doe
        Software Engineer
        
        EXPERIENCE:
        - Senior Software Engineer at Tech Corp (2020-2023)
        - Developed scalable web applications using Python and React
        - Led a team of 5 developers
        
        SKILLS:
        - Python, JavaScript, React, FastAPI
        - PostgreSQL, Docker, AWS
        - Agile development, team leadership
        
        EDUCATION:
        - Bachelor of Science in Computer Science
        - University of Technology (2016-2020)
        """
    }


@pytest.fixture
def created_resume(db_session, created_user, test_resume_data):
    """Create a test resume in the database"""
    resume = Resume(
        user_id=created_user.user_id,
        title=test_resume_data["title"],
        content=test_resume_data["content"]
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)
    return resume


@pytest.fixture
def test_application_data():
    """Test application data fixture"""
    return {
        "job_title": "Senior Python Developer",
        "company": "Tech Innovation Inc",
        "status": "applied",
        "job_description": "We are looking for an experienced Python developer...",
        "application_url": "https://example.com/jobs/123",
        "notes": "Applied through company website"
    }


@pytest.fixture
def created_application(db_session, created_user, created_resume, test_application_data):
    """Create a test application in the database"""
    application = Application(
        user_id=created_user.user_id,
        resume_id=created_resume.resume_id,
        job_title=test_application_data["job_title"],
        company=test_application_data["company"],
        status=test_application_data["status"],
        job_description=test_application_data["job_description"],
        application_url=test_application_data["application_url"],
        notes=test_application_data["notes"]
    )
    db_session.add(application)
    db_session.commit()
    db_session.refresh(application)
    return application
