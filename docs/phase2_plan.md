# Phase 2 Implementation Plan: Persistence & Daily Limits

**Goal**: Add SQLite database, daily limit enforcement, and placeholder videos

**Duration Estimate**: 2-4 sessions

**Current Date**: 2025-11-18

---

## Overview

Phase 2 transforms the stateless Phase 1 system into a persistent, limit-aware system. After Phase 2:
- Video metadata stored in SQLite database
- Each client has configurable daily limit (e.g., 3 programs/day)
- System tracks plays per client per day
- When limit reached, only placeholder videos are returned
- Limits reset automatically at midnight

---

## TDD Task Breakdown

### Group 1: Database Foundation (Est: 1 session)

#### Task 1.1: Database Models
**RED Phase**:
- [ ] Write test for Video model (id, path, title, tags, is_placeholder)
- [ ] Write test for ClientSettings model (client_id, friendly_name, daily_limit)
- [ ] Write test for PlayLog model (id, client_id, video_id, played_at, is_placeholder)
- [ ] Write test for model relationships

**GREEN Phase**:
- [ ] Implement Video model with SQLAlchemy
- [ ] Implement ClientSettings model
- [ ] Implement PlayLog model
- [ ] Set up model relationships

**Success Criteria**: All model tests pass, models can be instantiated

---

#### Task 1.2: Database Setup & Connection
**RED Phase**:
- [ ] Write test for database initialization
- [ ] Write test for session management
- [ ] Write test for table creation

**GREEN Phase**:
- [ ] Implement database.py with engine and session factory
- [ ] Implement Base.metadata.create_all()
- [ ] Add get_db() dependency for FastAPI

**Success Criteria**: Database can be created, sessions can be acquired

---

### Group 2: Data Access Layer (Est: 1 session)

#### Task 2.1: Video Repository
**RED Phase**:
- [ ] Write test for get_all_videos()
- [ ] Write test for get_by_id()
- [ ] Write test for get_by_path()
- [ ] Write test for create_video()
- [ ] Write test for get_placeholders()
- [ ] Write test for get_random_non_placeholder()

**GREEN Phase**:
- [ ] Implement VideoRepository class
- [ ] Implement all query methods

**Success Criteria**: All repository tests pass

---

#### Task 2.2: PlayLog Repository
**RED Phase**:
- [ ] Write test for log_play()
- [ ] Write test for count_plays_today()
- [ ] Write test for count_non_placeholder_plays_today()
- [ ] Write test for get_recent_plays()
- [ ] Write test for date boundary handling (midnight reset)

**GREEN Phase**:
- [ ] Implement PlayLogRepository class
- [ ] Implement play logging
- [ ] Implement count queries with date filtering

**Success Criteria**: Play logging works, counts are accurate per day

---

#### Task 2.3: Client Repository
**RED Phase**:
- [ ] Write test for get_client()
- [ ] Write test for create_client()
- [ ] Write test for update_client()
- [ ] Write test for get_or_create_client()

**GREEN Phase**:
- [ ] Implement ClientRepository class
- [ ] Implement CRUD operations

**Success Criteria**: Clients can be created and retrieved

---

### Group 3: Business Logic (Est: 1 session)

#### Task 3.1: Limit Service
**RED Phase**:
- [ ] Write test for is_limit_reached(client_id, date) → bool
- [ ] Write test for get_daily_limit(client_id) → int
- [ ] Write test for count_plays_today(client_id, date) → int
- [ ] Write test for limit with default limit (3)
- [ ] Write test for limit with custom client limit
- [ ] Write test for limit reset at midnight

**GREEN Phase**:
- [ ] Implement LimitService class
- [ ] Implement limit checking logic
- [ ] Implement default limit handling

**Success Criteria**: Limit checking is accurate and respects client settings

---

#### Task 3.2: Video Selection Service
**RED Phase**:
- [ ] Write test for select_next_video() with queue support (placeholder for Phase 3)
- [ ] Write test for select_random_video() excluding placeholders
- [ ] Write test for select_placeholder_video()

