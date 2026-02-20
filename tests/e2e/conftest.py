"""
MedeX E2E Tests Configuration
=============================
Pytest configuration for Playwright E2E tests.
"""

import pytest
from playwright.sync_api import Page, expect


def pytest_configure(config):
    """Configure pytest markers for E2E tests"""
    config.addinivalue_line("markers", "e2e: End-to-end tests with Playwright")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
    config.addinivalue_line("markers", "critical: Critical user flow tests")


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "locale": "es-ES",
        "timezone_id": "America/Buenos_Aires",
    }


@pytest.fixture
def medex_url():
    """Base URL for MedeX application"""
    return "http://localhost:8501"


@pytest.fixture
def api_url():
    """Base URL for MedeX API"""
    return "http://localhost:8000"


@pytest.fixture
def demo_api_key():
    """Demo API key for testing"""
    return "medex-demo-key-2024"
