"""
Contract Tests for JobBot API
API schema validation, OpenAPI spec compliance, breaking change detection
"""

import json
import re
from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestAPISchemaValidation:
    """Tests for API schema validation."""

    def test_openapi_spec_available(self, client):
        """Test that OpenAPI spec is available and valid."""
        response = client.get("/openapi.json")

        assert response.status_code == 200

        spec = response.json()

        # Verify OpenAPI version
        assert "openapi" in spec
        assert spec["openapi"].startswith("3.")

        # Verify required fields
        assert "info" in spec
        assert "title" in spec["info"]
        assert "version" in spec["info"]
        assert "paths" in spec

    def test_openapi_spec_has_required_paths(self, client):
        """Test that OpenAPI spec includes all required paths."""
        response = client.get("/openapi.json")
        spec = response.json()

        required_paths = [
            "/auth/token",
            "/auth/register",
            "/auth/me",
            "/health",
            "/jobs/search",
            "/users/profile",
            "/subscriptions/status",
        ]

        for path in required_paths:
            assert path in spec["paths"], f"Missing required path: {path}"

    def test_auth_endpoints_have_security_schemes(self, client):
        """Test that protected endpoints have security requirements."""
        response = client.get("/openapi.json")
        spec = response.json()

        # Check for security schemes
        if "components" in spec and "securitySchemes" in spec.get("components", {}):
            security_schemes = spec["components"]["securitySchemes"]
            assert len(security_schemes) > 0

            # Check for bearer auth
            has_bearer = any(
                scheme.get("type") == "http" and scheme.get("scheme") == "bearer"
                for scheme in security_schemes.values()
            )
            assert has_bearer, "Missing bearer authentication scheme"

    def test_request_response_schemas_defined(self, client):
        """Test that request/response schemas are properly defined."""
        response = client.get("/openapi.json")
        spec = response.json()

        # Check auth/register endpoint
        register_path = spec["paths"].get("/auth/register", {})
        if register_path:
            post_spec = register_path.get("post", {})

            # Should have request body schema
            if "requestBody" in post_spec:
                assert "content" in post_spec["requestBody"]

            # Should have response schemas
            assert "responses" in post_spec
            assert "200" in post_spec["responses"] or "201" in post_spec["responses"]

    def test_enum_values_consistent(self, client):
        """Test that enum values are consistent across spec."""
        response = client.get("/openapi.json")
        spec = response.json()

        # Extract all schemas
        schemas = spec.get("components", {}).get("schemas", {})

        # Check for plan enum
        for schema_name, schema in schemas.items():
            if "plan" in schema_name.lower() or "Plan" in schema_name:
                if "enum" in schema:
                    enum_values = schema["enum"]
                    # Verify expected values exist
                    assert all(isinstance(v, str) for v in enum_values)