**GREEN Phase**:
- [ ] Implement VideoService class
- [ ] Implement random selection from non-placeholder videos
- [ ] Implement placeholder selection logic

**Success Criteria**: Correct video type selected based on limit status

---

### Group 4: API Integration (Est: 1 session)

#### Task 4.1: Database Migration/Seeding
**RED Phase**:
- [ ] Write test for scanning media directory and populating database
- [ ] Write test for handling duplicate videos
- [ ] Write test for marking placeholder videos

**GREEN Phase**:
- [ ] Update VideoScanner to save to database
- [ ] Implement scan_and_populate() function
- [ ] Add placeholder detection logic

**Success Criteria**: Media directory can be scanned into database

---

#### Task 4.2: Updated /api/next Endpoint
**RED Phase**:
- [ ] Write test for /api/next returning video when under limit
- [ ] Write test for /api/next returning placeholder when at limit
- [ ] Write test for /api/next logging plays
- [ ] Write test for /api/next with client that doesn't exist (auto-create)
- [ ] Write test for plays incrementing correctly
- [ ] Write test for limit reset on new day

**GREEN Phase**:
- [ ] Update /api/next to use database
- [ ] Integrate LimitService
- [ ] Implement play logging
- [ ] Implement client auto-creation

**Success Criteria**: API enforces limits, logs plays correctly

---

#### Task 4.3: Client Management Endpoints
**RED Phase**:
- [ ] Write test for GET /api/clients
- [ ] Write test for GET /api/clients/{client_id}
- [ ] Write test for POST /api/clients
- [ ] Write test for PATCH /api/clients/{client_id}

**GREEN Phase**:
- [ ] Implement client list endpoint
- [ ] Implement client detail endpoint
- [ ] Implement client creation endpoint
- [ ] Implement client update endpoint

**Success Criteria**: Clients can be managed via API

---

#### Task 4.4: Video Management Endpoints
**RED Phase**:
- [ ] Write test for GET /api/videos
- [ ] Write test for GET /api/videos with filters (tags, search)
- [ ] Write test for POST /api/videos/scan
- [ ] Write test for PATCH /api/videos/{id} (mark as placeholder)

**GREEN Phase**:
- [ ] Implement video listing endpoint
- [ ] Implement filtering logic
- [ ] Implement scan endpoint
- [ ] Implement video update endpoint

**Success Criteria**: Videos can be listed and scanned via API

---

## Database Schema

```sql
-- Videos table
CREATE TABLE videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    tags TEXT,  -- comma-separated
    is_placeholder BOOLEAN DEFAULT 0,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Client settings table
CREATE TABLE client_settings (
    client_id TEXT PRIMARY KEY,
    friendly_name TEXT NOT NULL,
    daily_limit INTEGER DEFAULT 3,
    tag_filters TEXT,  -- comma-separated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Play log table
CREATE TABLE play_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT NOT NULL,
    video_id INTEGER NOT NULL,
    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    is_placeholder BOOLEAN NOT NULL,
    completed BOOLEAN DEFAULT 0,
    FOREIGN KEY (client_id) REFERENCES client_settings (client_id),
    FOREIGN KEY (video_id) REFERENCES videos (id)
);

-- Indexes for performance
CREATE INDEX idx_play_log_client_date ON play_log(client_id, played_at);
CREATE INDEX idx_play_log_is_placeholder ON play_log(is_placeholder);
CREATE INDEX idx_videos_is_placeholder ON videos(is_placeholder);
```

---

## Service Layer Architecture

```
┌─────────────────────────────────────────┐
│          FastAPI Endpoints              │
│  /api/next, /api/clients, /api/videos   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Service Layer                    │
│  - LimitService                         │
│  - VideoService                         │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│       Repository Layer                   │
│  - VideoRepository                      │
│  - PlayLogRepository                    │
│  - ClientRepository                     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Database Models                  │
│  - Video, ClientSettings, PlayLog       │
└─────────────────────────────────────────┘
```

---

## Core Algorithm: /api/next with Limits

