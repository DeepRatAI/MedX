"""
MedeX Design System - Professional Medical Grade
=================================================
A carefully crafted design system optimized for:
- Clinical environments (high contrast, low fatigue)
- Extended reading sessions (proper spacing, line heights)
- Critical information hierarchy (semantic colors for severity)
- WCAG AAA accessibility compliance
"""

from dataclasses import dataclass


# =============================================================================
# COLOR SYSTEM
# =============================================================================


@dataclass(frozen=True)
class Theme:
    """Color theme container."""

    # -------------------------------------------------------------------------
    # BRAND COLORS - Deep Blue Medical (Authority, Trust, Professionalism)
    # Inspired by Epic, Cerner, UpToDate professional interfaces
    # -------------------------------------------------------------------------

    # Primary - Deep Medical Blue
    PRIMARY_900: str = "#0C1929"  # Darkest - Headers, critical text
    PRIMARY_800: str = "#132A45"  # Dark nav backgrounds
    PRIMARY_700: str = "#1A3A5C"  # Sidebar background
    PRIMARY_600: str = "#1E4976"  # Active states
    PRIMARY_500: str = "#2563EB"  # Main interactive - buttons, links
    PRIMARY_400: str = "#3B82F6"  # Hover states
    PRIMARY_300: str = "#60A5FA"  # Light accents
    PRIMARY_200: str = "#93C5FD"  # Subtle highlights
    PRIMARY_100: str = "#DBEAFE"  # Background tints
    PRIMARY_50: str = "#EFF6FF"  # Lightest backgrounds

    # -------------------------------------------------------------------------
    # SEMANTIC COLORS - ESI Triage Based (Industry Standard)
    # -------------------------------------------------------------------------

    # ESI Level 1 - Resuscitation (Immediate life-threatening)
    CRITICAL_900: str = "#7F1D1D"
    CRITICAL_700: str = "#B91C1C"
    CRITICAL_500: str = "#DC2626"  # Primary critical
    CRITICAL_300: str = "#FCA5A5"
    CRITICAL_100: str = "#FEE2E2"
    CRITICAL_50: str = "#FEF2F2"

    # ESI Level 2 - Emergent (High risk)
    EMERGENT_900: str = "#7C2D12"
    EMERGENT_700: str = "#C2410C"
    EMERGENT_500: str = "#EA580C"  # Primary emergent
    EMERGENT_300: str = "#FDBA74"
    EMERGENT_100: str = "#FFEDD5"
    EMERGENT_50: str = "#FFF7ED"

    # ESI Level 3 - Urgent (Moderate risk)
    URGENT_900: str = "#78350F"
    URGENT_700: str = "#B45309"
    URGENT_500: str = "#D97706"  # Primary urgent
    URGENT_300: str = "#FCD34D"
    URGENT_100: str = "#FEF3C7"
    URGENT_50: str = "#FFFBEB"

    # ESI Level 4 - Less Urgent (Low risk)
    STABLE_900: str = "#14532D"
    STABLE_700: str = "#15803D"
    STABLE_500: str = "#16A34A"  # Primary stable
    STABLE_300: str = "#86EFAC"
    STABLE_100: str = "#DCFCE7"
    STABLE_50: str = "#F0FDF4"

    # ESI Level 5 - Non-Urgent (Routine)
    ROUTINE_900: str = "#1E3A8A"
    ROUTINE_700: str = "#1D4ED8"
    ROUTINE_500: str = "#3B82F6"  # Primary routine
    ROUTINE_300: str = "#93C5FD"
    ROUTINE_100: str = "#DBEAFE"
    ROUTINE_50: str = "#EFF6FF"

    # -------------------------------------------------------------------------
    # FUNCTIONAL COLORS
    # -------------------------------------------------------------------------

    # Backgrounds - Warm neutrals for reduced eye strain
    BG_PRIMARY: str = "#FAFBFC"  # Main page background
    BG_SECONDARY: str = "#F4F6F8"  # Secondary sections
    BG_TERTIARY: str = "#EBEEF2"  # Tertiary/muted
    BG_CARD: str = "#FFFFFF"  # Card surfaces
    BG_ELEVATED: str = "#FFFFFF"  # Elevated surfaces
    BG_OVERLAY: str = "rgba(0, 0, 0, 0.5)"  # Modal overlays

    # Sidebar - Dark theme for focus contrast
    SIDEBAR_BG: str = "#0F172A"  # Slate 900
    SIDEBAR_BG_HOVER: str = "#1E293B"  # Slate 800
    SIDEBAR_BG_ACTIVE: str = "#334155"  # Slate 700
    SIDEBAR_TEXT: str = "#E2E8F0"  # Slate 200
    SIDEBAR_TEXT_MUTED: str = "#94A3B8"  # Slate 400
    SIDEBAR_BORDER: str = "#1E293B"  # Slate 800

    # Text - High contrast for clinical environments (WCAG AAA)
    TEXT_PRIMARY: str = "#0F172A"  # Slate 900 - Main text
    TEXT_SECONDARY: str = "#334155"  # Slate 700 - Secondary (darker for contrast)
    TEXT_MUTED: str = (
        "#64748B"  # Slate 500 - Muted (was #94A3B8, now darker for readability)
    )
    TEXT_BODY: str = "#1E293B"  # Slate 800 - For markdown/body content
    TEXT_INVERSE: str = "#FFFFFF"  # On dark backgrounds
    TEXT_LINK: str = "#2563EB"  # Blue 600 - Links

    # Input colors - Ensure high contrast
    INPUT_TEXT: str = "#0F172A"  # Slate 900 - Text in inputs
    INPUT_PLACEHOLDER: str = "#64748B"  # Slate 500 - Placeholder text

    # Borders - Subtle separators
    BORDER_DEFAULT: str = "#E2E8F0"  # Slate 200
    BORDER_SUBTLE: str = "#F1F5F9"  # Slate 100
    BORDER_STRONG: str = "#CBD5E1"  # Slate 300
    BORDER_FOCUS: str = "#2563EB"  # Blue 600

    # Interactive states
    INTERACTIVE_HOVER: str = "#F8FAFC"
    INTERACTIVE_ACTIVE: str = "#F1F5F9"
    INTERACTIVE_SELECTED: str = "#EFF6FF"