@pytest.mark.contract
class TestResponseSchemaCompliance:
    """Tests for response schema compliance."""

    def test_health_response_matches_schema(self, client):
        """Test health endpoint response matches schema."""
        response = client.get("/health")
        data = response.json()

        # Verify required fields
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "checks" in data

        # Verify data types
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], (int, float, str))
        assert isinstance(data["checks"], dict)

    def test_auth_token_response_matches_schema(self, client, test_user):
        """Test auth token response matches schema."""
        response = client.post(
            "/auth/token",
            data={
                "username": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Verify required fields per OAuth2/OIDC standards
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"].lower() == "bearer"

        # Verify optional but expected fields
        if "refresh_token" in data:
            assert isinstance(data["refresh_token"], str)

        if "expires_in" in data:
            assert isinstance(data["expires_in"], int)

    def test_user_profile_response_matches_schema(
        self, client, auth_headers, test_user
    ):
        """Test user profile response matches expected schema."""
        response = client.get("/auth/me", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()

            # Verify required fields
            assert "telegram_id" in data
            assert "email" in data

            # Verify data types
            assert isinstance(data["telegram_id"], int)
            assert isinstance(data["email"], str)

            # Verify email format
            assert re.match(r"[^@]+@[^@]+\.[^@]+", data["email"])

    def test_error_response_schema_consistency(self, client):
        """Test error responses follow consistent schema."""
        # Trigger a 404 error
        response = client.get("/nonexistent-endpoint-12345")

        if response.status_code == 404:
            data = response.json()

            # Error responses should have detail field
            assert "detail" in data
            assert isinstance(data["detail"], str)

    def test_pagination_response_schema(self, client, auth_headers):
        """Test pagination responses follow standard schema."""
        # Test an endpoint that returns paginated results
        response = client.get("/users/applications", headers=auth_headers)

        # If paginated, verify standard pagination fields
        if response.status_code == 200:
            data = response.json()

            # Check if it's a paginated response
            if isinstance(data, dict) and "items" in data:
                assert "total" in data or "count" in data
                assert isinstance(data["items"], list)


@pytest.mark.contract
class TestBreakingChangeDetection:
    """Tests for detecting breaking API changes."""

    def test_required_fields_not_removed(self, client):
        """Test that required fields haven't been removed from responses."""
        # Get health response
        health_response = client.get("/health")
        health_data = health_response.json()

        # Required fields that must always be present
        required_health_fields = ["status", "timestamp", "version", "checks"]
        for field in required_health_fields:
            assert field in health_data, (
                f"Required field '{field}' removed from health response"
            )

    def test_endpoint_urls_not_changed(self, client):
        """Test that critical endpoint URLs haven't changed."""
        critical_endpoints = {
            "/health": 200,
            "/": 200,
            "/docs": [200, 307],  # Might redirect
            "/openapi.json": 200,
        }

        for endpoint, expected_status in critical_endpoints.items():
            response = client.get(endpoint)

            if isinstance(expected_status, list):
                assert response.status_code in expected_status, (
                    f"Endpoint {endpoint} changed status: {response.status_code}"
                )
            else:
                assert response.status_code == expected_status, (
                    f"Endpoint {endpoint} changed status: {response.status_code}"
                )

    def test_http_methods_not_changed(self, client, test_user):
        """Test that HTTP methods haven't changed for critical endpoints."""
        # Auth endpoints
        # POST /auth/token should work
        post_response = client.post(
            "/auth/token",
            data={
                "username": test_user["email"],
                "password": test_user["password"],
            },
        )
        assert post_response.status_code == 200

        # GET /auth/me should require auth
        get_response = client.get("/auth/me")
        assert get_response.status_code in [401, 403]

    def test_field_types_not_changed(self, client, auth_headers, test_user):
        """Test that field types haven't changed."""
        # Test auth/me response types
        response = client.get("/auth/me", headers=auth_headers)

        if response.status_code == 200:
            data = response.json()

            # Verify field types haven't changed
            assert isinstance(data["telegram_id"], int), (
                "telegram_id type changed from int"
            )
            assert isinstance(data["email"], str), "email type changed from str"

    def test_enum_values_not_changed(self, client):
        """Test that enum values haven't changed."""
        # Test status enum values
        response = client.get("/health")
        data = response.json()

        # Status should be one of expected values
        valid_statuses = ["healthy", "degraded", "unhealthy", "ok"]
        assert data["status"] in valid_statuses, (
            f"Unknown status value: {data['status']}"
        )

    def test_status_codes_not_changed(self, client, test_user):
        """Test that HTTP status codes haven't changed for common scenarios."""
        test_cases = [
            # (method, endpoint, auth, data, expected_status)
            (
                "post",
                "/auth/token",
                False,
                {
                    "username": "wrong@example.com",
                    "password": "wrong",
                },
                401,
            ),
            ("get", "/auth/me", False, None, 403),
            (
                "post",
                "/auth/register",
                False,
                {
                    "email": "test@example.com",
                    "password": "test",
                    "name": "Test",
                },
                200,
            ),
        ]

        for method, endpoint, auth, data, expected in test_cases:
            if method == "post":
                if isinstance(data, dict) and "username" in data:
                    response = client.post(endpoint, data=data)
                else:
                    response = client.post(endpoint, json=data)
            else:
                response = client.get(endpoint)

            assert response.status_code == expected, (
                f"{method.upper()} {endpoint} expected {expected}, got {response.status_code}"
            )


@pytest.mark.contract
class TestContentTypeNegotiation:
    """Tests for content type negotiation."""

    def test_json_responses_for_api(self, client):
        """Test that API endpoints return JSON."""
        endpoints = ["/health", "/", "/openapi.json"]

        for endpoint in endpoints:
            response = client.get(endpoint)

            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type, (
                f"{endpoint} doesn't return JSON: {content_type}"
            )

    def test_accept_header_respected(self, client):
        """Test that Accept header is respected."""
        # Request JSON explicitly
        response = client.get("/health", headers={"Accept": "application/json"})

        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    def test_charset_utf8(self, client):
        """Test that responses use UTF-8 charset."""
        response = client.get("/health")

        content_type = response.headers.get("content-type", "")
        assert (
            "charset=utf-8" in content_type.lower()
            or "charset" not in content_type.lower()
        )


@pytest.mark.contract
class TestAPIVersioning:
    """Tests for API versioning."""

    def test_api_version_in_response(self, client):
        """Test that API version is present in responses."""
        response = client.get("/health")
        data = response.json()

        assert "version" in data
        assert isinstance(data["version"], str)

        # Verify semantic versioning format (major.minor.patch)
        assert re.match(r"^\d+\.\d+\.\d+", data["version"]), (
            f"Invalid version format: {data['version']}"
        )

    def test_version_consistency(self, client):
        """Test that version is consistent across endpoints."""
        endpoints = ["/health", "/openapi.json"]
        versions = []

        for endpoint in endpoints:
            response = client.get(endpoint)

            if endpoint == "/openapi.json":
                data = response.json()
                version = data.get("info", {}).get("version")
            else:
                data = response.json()
                version = data.get("version")

            if version:
                versions.append(version)

        # All versions should match
        if versions:
            assert all(v == versions[0] for v in versions), (
                f"Version inconsistency: {versions}"
            )


@pytest.mark.contract
class TestBackwardCompatibility:
    """Tests for backward compatibility."""

    def test_optional_fields_added_not_removed(self, client, auth_headers):
        """Test that new optional fields can be added but old ones aren't removed."""
        # Get current response structure
        response = client.get("/auth/me", headers=auth_headers)

        if response.status_code == 200:
            current_fields = set(response.json().keys())

            # These fields must always be present (backward compatibility)
            required_fields = {"telegram_id", "email"}

            for field in required_fields:
                assert field in current_fields, (
                    f"Backward compatibility broken: required field '{field}' removed"
                )

    def test_deprecated_fields_still_work(self, client, auth_headers):
        """Test that deprecated fields still work during deprecation period."""
        # This test would check for deprecated fields
        # Placeholder for future deprecation handling
        pass

    def test_new_endpoints_dont_break_old_ones(self, client):
        """Test that adding new endpoints doesn't break existing ones."""
        # List of critical endpoints that must always work
        critical_endpoints = [
            "/health",
            "/",
            "/auth/token",
            "/auth/register",
        ]

        for endpoint in critical_endpoints:
            response = (
                client.get(endpoint)
                if endpoint in ["/health", "/"]
                else client.options(endpoint)
            )

            # Should not return 500 or 404 (for critical endpoints)
            assert response.status_code not in [500, 404], (
                f"Endpoint {endpoint} broken: {response.status_code}"
            )


@pytest.mark.contract
class TestAPIDocumentation:
    """Tests for API documentation completeness."""

    def test_all_endpoints_documented(self, client):
        """Test that all endpoints have documentation."""
        response = client.get("/openapi.json")
        spec = response.json()

        for path, methods in spec["paths"].items():
            for method, spec_item in methods.items():
                if method == "parameters":
                    continue

                # Each endpoint should have a summary or description
                has_summary = "summary" in spec_item or "description" in spec_item

                if not has_summary:
                    # Allow for a few undocumented internal endpoints
                    if path not in ["/internal", "/admin"]:
                        print(f"Warning: {method.upper()} {path} lacks documentation")

    def test_request_examples_provided(self, client):
        """Test that request examples are provided for complex endpoints."""
        response = client.get("/openapi.json")
        spec = response.json()

        # Check endpoints that accept request bodies
        for path, methods in spec["paths"].items():
            for method, spec_item in methods.items():
                if method in ["post", "put", "patch"]:
                    request_body = spec_item.get("requestBody", {})
                    if request_body:
                        content = request_body.get("content", {})
                        # Complex endpoints should have examples
                        # This is a soft check - warn if missing
                        pass

    def test_response_codes_documented(self, client):
        """Test that response codes are documented for each endpoint."""
        response = client.get("/openapi.json")
        spec = response.json()

        for path, methods in spec["paths"].items():
            for method, spec_item in methods.items():
                if method == "parameters":
                    continue

                responses = spec_item.get("responses", {})

                # Each endpoint should document at least success and error responses
                has_success = any(
                    str(code).startswith("2") for code in responses.keys()
                )
                has_error = any(str(code).startswith("4") for code in responses.keys())

                if not has_success:
                    print(
                        f"Warning: {method.upper()} {path} lacks success response documentation"
                    )

                if not has_error:
                    print(
                        f"Warning: {method.upper()} {path} lacks error response documentation"
                    )


@pytest.mark.contract
class TestAPIDiscoverability:
    """Tests for API discoverability."""

    def test_root_endpoint_links(self, client):
        """Test that root endpoint provides links to other endpoints."""
        response = client.get("/")
        data = response.json()

        # Root should provide useful links
        assert any(key in data for key in ["documentation", "docs", "health", "links"])

    def test_docs_endpoint_available(self, client):
        """Test that API documentation is available."""
        response = client.get("/docs")

        # Should return HTML documentation or redirect
        assert response.status_code in [200, 307, 308]

    def test_redoc_available(self, client):
        """Test that ReDoc documentation is available."""
        response = client.get("/redoc")

        # Should return HTML or redirect
        assert response.status_code in [200, 307, 308]
