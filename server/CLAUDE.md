# Server Development Guide

## Purpose

This guide provides detailed instructions for developing the **FastAPI backend server** for the Kids Single-Button Media Station. Follow this guide when working on server-related tasks.

**Technology Stack**: Python 3.11+, FastAPI, SQLAlchemy, SQLite, pytest

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Project Structure](#project-structure)
3. [Development Workflow](#development-workflow)
4. [Testing Strategy](#testing-strategy)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Phase-Specific Guides](#phase-specific-guides)
8. [Common Tasks](#common-tasks)

---

## Quick Start

### Initial Setup (Phase 0)

```bash
cd server

# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (including dev dependencies)
uv pip install -e ".[dev]"

# Or sync dependencies from pyproject.toml
uv sync
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_get_next_video

# Run in watch mode (requires pytest-watch)
ptw
```

### Running the Server

```bash
# Development mode (auto-reload)
uvicorn src.main:app --reload --port 8000

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

---

## Project Structure

```
server/
├── CLAUDE.md              ← You are here
├── pyproject.toml         ← Dependencies and configuration (UV)
├── requirements.txt       ← Legacy dependencies reference
├── pytest.ini             ← Test configuration (migrated to pyproject.toml)
├── .env.example           ← Environment variables template
│
├── src/
│   ├── __init__.py
│   ├── main.py            ← FastAPI app entry point
│   ├── config.py          ← Configuration management
│   │
│   ├── api/               ← API route handlers
│   │   ├── __init__.py
│   │   ├── routes.py      ← Core /api/next endpoint (Phase 1)
│   │   ├── clients.py     ← Client management (Phase 2)
│   │   ├── videos.py      ← Video library endpoints (Phase 3)
│   │   ├── queue.py       ← Queue management (Phase 3)
│   │   └── stats.py       ← Statistics endpoints (Phase 3)
│   │
│   ├── db/                ← Database layer
│   │   ├── __init__.py
│   │   ├── database.py    ← Database connection setup (Phase 2)
│   │   ├── models.py      ← SQLAlchemy models (Phase 2)
│   │   └── repositories.py← Data access layer (Phase 2)
│   │
│   ├── services/          ← Business logic
│   │   ├── __init__.py
│   │   ├── video_service.py   ← Video selection logic (Phase 1+)
│   │   ├── limit_service.py   ← Daily limit enforcement (Phase 2)
│   │   └── queue_service.py   ← Queue management (Phase 3)
│   │
│   ├── media/             ← Media file handling
│   │   ├── __init__.py
│   │   └── scanner.py     ← Media directory scanner (Phase 1+)
│   │
│   └── schemas/           ← Pydantic models
│       ├── __init__.py
│       ├── video.py       ← Video request/response models
│       └── client.py      ← Client request/response models
│
└── tests/
    ├── __init__.py
    ├── conftest.py        ← Shared fixtures
    ├── test_api.py        ← API endpoint tests
    ├── test_models.py     ← Database model tests
    ├── test_repositories.py← Repository tests
    ├── test_limit_service.py← Limit service tests
    └── test_scanner.py    ← Media scanner tests
```

---

## Development Workflow

### TDD Cycle for Server Features

#### Example: Implementing `/api/next` Endpoint

**Step 1: 🔴 RED - Write Failing Test**

```python
# tests/test_api.py
from fastapi.testclient import TestClient

def test_get_next_video_returns_video_url(client):
    """Test that /api/next returns a video URL."""
    # Arrange
    # (Setup done in fixtures)

    # Act
    response = client.get("/api/next?client_id=trolley1")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "title" in data
    assert "placeholder" in data
```

Run: `pytest tests/test_api.py::test_get_next_video_returns_video_url`
Expected: **FAIL** (endpoint doesn't exist)

Commit: `[PHASE-1] test: add test for /api/next endpoint`

**Step 2: 🟢 GREEN - Make Test Pass**

```python
# src/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/api/next")
def get_next_video(client_id: str):
    return {
        "url": "/media/library/video1.mp4",  # Hardcoded for now
        "title": "Test Video",
        "placeholder": False
    }
```

Run: `pytest tests/test_api.py::test_get_next_video_returns_video_url`
Expected: **PASS**

Commit: `[PHASE-1] feat: add basic /api/next endpoint`

**Step 3: ♻️ REFACTOR - Improve Code**

```python
# src/api/routes.py
from fastapi import APIRouter
from src.schemas.video import NextVideoResponse
from src.services.video_service import VideoService

router = APIRouter()

@router.get("/next", response_model=NextVideoResponse)
async def get_next_video(client_id: str):
    """Get the next video for a client."""
    service = VideoService()
    return service.get_next_video(client_id)

# src/main.py
from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(title="Kids Media Station API")
app.include_router(router, prefix="/api")
```

Run: `pytest`
Expected: **ALL PASS**

Commit: `[PHASE-1] refactor: extract routes to separate module`

---

## Testing Strategy

### Test Organization

#### Unit Tests
Test individual functions and classes in isolation.

```python
# tests/test_limit_service.py
from src.services.limit_service import LimitService

def test_count_plays_today_returns_zero_for_new_client():
    # Arrange
    service = LimitService(db_session=mock_db)

    # Act
    count = service.count_plays_today("new_client")

    # Assert
    assert count == 0
```

#### Integration Tests
Test multiple components working together.

```python
# tests/test_integration.py
def test_daily_limit_enforced_end_to_end(client, db_session):
    # Arrange
    setup_client("test", daily_limit=2)
    seed_videos(count=5)

    # Act
    response1 = client.get("/api/next?client_id=test")
    response2 = client.get("/api/next?client_id=test")
    response3 = client.get("/api/next?client_id=test")

    # Assert
    assert response1.json()["placeholder"] is False
    assert response2.json()["placeholder"] is False
    assert response3.json()["placeholder"] is True
```

### Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.db.database import Base

@pytest.fixture
def db_session():
    """Provide a clean database session for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

@pytest.fixture
def client(db_session):
    """Provide a test FastAPI client."""
    # Override database dependency
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def sample_videos():
    """Provide sample video data."""
    return [
        {"id": 1, "path": "kids/video1.mp4", "title": "Fun Cartoon"},
        {"id": 2, "path": "kids/video2.mp4", "title": "Learning Time"},
    ]
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch
import pytest

@pytest.fixture
def mock_filesystem():
    """Mock filesystem operations."""
    with patch('os.listdir') as mock_listdir:
        mock_listdir.return_value = ["video1.mp4", "video2.mp4"]
        yield mock_listdir

def test_scanner_lists_video_files(mock_filesystem):
    from src.media.scanner import VideoScanner

    scanner = VideoScanner(path="/fake/path")
    videos = scanner.scan()

    assert len(videos) == 2
    mock_filesystem.assert_called_once_with("/fake/path")
```

---

## API Endpoints

### Phase 1: Core Playback

#### `GET /api/next`
Get the next video for a client.

**Query Parameters**:
- `client_id` (string, required): Client identifier

**Response** (200 OK):
```json
{
  "url": "/media/library/video1.mp4",
  "title": "Fun Cartoon",
  "placeholder": false
}
```

**Implementation**:
```python
@router.get("/next", response_model=NextVideoResponse)
async def get_next_video(client_id: str):
    service = VideoService()
    return service.get_next_video(client_id)
```

### Phase 2: Client Management

#### `GET /api/clients`
List all registered clients.

**Response** (200 OK):
```json
[
  {
    "client_id": "trolley1",
    "friendly_name": "Living Room Trolley",
    "daily_limit": 3
  }
]
```

#### `PATCH /api/clients/{client_id}`
Update client settings.

**Request Body**:
```json
{
  "friendly_name": "Bedroom Trolley",
  "daily_limit": 2
}
```

### Phase 3: Queue & Library

#### `GET /api/videos`
List all videos in library.

**Query Parameters**:
- `tags` (string, optional): Filter by tags
- `search` (string, optional): Search in title

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "path": "kids/video1.mp4",
    "title": "Fun Cartoon",
    "tags": ["cartoon", "age-4-6"],
    "is_placeholder": false,
    "duration_seconds": 600
  }
]
```

#### `POST /api/queue/{client_id}`
Add videos to client's queue.

**Request Body**:
```json
{
  "video_ids": [5, 12, 8]
}
```

**Response** (200 OK):
```json
{
  "message": "3 videos added to queue"
}
```

#### `GET /api/queue/{client_id}`
Get client's queue.

**Response** (200 OK):
```json
[
  {
    "id": 1,
    "video_id": 5,
    "position": 0,
    "video": {
      "title": "Episode 1",
      "path": "show/ep1.mp4"
    }
  }
]
```

---

## Database Schema

### Models (Phase 2+)

```python
# src/db/models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    path = Column(String, unique=True, nullable=False)
    title = Column(String, nullable=False)
    tags = Column(String)  # Comma-separated
    is_placeholder = Column(Boolean, default=False)
    duration_seconds = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class ClientSettings(Base):
    __tablename__ = "client_settings"

    client_id = Column(String, primary_key=True)
    friendly_name = Column(String, nullable=False)
    daily_limit = Column(Integer, default=3)
    tag_filters = Column(String)  # Comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class QueueItem(Base):
    __tablename__ = "queue"

    id = Column(Integer, primary_key=True)
    client_id = Column(String, ForeignKey("client_settings.client_id"))
    video_id = Column(Integer, ForeignKey("videos.id"))
    position = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video")

class PlayLog(Base):
    __tablename__ = "play_log"

    id = Column(Integer, primary_key=True)
    client_id = Column(String, ForeignKey("client_settings.client_id"))
    video_id = Column(Integer, ForeignKey("videos.id"))
    played_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_placeholder = Column(Boolean, nullable=False)
    completed = Column(Boolean, default=False)

    video = relationship("Video")
```

### Repository Pattern

```python
# src/db/repositories.py
from sqlalchemy.orm import Session
from src.db.models import Video, ClientSettings, PlayLog
from datetime import date

class VideoRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> list[Video]:
        return self.db.query(Video).all()

    def get_by_id(self, video_id: int) -> Video | None:
        return self.db.query(Video).filter(Video.id == video_id).first()

    def get_placeholders(self) -> list[Video]:
        return self.db.query(Video).filter(Video.is_placeholder == True).all()

    def create(self, path: str, title: str, **kwargs) -> Video:
        video = Video(path=path, title=title, **kwargs)
        self.db.add(video)
        self.db.commit()
        self.db.refresh(video)
        return video

class PlayLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def count_plays_today(self, client_id: str, today: date) -> int:
        return (
            self.db.query(PlayLog)
            .filter(
                PlayLog.client_id == client_id,
                PlayLog.is_placeholder == False,
                PlayLog.played_at >= datetime.combine(today, time.min)
            )
            .count()
        )

    def log_play(self, client_id: str, video_id: int, is_placeholder: bool):
        log = PlayLog(
            client_id=client_id,
            video_id=video_id,
            is_placeholder=is_placeholder
        )
        self.db.add(log)
        self.db.commit()
```

---

## Phase-Specific Guides

### Phase 0: Project Setup

**Tasks**:
1. Set up Python environment
2. Install dependencies
3. Configure pytest
4. Create initial structure

**Checklist**:
- [ ] Virtual environment created
- [ ] Dependencies installed (FastAPI, pytest, etc.)
- [ ] `pytest.ini` configured
- [ ] Can run `pytest` and see "0 tests collected"
- [ ] Can run `uvicorn` and see FastAPI docs at http://localhost:8000/docs

**Initial Files**:

```python
# src/main.py
from fastapi import FastAPI

app = FastAPI(title="Kids Media Station API")

@app.get("/")
def root():
    return {"message": "Kids Media Station API"}
```

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

### Phase 1: Minimal Vertical Slice

**Goal**: Random video playback

**TDD Tasks**:
1. **TEST**: Test for media scanner
2. **CODE**: Implement media scanner
3. **TEST**: Test for `/api/next` endpoint
4. **CODE**: Implement `/api/next` with random selection
5. **TEST**: Test for static file serving
6. **CODE**: Implement static file serving

**Key Files**:
- `src/api/routes.py` - API endpoints
- `src/media/scanner.py` - Media file scanner
- `src/services/video_service.py` - Video selection logic
- `tests/test_api.py` - API tests
- `tests/test_scanner.py` - Scanner tests

**Example Test**:
```python
# tests/test_scanner.py
def test_scanner_finds_mp4_files(tmp_path):
    # Arrange
    (tmp_path / "video1.mp4").touch()
    (tmp_path / "video2.mp4").touch()
    (tmp_path / "readme.txt").touch()

    # Act
    scanner = VideoScanner(str(tmp_path))
    videos = scanner.scan()

    # Assert
    assert len(videos) == 2
    assert all(v.endswith(".mp4") for v in videos)
```

### Phase 2: Persistence & Daily Limits

**Goal**: Daily limit enforcement with database

**TDD Tasks**:
1. **TEST**: Test database models
2. **CODE**: Create SQLAlchemy models
3. **TEST**: Test repository operations
4. **CODE**: Implement repositories
5. **TEST**: Test limit service logic
6. **CODE**: Implement limit service
7. **TEST**: Test updated `/api/next` with limits
8. **CODE**: Update `/api/next` to use limit service

**Key Files**:
- `src/db/models.py` - Database models
- `src/db/database.py` - DB connection
- `src/db/repositories.py` - Data access
- `src/services/limit_service.py` - Limit logic
- `tests/test_models.py` - Model tests
- `tests/test_limit_service.py` - Service tests

**Example Test**:
```python
# tests/test_limit_service.py
def test_is_limit_reached_returns_true_when_at_limit(db_session):
    # Arrange
    service = LimitService(db_session)
    client_id = "test_client"
    setup_client(db_session, client_id, daily_limit=2)
    log_plays(db_session, client_id, count=2)

    # Act
    result = service.is_limit_reached(client_id)

    # Assert
    assert result is True
```

### Phase 3: Queue & Admin UI

**Goal**: Queue management and video library API

**TDD Tasks**:
1. **TEST**: Test queue repository
2. **CODE**: Implement queue operations
3. **TEST**: Test queue service
4. **CODE**: Implement queue service
5. **TEST**: Test video endpoints
6. **CODE**: Implement video listing and filtering
7. **TEST**: Test queue endpoints
8. **CODE**: Implement queue endpoints

**Key Files**:
- `src/api/videos.py` - Video endpoints
- `src/api/queue.py` - Queue endpoints
- `src/api/stats.py` - Stats endpoints
- `src/services/queue_service.py` - Queue logic
- `tests/test_queue_api.py` - Queue tests

---

## Common Tasks

### Adding a New Endpoint

1. **Write the test first**:
```python
# tests/test_api.py
def test_new_endpoint_returns_expected_data(client):
    response = client.get("/api/new-endpoint")
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

2. **Create the endpoint**:
```python
# src/api/routes.py
@router.get("/new-endpoint")
async def new_endpoint():
    return {"expected_field": "value"}
```

3. **Refactor as needed**

### Adding a Database Migration

```python
# Manual migration for SQLite (Phase 2)
from src.db.database import engine
from src.db.models import Base

# Create all tables
Base.metadata.create_all(engine)
```

For production, consider using Alembic:
```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Debugging Tests

```bash
# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s

# Drop into debugger on failure
pytest --pdb

# Run only failed tests from last run
pytest --lf
```

### Serving Static Files

```python
# src/main.py
from fastapi.staticfiles import StaticFiles

app.mount("/media", StaticFiles(directory="../media"), name="media")
app.mount("/admin", StaticFiles(directory="static/admin", html=True), name="admin")
```

---

## Best Practices

### Error Handling

```python
from fastapi import HTTPException, status

@router.get("/videos/{video_id}")
async def get_video(video_id: int, db: Session = Depends(get_db)):
    repo = VideoRepository(db)
    video = repo.get_by_id(video_id)

    if video is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video {video_id} not found"
        )

    return video
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

@router.get("/next")
async def get_next_video(client_id: str):
    logger.info(f"Client {client_id} requested next video")

    try:
        video = service.get_next_video(client_id)
        logger.info(f"Returning video {video.id} to client {client_id}")
        return video
    except Exception as e:
        logger.error(f"Error getting next video for {client_id}: {e}")
        raise
```

### Dependency Injection

```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/videos")
async def list_videos(db: Session = Depends(get_db)):
    repo = VideoRepository(db)
    return repo.get_all()
```

---

## Troubleshooting

### Tests Failing

1. **Check test isolation**: Each test should set up its own data
2. **Check fixtures**: Are fixtures being applied correctly?
3. **Check database**: Is the test database clean?
4. **Check mocks**: Are mocks configured correctly?

### Import Errors

```bash
# Make sure you're in the right directory
cd server

# Install package in development mode
pip install -e .
```

### Database Errors

```python
# Reset database in tests
@pytest.fixture(autouse=True)
def reset_db(db_session):
    """Reset database before each test."""
    Base.metadata.drop_all(bind=db_session.bind)
    Base.metadata.create_all(bind=db_session.bind)
```

---

## Next Steps

1. **Complete Phase 0 tasks** (see [Grand Plan](../docs/grand_plan.md))
2. **Move to Phase 1** when all tests pass and coverage is good
3. **Follow TDD cycle** for every feature
4. **Update this document** with lessons learned

---

**Ready to code? Open the Grand Plan, pick a task, and start with a test!**