```python
def get_next_video(client_id: str):
    # 1. Get or create client
    client = client_repo.get_or_create(client_id)

    # 2. Check if daily limit reached
    today = date.today()
    plays_today = play_log_repo.count_non_placeholder_plays_today(client_id, today)
    limit = client.daily_limit

    # 3. Select video based on limit status
    if plays_today >= limit:
        # Limit reached - return placeholder
        video = video_repo.get_random_placeholder()
        is_placeholder = True
    else:
        # Under limit - return real video
        # Phase 3 will check queue first
        video = video_repo.get_random_non_placeholder()
        is_placeholder = False

    # 4. Log the play
    play_log_repo.log_play(
        client_id=client_id,
        video_id=video.id,
        is_placeholder=is_placeholder
    )

    # 5. Return response
    return NextVideoResponse(
        url=f"/media/library/{video.path}",
        title=video.title,
        placeholder=is_placeholder
    )
```

---

## Testing Strategy

### Unit Tests
- Models: Test field validation, relationships
- Repositories: Test CRUD operations with in-memory DB
- Services: Test business logic with mocked repositories

### Integration Tests
- API endpoints: Test full flow with TestClient + in-memory DB
- Date boundaries: Test midnight reset behavior
- Limit enforcement: Test exact limit boundary (N-1, N, N+1 plays)

### Test Fixtures
```python
@pytest.fixture
def db_session():
    """In-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.fixture
def sample_client(db_session):
    """Create a test client with default settings."""
    client = ClientSettings(
        client_id="test_client",
        friendly_name="Test Client",
        daily_limit=3
    )
    db_session.add(client)
    db_session.commit()
    return client

@pytest.fixture
def sample_videos_in_db(db_session):
    """Create test videos in database."""
    videos = [
        Video(path="video1.mp4", title="Video 1", is_placeholder=False),
        Video(path="video2.mp4", title="Video 2", is_placeholder=False),
        Video(path="placeholder.mp4", title="All Done", is_placeholder=True),
    ]
    for video in videos:
        db_session.add(video)
    db_session.commit()
    return videos
```

---

## Success Criteria for Phase 2

- [ ] All tests pass (target: 30+ new tests)
- [ ] Code coverage > 85%
- [ ] Database can be created and populated
- [ ] Daily limits are enforced correctly
- [ ] Plays are logged accurately
- [ ] Limit resets at midnight (tested via date mocking)
- [ ] Clients can be managed via API
- [ ] Videos can be scanned and listed via API
- [ ] Placeholder videos are returned when limit reached
- [ ] System handles new clients automatically

---

## Edge Cases to Test

1. **First request from new client**: Should auto-create client with default limit
2. **Exactly at limit**: If limit is 3, after 3 plays, 4th should be placeholder
3. **Multiple clients**: Client A's plays don't affect Client B's limit
4. **Date boundary**: Plays at 11:59 PM vs 12:01 AM are different days
5. **No placeholder videos**: Should handle gracefully (return error or default)
6. **Empty database**: First scan should populate properly
7. **Duplicate videos**: Rescanning should not duplicate entries

---

## Dependencies to Add

```txt
# Add to server/requirements.txt
sqlalchemy>=2.0.0
aiosqlite>=0.19.0  # For async SQLite support (future)
python-dateutil>=2.8.0  # For date handling
```

---

## Implementation Order

**Session 1**: Models & Database Setup (Tasks 1.1, 1.2)
**Session 2**: Repositories (Tasks 2.1, 2.2, 2.3)
**Session 3**: Services (Tasks 3.1, 3.2)
**Session 4**: API Integration (Tasks 4.1, 4.2, 4.3, 4.4)

Each session follows strict TDD:
1. Write ALL tests for the group (RED)
2. Implement to pass tests (GREEN)
3. Refactor for clarity (REFACTOR)
4. Commit and push

---

## Next Immediate Steps

1. Add SQLAlchemy to requirements.txt
2. Create `server/src/db/` directory structure
3. Start with Task 1.1: Write tests for database models
4. Follow TDD cycle for each task

**Ready to begin Phase 2!** 🚀
