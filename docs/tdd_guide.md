# Test-Driven Development Guide

## Purpose

This guide establishes the TDD principles and practices for the Kids Single-Button Media Station project. Following these practices ensures high code quality, maintainability, and confidence in the system.

**Key Principle**: Tests are not just verification - they are documentation, specification, and design feedback.

---

## Table of Contents

1. [The TDD Cycle](#the-tdd-cycle)
2. [Writing Good Tests](#writing-good-tests)
3. [Test Patterns](#test-patterns)
4. [Testing Each Component](#testing-each-component)
5. [Common Pitfalls](#common-pitfalls)
6. [Examples](#examples)

---

## The TDD Cycle

### Red-Green-Refactor

Every feature follows this three-step cycle:

```
    ┌──────────────────────┐
    │     🔴 RED           │
    │  Write Failing Test  │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │     🟢 GREEN         │
    │  Make Test Pass      │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────┐
    │   ♻️ REFACTOR        │
    │  Improve Code        │
    └──────────┬───────────┘
               │
               │  Loop for
               │  next feature
               └──────────────► 🔴 RED
```

### Step-by-Step Process

#### 1. 🔴 RED: Write a Failing Test

**Before writing any production code:**

1. **Think about the behavior** you want to implement
2. **Write a test** that describes that behavior
3. **Run the test** and verify it fails
4. **Commit** with message: `[PHASE-X] test: add test for <feature>`

**Example thought process:**
```
Feature: Get next video for client

What should happen?
- When a client requests the next video
- And they have not reached their daily limit
- Then they should receive a random video URL

Test name: test_get_next_video_returns_random_video_when_under_limit
```

**Why this matters:**
- Ensures you're writing code for the right reason
- Prevents over-engineering
- Documents expected behavior
- Confirms your test can actually fail

#### 2. 🟢 GREEN: Make the Test Pass

**Write the minimum code to pass the test:**

1. **Don't worry about elegance** - just make it work
2. **It's OK to hardcode** at first if needed
3. **Run the test** until it passes
4. **Run all tests** to ensure you didn't break anything
5. **Commit** with message: `[PHASE-X] feat: implement <feature>`

**Example:**
```python
# Minimum code to pass
def get_next_video(client_id: str) -> str:
    return "video1.mp4"  # Hardcoded, but test passes!
```

**Why this matters:**
- Gets you to working code quickly
- Prevents premature optimization
- Each commit leaves the code in a working state
- Builds momentum

#### 3. ♻️ REFACTOR: Improve the Code

**Now make the code better:**

1. **Extract functions** if you see duplication
2. **Rename variables** for clarity
3. **Simplify logic** where possible
4. **Keep tests green** - they must pass during refactoring
5. **Commit** with message: `[PHASE-X] refactor: improve <component>`

**Example:**
```python
# Refactored version
def get_next_video(client_id: str) -> str:
    videos = _scan_video_library()
    return random.choice(videos)

def _scan_video_library() -> List[str]:
    # Extracted for reusability
    return os.listdir(MEDIA_DIR)
```

**Why this matters:**
- Keeps code clean and maintainable
- Tests protect you from breaking things
- Makes the code easier to understand later

---

## Writing Good Tests

### The FIRST Principles

Good tests are **FIRST**:

- **F**ast - Run in milliseconds
- **I**ndependent - Don't depend on other tests
- **R**epeatable - Same result every time
- **S**elf-validating - Pass or fail, no manual checking
- **T**imely - Written before production code

### Test Naming Convention

Use descriptive names that read like sentences:

```python
# ❌ Bad
def test_next_video():
    ...

# ✅ Good
def test_get_next_video_returns_random_video_when_under_daily_limit():
    ...

def test_get_next_video_returns_placeholder_when_limit_reached():
    ...

def test_get_next_video_returns_queued_video_when_queue_not_empty():
    ...
```

**Pattern**: `test_<function>_<expected_behavior>_when_<condition>`

### Test Structure: Arrange-Act-Assert

Every test follows the AAA pattern:

```python
def test_daily_limit_enforcement():
    # ARRANGE - Set up the test data and conditions
    client_id = "trolley1"
    daily_limit = 2
    setup_client(client_id, daily_limit=daily_limit)
    play_videos(client_id, count=2)  # Already watched 2 today

    # ACT - Perform the action being tested
    response = get_next_video(client_id)

    # ASSERT - Verify the expected outcome
    assert response.is_placeholder is True
    assert response.url.endswith("screen_time_over.mp4")
```

**Use blank lines** to separate the three sections visually.

### What to Test

#### Test Behavior, Not Implementation

```python
# ❌ Bad - Testing implementation details
def test_video_list_is_shuffled():
    videos = get_video_list()
    assert videos != sorted(videos)  # Assumes implementation

# ✅ Good - Testing behavior
def test_consecutive_next_calls_return_different_videos():
    video1 = get_next_video("client1")
    video2 = get_next_video("client1")
    # Statistically, they should differ (with enough videos)
    assert video1 != video2 or len(library) == 1
```

#### Test Public Interfaces

- Test functions/methods that will be called by other code
- Don't test private helper functions directly
- Private functions are tested indirectly through public ones

#### Test Edge Cases

For every feature, test:

- **Happy path** - Normal expected usage
- **Edge cases** - Boundaries and limits
- **Error cases** - What happens when things go wrong

```python
# Example: Testing daily limit
def test_first_video_of_day_is_not_placeholder():  # Happy path
    ...

def test_video_at_exact_limit_is_not_placeholder():  # Edge case
    ...

def test_video_after_limit_is_placeholder():  # Edge case
    ...

def test_limit_resets_on_new_day():  # Edge case
    ...
```

---

## Test Patterns

### Pattern 1: Fixture-Based Setup

Use pytest fixtures for common setup:

```python
# conftest.py
@pytest.fixture
def test_client():
    """Provides a test FastAPI client."""
    from main import app
    return TestClient(app)

@pytest.fixture
def sample_videos():
    """Provides a list of sample video data."""
    return [
        {"id": 1, "path": "video1.mp4", "title": "Video 1"},
        {"id": 2, "path": "video2.mp4", "title": "Video 2"},
    ]

# test_api.py
def test_get_videos_returns_list(test_client, sample_videos):
    # Fixture automatically provides test_client and sample_videos
    response = test_client.get("/api/videos")
    assert response.status_code == 200
```

### Pattern 2: Mocking External Dependencies

Mock things you don't control:

```python
from unittest.mock import Mock, patch

def test_button_press_calls_api(mock_http_client):
    # Mock the HTTP call
    mock_http_client.get.return_value = {
        "url": "/media/video.mp4",
        "title": "Test Video"
    }

    # Test the button handler
    button_handler = ButtonHandler(http_client=mock_http_client)
    button_handler.on_press()

    # Verify the API was called
    mock_http_client.get.assert_called_once_with("/api/next?client_id=trolley1")
```

### Pattern 3: Parameterized Tests

Test multiple cases with one test function:

```python
import pytest

@pytest.mark.parametrize("plays_today,daily_limit,should_be_placeholder", [
    (0, 3, False),  # First video of day
    (2, 3, False),  # At limit but not exceeded
    (3, 3, True),   # Exactly at limit
    (4, 3, True),   # Beyond limit
])
def test_placeholder_logic(plays_today, daily_limit, should_be_placeholder):
    setup_client("test", daily_limit=daily_limit)
    log_plays("test", count=plays_today)

    response = get_next_video("test")

    assert response.is_placeholder == should_be_placeholder
```

### Pattern 4: Test Doubles

Use different types of test doubles appropriately:

- **Stub**: Returns canned data
- **Mock**: Records calls and can verify
- **Fake**: Working implementation (e.g., in-memory database)
- **Spy**: Real object that records calls

```python
# Fake database for testing
class FakeDatabase:
    def __init__(self):
        self.videos = []

    def add_video(self, video):
        self.videos.append(video)

    def get_all_videos(self):
        return self.videos

def test_video_scan_populates_database():
    fake_db = FakeDatabase()
    scanner = VideoScanner(database=fake_db)

    scanner.scan("./test_media")

    assert len(fake_db.get_all_videos()) == 3
```

---

## Testing Each Component

### Server (FastAPI)

#### Testing API Endpoints

```python
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_get_next_endpoint_returns_video(client):
    response = client.get("/api/next?client_id=trolley1")

    assert response.status_code == 200
    data = response.json()
    assert "url" in data
    assert "title" in data
    assert "placeholder" in data
```

#### Testing Database Operations

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()

def test_create_video_record(db_session):
    video = Video(path="test.mp4", title="Test Video")
    db_session.add(video)
    db_session.commit()

    retrieved = db_session.query(Video).filter_by(path="test.mp4").first()
    assert retrieved is not None
    assert retrieved.title == "Test Video"
```

#### Testing Services

```python
def test_daily_limit_service_counts_correctly():
    # Arrange
    service = DailyLimitService(db_session)
    client_id = "test_client"
    setup_plays(client_id, count=2, date=today())

    # Act
    count = service.count_plays_today(client_id)

    # Assert
    assert count == 2
```

### Client (Raspberry Pi)

#### Testing Button Handler

```python
from unittest.mock import Mock

def test_button_press_starts_playback():
    # Arrange
    mock_player = Mock()
    mock_api = Mock()
    mock_api.get_next_video.return_value = {"url": "/media/test.mp4"}

    handler = ButtonHandler(player=mock_player, api_client=mock_api)

    # Act
    handler.handle_press()

    # Assert
    mock_api.get_next_video.assert_called_once()
    mock_player.play.assert_called_once_with("/media/test.mp4")
```

#### Testing State Machine

```python
def test_state_transitions_from_idle_to_playing():
    # Arrange
    state_machine = ClientStateMachine()
    assert state_machine.state == State.IDLE

    # Act
    state_machine.on_play_started()

    # Assert
    assert state_machine.state == State.PLAYING
```

#### Testing with Mocked GPIO

```python
from unittest.mock import patch

@patch('gpiozero.Button')
def test_button_initialization(mock_button_class):
    # Act
    button_handler = ButtonHandler(gpio_pin=17)

    # Assert
    mock_button_class.assert_called_once_with(17, pull_up=True, bounce_time=0.1)
```

### Admin UI (React + TypeScript)

#### Testing Components

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { VideoCard } from './VideoCard'

test('clicking queue button calls onQueue callback', () => {
  // Arrange
  const mockOnQueue = vi.fn()
  const video = { id: 1, title: 'Test Video', path: 'test.mp4' }

  render(<VideoCard video={video} onQueue={mockOnQueue} />)

  // Act
  const queueButton = screen.getByRole('button', { name: /queue/i })
  fireEvent.click(queueButton)

  // Assert
  expect(mockOnQueue).toHaveBeenCalledWith(video.id)
})
```

#### Testing API Client

```typescript
import { describe, it, expect, vi } from 'vitest'
import { ApiClient } from './api'

describe('ApiClient', () => {
  it('fetches videos from server', async () => {
    // Arrange
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [{ id: 1, title: 'Test' }]
    })

    const client = new ApiClient('http://localhost:8000')

    // Act
    const videos = await client.getVideos()

    // Assert
    expect(videos).toHaveLength(1)
    expect(videos[0].title).toBe('Test')
  })
})
```

---

## Common Pitfalls

### ❌ Pitfall 1: Writing Tests After Code

**Problem**: You write code first, then add tests as an afterthought.

**Why it's bad**:
- Tests don't drive design
- Miss edge cases
- Tests become harder to write
- Temptation to skip tests

**Solution**: Always write tests first, no exceptions.

### ❌ Pitfall 2: Testing Implementation Details

**Problem**: Tests break when you refactor, even though behavior is the same.

```python
# ❌ Bad
def test_uses_random_choice():
    videos = ["a.mp4", "b.mp4"]
    with patch('random.choice') as mock_choice:
        get_next_video()
        mock_choice.assert_called_once()

# ✅ Good
def test_returns_video_from_library():
    videos = ["a.mp4", "b.mp4"]
    result = get_next_video()
    assert result in videos
```

**Solution**: Test behavior and outcomes, not how it's implemented.

### ❌ Pitfall 3: Tests That Depend on Each Other

**Problem**: Test B only passes if Test A runs first.

```python
# ❌ Bad
def test_a_adds_video():
    add_video("test.mp4")
    assert len(get_videos()) == 1

def test_b_gets_video():
    # Depends on test_a running first!
    video = get_videos()[0]
    assert video == "test.mp4"

# ✅ Good
def test_a_adds_video():
    add_video("test.mp4")
    assert len(get_videos()) == 1

def test_b_gets_video():
    add_video("test.mp4")  # Set up own data
    video = get_videos()[0]
    assert video == "test.mp4"
```

**Solution**: Each test sets up its own data. Use fixtures for common setup.

### ❌ Pitfall 4: Slow Tests

**Problem**: Tests take seconds or minutes to run.

**Why it's bad**:
- Developers run tests less often
- Slows down TDD cycle
- CI/CD takes forever

**Solution**:
- Use in-memory databases
- Mock external services (network, filesystem)
- Keep unit tests fast (< 100ms each)
- Separate slow integration tests

### ❌ Pitfall 5: Not Testing Error Cases

**Problem**: Only testing the happy path.

```python
# ❌ Incomplete
def test_get_next_video_returns_video():
    video = get_next_video("client1")
    assert video is not None

# ✅ Complete
def test_get_next_video_returns_video():
    video = get_next_video("client1")
    assert video is not None

def test_get_next_video_raises_error_for_invalid_client():
    with pytest.raises(ClientNotFoundError):
        get_next_video("nonexistent_client")

def test_get_next_video_returns_placeholder_when_no_videos():
    clear_library()
    video = get_next_video("client1")
    assert video.is_placeholder is True
```

**Solution**: For each function, test happy path + edge cases + error cases.

---

## Examples

### Example 1: TDD Cycle for Daily Limit Feature

#### Iteration 1: Basic Limit Check

**🔴 RED**:
```python
# test_limit_service.py
def test_is_limit_reached_returns_false_when_under_limit():
    # Arrange
    service = LimitService()
    service.set_limit("client1", 3)
    service.log_play("client1", video_id=1, is_placeholder=False)

    # Act
    result = service.is_limit_reached("client1")

    # Assert
    assert result is False
```

Run test: **FAILS** (function doesn't exist)

**🟢 GREEN**:
```python
# limit_service.py
class LimitService:
    def __init__(self):
        self.limits = {}
        self.plays = []

    def set_limit(self, client_id, limit):
        self.limits[client_id] = limit

    def log_play(self, client_id, video_id, is_placeholder):
        self.plays.append({
            "client_id": client_id,
            "video_id": video_id,
            "is_placeholder": is_placeholder,
        })

    def is_limit_reached(self, client_id):
        return False  # Hardcoded to pass
```

Run test: **PASSES**

Commit: `[PHASE-2] test: add test for limit check`
Commit: `[PHASE-2] feat: add basic limit service`

#### Iteration 2: Actual Limit Logic

**🔴 RED**:
```python
def test_is_limit_reached_returns_true_when_at_limit():
    # Arrange
    service = LimitService()
    service.set_limit("client1", 2)
    service.log_play("client1", video_id=1, is_placeholder=False)
    service.log_play("client1", video_id=2, is_placeholder=False)

    # Act
    result = service.is_limit_reached("client1")

    # Assert
    assert result is True
```

Run test: **FAILS** (still returns False)

**🟢 GREEN**:
```python
def is_limit_reached(self, client_id):
    limit = self.limits.get(client_id, 3)
    non_placeholder_plays = [
        p for p in self.plays
        if p["client_id"] == client_id and not p["is_placeholder"]
    ]
    return len(non_placeholder_plays) >= limit
```

Run test: **PASSES**

Commit: `[PHASE-2] test: add test for limit reached`
Commit: `[PHASE-2] feat: implement limit checking logic`

**♻️ REFACTOR**:
```python
def is_limit_reached(self, client_id):
    limit = self.limits.get(client_id, 3)
    play_count = self._count_non_placeholder_plays(client_id)
    return play_count >= limit

def _count_non_placeholder_plays(self, client_id):
    """Count non-placeholder plays for a client."""
    return sum(
        1 for p in self.plays
        if p["client_id"] == client_id and not p["is_placeholder"]
    )
```

Run test: **STILL PASSES**

Commit: `[PHASE-2] refactor: extract play counting logic`

### Example 2: Integration Test

After several TDD cycles, write integration tests:

```python
# test_integration.py
def test_full_daily_limit_flow():
    """
    Integration test: Verify complete flow from API call to database.
    """
    # Arrange
    client = TestClient(app)
    setup_test_database()
    add_test_videos(count=5)
    add_placeholder_video()

    # Act - Play videos up to limit
    response1 = client.get("/api/next?client_id=trolley1")
    response2 = client.get("/api/next?client_id=trolley1")
    response3 = client.get("/api/next?client_id=trolley1")
    response4 = client.get("/api/next?client_id=trolley1")

    # Assert
    assert response1.json()["placeholder"] is False
    assert response2.json()["placeholder"] is False
    assert response3.json()["placeholder"] is False
    assert response4.json()["placeholder"] is True  # Limit reached

    # Verify database state
    plays = get_play_log("trolley1")
    assert len(plays) == 4
    assert plays[-1].is_placeholder is True
```

---

## Coverage Targets

### Minimum Coverage Requirements

- **Server**: 85% coverage
- **Client**: 85% coverage
- **Admin**: 70% coverage

### What Coverage Means

Coverage is not a goal itself - it's a metric. High coverage with bad tests is worthless.

**Good coverage**:
- Tests actual behavior
- Tests edge cases
- Tests error handling
- Provides confidence

**Bad coverage**:
- Tests that don't assert anything
- Tests that can never fail
- Tests that test nothing meaningful

### Checking Coverage

```bash
# Python (pytest)
pytest --cov=src --cov-report=html --cov-report=term

# JavaScript (Vitest)
npm run test:coverage
```

---

## Checklist for Good Tests

Before committing your tests, verify:

- [ ] Test name clearly describes the expected behavior
- [ ] Test follows Arrange-Act-Assert structure
- [ ] Test is independent (doesn't rely on other tests)
- [ ] Test is fast (< 100ms for unit tests)
- [ ] Test actually fails when it should (verified by breaking the code)
- [ ] Test tests behavior, not implementation details
- [ ] Test includes edge cases and error cases, not just happy path
- [ ] Mock/stub external dependencies (database, network, filesystem)
- [ ] Test has a single clear reason to fail

---

## Summary

### The Golden Rules

1. **Always write tests first** - No exceptions
2. **Red, Green, Refactor** - Follow the cycle religiously
3. **Test behavior, not implementation** - Tests should survive refactoring
4. **One assert per concept** - Tests should have one reason to fail
5. **Fast, independent, repeatable** - Tests you'll actually run

### When You're Tempted to Skip TDD

**Temptation**: "This is too simple to test"
**Response**: Simple code still has edge cases. Write the test.

**Temptation**: "I'll write tests after I get it working"
**Response**: You won't. And the code will be harder to test. Write the test first.

**Temptation**: "I don't know how to test this"
**Response**: That's design feedback. Simplify the design until it's testable.

**Temptation**: "Tests slow me down"
**Response**: Tests speed you up by catching bugs early and enabling fearless refactoring.

### Remember

> The goal is not to have tests. The goal is to have working, maintainable code. Tests are how we get there.

Now go forth and TDD! 🚀

---

**Next Steps**: Return to [CLAUDE.md](../CLAUDE.md) and start implementing Phase 0 tasks.
