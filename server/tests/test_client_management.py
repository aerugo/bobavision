"""Tests for client management API endpoints.

Following TDD principles:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve code while keeping tests green
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient


@pytest.fixture
def client_with_db(db_session, monkeypatch):
    """Create test client with database override."""
    from src.main import app
    from src.db.database import get_db

    # Mock init_db to prevent startup event from initializing wrong database
    import src.db.database
    monkeypatch.setattr(src.db.database, "init_db", lambda: None)

    # Override database dependency to use test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass  # Don't close test session

    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_clients(db_session):
    """Create sample clients in database."""
    from src.db.repositories import ClientRepository

    repo = ClientRepository(db_session)
    clients = [
        repo.create(client_id="client1", friendly_name="Living Room Pi", daily_limit=3),
        repo.create(client_id="client2", friendly_name="Bedroom Pi", daily_limit=5),
        repo.create(client_id="client3", friendly_name="Kitchen Pi", daily_limit=2),
    ]
    return clients


# GET /api/clients - List all clients
def test_get_clients_returns_empty_list_when_no_clients(client_with_db):
    """Test that GET /api/clients returns empty list when no clients exist.

    RED phase: Endpoint doesn't exist yet.
    """
    # Act
    response = client_with_db.get("/api/clients")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_clients_returns_all_clients(client_with_db, sample_clients):
    """Test that GET /api/clients returns all clients."""
    # Act
    response = client_with_db.get("/api/clients")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 3

    # Check that all clients are present
    client_ids = {c["client_id"] for c in data}
    assert client_ids == {"client1", "client2", "client3"}

    # Check structure of first client
    client = data[0]
    assert "client_id" in client
    assert "friendly_name" in client
    assert "daily_limit" in client
    assert "tag_filters" in client
    assert "created_at" in client
    assert "updated_at" in client


def test_get_clients_returns_clients_sorted_by_id(client_with_db, sample_clients):
    """Test that clients are returned in consistent order."""
    # Act
    response = client_with_db.get("/api/clients")

    # Assert
    assert response.status_code == 200
    data = response.json()

    client_ids = [c["client_id"] for c in data]
    assert client_ids == sorted(client_ids)


# GET /api/clients/{client_id} - Get single client
def test_get_client_by_id_returns_client_details(client_with_db, sample_clients):
    """Test that GET /api/clients/{client_id} returns client details."""
    # Act
    response = client_with_db.get("/api/clients/client1")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["client_id"] == "client1"
    assert data["friendly_name"] == "Living Room Pi"
    assert data["daily_limit"] == 3
    assert data["tag_filters"] is None
    assert "created_at" in data
    assert "updated_at" in data


def test_get_client_by_id_returns_404_for_nonexistent_client(client_with_db):
    """Test that GET /api/clients/{client_id} returns 404 for nonexistent client."""
    # Act
    response = client_with_db.get("/api/clients/nonexistent")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# POST /api/clients - Create new client
def test_create_client_with_minimal_data(client_with_db):
    """Test that POST /api/clients creates a new client with minimal data.

    Only client_id and friendly_name are required.
    """
    # Arrange
    new_client = {
        "client_id": "new_client",
        "friendly_name": "New Client"
    }

    # Act
    response = client_with_db.post("/api/clients", json=new_client)

    # Assert
    assert response.status_code == 201
    data = response.json()

    assert data["client_id"] == "new_client"
    assert data["friendly_name"] == "New Client"
    assert data["daily_limit"] == 3  # Default value
    assert data["tag_filters"] is None
    assert "created_at" in data
    assert "updated_at" in data


def test_create_client_with_all_fields(client_with_db):
    """Test that POST /api/clients creates a client with all fields specified."""
    # Arrange
    new_client = {
        "client_id": "custom_client",
        "friendly_name": "Custom Client",
        "daily_limit": 10,
        "tag_filters": "educational,cartoons"
    }

    # Act
    response = client_with_db.post("/api/clients", json=new_client)

    # Assert
    assert response.status_code == 201
    data = response.json()

    assert data["client_id"] == "custom_client"
    assert data["friendly_name"] == "Custom Client"
    assert data["daily_limit"] == 10
    assert data["tag_filters"] == "educational,cartoons"


def test_create_client_rejects_duplicate_client_id(client_with_db, sample_clients):
    """Test that POST /api/clients returns 409 for duplicate client_id."""
    # Arrange
    duplicate_client = {
        "client_id": "client1",  # Already exists
        "friendly_name": "Duplicate"
    }

    # Act
    response = client_with_db.post("/api/clients", json=duplicate_client)

    # Assert
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data


def test_create_client_validates_required_fields(client_with_db):
    """Test that POST /api/clients validates required fields."""
    # Arrange - Missing friendly_name
    incomplete_client = {
        "client_id": "incomplete"
    }

    # Act
    response = client_with_db.post("/api/clients", json=incomplete_client)

    # Assert
    assert response.status_code == 422  # Validation error


def test_create_client_validates_daily_limit_positive(client_with_db):
    """Test that daily_limit must be positive."""
    # Arrange
    invalid_client = {
        "client_id": "invalid",
        "friendly_name": "Invalid",
        "daily_limit": -1
    }

    # Act
    response = client_with_db.post("/api/clients", json=invalid_client)

    # Assert
    assert response.status_code == 422  # Validation error


# PATCH /api/clients/{client_id} - Update client
def test_update_client_friendly_name(client_with_db, sample_clients):
    """Test that PATCH /api/clients/{client_id} updates friendly_name."""
    # Arrange
    update_data = {
        "friendly_name": "Updated Living Room"
    }

    # Act
    response = client_with_db.patch("/api/clients/client1", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["client_id"] == "client1"
    assert data["friendly_name"] == "Updated Living Room"
    assert data["daily_limit"] == 3  # Unchanged


def test_update_client_daily_limit(client_with_db, sample_clients):
    """Test that PATCH /api/clients/{client_id} updates daily_limit."""
    # Arrange
    update_data = {
        "daily_limit": 7
    }

    # Act
    response = client_with_db.patch("/api/clients/client1", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["client_id"] == "client1"
    assert data["daily_limit"] == 7
    assert data["friendly_name"] == "Living Room Pi"  # Unchanged


def test_update_client_tag_filters(client_with_db, sample_clients):
    """Test that PATCH /api/clients/{client_id} updates tag_filters."""
    # Arrange
    update_data = {
        "tag_filters": "educational,bedtime"
    }

    # Act
    response = client_with_db.patch("/api/clients/client1", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["client_id"] == "client1"
    assert data["tag_filters"] == "educational,bedtime"


def test_update_client_multiple_fields(client_with_db, sample_clients):
    """Test that PATCH /api/clients/{client_id} can update multiple fields."""
    # Arrange
    update_data = {
        "friendly_name": "New Name",
        "daily_limit": 5,
        "tag_filters": "cartoons"
    }

    # Act
    response = client_with_db.patch("/api/clients/client1", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["client_id"] == "client1"
    assert data["friendly_name"] == "New Name"
    assert data["daily_limit"] == 5
    assert data["tag_filters"] == "cartoons"


def test_update_client_returns_404_for_nonexistent_client(client_with_db):
    """Test that PATCH /api/clients/{client_id} returns 404 for nonexistent client."""
    # Arrange
    update_data = {
        "friendly_name": "Updated"
    }

    # Act
    response = client_with_db.patch("/api/clients/nonexistent", json=update_data)

    # Assert
    assert response.status_code == 404


def test_update_client_cannot_change_client_id(client_with_db, sample_clients):
    """Test that client_id cannot be changed via PATCH."""
    # Arrange
    update_data = {
        "client_id": "new_id"  # Should be ignored
    }

    # Act
    response = client_with_db.patch("/api/clients/client1", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()

    # client_id should remain unchanged
    assert data["client_id"] == "client1"


def test_update_client_validates_daily_limit_positive(client_with_db, sample_clients):
    """Test that PATCH validates daily_limit is positive."""
    # Arrange
    update_data = {
        "daily_limit": 0
    }

    # Act
    response = client_with_db.patch("/api/clients/client1", json=update_data)

    # Assert
    assert response.status_code == 422  # Validation error


def test_update_client_updates_updated_at_timestamp(client_with_db, sample_clients, db_session):
    """Test that PATCH updates the updated_at timestamp."""
    # Arrange
    from src.db.repositories import ClientRepository
    repo = ClientRepository(db_session)

    original_client = repo.get_by_id("client1")
    original_updated_at = original_client.updated_at

    update_data = {
        "friendly_name": "Updated Name"
    }

    # Act
    response = client_with_db.patch("/api/clients/client1", json=update_data)

    # Assert
    assert response.status_code == 200

    updated_client = repo.get_by_id("client1")
    assert updated_client.updated_at > original_updated_at


# PUT /api/clients/{client_id} - Update client (alternative to PATCH)
def test_put_client_updates_settings(client_with_db, sample_clients):
    """Test that PUT /api/clients/{client_id} updates client settings.

    RED phase: PUT method not supported yet, should return 405.
    This test reproduces the error: PUT /api/clients/local-test-client returns 405.
    """
    # Arrange
    update_data = {
        "friendly_name": "Updated Living Room",
        "daily_limit": 5,
        "tag_filters": "educational"
    }

    # Act
    response = client_with_db.put("/api/clients/client1", json=update_data)

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["client_id"] == "client1"
    assert data["friendly_name"] == "Updated Living Room"
    assert data["daily_limit"] == 5
    assert data["tag_filters"] == "educational"


def test_put_client_returns_404_for_nonexistent_client(client_with_db):
    """Test that PUT /api/clients/{client_id} returns 404 for nonexistent client."""
    # Arrange
    update_data = {
        "friendly_name": "Updated"
    }

    # Act
    response = client_with_db.put("/api/clients/nonexistent", json=update_data)

    # Assert
    assert response.status_code == 404
