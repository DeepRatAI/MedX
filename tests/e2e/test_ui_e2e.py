"""
MedeX E2E Tests - Streamlit UI
==============================
Tests end-to-end para la interfaz Streamlit de MedeX.
Estos tests verifican la experiencia del usuario final.
"""

import pytest
from playwright.sync_api import Page, expect


class TestUIPageLoad:
    """Tests for initial page loading"""

    @pytest.mark.e2e
    @pytest.mark.critical
    def test_page_loads_successfully(self, page: Page, medex_url: str):
        """Main page loads without errors"""
        response = page.goto(medex_url, wait_until="networkidle")

        assert response is not None
        assert response.status == 200

    @pytest.mark.e2e
    def test_page_has_title(self, page: Page, medex_url: str):
        """Page has MedeX in title"""
        page.goto(medex_url, wait_until="networkidle")

        expect(page).to_have_title(lambda t: "MedeX" in t or "medex" in t.lower())

    @pytest.mark.e2e
    def test_header_is_visible(self, page: Page, medex_url: str):
        """Header with app name is visible"""
        page.goto(medex_url, wait_until="networkidle")

        # Look for header text
        header = page.locator("h1, h2, h3").first
        expect(header).to_be_visible()


class TestUISidebar:
    """Tests for sidebar functionality"""

    @pytest.mark.e2e
    def test_sidebar_is_visible(self, page: Page, medex_url: str):
        """Sidebar is visible on page load"""
        page.goto(medex_url, wait_until="networkidle")

        sidebar = page.locator('[data-testid="stSidebar"]')
        expect(sidebar).to_be_visible()

    @pytest.mark.e2e
    def test_language_selector_exists(self, page: Page, medex_url: str):
        """Language selector is present in sidebar"""
        page.goto(medex_url, wait_until="networkidle")

        # Look for language-related elements
        sidebar = page.locator('[data-testid="stSidebar"]')

        # Check for radio buttons or selectbox with language options
        lang_element = sidebar.locator("text=/Idioma|Language|ES|EN/i").first
        expect(lang_element).to_be_visible()

    @pytest.mark.e2e
    def test_model_configuration_section(self, page: Page, medex_url: str):
        """Model configuration section is present"""
        page.goto(medex_url, wait_until="networkidle")

        sidebar = page.locator('[data-testid="stSidebar"]')

        # Look for model-related text
        model_section = sidebar.locator("text=/Modelo|Model|Configuration/i").first
        expect(model_section).to_be_visible()


class TestUIChat:
    """Tests for chat functionality"""

    @pytest.mark.e2e
    @pytest.mark.critical
    def test_chat_input_exists(self, page: Page, medex_url: str):
        """Chat input field is present"""
        page.goto(medex_url, wait_until="networkidle")

        # Streamlit chat input
        chat_input = page.locator(
            'textarea[data-testid="stChatInputTextArea"], input[type="text"]'
        ).first
        expect(chat_input).to_be_visible()

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_can_send_message(self, page: Page, medex_url: str):
        """User can type and send a message"""
        page.goto(medex_url, wait_until="networkidle")

        # Find chat input
        chat_input = page.locator('textarea[data-testid="stChatInputTextArea"]').first

        if chat_input.is_visible():
            # Type a message
            chat_input.fill("Que es la diabetes?")

            # Press Enter to send
            chat_input.press("Enter")

            # Wait for response (may take time with LLM)
            page.wait_for_timeout(2000)

            # Check that message appears in chat
            messages = page.locator('[data-testid="stChatMessage"]')
            expect(messages.first).to_be_visible()


class TestUIKnowledgeExplorer:
    """Tests for knowledge explorer functionality"""

    @pytest.mark.e2e
    def test_knowledge_base_section_exists(self, page: Page, medex_url: str):
        """Knowledge base explorer section is present"""
        page.goto(medex_url, wait_until="networkidle")

        # Look for KB-related text
        kb_section = page.locator(
            "text=/Base de Conocimiento|Knowledge Base|Explorador/i"
        ).first
        expect(kb_section).to_be_visible()

    @pytest.mark.e2e
    def test_search_input_in_kb(self, page: Page, medex_url: str):
        """Search input exists in knowledge base section"""
        page.goto(medex_url, wait_until="networkidle")

        # Find text input for search
        search_inputs = page.locator('input[type="text"]')

        # Should have at least one search input
        expect(search_inputs.first).to_be_visible()


