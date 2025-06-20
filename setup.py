"""
Setup script for the Job Application Management Backend
Handles database initialization and basic configuration
"""

import os
import sys
import subprocess
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from database import DATABASE_URL, Base
from models import User, Resume, Application  # Import to ensure tables are created


def check_python_version():
    """Ensure Python version compatibility"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python version: {sys.version}")
    return True


def install_requirements():
    """Install required Python packages"""
    requirements = [
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pydantic[email]>=2.4.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "python-multipart>=0.0.6",
        "requests>=2.31.0",
        "pytest>=7.4.0",
        "httpx>=0.25.0"  # For testing
    ]
    
    print("📦 Installing required packages...")
    for requirement in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", requirement])
            print(f"✅ Installed: {requirement}")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {requirement}: {e}")
            return False
    
    return True


def check_database_connection():
    """Check database connectivity"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except OperationalError as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Make sure PostgreSQL is running and the DATABASE_URL is correct")
        print(f"   Current DATABASE_URL: {DATABASE_URL[:20]}...")
        return False


def create_database_tables():
    """Create all database tables"""
    try:
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
        expected_tables = ['users', 'resumes', 'applications']
        for table in expected_tables:
            if table in tables:
                print(f"✅ Table '{table}' created")
            else:
                print(f"❌ Table '{table}' not found")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
        return False


def create_test_database():
    """Create test database if it doesn't exist"""
    try:
        # Extract database name from URL for test database
        base_url = DATABASE_URL.rsplit('/', 1)[0]
        test_db_url = f"{base_url}/test_jobapp"
        
        # Try to create test database
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("COMMIT"))  # End any existing transaction
            try:
                conn.execute(text("CREATE DATABASE test_jobapp"))
                print("✅ Test database created")
            except Exception:
                print("ℹ️ Test database already exists or couldn't be created")
        
        # Create tables in test database
        test_engine = create_engine(test_db_url)
        Base.metadata.create_all(bind=test_engine)
        print("✅ Test database tables created")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Test database setup failed (this is optional): {e}")
        return True  # Not critical for main functionality


def setup_environment():
    """Set up environment variables and configuration"""
    env_vars = {
        'JWT_SECRET_KEY': 'your-secret-key-change-in-production-' + os.urandom(16).hex(),
        'ACCESS_TOKEN_EXPIRE_MINUTES': '30',
        'API_TIMEOUT': '30'
    }
    
    print("🔧 Setting up environment variables...")
    for key, default_value in env_vars.items():
        if not os.getenv(key):
            os.environ[key] = default_value
            print(f"✅ Set {key} (using default)")
        else:
            print(f"✅ {key} already configured")
    
    return True


def run_basic_tests():
    """Run basic functionality tests"""
    print("🧪 Running basic functionality tests...")
    
    try:
        # Test database operations
        from auth import auth_manager
        
        # Test password hashing
        test_password = "testpassword123"
        hashed = auth_manager.get_password_hash(test_password)
        if auth_manager.verify_password(test_password, hashed):
            print("✅ Password hashing works")
        else:
            print("❌ Password hashing failed")
            return False
        
        # Test JWT token creation
        token = auth_manager.create_access_token({"sub": "testuser", "user_id": 1})
        if token:
            print("✅ JWT token creation works")
        else:
            print("❌ JWT token creation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Basic tests failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Job Application Management Backend Setup")
    print("=" * 50)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing requirements", install_requirements),
        ("Setting up environment", setup_environment),
        ("Checking database connection", check_database_connection),
        ("Creating database tables", create_database_tables),
        ("Creating test database", create_test_database),
        ("Running basic tests", run_basic_tests)
    ]
    
    for step_name, step_function in steps:
        print(f"\n📋 {step_name}...")
        if not step_function():
            print(f"\n❌ Setup failed at: {step_name}")
            sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Start the server: python main.py")
    print("2. View API docs: http://localhost:8000/docs")
    print("3. Run tests: pytest tests/")
    print("4. Run integration tests: python integration_test.py")
    print("\n🔧 Configuration:")
    print(f"   - Server will run on: http://0.0.0.0:8000")
    print(f"   - Database URL: {DATABASE_URL[:30]}...")
    print(f"   - JWT Secret configured: {'✅' if os.getenv('JWT_SECRET_KEY') else '❌'}")


if __name__ == "__main__":
    main()
