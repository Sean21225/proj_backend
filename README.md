# Job Application Management Backend

A FastAPI backend for managing job applications, resumes, and user accounts with external service integrations.

## Features

**Core Functionality**
- User authentication with JWT tokens
- Resume management and storage
- Job application tracking with status updates
- User dashboard with basic analytics

**External Services**
- Resume optimization service integration
- LinkedIn job scraper for finding opportunities
- Application analytics and reporting

**Technical Stack**
- FastAPI with automatic OpenAPI documentation
- PostgreSQL database with SQLAlchemy
- JWT authentication and password hashing
- Comprehensive test suite
- Docker support

## Requirements

- Python 3.8 or higher
- PostgreSQL database
- Virtual environment recommended

## Setup

Install dependencies:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install fastapi uvicorn sqlalchemy psycopg2-binary "pydantic[email]" python-jose passlib[bcrypt] python-multipart requests pytest httpx email-validator
```

Set up your environment variables in a `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/job_db
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Start the server:

```bash
python main.py
```

The API will be available at http://localhost:5000 with documentation at http://localhost:5000/docs

## Testing

Run the test suite:

```bash
python app_test.py
```

For more detailed testing:

```bash
python integration_test.py
pytest tests/ -v
```

## Docker

Build and run with Docker:

```bash
docker build -t job-app-backend .
docker run -d -p 5000:5000 job-app-backend
```

## API Endpoints

Main endpoints include:

- `GET /health` - Check if API is running
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - User login
- `GET /user/profile` - Get user information
- `POST /resume` - Create new resume
- `GET /resume` - List user resumes
- `POST /applications` - Create job application
- `GET /applications` - List applications with filtering
- `POST /services/resume/optimize` - Optimize resume content
- `GET /services/linkedin/jobs` - Search for jobs on LinkedIn

Complete API documentation is available at `/docs` when the server is running.

## Project Structure

```
├── routers/           # API route handlers
├── services/          # External service integrations
├── tests/             # Test files
├── main.py           # Application entry point
├── models.py         # Database models
├── schemas.py        # Data validation schemas
├── auth.py           # Authentication utilities
├── database.py       # Database setup
└── Dockerfile        # Container configuration
```

## Development

For development with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 5000
```
