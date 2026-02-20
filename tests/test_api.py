"""
Tests para MedeX API REST
=========================
Tests unitarios y de integración para la API FastAPI.
"""

import pytest
from fastapi.testclient import TestClient

# Import with try/except for standalone testing
try:
    from api.auth import DEMO_API_KEY, _hash_key, validate_api_key
    from api.main import API_VERSION, app
    from api.models import Language, ResponseStatus, UrgencyLevel, UserType
    from api.services import get_ddx_service, get_kb_service, get_query_service
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from api.auth import DEMO_API_KEY, _hash_key, validate_api_key
    from api.main import API_VERSION, app
    from api.models import Language, ResponseStatus, UrgencyLevel, UserType
    from api.services import get_ddx_service, get_kb_service, get_query_service


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def client():
    """Create test client with exception handling disabled"""
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    """Headers with valid API key"""
    return {"X-API-Key": DEMO_API_KEY}


@pytest.fixture
def invalid_auth_headers():
    """Headers with invalid API key"""
    return {"X-API-Key": "invalid-key-12345"}


# =============================================================================
# AUTH TESTS
# =============================================================================


class TestAuthentication:
    """Tests for API authentication"""

    def test_demo_key_exists(self):
        """Verify demo key is defined"""
        assert DEMO_API_KEY is not None
        assert len(DEMO_API_KEY) > 10

    def test_validate_valid_key(self):
        """Validate demo API key"""
        result = validate_api_key(DEMO_API_KEY)
        assert result is not None
        assert "permissions" in result
        assert "query" in result["permissions"]

    def test_validate_invalid_key(self):
        """Validate invalid key returns None"""
        result = validate_api_key("invalid-key-12345")
        assert result is None

    def test_validate_empty_key(self):
        """Validate empty key returns None"""
        result = validate_api_key("")
        assert result is None

    def test_hash_key_consistent(self):
        """Hash function is consistent"""
        key = "test-key"
        hash1 = _hash_key(key)
        hash2 = _hash_key(key)
        assert hash1 == hash2

    def test_hash_key_unique(self):
        """Different keys produce different hashes"""
        hash1 = _hash_key("key1")
        hash2 = _hash_key("key2")
        assert hash1 != hash2