# Singleton theme instance
THEME = Theme()


# =============================================================================
# TYPOGRAPHY
# =============================================================================


class Font:
    """Typography system for medical clarity."""

    # Font Stack - Optimized for clinical readability
    FAMILY_PRIMARY: str = (
        "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif"
    )
    FAMILY_MONO: str = "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace"
    FAMILY_DISPLAY: str = "'Plus Jakarta Sans', 'Inter', sans-serif"

    # Size Scale (rem) - Larger base for medical environments
    SIZE_2XS: str = "0.625rem"  # 10px - Micro labels
    SIZE_XS: str = "0.75rem"  # 12px - Captions, badges
    SIZE_SM: str = "0.875rem"  # 14px - Secondary text
    SIZE_BASE: str = "1rem"  # 16px - Body text
    SIZE_MD: str = "1.0625rem"  # 17px - Slightly emphasized
    SIZE_LG: str = "1.125rem"  # 18px - Emphasized body
    SIZE_XL: str = "1.25rem"  # 20px - Small headings
    SIZE_2XL: str = "1.5rem"  # 24px - Section headings
    SIZE_3XL: str = "1.875rem"  # 30px - Page headings
    SIZE_4XL: str = "2.25rem"  # 36px - Display
    SIZE_5XL: str = "3rem"  # 48px - Hero display

    # Weights
    WEIGHT_NORMAL: str = "400"
    WEIGHT_MEDIUM: str = "500"
    WEIGHT_SEMIBOLD: str = "600"
    WEIGHT_BOLD: str = "700"

    # Line Heights - Generous for readability
    LINE_TIGHT: str = "1.25"
    LINE_SNUG: str = "1.375"
    LINE_NORMAL: str = "1.5"
    LINE_RELAXED: str = "1.625"
    LINE_LOOSE: str = "1.75"
    LINE_DOUBLE: str = "2"

    # Letter Spacing
    TRACKING_TIGHTER: str = "-0.02em"
    TRACKING_TIGHT: str = "-0.01em"
    TRACKING_NORMAL: str = "0"
    TRACKING_WIDE: str = "0.025em"
    TRACKING_WIDER: str = "0.05em"
    TRACKING_WIDEST: str = "0.1em"