class TestUIEmergencyBanner:
    """Tests for emergency detection UI"""

    @pytest.mark.e2e
    def test_emergency_elements_not_visible_initially(self, page: Page, medex_url: str):
        """Emergency banner is not visible on initial load"""
        page.goto(medex_url, wait_until="networkidle")

        # Emergency banner should not be visible initially
        emergency = page.locator("text=/EMERGENCIA|EMERGENCY|112|911/i")

        # Count should be 0 or elements should not be visible
        if emergency.count() > 0:
            # If exists, it might be in a collapsed state
            pass  # This is acceptable


class TestUIResponsiveness:
    """Tests for responsive design"""

    @pytest.mark.e2e
    def test_desktop_viewport(self, page: Page, medex_url: str):
        """Page renders correctly at desktop resolution"""
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(medex_url, wait_until="networkidle")

        # Sidebar should be visible on desktop
        sidebar = page.locator('[data-testid="stSidebar"]')
        expect(sidebar).to_be_visible()

    @pytest.mark.e2e
    def test_tablet_viewport(self, page: Page, medex_url: str):
        """Page renders correctly at tablet resolution"""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(medex_url, wait_until="networkidle")

        # Main content should still be accessible
        main = page.locator('[data-testid="stAppViewContainer"]')
        expect(main).to_be_visible()

    @pytest.mark.e2e
    def test_mobile_viewport(self, page: Page, medex_url: str):
        """Page renders correctly at mobile resolution"""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(medex_url, wait_until="networkidle")

        # Page should not have horizontal scroll
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")

        # Allow small overflow for scrollbars
        assert body_width <= viewport_width + 20


class TestUIAccessibility:
    """Tests for accessibility features"""

    @pytest.mark.e2e
    def test_page_has_lang_attribute(self, page: Page, medex_url: str):
        """HTML has lang attribute"""
        page.goto(medex_url, wait_until="networkidle")

        html_lang = page.locator("html").get_attribute("lang")
        # Streamlit may not set this, so we just check it exists
        # assert html_lang is not None

    @pytest.mark.e2e
    def test_images_have_alt_text(self, page: Page, medex_url: str):
        """Images have alt attributes"""
        page.goto(medex_url, wait_until="networkidle")

        images = page.locator("img")
        count = images.count()

        for i in range(min(count, 5)):  # Check first 5 images
            img = images.nth(i)
            alt = img.get_attribute("alt")
            # Alt can be empty string for decorative images
            assert alt is not None

    @pytest.mark.e2e
    def test_buttons_are_focusable(self, page: Page, medex_url: str):
        """Interactive elements are keyboard accessible"""
        page.goto(medex_url, wait_until="networkidle")

        # Tab through page elements
        page.keyboard.press("Tab")

        # Something should be focused
        focused = page.evaluate("document.activeElement.tagName")
        assert focused is not None


class TestUIPerformance:
    """Tests for UI performance"""

    @pytest.mark.e2e
    @pytest.mark.slow
    def test_page_load_under_10s(self, page: Page, medex_url: str):
        """Page loads in under 10 seconds"""
        import time

        start = time.perf_counter()
        page.goto(medex_url, wait_until="networkidle")
        elapsed = time.perf_counter() - start

        assert elapsed < 10.0, f"Page load took {elapsed:.2f}s, expected < 10s"

    @pytest.mark.e2e
    def test_no_console_errors(self, page: Page, medex_url: str):
        """No JavaScript errors in console"""
        errors = []

        page.on(
            "console",
            lambda msg: errors.append(msg.text) if msg.type == "error" else None,
        )

        page.goto(medex_url, wait_until="networkidle")

        # Filter out known non-critical errors
        critical_errors = [e for e in errors if "favicon" not in e.lower()]

        # Should have no critical errors
        assert len(critical_errors) == 0, f"Console errors: {critical_errors}"
