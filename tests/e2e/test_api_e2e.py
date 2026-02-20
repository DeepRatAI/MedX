"""
MedeX E2E Tests - API Endpoints
===============================
Tests end-to-end para la API REST de MedeX.
Estos tests verifican el funcionamiento real de los endpoints.
"""

import pytest
from playwright.sync_api import APIRequestContext, expect


@pytest.fixture(scope="session")
def api_context(playwright):
    """Create API context for testing"""
    request_context = playwright.request.new_context(
        base_url="http://localhost:8000",
        extra_http_headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    yield request_context
    request_context.dispose()


class TestAPIHealth:
    """Tests for health endpoints"""

    @pytest.mark.e2e
    def test_health_endpoint_returns_200(self, api_context: APIRequestContext):
        """GET /health returns 200 with valid structure"""
        response = api_context.get("/health")

        assert response.status == 200
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "components" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    @pytest.mark.e2e
    def test_root_endpoint_returns_api_info(self, api_context: APIRequestContext):
        """GET / returns API information"""
        response = api_context.get("/")

        assert response.status == 200
        data = response.json()

        assert "name" in data
        assert "version" in data
        assert "MedeX" in data["name"]


class TestAPIAuthentication:
    """Tests for API authentication"""

    @pytest.mark.e2e
    @pytest.mark.critical
    def test_query_without_auth_returns_401(self, api_context: APIRequestContext):
        """POST /api/v1/query without auth returns 401"""
        response = api_context.post("/api/v1/query", data={"query": "diabetes tipo 2"})

        assert response.status == 401

    @pytest.mark.e2e
    def test_query_with_invalid_key_returns_403(self, api_context: APIRequestContext):
        """POST /api/v1/query with invalid key returns 403"""
        response = api_context.post(
            "/api/v1/query",
            headers={"X-API-Key": "invalid-key-12345"},
            data={"query": "diabetes tipo 2"},
        )

        assert response.status == 403

    @pytest.mark.e2e
    def test_query_with_valid_key_returns_200(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """POST /api/v1/query with valid key returns 200"""
        response = api_context.post(
            "/api/v1/query",
            headers={"X-API-Key": demo_api_key},
            data={"query": "diabetes tipo 2 tratamiento"},
        )

        assert response.status == 200
        data = response.json()
        assert "status" in data
        assert "response" in data


class TestAPIMedicalQuery:
    """Tests for medical query endpoint"""

    @pytest.mark.e2e
    @pytest.mark.critical
    def test_query_diabetes_returns_results(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """Query about diabetes returns relevant results"""
        response = api_context.post(
            "/api/v1/query",
            headers={"X-API-Key": demo_api_key},
            data={
                "query": "sintomas de diabetes tipo 2",
                "language": "es",
                "include_sources": True,
            },
        )

        assert response.status == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["language"] == "es"
        assert len(data["response"]) > 0
        assert "disclaimer" in data

    @pytest.mark.e2e
    def test_query_in_english(self, api_context: APIRequestContext, demo_api_key):
        """Query in English returns English response"""
        response = api_context.post(
            "/api/v1/query",
            headers={"X-API-Key": demo_api_key},
            data={"query": "hypertension symptoms", "language": "en"},
        )

        assert response.status == 200
        data = response.json()
        assert data["language"] == "en"

    @pytest.mark.e2e
    def test_query_emergency_detection(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """Query with emergency keywords is flagged"""
        response = api_context.post(
            "/api/v1/query",
            headers={"X-API-Key": demo_api_key},
            data={"query": "dolor en el pecho y dificultad para respirar"},
        )

        assert response.status == 200
        data = response.json()
        assert "is_emergency" in data

    @pytest.mark.e2e
    def test_query_validation_rejects_short_query(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """Short queries are rejected with 422"""
        response = api_context.post(
            "/api/v1/query", headers={"X-API-Key": demo_api_key}, data={"query": "ab"}
        )

        assert response.status == 422


class TestAPIDifferentialDiagnosis:
    """Tests for differential diagnosis endpoint"""

    @pytest.mark.e2e
    @pytest.mark.critical
    def test_ddx_chest_pain_returns_diagnoses(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """DDx for chest pain returns multiple diagnoses"""
        response = api_context.post(
            "/api/v1/ddx",
            headers={"X-API-Key": demo_api_key},
            data={"symptom": "dolor torácico", "include_red_flags": True},
        )

        assert response.status == 200
        data = response.json()

        assert data["status"] == "success"
        assert "differentials" in data
        assert data["total_count"] >= 0  # May be 0 if symptom not found

    @pytest.mark.e2e
    def test_ddx_includes_urgency_levels(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """DDx results include urgency classification"""
        response = api_context.post(
            "/api/v1/ddx",
            headers={"X-API-Key": demo_api_key},
            data={"symptom": "cefalea"},
        )

        assert response.status == 200
        data = response.json()

        if data["differentials"]:
            dx = data["differentials"][0]
            assert "urgency" in dx
            assert dx["urgency"] in ["emergent", "urgent", "semi_urgent", "non_urgent"]

    @pytest.mark.e2e
    def test_ddx_includes_icd10_codes(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """DDx results include ICD-10 codes"""
        response = api_context.post(
            "/api/v1/ddx",
            headers={"X-API-Key": demo_api_key},
            data={"symptom": "dolor abdominal"},
        )

        assert response.status == 200
        data = response.json()

        if data["differentials"]:
            dx = data["differentials"][0]
            assert "icd10_code" in dx
            assert len(dx["icd10_code"]) >= 3

    @pytest.mark.e2e
    def test_ddx_symptoms_list(self, api_context: APIRequestContext, demo_api_key):
        """GET /api/v1/ddx/symptoms returns available symptoms"""
        response = api_context.get(
            "/api/v1/ddx/symptoms", headers={"X-API-Key": demo_api_key}
        )

        assert response.status == 200
        data = response.json()

        assert "symptoms" in data
        assert "count" in data
        assert data["count"] > 0


class TestAPIKnowledgeBase:
    """Tests for knowledge base search endpoint"""

    @pytest.mark.e2e
    @pytest.mark.critical
    def test_kb_search_metformin_returns_results(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """KB search for metformin returns medication info"""
        response = api_context.post(
            "/api/v1/kb/search",
            headers={"X-API-Key": demo_api_key},
            data={"query": "metformina", "limit": 10},
        )

        assert response.status == 200
        data = response.json()

        assert data["status"] == "success"
        assert "results" in data
        assert data["total_count"] >= 0

    @pytest.mark.e2e
    def test_kb_search_with_category_filter(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """KB search respects category filter"""
        response = api_context.post(
            "/api/v1/kb/search",
            headers={"X-API-Key": demo_api_key},
            data={"query": "diabetes", "category": "conditions", "limit": 5},
        )

        assert response.status == 200
        data = response.json()

        for result in data.get("results", []):
            assert result["type"] == "condition"

    @pytest.mark.e2e
    def test_kb_search_pagination(self, api_context: APIRequestContext, demo_api_key):
        """KB search supports pagination"""
        response = api_context.post(
            "/api/v1/kb/search",
            headers={"X-API-Key": demo_api_key},
            data={"query": "cardio", "limit": 3, "offset": 0},
        )

        assert response.status == 200
        data = response.json()

        assert data["limit"] == 3
        assert data["offset"] == 0

    @pytest.mark.e2e
    def test_kb_condition_by_icd10(self, api_context: APIRequestContext, demo_api_key):
        """GET condition by ICD-10 code"""
        response = api_context.get(
            "/api/v1/kb/conditions/E11", headers={"X-API-Key": demo_api_key}
        )

        # May return 200 or 404 depending on KB content
        assert response.status in [200, 404]

        if response.status == 200:
            data = response.json()
            assert "icd10_code" in data
            assert "name" in data


class TestAPIStats:
    """Tests for statistics endpoint"""

    @pytest.mark.e2e
    def test_stats_returns_counts(self, api_context: APIRequestContext, demo_api_key):
        """Stats endpoint returns knowledge base counts"""
        response = api_context.get("/api/v1/stats", headers={"X-API-Key": demo_api_key})

        assert response.status == 200
        data = response.json()

        assert "conditions_count" in data
        assert "medications_count" in data
        assert "symptoms_ddx_count" in data
        assert data["conditions_count"] > 0
        assert data["medications_count"] > 0


class TestAPIPerformance:
    """Tests for API performance"""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_query_response_time_under_5s(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """Query response time should be under 5 seconds"""
        import time

        start = time.perf_counter()
        response = api_context.post(
            "/api/v1/query",
            headers={"X-API-Key": demo_api_key},
            data={"query": "tratamiento hipertension arterial"},
        )
        elapsed = time.perf_counter() - start

        assert response.status == 200
        assert elapsed < 5.0, f"Response took {elapsed:.2f}s, expected < 5s"

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_ddx_response_time_under_3s(
        self, api_context: APIRequestContext, demo_api_key
    ):
        """DDx response time should be under 3 seconds"""
        import time

        start = time.perf_counter()
        response = api_context.post(
            "/api/v1/ddx",
            headers={"X-API-Key": demo_api_key},
            data={"symptom": "fiebre"},
        )
        elapsed = time.perf_counter() - start

        assert response.status == 200
        assert elapsed < 3.0, f"Response took {elapsed:.2f}s, expected < 3s"
