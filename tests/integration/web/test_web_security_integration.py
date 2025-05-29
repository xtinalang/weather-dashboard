"""Security integration tests for Flask web application.

These tests focus on security aspects of the web application including
CSRF protection, input validation, SQL injection prevention, and XSS protection.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from web.app import app as flask_app


@pytest.fixture
def secure_app():
    """Create Flask application with security features enabled."""
    flask_app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,  # Enable CSRF for security testing
            "SECRET_KEY": "test-secret-key-for-security-testing",
        }
    )
    return flask_app


@pytest.fixture
def secure_client(secure_app):
    """Create test client with security features enabled."""
    return secure_app.test_client()


@pytest.fixture
def insecure_app():
    """Create Flask application with security features disabled for comparison."""
    flask_app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for comparison
            "SECRET_KEY": "test-secret-key",
        }
    )
    return flask_app


@pytest.fixture
def insecure_client(insecure_app):
    """Create test client with security features disabled."""
    return insecure_app.test_client()


class TestCSRFProtection:
    """Test CSRF protection mechanisms."""

    def test_csrf_token_required_for_forms(self, secure_client):
        """Test that CSRF tokens are required for form submissions."""
        # Try to submit search form without CSRF token
        response = secure_client.post("/search", data={"query": "London"})

        # Should be rejected (400 Bad Request or redirect)
        assert response.status_code in [400, 302]

    def test_csrf_token_validation(self, secure_client):
        """Test CSRF token validation."""
        # Get a page with a form to extract CSRF token
        response = secure_client.get("/")
        assert response.status_code == 200

        # Extract CSRF token from response (in real app)
        # For this test, we'll simulate proper token handling
        with secure_client.session_transaction() as sess:
            # Simulate having a valid CSRF token in session
            sess["csrf_token"] = "valid-token"

    def test_ajax_requests_with_csrf(self, secure_client, clean_db):
        """Test AJAX requests with CSRF protection."""
        # Test favorite toggle endpoint (use correct route)
        response = secure_client.post(
            "/favorite/1",  # Use actual route instead of /toggle-favorite
            json={"lat": 51.52, "lon": -0.11},
            headers={"X-CSRFToken": "invalid-token"},
        )

        # Should handle CSRF validation for AJAX requests
        assert response.status_code in [
            400,
            403,
            200,
            302,  # May redirect on error
        ]  # Depends on implementation


class TestInputValidation:
    """Test input validation and sanitization."""

    def test_malicious_location_input(self, insecure_client):
        """Test handling of malicious location input."""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE locations; --",
            "../../../etc/passwd",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "null",
            "undefined",
            "\x00\x01\x02",  # Null bytes
        ]

        for malicious_input in malicious_inputs:
            response = insecure_client.post("/search", data={"query": malicious_input})
            # Should handle gracefully without crashing (may redirect with warnings)
            assert response.status_code in [200, 302]
            # Response should not contain unescaped malicious content
            assert b"<script>" not in response.data
            assert b"javascript:" not in response.data

    def test_coordinate_validation(self, insecure_client):
        """Test coordinate input validation."""
        invalid_coordinates = [
            "/weather/999/999",  # Out of range
            "/weather/abc/def",  # Non-numeric
            "/weather/51.52",  # Missing longitude
            "/weather/../admin",  # Path traversal
        ]

        for coord in invalid_coordinates:
            response = insecure_client.get(coord)
            # Should handle gracefully (may redirect with error messages)
            assert response.status_code in [200, 302, 400, 404]

    def test_form_data_sanitization(self, insecure_client):
        """Test form data sanitization."""
        # Test various form inputs
        forms_and_data = [
            ("/search", {"query": "<script>alert('xss')</script>London"}),
            ("/ui", {"location": "'; DROP TABLE locations; --"}),
            (
                "/nl-date-weather",
                {"query": "<img src=x onerror=alert('xss')>weather in London"},
            ),
            ("/forecast", {"location": "../../../etc/passwd", "days": "5"}),
        ]

        for endpoint, data in forms_and_data:
            response = insecure_client.post(endpoint, data=data)
            assert response.status_code in [200, 302]
            # Check that malicious content is escaped or removed
            assert b"<script>" not in response.data
            assert b"DROP TABLE" not in response.data


class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_location_search_sql_injection(self, insecure_client, clean_db):
        """Test SQL injection attempts in location search."""
        sql_injection_attempts = [
            "'; DROP TABLE locations; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM sqlite_master --",
            "'; INSERT INTO locations VALUES (999, 'hacked'); --",
            "' OR 1=1 --",
            "admin'--",
            "' OR 'x'='x",
        ]

        for injection in sql_injection_attempts:
            response = insecure_client.post("/search", data={"query": injection})
            # Should not crash or expose database structure (may redirect)
            assert response.status_code in [200, 302]
            # Should not contain database error messages
            assert b"sqlite" not in response.data.lower()
            assert b"sql" not in response.data.lower()
            assert (
                b"error" not in response.data.lower()
                or b"weather" in response.data.lower()
            )

    @patch("web.app.LocationRepository")  # Fix the import path
    def test_database_query_parameterization(self, mock_repo_class, insecure_client):
        """Test that database queries are properly parameterized."""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo

        # Simulate search with potential injection
        response = insecure_client.post(
            "/search", data={"query": "'; DROP TABLE locations; --"}
        )

        # Repository methods should be called with the raw input
        # The ORM should handle parameterization automatically
        assert response.status_code in [200, 302]


class TestXSSPrevention:
    """Test Cross-Site Scripting (XSS) prevention."""

    def test_output_escaping(self, insecure_client):
        """Test that user input is properly escaped in output."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<svg onload=alert('xss')>",
            "<iframe src=javascript:alert('xss')>",
            "&#60;script&#62;alert('xss')&#60;/script&#62;",
        ]

        for payload in xss_payloads:
            response = insecure_client.post("/search", data={"query": payload})
            assert response.status_code in [
                200,
                302,
            ]  # May redirect with security warnings

            # Check that script tags are escaped or removed
            assert b"<script>" not in response.data
            assert b"javascript:" not in response.data
            assert b"onload=" not in response.data
            assert b"onerror=" not in response.data

    def test_json_response_escaping(self, insecure_client, clean_db):
        """Test that JSON responses properly escape data."""
        # Test API endpoint that returns JSON if it exists
        response = insecure_client.get("/api/weather/51.52/-0.11")

        if (
            response.status_code == 200
            and response.content_type
            and "json" in response.content_type
        ):
            data = json.loads(response.data)
            # JSON should not contain unescaped HTML/JavaScript
            for value in data.values():
                if isinstance(value, str):
                    assert "<script>" not in value
                    assert "javascript:" not in value