# =============================================================================
# HEALTH ENDPOINT TESTS
# =============================================================================


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_endpoint(self, client):
        """Health endpoint returns 200"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        """Health response has correct structure"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "components" in data

    def test_health_version(self, client):
        """Health returns correct version"""
        response = client.get("/health")
        data = response.json()
        assert data["version"] == API_VERSION

    def test_root_endpoint(self, client):
        """Root endpoint returns API info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data


# =============================================================================
# QUERY ENDPOINT TESTS
# =============================================================================


class TestQueryEndpoint:
    """Tests for medical query endpoint"""

    def test_query_requires_auth(self, client):
        """Query endpoint requires authentication"""
        response = client.post("/api/v1/query", json={"query": "diabetes"})
        assert response.status_code == 401

    def test_query_with_auth(self, client, auth_headers):
        """Query with valid auth returns 200"""
        response = client.post(
            "/api/v1/query", json={"query": "diabetes tipo 2"}, headers=auth_headers
        )
        assert response.status_code == 200

    def test_query_response_structure(self, client, auth_headers):
        """Query response has correct structure"""
        response = client.post(
            "/api/v1/query",
            json={"query": "hipertensión arterial"},
            headers=auth_headers,
        )
        data = response.json()

        assert "status" in data
        assert "query" in data
        assert "response" in data
        assert "language" in data
        assert "processing_time_ms" in data
        assert "disclaimer" in data

    def test_query_language_spanish(self, client, auth_headers):
        """Query returns Spanish response"""
        response = client.post(
            "/api/v1/query",
            json={"query": "diabetes", "language": "es"},
            headers=auth_headers,
        )
        data = response.json()
        assert data["language"] == "es"

    def test_query_language_english(self, client, auth_headers):
        """Query returns English response"""
        response = client.post(
            "/api/v1/query",
            json={"query": "diabetes", "language": "en"},
            headers=auth_headers,
        )
        data = response.json()
        assert data["language"] == "en"

    def test_query_emergency_detection(self, client, auth_headers):
        """Query detects emergency keywords"""
        response = client.post(
            "/api/v1/query",
            json={"query": "dolor en el pecho e infarto"},
            headers=auth_headers,
        )
        data = response.json()
        # May or may not be emergency depending on detection
        assert "is_emergency" in data

    def test_query_validation_short(self, client, auth_headers):
        """Query validation rejects short queries"""
        response = client.post(
            "/api/v1/query",
            json={"query": "ab"},  # Too short
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_query_with_sources(self, client, auth_headers):
        """Query includes sources when requested"""
        response = client.post(
            "/api/v1/query",
            json={"query": "metformina", "include_sources": True},
            headers=auth_headers,
        )
        data = response.json()
        assert "sources" in data


# =============================================================================
# DDX ENDPOINT TESTS
# =============================================================================


class TestDDxEndpoint:
    """Tests for differential diagnosis endpoint"""

    def test_ddx_requires_auth(self, client):
        """DDx endpoint requires authentication"""
        response = client.post("/api/v1/ddx", json={"symptom": "dolor torácico"})
        assert response.status_code == 401

    def test_ddx_with_auth(self, client, auth_headers):
        """DDx with valid auth returns 200"""
        response = client.post(
            "/api/v1/ddx", json={"symptom": "dolor torácico"}, headers=auth_headers
        )
        assert response.status_code == 200

    def test_ddx_response_structure(self, client, auth_headers):
        """DDx response has correct structure"""
        response = client.post(
            "/api/v1/ddx", json={"symptom": "cefalea"}, headers=auth_headers
        )
        data = response.json()

        assert "status" in data
        assert "symptom" in data
        assert "differentials" in data
        assert "total_count" in data
        assert "processing_time_ms" in data
        assert "disclaimer" in data

    def test_ddx_returns_diagnoses(self, client, auth_headers):
        """DDx returns list of diagnoses"""
        response = client.post(
            "/api/v1/ddx", json={"symptom": "dolor torácico"}, headers=auth_headers
        )
        data = response.json()

        # May return differentials if symptom is recognized
        assert isinstance(data["differentials"], list)

    def test_ddx_with_red_flags(self, client, auth_headers):
        """DDx includes red flags when requested"""
        response = client.post(
            "/api/v1/ddx",
            json={"symptom": "cefalea", "include_red_flags": True},
            headers=auth_headers,
        )
        data = response.json()

        # Check structure includes red_flags field
        for dx in data.get("differentials", []):
            assert "red_flags" in dx

    def test_ddx_symptoms_list(self, client, auth_headers):
        """Get available symptoms list"""
        response = client.get("/api/v1/ddx/symptoms", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert "symptoms" in data
        assert "count" in data
        assert isinstance(data["symptoms"], list)


# =============================================================================
# KB SEARCH ENDPOINT TESTS
# =============================================================================


class TestKBSearchEndpoint:
    """Tests for knowledge base search endpoint"""

    def test_kb_search_requires_auth(self, client):
        """KB search requires authentication"""
        response = client.post("/api/v1/kb/search", json={"query": "diabetes"})
        assert response.status_code == 401

    def test_kb_search_with_auth(self, client, auth_headers):
        """KB search with valid auth returns 200"""
        response = client.post(
            "/api/v1/kb/search", json={"query": "diabetes"}, headers=auth_headers
        )
        assert response.status_code == 200

    def test_kb_search_response_structure(self, client, auth_headers):
        """KB search response has correct structure"""
        response = client.post(
            "/api/v1/kb/search", json={"query": "metformina"}, headers=auth_headers
        )
        data = response.json()

        assert "status" in data
        assert "query" in data
        assert "results" in data
        assert "total_count" in data
        assert "limit" in data
        assert "offset" in data
        assert "processing_time_ms" in data

    def test_kb_search_returns_results(self, client, auth_headers):
        """KB search returns results for known terms"""
        response = client.post(
            "/api/v1/kb/search", json={"query": "diabetes"}, headers=auth_headers
        )
        data = response.json()

        assert isinstance(data["results"], list)

    def test_kb_search_pagination(self, client, auth_headers):
        """KB search respects pagination"""
        response = client.post(
            "/api/v1/kb/search",
            json={"query": "cardio", "limit": 5, "offset": 0},
            headers=auth_headers,
        )
        data = response.json()

        assert data["limit"] == 5
        assert data["offset"] == 0

    def test_kb_search_category_filter(self, client, auth_headers):
        """KB search filters by category"""
        response = client.post(
            "/api/v1/kb/search",
            json={"query": "diabetes", "category": "conditions"},
            headers=auth_headers,
        )
        data = response.json()

        # All results should be conditions
        for result in data.get("results", []):
            assert result["type"] == "condition"

    def test_kb_condition_by_icd10(self, client, auth_headers):
        """Get condition by ICD-10 code"""
        response = client.get("/api/v1/kb/conditions/E11", headers=auth_headers)
        # May return 200 or 404 depending on KB content
        assert response.status_code in [200, 404]

    def test_kb_condition_not_found(self, client, auth_headers):
        """Get non-existent condition returns 404"""
        response = client.get("/api/v1/kb/conditions/XXXXX", headers=auth_headers)
        assert response.status_code == 404


# =============================================================================
# STATS ENDPOINT TESTS
# =============================================================================


class TestStatsEndpoint:
    """Tests for statistics endpoint"""

    def test_stats_requires_auth(self, client):
        """Stats endpoint requires authentication"""
        response = client.get("/api/v1/stats")
        assert response.status_code == 401

    def test_stats_with_auth(self, client, auth_headers):
        """Stats with valid auth returns 200"""
        response = client.get("/api/v1/stats", headers=auth_headers)
        assert response.status_code == 200

    def test_stats_response_structure(self, client, auth_headers):
        """Stats response has correct structure"""
        response = client.get("/api/v1/stats", headers=auth_headers)
        data = response.json()

        assert "conditions_count" in data
        assert "medications_count" in data
        assert "symptoms_ddx_count" in data
        assert "languages_supported" in data
        assert "api_version" in data


# =============================================================================
# SERVICE TESTS
# =============================================================================


class TestServices:
    """Tests for API services"""

    def test_query_service_singleton(self):
        """Query service is singleton"""
        s1 = get_query_service()
        s2 = get_query_service()
        assert s1 is s2

    def test_ddx_service_singleton(self):
        """DDx service is singleton"""
        s1 = get_ddx_service()
        s2 = get_ddx_service()
        assert s1 is s2

    def test_kb_service_singleton(self):
        """KB service is singleton"""
        s1 = get_kb_service()
        s2 = get_kb_service()
        assert s1 is s2

    def test_query_service_initialized(self):
        """Query service initializes correctly"""
        service = get_query_service()
        assert hasattr(service, "_initialized")

    def test_ddx_service_initialized(self):
        """DDx service initializes correctly"""
        service = get_ddx_service()
        assert hasattr(service, "_initialized")

    def test_kb_service_initialized(self):
        """KB service initializes correctly"""
        service = get_kb_service()
        assert hasattr(service, "_initialized")


# =============================================================================
# MODEL TESTS
# =============================================================================


class TestModels:
    """Tests for Pydantic models"""

    def test_language_enum(self):
        """Language enum values"""
        assert Language.ES.value == "es"
        assert Language.EN.value == "en"

    def test_user_type_enum(self):
        """UserType enum values"""
        assert UserType.PROFESSIONAL.value == "professional"
        assert UserType.EDUCATIONAL.value == "educational"
        assert UserType.EMERGENCY.value == "emergency"

    def test_urgency_level_enum(self):
        """UrgencyLevel enum values"""
        assert UrgencyLevel.EMERGENT.value == "emergent"
        assert UrgencyLevel.URGENT.value == "urgent"

    def test_response_status_enum(self):
        """ResponseStatus enum values"""
        assert ResponseStatus.SUCCESS.value == "success"
        assert ResponseStatus.ERROR.value == "error"


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


class TestErrorHandling:
    """Tests for error handling"""

    def test_invalid_auth_returns_403(self, client, invalid_auth_headers):
        """Invalid API key returns 403"""
        response = client.post(
            "/api/v1/query", json={"query": "test query"}, headers=invalid_auth_headers
        )
        assert response.status_code == 403

    def test_missing_auth_returns_401(self, client):
        """Missing API key returns 401"""
        response = client.post("/api/v1/query", json={"query": "test query"})
        assert response.status_code == 401

    def test_invalid_json_returns_422(self, client, auth_headers):
        """Invalid JSON body returns 422"""
        response = client.post(
            "/api/v1/query",
            content="not valid json",
            headers={**auth_headers, "Content-Type": "application/json"},
        )
        assert response.status_code == 422

    def test_missing_required_field_returns_422(self, client, auth_headers):
        """Missing required field returns 422"""
        response = client.post(
            "/api/v1/query",
            json={},  # Missing 'query' field
            headers=auth_headers,
        )
        assert response.status_code == 422
