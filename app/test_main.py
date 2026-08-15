"""
Unit tests for the Hello World Flask application.

Tests cover all endpoints and the database connection helper using mocks
so no real database is required during CI.
"""

from unittest.mock import MagicMock, patch

import psycopg2
import pytest

from main import app, get_db_connection


@pytest.fixture
def client():
    """
    Provide a Flask test client with testing mode enabled.

    Yields:
        flask.testing.FlaskClient: Configured test client.
    """
    app.config["TESTING"] = True
    with app.test_client() as test_client:
        yield test_client


class TestHelloEndpoint:
    """Tests for the GET / endpoint."""

    def test_hello_returns_200(self, client):
        """Root endpoint should return HTTP 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_hello_returns_json_message(self, client):
        """Root endpoint should return Hello World message."""
        response = client.get("/")
        data = response.get_json()
        assert data["message"] == "Hello, World!"

    def test_hello_returns_ok_status(self, client):
        """Root endpoint should return status ok."""
        response = client.get("/")
        data = response.get_json()
        assert data["status"] == "ok"

    def test_hello_content_type_is_json(self, client):
        """Root endpoint should return Content-Type application/json."""
        response = client.get("/")
        assert "application/json" in response.content_type


class TestHealthEndpoint:
    """Tests for the GET /health endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        data = response.get_json()
        assert data["status"] == "healthy"


class TestDbCheckEndpoint:
    """Tests for the GET /db-check endpoint."""

    @patch("main.get_db_connection")
    def test_db_check_returns_200_when_connected(self, mock_conn_fn, client):
        """db-check should return 200 when database is reachable."""
        mock_conn_fn.return_value = MagicMock()
        response = client.get("/db-check")
        assert response.status_code == 200

    @patch("main.get_db_connection")
    def test_db_check_returns_connected_message(self, mock_conn_fn, client):
        """db-check should return connected message on success."""
        mock_conn_fn.return_value = MagicMock()
        response = client.get("/db-check")
        assert response.get_json()["database"] == "connected"

    @patch("main.get_db_connection")
    def test_db_check_returns_503_when_unreachable(self, mock_conn_fn, client):
        """db-check should return 503 when database is unreachable."""
        mock_conn_fn.return_value = None
        response = client.get("/db-check")
        assert response.status_code == 503

    @patch("main.get_db_connection")
    def test_db_check_returns_unreachable_message(self, mock_conn_fn, client):
        """db-check should return unreachable message on failure."""
        mock_conn_fn.return_value = None
        response = client.get("/db-check")
        assert response.get_json()["database"] == "unreachable"


class TestGetDbConnection:
    """Tests for the get_db_connection helper function."""

    @patch("main.psycopg2.connect")
    def test_returns_connection_on_success(self, mock_connect):
        """Should return a connection object when psycopg2 succeeds."""
        mock_connect.return_value = MagicMock()
        result = get_db_connection()
        assert result is not None

    @patch("main.psycopg2.connect")
    def test_returns_none_on_operational_error(self, mock_connect):
        """Should return None and not raise when database is unreachable."""
        mock_connect.side_effect = psycopg2.OperationalError("Connection refused")
        result = get_db_connection()
        assert result is None