# =============================================================================
# SPACING
# =============================================================================


class Space:
    """Spacing system with 4px base unit."""

    S0: str = "0"
    S0_5: str = "0.125rem"  # 2px
    S1: str = "0.25rem"  # 4px
    S1_5: str = "0.375rem"  # 6px
    S2: str = "0.5rem"  # 8px
    S2_5: str = "0.625rem"  # 10px
    S3: str = "0.75rem"  # 12px
    S3_5: str = "0.875rem"  # 14px
    S4: str = "1rem"  # 16px
    S5: str = "1.25rem"  # 20px
    S6: str = "1.5rem"  # 24px
    S7: str = "1.75rem"  # 28px
    S8: str = "2rem"  # 32px
    S9: str = "2.25rem"  # 36px
    S10: str = "2.5rem"  # 40px
    S11: str = "2.75rem"  # 44px
    S12: str = "3rem"  # 48px
    S14: str = "3.5rem"  # 56px
    S16: str = "4rem"  # 64px
    S20: str = "5rem"  # 80px
    S24: str = "6rem"  # 96px


# =============================================================================
# BORDERS & RADII
# =============================================================================


class Radius:
    """Border radius scale."""

    NONE: str = "0"
    XS: str = "0.125rem"  # 2px - Subtle
    SM: str = "0.25rem"  # 4px - Small elements
    DEFAULT: str = "0.375rem"  # 6px - Buttons, inputs
    MD: str = "0.5rem"  # 8px - Cards
    LG: str = "0.75rem"  # 12px - Large cards
    XL: str = "1rem"  # 16px - Modals
    XXL: str = "1.5rem"  # 24px - Large containers
    FULL: str = "9999px"  # Circular


# =============================================================================
# SHADOWS
# =============================================================================


class Shadow:
    """Elevation shadow system."""

    NONE: str = "none"
    XS: str = "0 1px 2px 0 rgba(0, 0, 0, 0.03)"
    SM: str = "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)"
    DEFAULT: str = (
        "0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)"
    )
    MD: str = "0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05)"
    LG: str = (
        "0 20px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.05)"
    )
    XL: str = "0 25px 50px -12px rgba(0, 0, 0, 0.15)"
    INNER: str = "inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)"

    # Colored shadows for emphasis
    CRITICAL: str = "0 4px 14px -3px rgba(220, 38, 38, 0.25)"
    EMERGENT: str = "0 4px 14px -3px rgba(234, 88, 12, 0.25)"
    PRIMARY: str = "0 4px 14px -3px rgba(37, 99, 235, 0.25)"
    SUCCESS: str = "0 4px 14px -3px rgba(22, 163, 74, 0.25)"


# =============================================================================
# LAYOUT
# =============================================================================


class Layout:
    """Layout dimensions."""

    # Sidebar
    SIDEBAR_WIDTH: str = "280px"
    SIDEBAR_COLLAPSED: str = "72px"

    # Content
    CONTENT_MAX_WIDTH: str = "1400px"
    CHAT_MAX_WIDTH: str = "900px"

    # Header
    HEADER_HEIGHT: str = "64px"

    # Chat
    MESSAGE_MAX_WIDTH: str = "75%"
    INPUT_HEIGHT: str = "56px"

    # Cards
    CARD_MIN_HEIGHT: str = "120px"


# =============================================================================
# TRANSITIONS
# =============================================================================


class Transition:
    """Animation timing."""

    INSTANT: str = "0ms"
    FAST: str = "100ms"
    NORMAL: str = "200ms"
    SLOW: str = "300ms"
    SLOWER: str = "500ms"

    # Easing
    EASE_DEFAULT: str = "cubic-bezier(0.4, 0, 0.2, 1)"
    EASE_IN: str = "cubic-bezier(0.4, 0, 1, 1)"
    EASE_OUT: str = "cubic-bezier(0, 0, 0.2, 1)"
    EASE_IN_OUT: str = "cubic-bezier(0.4, 0, 0.2, 1)"
    EASE_BOUNCE: str = "cubic-bezier(0.68, -0.55, 0.265, 1.55)"