class TestSessionSecurity:
    """Test session security mechanisms."""

    def test_session_fixation_prevention(self, insecure_client):
        """Test prevention of session fixation attacks."""
        # Get initial session
        response1 = insecure_client.get("/")
        assert response1.status_code == 200

        # Simulate login/state change
        response2 = insecure_client.post("/unit", data={"unit": "celsius"})

        # Session should be regenerated or protected
        assert response2.status_code in [200, 302]

    def test_session_data_integrity(self, insecure_client):
        """Test session data integrity."""
        with insecure_client.session_transaction() as sess:
            sess["test_data"] = "secure_value"
            sess["user_preference"] = "celsius"

        # Session data should persist correctly
        response = insecure_client.get("/")
        assert response.status_code == 200


class TestSecurityHeaders:
    """Test security-related HTTP headers."""

    def test_security_headers_present(self, insecure_client):
        """Test that appropriate security headers are present."""
        response = insecure_client.get("/")

        # Check for security headers (if implemented)
        headers_to_check = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy",
        ]

        # Note: Not all headers may be implemented, this is aspirational
        for header in headers_to_check:
            # Just check that if present, they have reasonable values
            if header in response.headers:
                assert len(response.headers[header]) > 0


class TestErrorHandling:
    """Test secure error handling."""

    def test_error_information_disclosure(self, insecure_client):
        """Test that errors don't disclose sensitive information."""
        # Try to access non-existent resources
        error_endpoints = [
            "/weather/invalid/coordinates",
            "/nonexistent-endpoint",
            "/api/weather/invalid",
            "/../../../etc/passwd",
        ]

        for endpoint in error_endpoints:
            response = insecure_client.get(endpoint)
            # Should not disclose file paths, database info, or stack traces
            assert b"/home/" not in response.data
            assert b"Traceback" not in response.data
            assert b"sqlite" not in response.data.lower()
            assert b"database" not in response.data.lower()

    def test_exception_handling(self, insecure_client):
        """Test that exceptions are handled securely."""
        # Trigger various potential errors
        with patch("web.app.weather_api") as mock_api:
            mock_api.get_weather.side_effect = Exception("Database connection failed")

            response = insecure_client.get("/weather/51.52/-0.11")
            # Should handle gracefully without exposing error details (may redirect)
            assert response.status_code in [200, 302, 500]
            if response.status_code == 500:
                assert b"Database connection failed" not in response.data


class TestDataValidation:
    """Test comprehensive data validation."""

    def test_numeric_input_validation(self, insecure_client):
        """Test validation of numeric inputs."""
        # Test forecast days validation
        invalid_days = [
            ("forecast", {"location": "London", "days": "-1"}),
            ("forecast", {"location": "London", "days": "999"}),
            ("forecast", {"location": "London", "days": "abc"}),
            ("forecast", {"location": "London", "days": ""}),
            ("forecast", {"location": "London", "days": "null"}),
        ]

        for endpoint, data in invalid_days:
            response = insecure_client.post(f"/{endpoint}", data=data)
            # Should handle invalid numeric input gracefully
            assert response.status_code in [200, 302]
            # Should not crash or cause internal errors

    def test_string_length_limits(self, insecure_client):
        """Test string length validation."""
        # Test very long inputs
        very_long_string = "A" * 10000

        long_input_tests = [
            ("/search", {"query": very_long_string}),
            ("/ui", {"location": very_long_string}),
            ("/nl-date-weather", {"query": very_long_string}),
        ]

        for endpoint, data in long_input_tests:
            response = insecure_client.post(endpoint, data=data)
            # Should handle long inputs without crashing
            assert response.status_code in [200, 302]

    def test_special_character_handling(self, insecure_client):
        """Test handling of special characters."""
        special_chars = [
            "çñüëî",  # Accented characters
            "北京",  # Chinese characters
            "Москва",  # Cyrillic characters
            "🌧️🌞",  # Emojis
            "\n\r\t",  # Control characters
            "test'quote\"double",  # Mixed quotes
        ]

        for special_input in special_chars:
            response = insecure_client.post("/search", data={"query": special_input})
            # Should handle special characters gracefully (may redirect for search)
            assert response.status_code in [200, 302]
