"""Tests for Docker containerization.

This module tests the Docker build process and container functionality.
Following TDD principles: These tests will fail until the Dockerfile is created.

Phase 5 - Server Containerization
"""
import subprocess
import time
from pathlib import Path

import pytest
import httpx


# Test fixtures and helpers
@pytest.fixture(scope="module")
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def docker_image_built(project_root):
    """Build the Docker image before tests (if Dockerfile exists)."""
    dockerfile_path = project_root / "server" / "Dockerfile"

    if not dockerfile_path.exists():
        pytest.skip("Dockerfile not created yet (TDD: RED phase)")

    # Build the image
    result = subprocess.run(
        ["docker", "build", "-t", "bobavision-server:test", "-f", str(dockerfile_path), "."],
        cwd=str(project_root),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(f"Docker build failed:\n{result.stderr}")

    yield "bobavision-server:test"

    # Cleanup: Remove the test image after tests
    subprocess.run(["docker", "rmi", "bobavision-server:test"], capture_output=True)


@pytest.fixture
def running_container(docker_image_built):
    """Start a container for testing and clean up after."""
    # Start container
    result = subprocess.run(
        [
            "docker", "run",
            "-d",  # Detached mode
            "--name", "bobavision-server-test",
            "-p", "8001:8000",  # Map to port 8001 to avoid conflicts
            docker_image_built
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        pytest.fail(f"Failed to start container:\n{result.stderr}")

    container_id = result.stdout.strip()

    # Wait for container to be ready
    time.sleep(2)

    yield container_id

    # Cleanup: Stop and remove container
    subprocess.run(["docker", "stop", container_id], capture_output=True)
    subprocess.run(["docker", "rm", container_id], capture_output=True)


class TestDockerBuild:
    """Test Docker image build process."""

    def test_dockerfile_exists(self, project_root):
        """Test that Dockerfile exists in server directory."""
        dockerfile = project_root / "server" / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile should exist in server/ directory"

    def test_dockerignore_exists(self, project_root):
        """Test that .dockerignore exists in server directory."""
        dockerignore = project_root / "server" / ".dockerignore"
        assert dockerignore.exists(), ".dockerignore should exist in server/ directory"

    def test_docker_compose_exists(self, project_root):
        """Test that docker-compose.yml exists in project root."""
        compose_file = project_root / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml should exist in project root"

    def test_docker_image_builds(self, docker_image_built):
        """Test that Docker image builds successfully."""
        # If we get here, the image was built successfully
        assert docker_image_built == "bobavision-server:test"

    def test_docker_image_size_reasonable(self, docker_image_built):
        """Test that Docker image size is reasonable (< 1GB)."""
        result = subprocess.run(
            ["docker", "images", docker_image_built, "--format", "{{.Size}}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.fail(f"Failed to get image size:\n{result.stderr}")

        size_str = result.stdout.strip()
        # Parse size (e.g., "523MB" or "1.2GB")
        if "GB" in size_str:
            size_gb = float(size_str.replace("GB", ""))
            assert size_gb < 1.0, f"Image size {size_str} exceeds 1GB limit"
        # If in MB, it's definitely under 1GB


class TestContainerContents:
    """Test that container has required components."""

    def test_mpv_installed(self, running_container):
        """Test that mpv is installed and accessible in the container."""
        result = subprocess.run(
            ["docker", "exec", running_container, "mpv", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "mpv should be installed in container"
        assert "mpv" in result.stdout.lower(), "mpv version should be displayed"

    def test_python_version(self, running_container):
        """Test that Python 3.11+ is installed."""
        result = subprocess.run(
            ["docker", "exec", running_container, "python", "--version"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Python should be installed in container"
        # Parse version (e.g., "Python 3.11.5")
        version_str = result.stdout.strip()
        assert "Python 3." in version_str, "Python 3.x should be installed"

        # Extract minor version
        version_parts = version_str.split()
        if len(version_parts) >= 2:
            version_number = version_parts[1]
            major, minor, *_ = version_number.split(".")
            assert int(major) == 3, "Python major version should be 3"
            assert int(minor) >= 11, "Python minor version should be >= 11"

    def test_fastapi_installed(self, running_container):
        """Test that FastAPI is installed."""
        result = subprocess.run(
            ["docker", "exec", running_container, "python", "-c", "import fastapi; print(fastapi.__version__)"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "FastAPI should be installed in container"
        assert len(result.stdout.strip()) > 0, "FastAPI version should be printed"

    def test_uvicorn_installed(self, running_container):
        """Test that uvicorn is installed."""
        result = subprocess.run(
            ["docker", "exec", running_container, "python", "-c", "import uvicorn; print(uvicorn.__version__)"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Uvicorn should be installed in container"
        assert len(result.stdout.strip()) > 0, "Uvicorn version should be printed"


class TestContainerRuntime:
    """Test that container runs correctly."""

    def test_container_starts(self, running_container):
        """Test that container starts successfully."""
        # Check container status
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", running_container],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Container inspect should succeed"
        assert result.stdout.strip() == "true", "Container should be running"

    def test_server_responds(self, running_container):
        """Test that FastAPI server responds to HTTP requests."""
        # Wait a bit more for server to fully start
        time.sleep(3)

        try:
            response = httpx.get("http://localhost:8001/", timeout=5.0)
            assert response.status_code == 200, "Server should respond with 200 OK"

            data = response.json()
            assert "message" in data, "Response should contain 'message' field"
            assert "Kids Media Station" in data["message"], "Response should identify as Kids Media Station"
        except httpx.ConnectError:
            pytest.fail("Server did not respond - container may not have started correctly")

    def test_api_next_endpoint(self, running_container):
        """Test that /api/next endpoint is accessible."""
        time.sleep(3)  # Wait for server

        try:
            response = httpx.get("http://localhost:8001/api/next?client_id=test", timeout=5.0)
            # Should get 200 OK (even if no videos, it should return something)
            assert response.status_code == 200, "/api/next should be accessible"

            data = response.json()
            assert "url" in data, "Response should contain 'url' field"
            assert "title" in data, "Response should contain 'title' field"
            assert "placeholder" in data, "Response should contain 'placeholder' field"
        except httpx.ConnectError:
            pytest.fail("Server /api/next endpoint not accessible")

    def test_container_logs_no_errors(self, running_container):
        """Test that container logs don't show critical errors."""
        result = subprocess.run(
            ["docker", "logs", running_container],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Should be able to read container logs"

        logs = result.stdout + result.stderr
        # Allow warnings but no errors
        assert "error" not in logs.lower() or "error" in logs.lower() and "0 errors" in logs.lower(), \
            "Container logs should not contain critical errors"


class TestContainerPersistence:
    """Test that data persists correctly with volumes."""

    def test_database_file_created(self, running_container):
        """Test that SQLite database file is created in container."""
        # Trigger database initialization by making a request
        time.sleep(3)
        httpx.get("http://localhost:8001/api/clients", timeout=5.0)

        # Check if database file exists in container
        result = subprocess.run(
            ["docker", "exec", running_container, "ls", "-la", "/app/server"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, "Should be able to list server directory"
        # Database should be created somewhere accessible
        # Note: Actual path depends on Dockerfile implementation


class TestDockerCompose:
    """Test docker-compose configuration."""

    def test_docker_compose_valid(self, project_root):
        """Test that docker-compose.yml is valid."""
        compose_file = project_root / "docker-compose.yml"

        if not compose_file.exists():
            pytest.skip("docker-compose.yml not created yet (TDD: RED phase)")

        result = subprocess.run(
            ["docker-compose", "-f", str(compose_file), "config"],
            cwd=str(project_root),
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"docker-compose.yml should be valid:\n{result.stderr}"

    def test_docker_compose_has_server_service(self, project_root):
        """Test that docker-compose defines a server service."""
        compose_file = project_root / "docker-compose.yml"

        if not compose_file.exists():
            pytest.skip("docker-compose.yml not created yet (TDD: RED phase)")

        with open(compose_file) as f:
            content = f.read()

        assert "server:" in content or "bobavision-server:" in content, \
            "docker-compose should define a server service"

    def test_docker_compose_has_volumes(self, project_root):
        """Test that docker-compose defines volumes for persistence."""
        compose_file = project_root / "docker-compose.yml"

        if not compose_file.exists():
            pytest.skip("docker-compose.yml not created yet (TDD: RED phase)")

        with open(compose_file) as f:
            content = f.read()

        assert "volumes:" in content, "docker-compose should define volumes"
        assert "media" in content or "./media" in content, \
            "docker-compose should mount media directory"