# =============================================================================
# Z-INDEX
# =============================================================================


class ZIndex:
    """Z-index layers."""

    BASE: str = "0"
    DROPDOWN: str = "100"
    STICKY: str = "200"
    FIXED: str = "300"
    MODAL_BACKDROP: str = "400"
    MODAL: str = "500"
    POPOVER: str = "600"
    TOOLTIP: str = "700"
    TOAST: str = "800"


# =============================================================================
# ESI LEVEL CONFIGURATIONS
# =============================================================================

ESI_LEVELS = {
    1: {
        "name": "Resuscitation",
        "color": THEME.CRITICAL_500,
        "bg": THEME.CRITICAL_50,
        "border": THEME.CRITICAL_300,
        "text": THEME.CRITICAL_700,
        "icon": "heart-off",
        "description": "Immediate life-saving intervention required",
        "wait_time": "Immediate",
    },
    2: {
        "name": "Emergent",
        "color": THEME.EMERGENT_500,
        "bg": THEME.EMERGENT_50,
        "border": THEME.EMERGENT_300,
        "text": THEME.EMERGENT_700,
        "icon": "alert-triangle",
        "description": "High risk, time-sensitive condition",
        "wait_time": "<10 min",
    },
    3: {
        "name": "Urgent",
        "color": THEME.URGENT_500,
        "bg": THEME.URGENT_50,
        "border": THEME.URGENT_300,
        "text": THEME.URGENT_700,
        "icon": "clock",
        "description": "Moderate acuity, requires multiple resources",
        "wait_time": "<30 min",
    },
    4: {
        "name": "Less Urgent",
        "color": THEME.STABLE_500,
        "bg": THEME.STABLE_50,
        "border": THEME.STABLE_300,
        "text": THEME.STABLE_700,
        "icon": "check-circle",
        "description": "Low acuity, single resource needed",
        "wait_time": "<60 min",
    },
    5: {
        "name": "Non-Urgent",
        "color": THEME.ROUTINE_500,
        "bg": THEME.ROUTINE_50,
        "border": THEME.ROUTINE_300,
        "text": THEME.ROUTINE_700,
        "icon": "info",
        "description": "Routine care, can wait safely",
        "wait_time": "<120 min",
    },
}


# =============================================================================
# USER TYPE CONFIGURATIONS
# =============================================================================

USER_TYPES = {
    "professional": {
        "label": "Professional",
        "description": "Healthcare providers",
        "icon": "stethoscope",
        "color": THEME.PRIMARY_500,
        "bg": THEME.PRIMARY_50,
        "badge_color": "blue",
    },
    "educational": {
        "label": "Educational",
        "description": "Students & general public",
        "icon": "graduation-cap",
        "color": THEME.STABLE_500,
        "bg": THEME.STABLE_50,
        "badge_color": "green",
    },
    "research": {
        "label": "Research",
        "description": "Academic & research use",
        "icon": "flask-conical",
        "color": "#9333EA",  # Purple
        "bg": "#FAF5FF",
        "badge_color": "purple",
    },
}


# =============================================================================
# INTERACTION SEVERITY
# =============================================================================

SEVERITY_CONFIG = {
    "critical": {
        "label": "Critical",
        "color": THEME.CRITICAL_500,
        "bg": THEME.CRITICAL_50,
        "border": THEME.CRITICAL_300,
        "icon": "octagon",
    },
    "high": {
        "label": "High",
        "color": THEME.EMERGENT_500,
        "bg": THEME.EMERGENT_50,
        "border": THEME.EMERGENT_300,
        "icon": "alert-triangle",
    },
    "moderate": {
        "label": "Moderate",
        "color": THEME.URGENT_500,
        "bg": THEME.URGENT_50,
        "border": THEME.URGENT_300,
        "icon": "alert-circle",
    },
    "low": {
        "label": "Low",
        "color": THEME.STABLE_500,
        "bg": THEME.STABLE_50,
        "border": THEME.STABLE_300,
        "icon": "info",
    },
}
