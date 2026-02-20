"""
MedeX UI - Professional Medical AI Interface
=============================================
Main application entry point.
"""

from __future__ import annotations

import reflex as rx

from .design import THEME, Font, Space, Radius, Shadow, Layout, Transition, USER_TYPES
from .state import MedeXState


# =============================================================================
# SIDEBAR COMPONENTS
# =============================================================================


def logo() -> rx.Component:
    """MedeX logo component."""
    return rx.hstack(
        rx.box(
            rx.icon("heart-pulse", size=22, color=THEME.TEXT_INVERSE),
            padding=Space.S3,
            background=THEME.PRIMARY_500,
            border_radius=Radius.MD,
        ),
        rx.vstack(
            rx.text(
                "MedeX",
                font_size=Font.SIZE_XL,
                font_weight=Font.WEIGHT_BOLD,
                color=THEME.SIDEBAR_TEXT,
                line_height="1.1",
            ),
            rx.text(
                "Medical AI Assistant",
                font_size=Font.SIZE_2XS,
                color=THEME.SIDEBAR_TEXT_MUTED,
                line_height="1",
            ),
            gap="2px",
            align="start",
        ),
        gap=Space.S3,
        align="center",
    )


def connection_badge() -> rx.Component:
    """Connection status badge."""
    return rx.cond(
        MedeXState.is_connected,
        rx.hstack(
            rx.box(
                width="8px",
                height="8px",
                background=THEME.STABLE_500,
                border_radius=Radius.FULL,
            ),
            rx.text("Connected", font_size=Font.SIZE_XS, color=THEME.STABLE_500),
            gap="6px",
            align="center",
            padding=f"{Space.S1_5} {Space.S3}",
            background=f"{THEME.STABLE_500}15",
            border_radius=Radius.FULL,
        ),
        rx.hstack(
            rx.box(
                width="8px",
                height="8px",
                background=THEME.URGENT_500,
                border_radius=Radius.FULL,
            ),
            rx.text("Offline", font_size=Font.SIZE_XS, color=THEME.URGENT_500),
            gap="6px",
            align="center",
            padding=f"{Space.S1_5} {Space.S3}",
            background=f"{THEME.URGENT_500}15",
            border_radius=Radius.FULL,
        ),
    )


def user_type_educational() -> rx.Component:
    """Educational user type button."""
    config = USER_TYPES["educational"]
    return rx.box(
        rx.hstack(
            rx.icon(config["icon"], size=16, color=THEME.SIDEBAR_TEXT_MUTED),
            rx.text(config["label"], font_size=Font.SIZE_SM, color=THEME.SIDEBAR_TEXT),
            gap=Space.S2,
            align="center",
        ),
        padding=f"{Space.S2} {Space.S3}",
        border_radius=Radius.DEFAULT,
        cursor="pointer",
        background=rx.cond(
            MedeXState.user_type == "educational",
            THEME.SIDEBAR_BG_ACTIVE,
            "transparent",
        ),
        border=rx.cond(
            MedeXState.user_type == "educational",
            f"1px solid {THEME.PRIMARY_500}",
            "1px solid transparent",
        ),
        on_click=MedeXState.set_user_type_educational,
        _hover={"background": THEME.SIDEBAR_BG_HOVER},
        transition=f"all {Transition.FAST}",
        width="100%",
    )


def user_type_professional() -> rx.Component:
    """Professional user type button."""
    config = USER_TYPES["professional"]
    return rx.box(
        rx.hstack(
            rx.icon(config["icon"], size=16, color=THEME.SIDEBAR_TEXT_MUTED),
            rx.text(config["label"], font_size=Font.SIZE_SM, color=THEME.SIDEBAR_TEXT),
            gap=Space.S2,
            align="center",
        ),
        padding=f"{Space.S2} {Space.S3}",
        border_radius=Radius.DEFAULT,
        cursor="pointer",
        background=rx.cond(
            MedeXState.user_type == "professional",
            THEME.SIDEBAR_BG_ACTIVE,
            "transparent",
        ),
        border=rx.cond(
            MedeXState.user_type == "professional",
            f"1px solid {THEME.PRIMARY_500}",
            "1px solid transparent",
        ),
        on_click=MedeXState.set_user_type_professional,
        _hover={"background": THEME.SIDEBAR_BG_HOVER},
        transition=f"all {Transition.FAST}",
        width="100%",
    )


def user_type_research() -> rx.Component:
    """Research user type button."""
    config = USER_TYPES["research"]
    return rx.box(
        rx.hstack(
            rx.icon(config["icon"], size=16, color=THEME.SIDEBAR_TEXT_MUTED),
            rx.text(config["label"], font_size=Font.SIZE_SM, color=THEME.SIDEBAR_TEXT),
            gap=Space.S2,
            align="center",
        ),
        padding=f"{Space.S2} {Space.S3}",
        border_radius=Radius.DEFAULT,
        cursor="pointer",
        background=rx.cond(
            MedeXState.user_type == "research",
            THEME.SIDEBAR_BG_ACTIVE,
            "transparent",
        ),
        border=rx.cond(
            MedeXState.user_type == "research",
            f"1px solid {THEME.PRIMARY_500}",
            "1px solid transparent",
        ),
        on_click=MedeXState.set_user_type_research,
        _hover={"background": THEME.SIDEBAR_BG_HOVER},
        transition=f"all {Transition.FAST}",
        width="100%",
    )


def user_type_selector() -> rx.Component:
    """User type selector section - Educational and Professional modes only."""
    return rx.vstack(
        rx.text(
            "MODO DE USUARIO",
            font_size=Font.SIZE_2XS,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.SIDEBAR_TEXT_MUTED,
            letter_spacing=Font.TRACKING_WIDER,
        ),
        user_type_educational(),
        user_type_professional(),
        gap=Space.S1,
        width="100%",
        align="stretch",
    )


def nav_item_base(
    icon: str, label: str, section: str, on_click_handler
) -> rx.Component:
    """Base navigation item."""
    return rx.box(
        rx.hstack(
            rx.icon(
                icon,
                size=18,
                color=rx.cond(
                    MedeXState.active_section == section,
                    THEME.PRIMARY_400,
                    THEME.SIDEBAR_TEXT_MUTED,
                ),
            ),
            rx.text(
                label,
                font_size=Font.SIZE_SM,
                font_weight=rx.cond(
                    MedeXState.active_section == section,
                    Font.WEIGHT_MEDIUM,
                    Font.WEIGHT_NORMAL,
                ),
                color=rx.cond(
                    MedeXState.active_section == section,
                    THEME.SIDEBAR_TEXT,
                    THEME.SIDEBAR_TEXT_MUTED,
                ),
            ),
            gap=Space.S3,
            align="center",
            width="100%",
        ),
        padding=f"{Space.S2_5} {Space.S3}",
        border_radius=Radius.DEFAULT,
        cursor="pointer",
        background=rx.cond(
            MedeXState.active_section == section,
            THEME.SIDEBAR_BG_ACTIVE,
            "transparent",
        ),
        on_click=on_click_handler,
        _hover={"background": THEME.SIDEBAR_BG_HOVER},
        transition=f"all {Transition.FAST}",
        width="100%",
    )


def nav_chat() -> rx.Component:
    return nav_item_base("message-circle", "Chat", "chat", MedeXState.set_section_chat)


def nav_tools() -> rx.Component:
    return nav_item_base("pill", "Drug Tools", "tools", MedeXState.set_section_tools)


def nav_knowledge() -> rx.Component:
    return nav_item_base(
        "database", "Knowledge Base", "knowledge", MedeXState.set_section_knowledge
    )


def nav_triage() -> rx.Component:
    return nav_item_base("activity", "Triage", "triage", MedeXState.set_section_triage)


def nav_history() -> rx.Component:
    return nav_item_base(
        "history", "Historial", "history", MedeXState.set_section_history
    )


def nav_research() -> rx.Component:
    return nav_item_base(
        "search", "Deep Research", "research", MedeXState.set_section_research
    )


def navigation() -> rx.Component:
    """Main navigation - Core modules only."""
    return rx.vstack(
        rx.text(
            "NAVEGACIÓN",
            font_size=Font.SIZE_2XS,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.SIDEBAR_TEXT_MUTED,
            letter_spacing=Font.TRACKING_WIDER,
        ),
        nav_chat(),
        nav_tools(),
        nav_research(),
        nav_history(),
        gap=Space.S1,
        width="100%",
        align="stretch",
    )


def session_stats() -> rx.Component:
    """Session statistics."""
    return rx.vstack(
        rx.text(
            "SESSION",
            font_size=Font.SIZE_2XS,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.SIDEBAR_TEXT_MUTED,
            letter_spacing=Font.TRACKING_WIDER,
        ),
        rx.hstack(
            rx.vstack(
                rx.text(
                    MedeXState.total_queries,
                    font_size=Font.SIZE_LG,
                    font_weight=Font.WEIGHT_BOLD,
                    color=THEME.SIDEBAR_TEXT,
                ),
                rx.text(
                    "Queries", font_size=Font.SIZE_2XS, color=THEME.SIDEBAR_TEXT_MUTED
                ),
                gap="0",
                align="center",
            ),
            rx.vstack(
                rx.text(
                    MedeXState.session_duration_minutes,
                    font_size=Font.SIZE_LG,
                    font_weight=Font.WEIGHT_BOLD,
                    color=THEME.SIDEBAR_TEXT,
                ),
                rx.text(
                    "Minutes", font_size=Font.SIZE_2XS, color=THEME.SIDEBAR_TEXT_MUTED
                ),
                gap="0",
                align="center",
            ),
            width="100%",
            justify="between",
            padding=Space.S3,
            background=THEME.SIDEBAR_BG_HOVER,
            border_radius=Radius.DEFAULT,
        ),
        gap=Space.S2,
        width="100%",
    )


def disclaimer() -> rx.Component:
    """Medical disclaimer."""
    return rx.box(
        rx.hstack(
            rx.icon("shield-alert", size=14, color=THEME.URGENT_500),
            rx.text(
                "Educational use only. Does not replace medical advice.",
                font_size=Font.SIZE_2XS,
                color=THEME.SIDEBAR_TEXT_MUTED,
                line_height=Font.LINE_SNUG,
            ),
            gap=Space.S2,
            align="start",
        ),
        padding=Space.S3,
        background=f"{THEME.URGENT_500}10",
        border_radius=Radius.DEFAULT,
        border=f"1px solid {THEME.URGENT_500}30",
    )


def conversations_list() -> rx.Component:
    """List of recent conversations."""
    return rx.vstack(
        rx.text(
            "CONVERSATIONS",
            font_size=Font.SIZE_2XS,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.SIDEBAR_TEXT_MUTED,
            letter_spacing=Font.TRACKING_WIDER,
        ),
        rx.cond(
            MedeXState.has_conversations,
            rx.vstack(
                rx.foreach(
                    MedeXState.conversations,
                    lambda conv: rx.box(
                        rx.hstack(
                            rx.icon(
                                "message-circle",
                                size=14,
                                color=rx.cond(
                                    MedeXState.active_conversation_id == conv["id"],
                                    THEME.PRIMARY_400,
                                    THEME.SIDEBAR_TEXT_MUTED,
                                ),
                            ),
                            rx.vstack(
                                rx.text(
                                    conv["title"],
                                    font_size=Font.SIZE_XS,
                                    color=THEME.SIDEBAR_TEXT,
                                    no_of_lines=1,
                                    font_weight=rx.cond(
                                        MedeXState.active_conversation_id == conv["id"],
                                        Font.WEIGHT_MEDIUM,
                                        Font.WEIGHT_NORMAL,
                                    ),
                                ),
                                rx.text(
                                    conv["message_count"],
                                    " messages",
                                    font_size=Font.SIZE_2XS,
                                    color=THEME.SIDEBAR_TEXT_MUTED,
                                ),
                                gap="0",
                                align="start",
                                flex="1",
                            ),
                            gap=Space.S2,
                            align="center",
                            width="100%",
                        ),
                        padding=f"{Space.S2} {Space.S3}",
                        border_radius=Radius.DEFAULT,
                        cursor="pointer",
                        background=rx.cond(
                            MedeXState.active_conversation_id == conv["id"],
                            THEME.SIDEBAR_BG_ACTIVE,
                            "transparent",
                        ),
                        on_click=MedeXState.switch_conversation(conv["id"]),
                        _hover={"background": THEME.SIDEBAR_BG_HOVER},
                        width="100%",
                    ),
                ),
                gap=Space.S1,
                width="100%",
                max_height="200px",
                overflow_y="auto",
            ),
            rx.text(
                "No conversations yet",
                font_size=Font.SIZE_XS,
                color=THEME.SIDEBAR_TEXT_MUTED,
            ),
        ),
        gap=Space.S2,
        width="100%",
    )


def sidebar() -> rx.Component:
    """Complete sidebar with collapse functionality."""
    # Toggle button that's always visible
    toggle_btn = rx.tooltip(
        rx.icon_button(
            rx.cond(
                MedeXState.sidebar_collapsed,
                rx.icon("panel-left-open", size=18, color=THEME.SIDEBAR_TEXT),
                rx.icon("panel-left-close", size=18, color=THEME.SIDEBAR_TEXT),
            ),
            variant="ghost",
            size="2",
            cursor="pointer",
            on_click=MedeXState.toggle_sidebar,
            _hover={"background": THEME.SIDEBAR_BG_HOVER},
        ),
        content=rx.cond(
            MedeXState.sidebar_collapsed,
            "Expandir menú",
            "Colapsar menú",
        ),
    )

    # Collapsed version - only icons
    collapsed_sidebar = rx.el.aside(
        rx.vstack(
            # Toggle at top
            rx.box(toggle_btn, padding=Space.S2),
            rx.divider(margin=f"{Space.S2} 0", border_color=THEME.SIDEBAR_BORDER),
            # Logo icon only
            rx.tooltip(
                rx.box(
                    rx.icon("heart-pulse", size=22, color=THEME.TEXT_INVERSE),
                    padding=Space.S3,
                    background=THEME.PRIMARY_500,
                    border_radius=Radius.MD,
                    cursor="pointer",
                ),
                content="MedeX",
            ),
            rx.divider(margin=f"{Space.S2} 0", border_color=THEME.SIDEBAR_BORDER),
            # Connection status - just dot
            rx.cond(
                MedeXState.is_connected,
                rx.tooltip(
                    rx.box(
                        width="10px",
                        height="10px",
                        background=THEME.STABLE_500,
                        border_radius=Radius.FULL,
                    ),
                    content="Conectado",
                ),
                rx.tooltip(
                    rx.box(
                        width="10px",
                        height="10px",
                        background=THEME.URGENT_500,
                        border_radius=Radius.FULL,
                    ),
                    content="Sin conexión",
                ),
            ),
            rx.divider(margin=f"{Space.S2} 0", border_color=THEME.SIDEBAR_BORDER),
            # Nav icons only
            rx.vstack(
                rx.tooltip(
                    rx.box(
                        rx.icon(
                            "message-circle",
                            size=20,
                            color=rx.cond(
                                MedeXState.active_section == "chat",
                                THEME.PRIMARY_400,
                                THEME.SIDEBAR_TEXT_MUTED,
                            ),
                        ),
                        padding=Space.S2,
                        border_radius=Radius.DEFAULT,
                        cursor="pointer",
                        background=rx.cond(
                            MedeXState.active_section == "chat",
                            THEME.SIDEBAR_BG_ACTIVE,
                            "transparent",
                        ),
                        _hover={"background": THEME.SIDEBAR_BG_HOVER},
                        on_click=MedeXState.set_section_chat,
                    ),
                    content="Chat",
                ),
                rx.tooltip(
                    rx.box(
                        rx.icon(
                            "pill",
                            size=20,
                            color=rx.cond(
                                MedeXState.active_section == "tools",
                                THEME.PRIMARY_400,
                                THEME.SIDEBAR_TEXT_MUTED,
                            ),
                        ),
                        padding=Space.S2,
                        border_radius=Radius.DEFAULT,
                        cursor="pointer",
                        background=rx.cond(
                            MedeXState.active_section == "tools",
                            THEME.SIDEBAR_BG_ACTIVE,
                            "transparent",
                        ),
                        _hover={"background": THEME.SIDEBAR_BG_HOVER},
                        on_click=MedeXState.set_section_tools,
                    ),
                    content="Drug Tools",
                ),
                rx.tooltip(
                    rx.box(
                        rx.icon(
                            "search",
                            size=20,
                            color=rx.cond(
                                MedeXState.active_section == "research",
                                THEME.PRIMARY_400,
                                THEME.SIDEBAR_TEXT_MUTED,
                            ),
                        ),
                        padding=Space.S2,
                        border_radius=Radius.DEFAULT,
                        cursor="pointer",
                        background=rx.cond(
                            MedeXState.active_section == "research",
                            THEME.SIDEBAR_BG_ACTIVE,
                            "transparent",
                        ),
                        _hover={"background": THEME.SIDEBAR_BG_HOVER},
                        on_click=MedeXState.set_section_research,
                    ),
                    content="Deep Research",
                ),
                rx.tooltip(
                    rx.box(
                        rx.icon(
                            "history",
                            size=20,
                            color=rx.cond(
                                MedeXState.active_section == "history",
                                THEME.PRIMARY_400,
                                THEME.SIDEBAR_TEXT_MUTED,
                            ),
                        ),
                        padding=Space.S2,
                        border_radius=Radius.DEFAULT,
                        cursor="pointer",
                        background=rx.cond(
                            MedeXState.active_section == "history",
                            THEME.SIDEBAR_BG_ACTIVE,
                            "transparent",
                        ),
                        _hover={"background": THEME.SIDEBAR_BG_HOVER},
                        on_click=MedeXState.set_section_history,
                    ),
                    content="Historial",
                ),
                gap=Space.S1,
                align="center",
            ),
            rx.spacer(),
            # Version at bottom
            rx.text("Alpha", font_size=Font.SIZE_2XS, color=THEME.SIDEBAR_TEXT_MUTED),
            height="100%",
            padding=Space.S2,
            gap=Space.S2,
            align="center",
        ),
        style={
            "width": Layout.SIDEBAR_COLLAPSED,
            "min-width": Layout.SIDEBAR_COLLAPSED,
            "height": "100vh",
            "background": THEME.SIDEBAR_BG,
            "overflow-y": "auto",
            "flex-shrink": "0",
            "transition": f"width {Transition.NORMAL}",
        },
    )

    # Expanded version - full sidebar
    expanded_sidebar = rx.el.aside(
        rx.vstack(
            # Toggle button row
            rx.hstack(
                logo(),
                rx.spacer(),
                toggle_btn,
                width="100%",
                align="center",
            ),
            rx.divider(margin=f"{Space.S4} 0", border_color=THEME.SIDEBAR_BORDER),
            connection_badge(),
            rx.divider(margin=f"{Space.S4} 0", border_color=THEME.SIDEBAR_BORDER),
            user_type_selector(),
            rx.divider(margin=f"{Space.S4} 0", border_color=THEME.SIDEBAR_BORDER),
            navigation(),
            rx.divider(margin=f"{Space.S4} 0", border_color=THEME.SIDEBAR_BORDER),
            conversations_list(),
            rx.spacer(),
            disclaimer(),
            rx.text(
                "MedeX Alpha",
                font_size=Font.SIZE_2XS,
                color=THEME.SIDEBAR_TEXT_MUTED,
                text_align="center",
                margin_top=Space.S2,
            ),
            height="100%",
            padding=Space.S4,
            gap=Space.S1,
            align="stretch",
        ),
        style={
            "width": Layout.SIDEBAR_WIDTH,
            "min-width": Layout.SIDEBAR_WIDTH,
            "height": "100vh",
            "background": THEME.SIDEBAR_BG,
            "overflow-y": "auto",
            "flex-shrink": "0",
            "transition": f"width {Transition.NORMAL}",
        },
    )

    return rx.cond(
        MedeXState.sidebar_collapsed,
        collapsed_sidebar,
        expanded_sidebar,
    )


# =============================================================================
# HEADER
# =============================================================================


def model_option_card(m: dict) -> rx.Component:
    """Individual model option in selector dropdown.

    Uses direct State.method(arg) syntax for event binding in rx.foreach context.
    Do NOT use lambda: - it causes React child rendering errors.
    """
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        m["name"],
                        font_size=Font.SIZE_SM,
                        font_weight=Font.WEIGHT_MEDIUM,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    # Category badge based on model type
                    rx.cond(
                        m["category"] == "medical",
                        rx.badge(
                            "MED",
                            color_scheme="green",
                            size="1",
                            variant="soft",
                        ),
                        rx.cond(
                            m["category"] == "reasoning",
                            rx.badge(
                                "AI",
                                color_scheme="purple",
                                size="1",
                                variant="soft",
                            ),
                            rx.fragment(),
                        ),
                    ),
                    gap=Space.S1,
                    align="center",
                ),
                rx.text(
                    m["provider"],
                    font_size=Font.SIZE_2XS,
                    color=THEME.TEXT_MUTED,
                ),
                gap="2px",
                align="start",
            ),
            rx.spacer(),
            rx.cond(
                MedeXState.selected_model == m["id"],
                rx.icon("check", size=14, color=THEME.PRIMARY_500),
                rx.fragment(),
            ),
            width="100%",
            align="center",
        ),
        padding=f"{Space.S2} {Space.S3}",
        cursor="pointer",
        background=rx.cond(
            MedeXState.selected_model == m["id"],
            THEME.PRIMARY_50,
            "transparent",
        ),
        _hover={"background": THEME.INTERACTIVE_HOVER},
        # CRITICAL: Use direct call syntax in rx.foreach, NOT lambda
        on_click=MedeXState.select_model_by_id(m["id"]),
        width="100%",
        border_radius=Radius.SM,
    )


def model_selector_dropdown() -> rx.Component:
    """Enhanced model selector dropdown with categories."""
    return rx.cond(
        MedeXState.show_model_selector,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Seleccionar Modelo",
                        font_size=Font.SIZE_SM,
                        font_weight=Font.WEIGHT_SEMIBOLD,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon("x", size=12),
                        size="1",
                        variant="ghost",
                        on_click=MedeXState.toggle_model_selector,
                    ),
                    width="100%",
                    align="center",
                    padding=f"0 {Space.S3}",
                ),
                rx.divider(),
                # Scrollable model list with enhanced info
                rx.scroll_area(
                    rx.vstack(
                        rx.foreach(
                            MedeXState.available_models,
                            model_option_card,
                        ),
                        gap=Space.S1,
                        width="100%",
                        padding=f"0 {Space.S1}",
                    ),
                    type="auto",
                    scrollbars="vertical",
                    style={"max-height": "320px"},
                ),
                rx.divider(),
                rx.hstack(
                    rx.badge("MED", color_scheme="green", size="1"),
                    rx.text(
                        "Especializado Médico",
                        font_size=Font.SIZE_2XS,
                        color=THEME.TEXT_MUTED,
                    ),
                    gap=Space.S1,
                    padding=f"0 {Space.S3}",
                ),
                gap=Space.S2,
                padding=Space.S2,
                width="100%",
            ),
            position="absolute",
            top="100%",
            right="0",
            margin_top=Space.S1,
            background=THEME.BG_CARD,
            border=f"1px solid {THEME.BORDER_DEFAULT}",
            border_radius=Radius.MD,
            box_shadow=Shadow.LG,
            min_width="280px",
            z_index="100",
        ),
        rx.fragment(),
    )


def header() -> rx.Component:
    """Application header with model selector."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon("bot", size=20, color=THEME.PRIMARY_500),
                rx.text(
                    rx.match(
                        MedeXState.active_section,
                        ("chat", "Asistente Médico IA"),
                        ("tools", "Herramientas Clínicas"),
                        ("knowledge", "Base de Conocimiento"),
                        ("triage", "Evaluación de Triage"),
                        ("history", "Historial de Sesión"),
                        ("research", "Deep Research"),
                        "MedeX",
                    ),
                    font_size=Font.SIZE_LG,
                    font_weight=Font.WEIGHT_SEMIBOLD,
                    color=THEME.TEXT_PRIMARY,
                ),
                gap=Space.S3,
                align="center",
            ),
            rx.spacer(),
            rx.hstack(
                # Model Selector Button
                rx.box(
                    rx.button(
                        rx.hstack(
                            rx.icon("cpu", size=14),
                            rx.text(
                                MedeXState.selected_model_name, font_size=Font.SIZE_XS
                            ),
                            rx.icon("chevron-down", size=12),
                            gap="4px",
                            align="center",
                        ),
                        variant="outline",
                        color_scheme="gray",
                        size="1",
                        on_click=MedeXState.toggle_model_selector,
                    ),
                    model_selector_dropdown(),
                    position="relative",
                ),
                rx.badge(
                    MedeXState.user_type_label,
                    color_scheme=rx.match(
                        MedeXState.user_type,
                        ("professional", "blue"),
                        ("research", "purple"),
                        "green",
                    ),
                    size="2",
                ),
                rx.button(
                    rx.hstack(rx.icon("plus", size=14), rx.text("New Chat"), gap="4px"),
                    variant="outline",
                    color_scheme="blue",
                    size="1",
                    on_click=MedeXState.new_conversation,
                ),
                rx.button(
                    rx.icon("trash-2", size=14),
                    variant="ghost",
                    color_scheme="gray",
                    size="1",
                    on_click=MedeXState.clear_chat,
                ),
                gap=Space.S2,
                align="center",
            ),
            width="100%",
            padding=f"{Space.S3} {Space.S6}",
            align="center",
        ),
        background=THEME.BG_CARD,
        border_bottom=f"1px solid {THEME.BORDER_DEFAULT}",
        width="100%",
        flex_shrink="0",
    )


# =============================================================================
# CHAT COMPONENTS
# =============================================================================


def empty_chat_state() -> rx.Component:
    """Empty chat welcome state - centered in the viewport."""
    return rx.center(
        rx.vstack(
            rx.box(
                rx.icon("stethoscope", size=48, color=THEME.PRIMARY_400),
                padding=Space.S6,
                background=THEME.PRIMARY_50,
                border_radius=Radius.XL,
            ),
            rx.text(
                "Bienvenido a MedeX",
                font_size=Font.SIZE_2XL,
                font_weight=Font.WEIGHT_BOLD,
                color=THEME.TEXT_PRIMARY,
                text_align="center",
            ),
            rx.text(
                "Tu asistente médico impulsado por IA. Haz cualquier consulta médica para comenzar.",
                font_size=Font.SIZE_BASE,
                color=THEME.TEXT_SECONDARY,
                text_align="center",
                max_width="420px",
            ),
            rx.hstack(
                rx.box(
                    rx.vstack(
                        rx.icon("graduation-cap", size=20, color=THEME.STABLE_500),
                        rx.text(
                            "Educacional",
                            font_size=Font.SIZE_SM,
                            font_weight=Font.WEIGHT_MEDIUM,
                            color=THEME.TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Explicaciones claras",
                            font_size=Font.SIZE_XS,
                            color=THEME.TEXT_MUTED,
                        ),
                        gap=Space.S1,
                        align="center",
                    ),
                    padding=Space.S4,
                    background=THEME.BG_SECONDARY,
                    border_radius=Radius.MD,
                    border=f"1px solid {THEME.BORDER_DEFAULT}",
                    flex="1",
                ),
                rx.box(
                    rx.vstack(
                        rx.icon("stethoscope", size=20, color=THEME.PRIMARY_500),
                        rx.text(
                            "Profesional",
                            font_size=Font.SIZE_SM,
                            font_weight=Font.WEIGHT_MEDIUM,
                            color=THEME.TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Detalle clínico",
                            font_size=Font.SIZE_XS,
                            color=THEME.TEXT_MUTED,
                        ),
                        gap=Space.S1,
                        align="center",
                    ),
                    padding=Space.S4,
                    background=THEME.BG_SECONDARY,
                    border_radius=Radius.MD,
                    border=f"1px solid {THEME.BORDER_DEFAULT}",
                    flex="1",
                ),
                gap=Space.S3,
                width="100%",
                max_width="320px",
                justify="center",
            ),
            gap=Space.S4,
            align="center",
            justify="center",
        ),
        width="100%",
        height="100%",
        flex="1",
        padding=Space.S8,
    )


def user_message(msg: dict) -> rx.Component:
    """User message bubble."""
    return rx.box(
        rx.flex(
            rx.box(
                rx.text(msg["content"], color=THEME.TEXT_INVERSE),
                background=THEME.PRIMARY_500,
                color=THEME.TEXT_INVERSE,
                padding=f"{Space.S3} {Space.S4}",
                border_radius="18px 18px 4px 18px",
                max_width=Layout.MESSAGE_MAX_WIDTH,
                box_shadow=Shadow.SM,
            ),
            justify="end",
            width="100%",
        ),
        margin_bottom=Space.S3,
    )


def assistant_message(msg: dict) -> rx.Component:
    """Assistant message bubble with enhanced formatting and copy button."""
    return rx.box(
        rx.flex(
            rx.hstack(
                rx.box(
                    rx.icon("bot", size=16, color=THEME.TEXT_INVERSE),
                    background=THEME.PRIMARY_500,
                    padding="8px",
                    border_radius=Radius.FULL,
                    flex_shrink="0",
                ),
                rx.box(
                    rx.cond(
                        # State 1: Still streaming AND has thinking but no content yet
                        msg["is_streaming"]
                        & (msg["thinking_content"] != "")
                        & (msg["content"] == ""),
                        # LIVE THINKING STATE - Show thinking in real-time (ChatGPT style)
                        rx.vstack(
                            # Thinking indicator header (open by default while streaming)
                            rx.box(
                                rx.hstack(
                                    rx.icon("brain", size=14, color=THEME.URGENT_500),
                                    rx.text(
                                        "Razonando...",
                                        font_size=Font.SIZE_SM,
                                        color=THEME.URGENT_700,
                                        font_weight="500",
                                    ),
                                    rx.spinner(size="1", color=THEME.URGENT_500),
                                    gap=Space.S2,
                                ),
                                padding=Space.S2,
                                border_radius=Radius.SM,
                                background=THEME.URGENT_50,
                            ),
                            # Live thinking content (visible while thinking)
                            rx.box(
                                rx.markdown(
                                    msg["thinking_content"],
                                    style={
                                        "color": THEME.TEXT_MUTED,
                                        "font-size": "0.85rem",
                                        "line-height": "1.5",
                                        "font-style": "italic",
                                    },
                                ),
                                background=THEME.URGENT_50,
                                padding=Space.S3,
                                border_radius=Radius.SM,
                                margin_top=Space.S2,
                                border_left=f"3px solid {THEME.URGENT_300}",
                                max_height="300px",
                                overflow_y="auto",
                            ),
                            width="100%",
                            gap=Space.S1,
                        ),
                        rx.cond(
                            msg["is_streaming"]
                            & (msg["content"] == "")
                            & (msg["thinking_content"] == ""),
                            # State 2: Initial thinking state - no content yet
                            rx.hstack(
                                rx.spinner(size="1"),
                                rx.text(
                                    "Pensando...",
                                    color=THEME.TEXT_MUTED,
                                    font_size=Font.SIZE_SM,
                                ),
                                gap=Space.S2,
                            ),
                            # State 3: Has content (streaming response or complete)
                            rx.vstack(
                                # Show thinking content for reasoning models (collapsible details)
                                rx.cond(
                                    msg["thinking_content"] != "",
                                    rx.el.details(
                                        rx.el.summary(
                                            rx.hstack(
                                                rx.icon(
                                                    "brain",
                                                    size=14,
                                                    color=THEME.URGENT_500,
                                                ),
                                                rx.text(
                                                    "Ver razonamiento del modelo",
                                                    font_size=Font.SIZE_SM,
                                                    color=THEME.URGENT_700,
                                                    font_weight="500",
                                                ),
                                                gap=Space.S2,
                                            ),
                                            cursor="pointer",
                                            padding=Space.S2,
                                            border_radius=Radius.SM,
                                            _hover={"background": THEME.URGENT_50},
                                            list_style="none",
                                        ),
                                        rx.box(
                                            rx.markdown(
                                                msg["thinking_content"],
                                                style={
                                                    "color": THEME.TEXT_MUTED,
                                                    "font-size": "0.85rem",
                                                    "line-height": "1.5",
                                                    "font-style": "italic",
                                                },
                                            ),
                                            background=THEME.URGENT_50,
                                            padding=Space.S3,
                                            border_radius=Radius.SM,
                                            margin_top=Space.S2,
                                            border_left=f"3px solid {THEME.URGENT_300}",
                                            max_height="400px",
                                            overflow_y="auto",
                                        ),
                                        margin_bottom=Space.S3,
                                        width="100%",
                                    ),
                                    rx.fragment(),
                                ),
                                rx.markdown(
                                    msg["content"],
                                    style={
                                        # Base text color for all markdown content
                                        "color": THEME.TEXT_PRIMARY,
                                        "font-size": "0.95rem",
                                        "line-height": "1.6",
                                        "& h1, & h2, & h3": {
                                            "margin-top": "1rem",
                                            "margin-bottom": "0.5rem",
                                            "color": THEME.PRIMARY_700,
                                            "font-weight": "600",
                                        },
                                        "& h2": {"font-size": "1.1rem"},
                                        "& h3": {"font-size": "1rem"},
                                        "& p": {
                                            "margin-bottom": "0.75rem",
                                            "line-height": "1.6",
                                            "color": THEME.TEXT_PRIMARY,
                                        },
                                        "& ul, & ol": {
                                            "margin-left": "1.25rem",
                                            "margin-bottom": "0.75rem",
                                            "color": THEME.TEXT_PRIMARY,
                                        },
                                        "& li": {
                                            "margin-bottom": "0.25rem",
                                            "line-height": "1.5",
                                            "color": THEME.TEXT_PRIMARY,
                                        },
                                        "& strong": {
                                            "color": THEME.PRIMARY_600,
                                            "font-weight": "600",
                                        },
                                        "& code": {
                                            "background": THEME.BG_SECONDARY,
                                            "padding": "0.125rem 0.375rem",
                                            "color": THEME.TEXT_PRIMARY,
                                            "border-radius": "4px",
                                            "font-size": "0.875em",
                                        },
                                        "& blockquote": {
                                            "border-left": f"3px solid {THEME.PRIMARY_400}",
                                            "padding-left": "1rem",
                                            "margin": "0.75rem 0",
                                            "color": THEME.TEXT_MUTED,
                                            "font-style": "italic",
                                        },
                                        "& table": {
                                            "width": "100%",
                                            "border-collapse": "collapse",
                                            "margin": "0.75rem 0",
                                        },
                                        "& th, & td": {
                                            "border": f"1px solid {THEME.BORDER_DEFAULT}",
                                            "padding": "0.5rem",
                                            "text-align": "left",
                                        },
                                        "& th": {
                                            "background": THEME.BG_SECONDARY,
                                            "font-weight": "600",
                                        },
                                    },
                                ),
                                # Show blinking cursor while streaming
                                rx.cond(
                                    msg["is_streaming"],
                                    rx.box(
                                        rx.text("▊", color=THEME.PRIMARY_500),
                                        class_name="animate-pulse",
                                    ),
                                    rx.fragment(),
                                ),
                                # Copy button - shown only when NOT streaming
                                rx.cond(
                                    ~msg["is_streaming"],
                                    rx.hstack(
                                        rx.tooltip(
                                            rx.icon_button(
                                                rx.cond(
                                                    MedeXState.copied_message_id
                                                    == msg["id"],
                                                    rx.icon(
                                                        "check",
                                                        size=14,
                                                        color=THEME.STABLE_500,
                                                    ),
                                                    rx.icon(
                                                        "copy",
                                                        size=14,
                                                        color=THEME.TEXT_MUTED,
                                                    ),
                                                ),
                                                variant="ghost",
                                                size="1",
                                                cursor="pointer",
                                                on_click=[
                                                    MedeXState.copy_message_to_clipboard(
                                                        msg["content"], msg["id"]
                                                    ),
                                                    rx.call_script(
                                                        "setTimeout(() => reflex___state___state.medex_state.clear_copied_feedback(), 2000)"
                                                    ),
                                                ],
                                                _hover={
                                                    "background": THEME.INTERACTIVE_HOVER
                                                },
                                            ),
                                            content=rx.cond(
                                                MedeXState.copied_message_id
                                                == msg["id"],
                                                "¡Copiado!",
                                                "Copiar mensaje",
                                            ),
                                        ),
                                        justify="end",
                                        width="100%",
                                        padding_top=Space.S2,
                                    ),
                                    rx.fragment(),
                                ),
                                gap="0",
                                width="100%",
                            ),
                        ),
                    ),
                    background=THEME.BG_CARD,
                    padding=Space.S4,
                    border_radius="4px 18px 18px 18px",
                    border=f"1px solid {THEME.BORDER_DEFAULT}",
                    max_width=Layout.MESSAGE_MAX_WIDTH,
                    box_shadow=Shadow.XS,
                    flex="1",
                ),
                gap=Space.S3,
                align="start",
                width="100%",
            ),
            justify="start",
            width="100%",
        ),
        margin_bottom=Space.S3,
    )


def message_item(msg: dict) -> rx.Component:
    """Render a single message."""
    return rx.cond(
        msg["role"] == "user",
        user_message(msg),
        assistant_message(msg),
    )


def chat_messages() -> rx.Component:
    """Chat messages container."""
    return rx.box(
        rx.foreach(
            MedeXState.messages_as_dicts,
            message_item,
        ),
        flex="1",
        overflow_y="auto",
        padding=Space.S6,
        width="100%",
    )


def chat_input() -> rx.Component:
    """Chat input area."""
    return rx.box(
        rx.hstack(
            rx.input(
                placeholder="Haz una pregunta médica...",
                value=MedeXState.current_input,
                on_change=MedeXState.set_input,
                on_key_down=MedeXState.handle_key_down,
                disabled=MedeXState.is_loading,
                size="3",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
                style={
                    "border-radius": Radius.LG,
                    "border": f"1px solid {THEME.BORDER_DEFAULT}",
                    "background": THEME.BG_CARD,
                    "padding": f"{Space.S3} {Space.S4}",
                    "font-size": "1rem",
                },
            ),
            rx.button(
                rx.cond(
                    MedeXState.is_loading,
                    rx.spinner(size="1"),
                    rx.icon("send", size=18),
                ),
                on_click=MedeXState.send_message,
                disabled=MedeXState.is_loading,
                size="3",
                color_scheme="blue",
                style={
                    "border-radius": Radius.LG,
                    "min-width": "48px",
                },
            ),
            gap=Space.S2,
            width="100%",
            align="center",
        ),
        padding=Space.S4,
        background=THEME.BG_CARD,
        border_top=f"1px solid {THEME.BORDER_DEFAULT}",
        width="100%",
    )


def chat_input_area() -> rx.Component:
    """Clean chat input area without external search tools.
    
    Design Decision: Chat module uses only the model's base knowledge
    to ensure responses are based on audited medical information.
    External search capabilities are reserved for Deep Research module.
    """
    return rx.box(
        rx.hstack(
            rx.input(
                placeholder="Haz una pregunta médica...",
                value=MedeXState.current_input,
                on_change=MedeXState.set_input,
                on_key_down=MedeXState.handle_key_down,
                disabled=MedeXState.is_loading,
                size="3",
                width="100%",
                style={
                    "border-radius": Radius.LG,
                    "border": f"1px solid {THEME.BORDER_DEFAULT}",
                    "background": THEME.BG_CARD,
                    "padding": f"{Space.S3} {Space.S4}",
                    "color": THEME.TEXT_PRIMARY,
                    "font-size": "1rem",
                },
            ),
            rx.button(
                rx.cond(
                    MedeXState.is_loading,
                    rx.spinner(size="1"),
                    rx.icon("send", size=18),
                ),
                on_click=MedeXState.send_message,
                disabled=MedeXState.is_loading,
                size="3",
                color_scheme="blue",
                style={
                    "border-radius": Radius.LG,
                    "min-width": "48px",
                },
            ),
            gap=Space.S2,
            width="100%",
            align="center",
        ),
        padding=Space.S4,
        background=THEME.BG_CARD,
        border_top=f"1px solid {THEME.BORDER_DEFAULT}",
        width="100%",
    )


def chat_panel() -> rx.Component:
    """Complete chat panel."""
    return rx.vstack(
        rx.cond(
            MedeXState.has_messages,
            chat_messages(),
            empty_chat_state(),
        ),
        chat_input_area(),
        height="100%",
        width="100%",
        gap="0",
    )


# =============================================================================
# TOOLS PANEL
# =============================================================================


def tool_tab_interactions() -> rx.Component:
    """Interactions tool tab."""
    tool_id = "interactions"
    return rx.box(
        rx.hstack(
            rx.icon(
                "git-compare",
                size=16,
                color=rx.cond(
                    MedeXState.active_tool == tool_id,
                    THEME.PRIMARY_500,
                    THEME.TEXT_MUTED,
                ),
            ),
            rx.text(
                "Drug Interactions",
                font_size=Font.SIZE_SM,
                font_weight=rx.cond(
                    MedeXState.active_tool == tool_id,
                    Font.WEIGHT_MEDIUM,
                    Font.WEIGHT_NORMAL,
                ),
                color=rx.cond(
                    MedeXState.active_tool == tool_id,
                    THEME.TEXT_PRIMARY,
                    THEME.TEXT_SECONDARY,
                ),
            ),
            gap=Space.S2,
            align="center",
        ),
        padding=f"{Space.S2} {Space.S4}",
        border_radius=Radius.DEFAULT,
        cursor="pointer",
        background=rx.cond(
            MedeXState.active_tool == tool_id, THEME.PRIMARY_50, "transparent"
        ),
        on_click=MedeXState.set_tool_interactions,
        _hover={"background": THEME.INTERACTIVE_HOVER},
    )


def tool_tab_dosage() -> rx.Component:
    """Dosage tool tab."""
    tool_id = "dosage"
    return rx.box(
        rx.hstack(
            rx.icon(
                "calculator",
                size=16,
                color=rx.cond(
                    MedeXState.active_tool == tool_id,
                    THEME.PRIMARY_500,
                    THEME.TEXT_MUTED,
                ),
            ),
            rx.text(
                "Dosage Calculator",
                font_size=Font.SIZE_SM,
                font_weight=rx.cond(
                    MedeXState.active_tool == tool_id,
                    Font.WEIGHT_MEDIUM,
                    Font.WEIGHT_NORMAL,
                ),
                color=rx.cond(
                    MedeXState.active_tool == tool_id,
                    THEME.TEXT_PRIMARY,
                    THEME.TEXT_SECONDARY,
                ),
            ),
            gap=Space.S2,
            align="center",
        ),
        padding=f"{Space.S2} {Space.S4}",
        border_radius=Radius.DEFAULT,
        cursor="pointer",
        background=rx.cond(
            MedeXState.active_tool == tool_id, THEME.PRIMARY_50, "transparent"
        ),
        on_click=MedeXState.set_tool_dosage,
        _hover={"background": THEME.INTERACTIVE_HOVER},
    )


def tool_tab_labs() -> rx.Component:
    """Labs tool tab."""
    tool_id = "labs"
    return rx.box(
        rx.hstack(
            rx.icon(
                "flask-conical",
                size=16,
                color=rx.cond(
                    MedeXState.active_tool == tool_id,
                    THEME.PRIMARY_500,
                    THEME.TEXT_MUTED,
                ),
            ),
            rx.text(
                "Lab Interpreter",
                font_size=Font.SIZE_SM,
                font_weight=rx.cond(
                    MedeXState.active_tool == tool_id,
                    Font.WEIGHT_MEDIUM,
                    Font.WEIGHT_NORMAL,
                ),
                color=rx.cond(
                    MedeXState.active_tool == tool_id,
                    THEME.TEXT_PRIMARY,
                    THEME.TEXT_SECONDARY,
                ),
            ),
            gap=Space.S2,
            align="center",
        ),
        padding=f"{Space.S2} {Space.S4}",
        border_radius=Radius.DEFAULT,
        cursor="pointer",
        background=rx.cond(
            MedeXState.active_tool == tool_id, THEME.PRIMARY_50, "transparent"
        ),
        on_click=MedeXState.set_tool_labs,
        _hover={"background": THEME.INTERACTIVE_HOVER},
    )


# =============================================================================
# ARTIFACT CATALOG COMPONENTS
# =============================================================================


def artifact_card(artifact: dict) -> rx.Component:
    """Individual artifact card for catalog display."""
    return rx.box(
        rx.vstack(
            # Header with number and badges
            rx.hstack(
                rx.hstack(
                    rx.text(
                        artifact["number"],
                        font_size=Font.SIZE_XS,
                        font_weight=Font.WEIGHT_BOLD,
                        color=THEME.TEXT_INVERSE,
                    ),
                    background=THEME.PRIMARY_500,
                    padding=f"2px {Space.S2}",
                    border_radius=Radius.SM,
                ),
                rx.cond(
                    artifact["is_new"],
                    rx.badge("New!", color_scheme="green", size="1", variant="solid"),
                    rx.fragment(),
                ),
                rx.spacer(),
                rx.badge(
                    artifact["severity_label"],
                    color_scheme=artifact["severity_color"],
                    size="1",
                    variant="soft",
                ),
                width="100%",
                align="center",
            ),
            # Title
            rx.text(
                artifact["title"],
                font_size=Font.SIZE_SM,
                font_weight=Font.WEIGHT_SEMIBOLD,
                color=THEME.TEXT_PRIMARY,
            ),
            # Subtitle
            rx.text(
                artifact["subtitle"],
                font_size=Font.SIZE_XS,
                color=THEME.TEXT_SECONDARY,
                no_of_lines=1,
            ),
            # Summary
            rx.text(
                artifact["summary"],
                font_size=Font.SIZE_XS,
                color=THEME.TEXT_MUTED,
                no_of_lines=2,
            ),
            # Spacer to push buttons to bottom
            rx.spacer(),
            # Action buttons row - Ver Más left, Download/Delete right
            rx.hstack(
                # Ver Más button - left side
                rx.button(
                    rx.hstack(
                        rx.icon("eye", size=12),
                        rx.text("Ver Más", font_size=Font.SIZE_XS),
                        gap="4px",
                    ),
                    size="1",
                    variant="soft",
                    color_scheme="blue",
                    # CRITICAL: Direct call in rx.foreach, NOT lambda
                    on_click=MedeXState.open_artifact_modal_by_id(
                        artifact["id"], artifact["type"]
                    ),
                ),
                rx.spacer(),
                # Download and Delete buttons - right side with good spacing
                rx.hstack(
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("download", size=14),
                            size="1",
                            variant="ghost",
                            color_scheme="green",
                            # CRITICAL: Direct call in rx.foreach, NOT lambda
                            on_click=MedeXState.export_artifact_pdf_by_id(
                                artifact["id"], artifact["type"]
                            ),
                        ),
                        content="Exportar PDF",
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon("trash-2", size=14),
                            size="1",
                            variant="ghost",
                            color_scheme="red",
                            # CRITICAL: Direct call in rx.foreach, NOT lambda
                            on_click=MedeXState.delete_artifact(
                                artifact["id"], artifact["type"]
                            ),
                        ),
                        content="Eliminar",
                    ),
                    gap=Space.S2,  # Good spacing between buttons
                ),
                width="100%",
                align="center",
            ),
            gap=Space.S2,
            align="start",
            width="100%",
            height="100%",  # Full height for spacer to work
            min_height="180px",  # Minimum card height
        ),
        padding=Space.S3,
        background=THEME.BG_CARD,
        border=f"1px solid {THEME.BORDER_DEFAULT}",
        border_radius=Radius.MD,
        box_shadow=Shadow.SM,
        transition=f"all {Transition.NORMAL}",
        _hover={
            "box_shadow": Shadow.MD,
            "border_color": THEME.PRIMARY_300,
        },
        min_width="200px",
        max_width="280px",
    )


def artifact_modal() -> rx.Component:
    """Modal dialog for viewing full artifact content."""
    return rx.cond(
        MedeXState.show_artifact_modal,
        rx.box(
            # Overlay
            rx.box(
                position="fixed",
                top="0",
                left="0",
                right="0",
                bottom="0",
                background="rgba(0, 0, 0, 0.5)",
                z_index="998",
                on_click=MedeXState.close_artifact_modal,
            ),
            # Modal content
            rx.box(
                rx.vstack(
                    # Modal header
                    rx.hstack(
                        rx.hstack(
                            rx.badge(
                                MedeXState.active_artifact_severity_label,
                                color_scheme=MedeXState.active_artifact_severity_color,
                                size="2",
                            ),
                            rx.text(
                                MedeXState.active_artifact_title,
                                font_size=Font.SIZE_LG,
                                font_weight=Font.WEIGHT_SEMIBOLD,
                                color=THEME.TEXT_PRIMARY,
                            ),
                            gap=Space.S2,
                            align="center",
                        ),
                        rx.spacer(),
                        rx.icon_button(
                            rx.icon("x", size=16),
                            size="2",
                            variant="ghost",
                            on_click=MedeXState.close_artifact_modal,
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.text(
                        MedeXState.active_artifact_subtitle,
                        font_size=Font.SIZE_SM,
                        color=THEME.TEXT_SECONDARY,
                    ),
                    rx.divider(),
                    # Modal body - scrollable markdown content
                    rx.scroll_area(
                        rx.markdown(
                            MedeXState.active_artifact_full_content,
                            style={
                                "color": THEME.TEXT_PRIMARY,
                                "& h1, & h2, & h3, & h4": {
                                    "color": THEME.PRIMARY_700,
                                    "margin-top": "1rem",
                                    "margin-bottom": "0.5rem",
                                },
                                "& h2": {"font-size": "1.1rem"},
                                "& h3": {"font-size": "1rem"},
                                "& p": {
                                    "margin-bottom": "0.75rem",
                                    "line-height": "1.6",
                                    "color": THEME.TEXT_PRIMARY,
                                },
                                "& ul, & ol": {
                                    "margin-left": "1.5rem",
                                    "margin-bottom": "0.75rem",
                                    "color": THEME.TEXT_PRIMARY,
                                },
                                "& li": {
                                    "margin-bottom": "0.25rem",
                                    "color": THEME.TEXT_PRIMARY,
                                },
                                "& strong": {
                                    "color": THEME.PRIMARY_600,
                                },
                                "& table": {
                                    "width": "100%",
                                    "border-collapse": "collapse",
                                    "margin-bottom": "1rem",
                                },
                                "& th, & td": {
                                    "border": f"1px solid {THEME.BORDER_DEFAULT}",
                                    "padding": "0.5rem",
                                    "text-align": "left",
                                    "color": THEME.TEXT_PRIMARY,
                                },
                                "& th": {
                                    "background": THEME.BG_SECONDARY,
                                    "font-weight": "600",
                                },
                            },
                        ),
                        type="auto",
                        scrollbars="vertical",
                        style={"max-height": "60vh"},
                    ),
                    rx.divider(),
                    # Modal footer
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.icon("download", size=14),
                                rx.text("Exportar PDF"),
                                gap="4px",
                            ),
                            variant="solid",
                            color_scheme="blue",
                            on_click=MedeXState.export_active_artifact_pdf,
                        ),
                        rx.button(
                            "Cerrar",
                            variant="outline",
                            color_scheme="gray",
                            on_click=MedeXState.close_artifact_modal,
                        ),
                        gap=Space.S2,
                        justify="end",
                        width="100%",
                    ),
                    gap=Space.S3,
                    width="100%",
                ),
                position="fixed",
                top="50%",
                left="50%",
                transform="translate(-50%, -50%)",
                background=THEME.BG_CARD,
                padding=Space.S6,
                border_radius=Radius.LG,
                box_shadow=Shadow.XL,
                z_index="999",
                width="90%",
                max_width="700px",
            ),
        ),
        rx.fragment(),
    )


def interaction_artifacts_grid() -> rx.Component:
    """Grid display of interaction artifact cards."""
    return rx.cond(
        MedeXState.has_interaction_artifacts,
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("layout-grid", size=16, color=THEME.PRIMARY_500),
                    rx.text(
                        "Resultados",
                        font_size=Font.SIZE_SM,
                        font_weight=Font.WEIGHT_MEDIUM,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.badge(
                        MedeXState.interaction_artifacts_count,
                        color_scheme="blue",
                        size="1",
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon("trash-2", size=12),
                        rx.text("Limpiar Todo", font_size=Font.SIZE_XS),
                        gap="4px",
                    ),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=MedeXState.clear_interaction_artifacts,
                ),
                width="100%",
                align="center",
            ),
            rx.box(
                rx.foreach(
                    MedeXState.interaction_artifacts,
                    artifact_card,
                ),
                display="grid",
                grid_template_columns="repeat(auto-fill, minmax(220px, 1fr))",
                gap=Space.S3,
                width="100%",
            ),
            gap=Space.S3,
            width="100%",
        ),
        rx.fragment(),
    )


def dosage_artifacts_grid() -> rx.Component:
    """Grid display of dosage artifact cards."""
    return rx.cond(
        MedeXState.has_dosage_artifacts,
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("layout-grid", size=16, color=THEME.PRIMARY_500),
                    rx.text(
                        "Resultados",
                        font_size=Font.SIZE_SM,
                        font_weight=Font.WEIGHT_MEDIUM,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.badge(
                        MedeXState.dosage_artifacts_count,
                        color_scheme="blue",
                        size="1",
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon("trash-2", size=12),
                        rx.text("Limpiar Todo", font_size=Font.SIZE_XS),
                        gap="4px",
                    ),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=MedeXState.clear_dosage_artifacts,
                ),
                width="100%",
                align="center",
            ),
            rx.box(
                rx.foreach(
                    MedeXState.dosage_artifacts,
                    artifact_card,
                ),
                display="grid",
                grid_template_columns="repeat(auto-fill, minmax(220px, 1fr))",
                gap=Space.S3,
                width="100%",
            ),
            gap=Space.S3,
            width="100%",
        ),
        rx.fragment(),
    )


def lab_artifacts_grid() -> rx.Component:
    """Grid display of lab artifact cards."""
    return rx.cond(
        MedeXState.has_lab_artifacts,
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("layout-grid", size=16, color=THEME.PRIMARY_500),
                    rx.text(
                        "Resultados",
                        font_size=Font.SIZE_SM,
                        font_weight=Font.WEIGHT_MEDIUM,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.badge(
                        MedeXState.lab_artifacts_count,
                        color_scheme="blue",
                        size="1",
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon("trash-2", size=12),
                        rx.text("Limpiar Todo", font_size=Font.SIZE_XS),
                        gap="4px",
                    ),
                    size="1",
                    variant="ghost",
                    color_scheme="red",
                    on_click=MedeXState.clear_lab_artifacts,
                ),
                width="100%",
                align="center",
            ),
            rx.box(
                rx.foreach(
                    MedeXState.lab_artifacts,
                    artifact_card,
                ),
                display="grid",
                grid_template_columns="repeat(auto-fill, minmax(220px, 1fr))",
                gap=Space.S3,
                width="100%",
            ),
            gap=Space.S3,
            width="100%",
        ),
        rx.fragment(),
    )


def tool_tabs() -> rx.Component:
    """Tool tabs navigation."""
    return rx.hstack(
        tool_tab_interactions(),
        tool_tab_dosage(),
        tool_tab_labs(),
        gap=Space.S1,
        padding=Space.S2,
        background=THEME.BG_SECONDARY,
        border_radius=Radius.MD,
        width="100%",
    )


def drug_interactions_panel() -> rx.Component:
    """Drug interactions checker panel."""
    return rx.vstack(
        rx.text(
            "Verificar Interacciones Farmacológicas",
            font_size=Font.SIZE_LG,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.TEXT_PRIMARY,
        ),
        rx.text(
            "Ingrese los medicamentos separados por coma para verificar interacciones.",
            font_size=Font.SIZE_SM,
            color=THEME.TEXT_SECONDARY,
        ),
        rx.vstack(
            rx.input(
                placeholder="Ej: Warfarina, Aspirina, Ibuprofeno (separados por coma)",
                value=MedeXState.drugs_input,
                on_change=MedeXState.set_drugs_input,
                size="3",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            rx.text(
                "Mínimo 2 medicamentos", font_size=Font.SIZE_XS, color=THEME.TEXT_MUTED
            ),
            gap="4px",
            width="100%",
        ),
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.cond(
                        MedeXState.interactions_loading,
                        rx.spinner(size="1"),
                        rx.icon("search", size=16),
                    ),
                    rx.text("Verificar Interacciones"),
                    gap=Space.S2,
                ),
                on_click=MedeXState.check_interactions,
                disabled=MedeXState.interactions_loading,
                size="3",
                color_scheme="blue",
            ),
            rx.button(
                "Limpiar",
                variant="outline",
                color_scheme="gray",
                size="3",
                on_click=MedeXState.clear_interactions,
            ),
            rx.cond(
                MedeXState.has_interactions,
                rx.button(
                    rx.hstack(
                        rx.icon("download", size=14), rx.text("Exportar"), gap="4px"
                    ),
                    variant="outline",
                    color_scheme="green",
                    size="3",
                    on_click=MedeXState.export_interactions_pdf,
                ),
                rx.fragment(),
            ),
            gap=Space.S2,
        ),
        # Progress indicator
        rx.cond(
            MedeXState.interactions_loading,
            rx.box(
                rx.hstack(
                    rx.spinner(size="1"),
                    rx.text(
                        MedeXState.interactions_status,
                        font_size=Font.SIZE_SM,
                        color=THEME.PRIMARY_600,
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                padding=Space.S3,
                background=THEME.PRIMARY_50,
                border_radius=Radius.MD,
                border=f"1px solid {THEME.PRIMARY_200}",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MedeXState.interactions_error != "",
            rx.box(
                rx.text(
                    MedeXState.interactions_error,
                    color=THEME.TEXT_SECONDARY,
                    font_size=Font.SIZE_SM,
                ),
                padding=Space.S4,
                background=THEME.BG_SECONDARY,
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.fragment(),
        ),
        # Artifact Catalog Grid for Interactions
        interaction_artifacts_grid(),
        gap=Space.S4,
        padding=Space.S6,
        width="100%",
        align="start",
    )


def dosage_calculator_panel() -> rx.Component:
    """Dosage calculator panel."""
    return rx.vstack(
        rx.text(
            "Calculadora de Dosificación",
            font_size=Font.SIZE_LG,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.TEXT_PRIMARY,
        ),
        rx.text(
            "Calcule la dosificación según parámetros del paciente.",
            font_size=Font.SIZE_SM,
            color=THEME.TEXT_SECONDARY,
        ),
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Medicamento",
                    font_size=Font.SIZE_SM,
                    font_weight=Font.WEIGHT_MEDIUM,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.input(
                    placeholder="ej: Amoxicilina",
                    value=MedeXState.dosage_drug_name,
                    on_change=MedeXState.set_dosage_drug,
                    size="3",
                    width="100%",
                    color=THEME.TEXT_PRIMARY,
                    _placeholder={"color": THEME.INPUT_PLACEHOLDER},
                ),
                gap=Space.S1,
                flex="2",
            ),
            rx.vstack(
                rx.text(
                    "Peso (kg)",
                    font_size=Font.SIZE_SM,
                    font_weight=Font.WEIGHT_MEDIUM,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.input(
                    placeholder="ej: 70",
                    value=MedeXState.dosage_patient_weight,
                    on_change=MedeXState.set_dosage_weight,
                    size="3",
                    width="100%",
                    color=THEME.TEXT_PRIMARY,
                    _placeholder={"color": THEME.INPUT_PLACEHOLDER},
                ),
                gap=Space.S1,
                flex="1",
            ),
            rx.vstack(
                rx.text(
                    "Edad (años)",
                    font_size=Font.SIZE_SM,
                    font_weight=Font.WEIGHT_MEDIUM,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.input(
                    placeholder="ej: 45",
                    value=MedeXState.dosage_patient_age,
                    on_change=MedeXState.set_dosage_age,
                    size="3",
                    width="100%",
                    color=THEME.TEXT_PRIMARY,
                    _placeholder={"color": THEME.INPUT_PLACEHOLDER},
                ),
                gap=Space.S1,
                flex="1",
            ),
            gap=Space.S3,
            width="100%",
        ),
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.cond(
                        MedeXState.dosage_loading,
                        rx.spinner(size="1"),
                        rx.icon("calculator", size=16),
                    ),
                    rx.text("Calcular"),
                    gap=Space.S2,
                ),
                on_click=MedeXState.calculate_dosage,
                disabled=MedeXState.dosage_loading,
                size="3",
                color_scheme="blue",
            ),
            rx.button(
                "Limpiar",
                variant="outline",
                color_scheme="gray",
                size="3",
                on_click=MedeXState.clear_dosage,
            ),
            rx.cond(
                MedeXState.dosage_result != "",
                rx.button(
                    rx.hstack(
                        rx.icon("download", size=14), rx.text("Exportar"), gap="4px"
                    ),
                    variant="outline",
                    color_scheme="green",
                    size="3",
                    on_click=MedeXState.export_dosage_pdf,
                ),
                rx.fragment(),
            ),
            gap=Space.S2,
        ),
        # Progress indicator
        rx.cond(
            MedeXState.dosage_loading,
            rx.box(
                rx.hstack(
                    rx.spinner(size="1"),
                    rx.text(
                        MedeXState.dosage_status,
                        font_size=Font.SIZE_SM,
                        color=THEME.PRIMARY_600,
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                padding=Space.S3,
                background=THEME.PRIMARY_50,
                border_radius=Radius.MD,
                border=f"1px solid {THEME.PRIMARY_200}",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MedeXState.dosage_error != "",
            rx.box(
                rx.text(
                    MedeXState.dosage_error,
                    color=THEME.CRITICAL_500,
                    font_size=Font.SIZE_SM,
                ),
                padding=Space.S3,
                background=THEME.CRITICAL_50,
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.fragment(),
        ),
        # Artifact Catalog Grid for Dosage
        dosage_artifacts_grid(),
        gap=Space.S4,
        padding=Space.S6,
        width="100%",
        align="start",
    )


def lab_interpreter_panel() -> rx.Component:
    """Lab results interpreter panel."""
    return rx.vstack(
        rx.text(
            "Interpretación de Laboratorio",
            font_size=Font.SIZE_LG,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.TEXT_PRIMARY,
        ),
        rx.text(
            "Ingrese los resultados de laboratorio para interpretación con IA.",
            font_size=Font.SIZE_SM,
            color=THEME.TEXT_SECONDARY,
        ),
        rx.text_area(
            placeholder="Pegue los resultados aquí...\n\nEjemplo:\nHb: 9.8 g/dL\nWBC: 12,000/μL\nPlaquetas: 250,000/μL\nGlucosa: 126 mg/dL",
            value=MedeXState.lab_text_input,
            on_change=MedeXState.set_lab_text,
            size="3",
            width="100%",
            min_height="150px",
            color=THEME.TEXT_PRIMARY,
            _placeholder={"color": THEME.INPUT_PLACEHOLDER},
        ),
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.cond(
                        MedeXState.lab_loading,
                        rx.spinner(size="1"),
                        rx.icon("flask-conical", size=16),
                    ),
                    rx.text("Interpretar"),
                    gap=Space.S2,
                ),
                on_click=MedeXState.interpret_labs,
                disabled=MedeXState.lab_loading,
                size="3",
                color_scheme="blue",
            ),
            rx.button(
                "Limpiar",
                variant="outline",
                color_scheme="gray",
                size="3",
                on_click=MedeXState.clear_labs,
            ),
            rx.cond(
                MedeXState.lab_interpretation != "",
                rx.button(
                    rx.hstack(
                        rx.icon("download", size=14), rx.text("Exportar"), gap="4px"
                    ),
                    variant="outline",
                    color_scheme="green",
                    size="3",
                    on_click=MedeXState.export_labs_pdf,
                ),
                rx.fragment(),
            ),
            gap=Space.S2,
        ),
        # Progress indicator
        rx.cond(
            MedeXState.lab_loading,
            rx.box(
                rx.hstack(
                    rx.spinner(size="1"),
                    rx.text(
                        MedeXState.lab_status,
                        font_size=Font.SIZE_SM,
                        color=THEME.PRIMARY_600,
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                padding=Space.S3,
                background=THEME.PRIMARY_50,
                border_radius=Radius.MD,
                border=f"1px solid {THEME.PRIMARY_200}",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MedeXState.lab_error != "",
            rx.box(
                rx.text(
                    MedeXState.lab_error,
                    color=THEME.CRITICAL_500,
                    font_size=Font.SIZE_SM,
                ),
                padding=Space.S3,
                background=THEME.CRITICAL_50,
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.fragment(),
        ),
        # Artifact Catalog Grid for Labs
        lab_artifacts_grid(),
        gap=Space.S4,
        padding=Space.S6,
        width="100%",
        align="start",
    )


def tools_panel() -> rx.Component:
    """Complete tools panel."""
    return rx.vstack(
        tool_tabs(),
        rx.match(
            MedeXState.active_tool,
            ("interactions", drug_interactions_panel()),
            ("dosage", dosage_calculator_panel()),
            ("labs", lab_interpreter_panel()),
            drug_interactions_panel(),
        ),
        height="100%",
        width="100%",
        overflow_y="auto",
    )


# =============================================================================
# RESEARCH PANEL (Deep Research Mode)
# =============================================================================


def research_step_item(step: dict) -> rx.Component:
    """Single research step indicator."""
    return rx.hstack(
        rx.cond(
            step["status"] == "completed",
            rx.icon("check", size=16, color=THEME.STABLE_500),
            rx.cond(
                step["status"] == "in_progress",
                rx.spinner(size="1"),
                rx.icon("circle", size=16, color=THEME.TEXT_MUTED),
            ),
        ),
        rx.text(
            step["title"],
            font_size=Font.SIZE_SM,
            color=rx.cond(
                step["status"] == "completed",
                THEME.TEXT_PRIMARY,
                rx.cond(
                    step["status"] == "in_progress",
                    THEME.PRIMARY_600,
                    THEME.TEXT_MUTED,
                ),
            ),
        ),
        gap=Space.S2,
        align="center",
    )


def research_clarification_panel() -> rx.Component:
    """Panel for clarification questions before research - ChatGPT style protocol.

    Uses static UI components instead of dynamic foreach to avoid Reflex type issues.
    """
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("circle-help", size=20, color=THEME.PRIMARY_500),
                rx.text(
                    "Antes de investigar, configura tu búsqueda...",
                    font_size=Font.SIZE_BASE,
                    font_weight=Font.WEIGHT_SEMIBOLD,
                    color=THEME.TEXT_PRIMARY,
                ),
                gap=Space.S2,
                align="center",
            ),
            rx.text(
                "Para brindarte resultados de la más alta calidad académica, necesito entender mejor tus necesidades:",
                font_size=Font.SIZE_SM,
                color=THEME.TEXT_SECONDARY,
                margin_bottom=Space.S2,
            ),
            rx.divider(),
            # Question 1: Format preference
            rx.box(
                rx.vstack(
                    rx.text(
                        "¿Qué formato de respuesta prefieres?",
                        font_size=Font.SIZE_SM,
                        font_weight=Font.WEIGHT_MEDIUM,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.select.root(
                        rx.select.trigger(placeholder="Seleccionar formato..."),
                        rx.select.content(
                            rx.select.item(
                                "📚 Informe completo con referencias académicas (estilo tesis doctoral)",
                                value="comprehensive",
                            ),
                            rx.select.item(
                                "🏥 Síntesis clínica práctica (estilo guía de práctica clínica)",
                                value="clinical",
                            ),
                            rx.select.item(
                                "📋 Resumen ejecutivo (puntos clave en 1-2 páginas)",
                                value="summary",
                            ),
                        ),
                        default_value="comprehensive",
                        on_change=lambda v: MedeXState.set_clarification_answer(
                            "format", v
                        ),
                        size="2",
                        width="100%",
                    ),
                    gap=Space.S2,
                    align="start",
                    width="100%",
                ),
                padding=Space.S3,
                background=THEME.BG_SECONDARY,
                border_radius=Radius.MD,
                margin_bottom=Space.S2,
                width="100%",
            ),
            # Question 2: Include references
            rx.box(
                rx.vstack(
                    rx.text(
                        "¿Deseas incluir referencias bibliográficas detalladas?",
                        font_size=Font.SIZE_SM,
                        font_weight=Font.WEIGHT_MEDIUM,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.hstack(
                        rx.switch(
                            default_checked=True,
                            on_change=lambda v: MedeXState.set_clarification_answer(
                                "references", str(v)
                            ),
                            size="2",
                        ),
                        rx.text(
                            "Incluir referencias (estilo Vancouver/APA)",
                            font_size=Font.SIZE_SM,
                            color=THEME.TEXT_SECONDARY,
                        ),
                        gap=Space.S2,
                        align="center",
                    ),
                    gap=Space.S2,
                    align="start",
                    width="100%",
                ),
                padding=Space.S3,
                background=THEME.BG_SECONDARY,
                border_radius=Radius.MD,
                margin_bottom=Space.S2,
                width="100%",
            ),
            # Question 3: Evidence level preference
            rx.box(
                rx.vstack(
                    rx.text(
                        "¿Qué nivel de evidencia prefieres priorizar?",
                        font_size=Font.SIZE_SM,
                        font_weight=Font.WEIGHT_MEDIUM,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Seleccionar nivel de evidencia..."
                        ),
                        rx.select.content(
                            rx.select.item(
                                "🔍 Toda la literatura disponible (más completo)",
                                value="all",
                            ),
                            rx.select.item(
                                "⭐ Solo evidencia alta (meta-análisis, ECAs)",
                                value="high",
                            ),
                            rx.select.item(
                                "🧪 Enfoque en ensayos clínicos",
                                value="clinical_trials",
                            ),
                        ),
                        default_value="all",
                        on_change=lambda v: MedeXState.set_clarification_answer(
                            "evidence_level", v
                        ),
                        size="2",
                        width="100%",
                    ),
                    gap=Space.S2,
                    align="start",
                    width="100%",
                ),
                padding=Space.S3,
                background=THEME.BG_SECONDARY,
                border_radius=Radius.MD,
                margin_bottom=Space.S2,
                width="100%",
            ),
            rx.divider(),
            # Action buttons
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("check", size=16),
                        rx.text("Confirmar y Comenzar"),
                        gap=Space.S2,
                    ),
                    on_click=[
                        MedeXState.confirm_clarification,
                        MedeXState.start_research,
                    ],
                    size="3",
                    color_scheme="blue",
                ),
                rx.button(
                    "Usar configuración predeterminada",
                    on_click=[
                        MedeXState.skip_clarification,
                        MedeXState.start_research,
                    ],
                    variant="outline",
                    size="3",
                    color_scheme="gray",
                ),
                rx.button(
                    "Volver",
                    on_click=MedeXState.clear_research,
                    variant="ghost",
                    size="3",
                    color_scheme="gray",
                ),
                gap=Space.S2,
                flex_wrap="wrap",
            ),
            gap=Space.S3,
            align="start",
            width="100%",
        ),
        padding=Space.S4,
        background=THEME.PRIMARY_50,
        border=f"1px solid {THEME.PRIMARY_200}",
        border_radius=Radius.MD,
        margin_top=Space.S3,
        width="100%",
    )


def research_panel() -> rx.Component:
    """Deep Research mode panel with scientific literature search."""
    return rx.vstack(
        rx.hstack(
            rx.icon("microscope", size=24, color=THEME.PRIMARY_500),
            rx.vstack(
                rx.text(
                    "Deep Research",
                    font_size=Font.SIZE_LG,
                    font_weight=Font.WEIGHT_SEMIBOLD,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.text(
                    "Investigación científica con acceso a PubMed, Semantic Scholar y clasificación de evidencia.",
                    font_size=Font.SIZE_SM,
                    color=THEME.TEXT_SECONDARY,
                ),
                gap="2px",
                align="start",
            ),
            gap=Space.S3,
            align="center",
            width="100%",
        ),
        rx.divider(margin=f"{Space.S3} 0"),
        rx.vstack(
            rx.text(
                "Tema de Investigación",
                font_size=Font.SIZE_SM,
                font_weight=Font.WEIGHT_MEDIUM,
                color=THEME.TEXT_PRIMARY,
            ),
            rx.text_area(
                placeholder="Ingrese el tema médico que desea investigar en profundidad.\n\nEjemplo: 'Nuevas terapias para diabetes tipo 2 resistente a metformina'",
                value=MedeXState.research_query,
                on_change=MedeXState.set_research_query,
                size="3",
                width="100%",
                min_height="100px",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            gap=Space.S1,
            width="100%",
        ),
        # Action buttons - Phase dependent
        rx.cond(
            MedeXState.research_phase == "input",
            # Phase: Input - Show "Configure Research" button
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("settings", size=16),
                        rx.text("Configurar Investigación"),
                        gap=Space.S2,
                    ),
                    on_click=MedeXState.initiate_research_clarification,
                    size="3",
                    color_scheme="blue",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon("zap", size=16),
                        rx.text("Iniciar Rápido"),
                        gap=Space.S2,
                    ),
                    on_click=MedeXState.start_research,
                    variant="outline",
                    size="3",
                    color_scheme="gray",
                ),
                rx.button(
                    "Limpiar",
                    variant="ghost",
                    color_scheme="gray",
                    size="3",
                    on_click=MedeXState.clear_research,
                ),
                gap=Space.S2,
            ),
            rx.fragment(),
        ),
        # Phase: Clarification - Show clarification questions
        rx.cond(
            MedeXState.research_phase == "clarify",
            research_clarification_panel(),
            rx.fragment(),
        ),
        # Phase: Researching - Show loading state
        rx.cond(
            MedeXState.research_phase == "researching",
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.cond(
                            MedeXState.research_loading,
                            rx.spinner(size="1"),
                            rx.icon("search", size=16),
                        ),
                        rx.text("Investigando..."),
                        gap=Space.S2,
                    ),
                    disabled=True,
                    size="3",
                    color_scheme="blue",
                ),
                rx.button(
                    "Cancelar",
                    variant="outline",
                    color_scheme="red",
                    size="3",
                    on_click=MedeXState.clear_research,
                ),
                gap=Space.S2,
            ),
            rx.fragment(),
        ),
        # Legacy button row for backwards compatibility
        rx.cond(
            (MedeXState.research_phase == "complete")
            | (MedeXState.research_result != ""),
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("refresh-cw", size=16),
                        rx.text("Nueva Investigación"),
                        gap=Space.S2,
                    ),
                    on_click=MedeXState.clear_research,
                    size="3",
                    color_scheme="blue",
                    variant="outline",
                ),
                rx.cond(
                    MedeXState.research_result != "",
                    rx.button(
                        rx.hstack(
                            rx.icon("download", size=14),
                            rx.text("Exportar PDF"),
                            gap="4px",
                        ),
                        variant="solid",
                        color_scheme="green",
                        size="3",
                        on_click=MedeXState.export_research_pdf,
                    ),
                    rx.fragment(),
                ),
                gap=Space.S2,
            ),
            rx.fragment(),
        ),
        # Progress section
        rx.cond(
            MedeXState.research_loading,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            "Progreso:",
                            font_size=Font.SIZE_SM,
                            font_weight=Font.WEIGHT_MEDIUM,
                            color=THEME.TEXT_PRIMARY,
                        ),
                        rx.text(
                            f"{MedeXState.research_progress}%",
                            font_size=Font.SIZE_SM,
                            color=THEME.PRIMARY_600,
                        ),
                        gap=Space.S2,
                    ),
                    rx.progress(
                        value=MedeXState.research_progress, max=100, width="100%"
                    ),
                    rx.text(
                        MedeXState.research_status,
                        font_size=Font.SIZE_SM,
                        color=THEME.PRIMARY_600,
                    ),
                    rx.divider(margin=f"{Space.S2} 0"),
                    rx.text(
                        "Pasos de Investigación:",
                        font_size=Font.SIZE_XS,
                        font_weight=Font.WEIGHT_MEDIUM,
                        color=THEME.TEXT_MUTED,
                    ),
                    rx.foreach(
                        MedeXState.research_steps,
                        research_step_item,
                    ),
                    gap=Space.S2,
                    align="start",
                    width="100%",
                ),
                padding=Space.S4,
                background=THEME.PRIMARY_50,
                border_radius=Radius.MD,
                border=f"1px solid {THEME.PRIMARY_200}",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Error message
        rx.cond(
            MedeXState.research_error != "",
            rx.box(
                rx.text(
                    MedeXState.research_error,
                    color=THEME.CRITICAL_500,
                    font_size=Font.SIZE_SM,
                ),
                padding=Space.S3,
                background=THEME.CRITICAL_50,
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.fragment(),
        ),
        # Results
        rx.cond(
            MedeXState.research_result != "",
            rx.vstack(
                rx.hstack(
                    rx.text(
                        "Resultados de la Investigación",
                        font_size=Font.SIZE_BASE,
                        font_weight=Font.WEIGHT_SEMIBOLD,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.spacer(),
                    rx.badge(
                        f"{MedeXState.research_sources_count} fuentes consultadas",
                        color_scheme="blue",
                        size="1",
                    ),
                    width="100%",
                    align="center",
                ),
                rx.box(
                    rx.markdown(
                        MedeXState.research_result,
                        style={
                            "color": THEME.TEXT_PRIMARY,
                            "& p, & li, & td, & th": {"color": THEME.TEXT_PRIMARY},
                            "& h1, & h2, & h3, & h4": {"color": THEME.PRIMARY_700},
                        },
                    ),
                    padding=Space.S4,
                    background=THEME.BG_CARD,
                    border=f"1px solid {THEME.BORDER_DEFAULT}",
                    border_radius=Radius.MD,
                    width="100%",
                    max_height="500px",
                    overflow_y="auto",
                ),
                # Sources section - SCIENTIFIC ARTICLES WITH EVIDENCE LEVELS
                rx.cond(
                    MedeXState.has_research_sources,
                    rx.vstack(
                        rx.hstack(
                            rx.icon("book-open", size=16, color=THEME.PRIMARY_500),
                            rx.text(
                                "Literatura Científica",
                                font_size=Font.SIZE_SM,
                                font_weight=Font.WEIGHT_SEMIBOLD,
                                color=THEME.TEXT_PRIMARY,
                            ),
                            rx.spacer(),
                            rx.tooltip(
                                rx.badge(
                                    "Nivel de Evidencia",
                                    color_scheme="purple",
                                    size="1",
                                    variant="soft",
                                ),
                                content="Verde=Alta (1a-1b), Amarillo=Moderada (2a-2b), Naranja=Baja (3-4)",
                            ),
                            gap=Space.S2,
                            align="center",
                            width="100%",
                        ),
                        rx.foreach(
                            MedeXState.research_sources,
                            lambda source: rx.box(
                                rx.hstack(
                                    # Evidence level badge with dynamic color
                                    rx.tooltip(
                                        rx.box(
                                            rx.text(
                                                source["evidence_level"],
                                                font_size="10px",
                                                font_weight="bold",
                                                color="white",
                                            ),
                                            padding_x="6px",
                                            padding_y="2px",
                                            background=source["badge_color"],
                                            border_radius="4px",
                                            min_width="24px",
                                            text_align="center",
                                        ),
                                        content=source["evidence_description"],
                                    ),
                                    # Source API badge
                                    rx.badge(
                                        source["source_api"],
                                        color_scheme="gray",
                                        size="1",
                                        variant="outline",
                                    ),
                                    # Article info
                                    rx.vstack(
                                        rx.link(
                                            rx.text(
                                                source["title"],
                                                font_size=Font.SIZE_XS,
                                                font_weight="medium",
                                                color=THEME.PRIMARY_600,
                                            ),
                                            href=source["url"],
                                            is_external=True,
                                        ),
                                        rx.text(
                                            f"{source['authors']} - {source['journal']} ({source['year']})",
                                            font_size="10px",
                                            color=THEME.TEXT_MUTED,
                                        ),
                                        gap="1px",
                                        align="start",
                                    ),
                                    gap=Space.S2,
                                    align="center",
                                    width="100%",
                                ),
                                padding="8px",
                                background=THEME.BG_CARD,
                                border=f"1px solid {THEME.BORDER_DEFAULT}",
                                border_radius=Radius.SM,
                                _hover={"background": THEME.BG_SECONDARY},
                            ),
                        ),
                        gap=Space.S2,
                        padding=Space.S3,
                        background=THEME.BG_SECONDARY,
                        border_radius=Radius.MD,
                        width="100%",
                        max_height="300px",
                        overflow_y="auto",
                    ),
                    rx.fragment(),
                ),
                gap=Space.S3,
                width="100%",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("search", size=48, color=THEME.TEXT_MUTED),
                    rx.text(
                        "Ingrese un tema y presione 'Iniciar Investigación'",
                        font_size=Font.SIZE_SM,
                        color=THEME.TEXT_MUTED,
                    ),
                    rx.text(
                        "La investigación profunda analiza múltiples fuentes y sintetiza la información.",
                        font_size=Font.SIZE_XS,
                        color=THEME.TEXT_MUTED,
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                flex="1",
                padding=Space.S12,
            ),
        ),
        gap=Space.S4,
        padding=Space.S6,
        width="100%",
        height="100%",
        overflow_y="auto",
    )


# =============================================================================
# KNOWLEDGE BASE PANEL
# =============================================================================


def knowledge_panel() -> rx.Component:
    """Knowledge base search panel."""
    return rx.vstack(
        rx.text(
            "Base de Conocimiento Médico",
            font_size=Font.SIZE_LG,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.TEXT_PRIMARY,
        ),
        rx.text(
            "Busque en la base de conocimiento médico potenciada por RAG.",
            font_size=Font.SIZE_SM,
            color=THEME.TEXT_SECONDARY,
        ),
        rx.hstack(
            rx.input(
                placeholder="Buscar condiciones, medicamentos, procedimientos...",
                value=MedeXState.kb_search_query,
                on_change=MedeXState.set_kb_query,
                size="3",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            rx.button(
                rx.hstack(
                    rx.cond(
                        MedeXState.kb_loading,
                        rx.spinner(size="1"),
                        rx.icon("search", size=16),
                    ),
                    rx.text("Buscar"),
                    gap=Space.S2,
                ),
                on_click=MedeXState.search_knowledge_base,
                disabled=MedeXState.kb_loading,
                size="3",
                color_scheme="blue",
            ),
            gap=Space.S2,
            width="100%",
        ),
        rx.cond(
            MedeXState.kb_error != "",
            rx.box(
                rx.text(
                    MedeXState.kb_error,
                    color=THEME.CRITICAL_500,
                    font_size=Font.SIZE_SM,
                ),
                padding=Space.S3,
                background=THEME.CRITICAL_50,
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MedeXState.has_kb_results,
            rx.vstack(
                rx.text(
                    MedeXState.kb_results_count,
                    " resultados encontrados",
                    font_size=Font.SIZE_SM,
                    color=THEME.TEXT_MUTED,
                ),
                rx.foreach(
                    MedeXState.kb_results_as_dicts,
                    lambda doc: rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.badge(
                                    doc["category"], color_scheme="blue", size="1"
                                ),
                                rx.text(
                                    "Score: ",
                                    doc["score"],
                                    font_size=Font.SIZE_XS,
                                    color=THEME.TEXT_MUTED,
                                ),
                                gap=Space.S2,
                            ),
                            rx.text(
                                doc["title"],
                                font_weight=Font.WEIGHT_SEMIBOLD,
                                color=THEME.TEXT_PRIMARY,
                            ),
                            rx.text(
                                doc["content"],
                                font_size=Font.SIZE_SM,
                                color=THEME.TEXT_SECONDARY,
                                line_height=Font.LINE_RELAXED,
                            ),
                            rx.text(
                                "Source: ",
                                doc["source"],
                                font_size=Font.SIZE_XS,
                                color=THEME.TEXT_MUTED,
                            ),
                            gap=Space.S2,
                            align="start",
                        ),
                        padding=Space.S4,
                        background=THEME.BG_CARD,
                        border=f"1px solid {THEME.BORDER_DEFAULT}",
                        border_radius=Radius.MD,
                        width="100%",
                        _hover={"border_color": THEME.PRIMARY_300},
                    ),
                ),
                gap=Space.S3,
                width="100%",
            ),
            rx.center(
                rx.vstack(
                    rx.icon("database", size=48, color=THEME.TEXT_MUTED),
                    rx.text(
                        "Search the knowledge base",
                        font_size=Font.SIZE_SM,
                        color=THEME.TEXT_MUTED,
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                flex="1",
                padding=Space.S12,
            ),
        ),
        gap=Space.S4,
        padding=Space.S6,
        width="100%",
        height="100%",
        overflow_y="auto",
    )


# =============================================================================
# TRIAGE PANEL
# =============================================================================


def triage_panel() -> rx.Component:
    """Triage assessment panel."""
    return rx.vstack(
        rx.text(
            "Evaluación de Triage ESI",
            font_size=Font.SIZE_LG,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.TEXT_PRIMARY,
        ),
        rx.text(
            "Ingrese la información del paciente para evaluación del nivel de triage.",
            font_size=Font.SIZE_SM,
            color=THEME.TEXT_SECONDARY,
        ),
        rx.box(
            rx.vstack(
                rx.text(
                    "Queja Principal *",
                    font_size=Font.SIZE_SM,
                    font_weight=Font.WEIGHT_MEDIUM,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.text_area(
                    placeholder="Describa el motivo de consulta principal...",
                    value=MedeXState.triage_chief_complaint,
                    on_change=MedeXState.set_triage_complaint,
                    size="3",
                    width="100%",
                    min_height="80px",
                    color=THEME.TEXT_PRIMARY,
                    _placeholder={"color": THEME.INPUT_PLACEHOLDER},
                ),
                gap=Space.S1,
                width="100%",
            ),
            width="100%",
        ),
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Duración",
                    font_size=Font.SIZE_SM,
                    font_weight=Font.WEIGHT_MEDIUM,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.input(
                    placeholder="ej: 2 horas",
                    value=MedeXState.triage_duration,
                    on_change=MedeXState.set_triage_duration,
                    size="3",
                    width="100%",
                    color=THEME.TEXT_PRIMARY,
                    _placeholder={"color": THEME.INPUT_PLACEHOLDER},
                ),
                gap=Space.S1,
                width="100%",
            ),
            rx.vstack(
                rx.text(
                    "Nivel de Dolor (0-10)",
                    font_size=Font.SIZE_SM,
                    font_weight=Font.WEIGHT_MEDIUM,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.hstack(
                    rx.text(
                        MedeXState.triage_pain_level,
                        font_size=Font.SIZE_SM,
                        color=THEME.TEXT_SECONDARY,
                        min_width="30px",
                    ),
                    rx.slider(
                        default_value=[0],
                        min=0,
                        max=10,
                        on_value_commit=MedeXState.set_triage_pain,
                        width="100%",
                    ),
                    gap=Space.S2,
                    align="center",
                    width="100%",
                ),
                gap=Space.S1,
                width="100%",
            ),
            gap=Space.S4,
            width="100%",
        ),
        rx.text(
            "Signos Vitales (Opcional)",
            font_size=Font.SIZE_SM,
            font_weight=Font.WEIGHT_SEMIBOLD,
            color=THEME.TEXT_PRIMARY,
            margin_top=Space.S2,
        ),
        rx.hstack(
            rx.input(
                placeholder="FC (lpm)",
                value=MedeXState.triage_vital_hr,
                on_change=MedeXState.set_vital_hr,
                size="2",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            rx.input(
                placeholder="PA Sis",
                value=MedeXState.triage_vital_bp_sys,
                on_change=MedeXState.set_vital_bp_sys,
                size="2",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            rx.input(
                placeholder="PA Dia",
                value=MedeXState.triage_vital_bp_dia,
                on_change=MedeXState.set_vital_bp_dia,
                size="2",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            gap=Space.S2,
            width="100%",
        ),
        rx.hstack(
            rx.input(
                placeholder="FR (/min)",
                value=MedeXState.triage_vital_rr,
                on_change=MedeXState.set_vital_rr,
                size="2",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            rx.input(
                placeholder="Temp (°C)",
                value=MedeXState.triage_vital_temp,
                on_change=MedeXState.set_vital_temp,
                size="2",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            rx.input(
                placeholder="SpO2 (%)",
                value=MedeXState.triage_vital_spo2,
                on_change=MedeXState.set_vital_spo2,
                size="2",
                width="100%",
                color=THEME.TEXT_PRIMARY,
                _placeholder={"color": THEME.INPUT_PLACEHOLDER},
            ),
            gap=Space.S2,
            width="100%",
        ),
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.cond(
                        MedeXState.triage_loading,
                        rx.spinner(size="1"),
                        rx.icon("activity", size=16),
                    ),
                    rx.text("Evaluar Triage"),
                    gap=Space.S2,
                ),
                on_click=MedeXState.assess_triage,
                disabled=MedeXState.triage_loading,
                size="3",
                color_scheme="blue",
            ),
            rx.button(
                "Clear",
                variant="outline",
                color_scheme="gray",
                size="3",
                on_click=MedeXState.clear_triage,
            ),
            gap=Space.S2,
        ),
        rx.cond(
            MedeXState.triage_error != "",
            rx.box(
                rx.text(
                    MedeXState.triage_error,
                    color=THEME.CRITICAL_500,
                    font_size=Font.SIZE_SM,
                ),
                padding=Space.S3,
                background=THEME.CRITICAL_50,
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            MedeXState.has_triage_result,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.text(
                                MedeXState.triage_esi_level,
                                font_size=Font.SIZE_3XL,
                                font_weight=Font.WEIGHT_BOLD,
                                color=THEME.TEXT_INVERSE,
                            ),
                            padding=Space.S4,
                            background=rx.match(
                                MedeXState.triage_esi_level,
                                (1, THEME.CRITICAL_500),
                                (2, THEME.EMERGENT_500),
                                (3, THEME.URGENT_500),
                                (4, THEME.STABLE_500),
                                THEME.ROUTINE_500,
                            ),
                            border_radius=Radius.MD,
                            min_width="80px",
                            text_align="center",
                        ),
                        rx.vstack(
                            rx.text(
                                "ESI Level ",
                                MedeXState.triage_esi_level,
                                font_size=Font.SIZE_LG,
                                font_weight=Font.WEIGHT_BOLD,
                                color=THEME.TEXT_PRIMARY,
                            ),
                            rx.text(
                                MedeXState.triage_esi_name,
                                font_size=Font.SIZE_BASE,
                                color=THEME.TEXT_SECONDARY,
                            ),
                            gap=Space.S1,
                            align="start",
                        ),
                        gap=Space.S4,
                        align="center",
                    ),
                    rx.cond(
                        MedeXState.has_red_flags,
                        rx.box(
                            rx.vstack(
                                rx.text(
                                    "🚨 Red Flags Detected",
                                    font_weight=Font.WEIGHT_SEMIBOLD,
                                    color=THEME.CRITICAL_700,
                                ),
                                rx.foreach(
                                    MedeXState.triage_red_flags,
                                    lambda flag: rx.text(
                                        "• ",
                                        flag,
                                        font_size=Font.SIZE_SM,
                                        color=THEME.CRITICAL_700,
                                    ),
                                ),
                                gap=Space.S1,
                                align="start",
                            ),
                            padding=Space.S3,
                            background=THEME.CRITICAL_50,
                            border_radius=Radius.MD,
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.text(
                        MedeXState.triage_recommendation,
                        font_size=Font.SIZE_SM,
                        color=THEME.TEXT_SECONDARY,
                    ),
                    gap=Space.S4,
                    align="start",
                    width="100%",
                ),
                padding=Space.S4,
                background=THEME.BG_CARD,
                border=f"1px solid {THEME.BORDER_DEFAULT}",
                border_radius=Radius.MD,
                width="100%",
            ),
            rx.fragment(),
        ),
        gap=Space.S4,
        padding=Space.S6,
        width="100%",
        height="100%",
        overflow_y="auto",
    )


# =============================================================================
# HISTORY PANEL
# =============================================================================


def history_artifact_card(artifact: dict) -> rx.Component:
    """Single artifact card in the history."""
    return rx.box(
        rx.hstack(
            rx.box(
                # Use rx.match for dynamic icons based on artifact type
                rx.match(
                    artifact["type"],
                    ("interactions", rx.icon("pill", size=18, color=THEME.PRIMARY_500)),
                    ("dosage", rx.icon("calculator", size=18, color=THEME.PRIMARY_500)),
                    ("lab", rx.icon("test-tube", size=18, color=THEME.PRIMARY_500)),
                    (
                        "research",
                        rx.icon("microscope", size=18, color=THEME.PRIMARY_500),
                    ),
                    rx.icon("file-text", size=18, color=THEME.PRIMARY_500),  # default
                ),
                padding=Space.S2,
                background=THEME.PRIMARY_50,
                border_radius=Radius.MD,
            ),
            rx.vstack(
                rx.text(
                    artifact["title"],
                    font_size=Font.SIZE_SM,
                    font_weight=Font.WEIGHT_MEDIUM,
                    color=THEME.TEXT_PRIMARY,
                    no_of_lines=1,
                ),
                rx.hstack(
                    rx.badge(
                        artifact["type"],
                        color_scheme=rx.match(
                            artifact["type"],
                            ("interactions", "orange"),
                            ("dosage", "blue"),
                            ("lab", "purple"),
                            ("research", "green"),
                            "gray",
                        ),
                        size="1",
                    ),
                    rx.text(
                        rx.cond(
                            artifact["timestamp"] != "",
                            artifact["timestamp"][:16].replace("T", " "),
                            "",
                        ),
                        font_size=Font.SIZE_2XS,
                        color=THEME.TEXT_MUTED,
                    ),
                    gap=Space.S2,
                    align="center",
                ),
                gap="2px",
                align="start",
                flex="1",
            ),
            rx.icon_button(
                rx.icon("external-link", size=14),
                variant="ghost",
                size="1",
                color_scheme="gray",
            ),
            gap=Space.S3,
            align="center",
            width="100%",
        ),
        padding=Space.S3,
        background=THEME.BG_CARD,
        border=f"1px solid {THEME.BORDER_DEFAULT}",
        border_radius=Radius.DEFAULT,
        _hover={"border_color": THEME.PRIMARY_300, "box_shadow": Shadow.SM},
        transition=f"all {Transition.FAST}",
        cursor="pointer",
        width="100%",
    )


def history_panel() -> rx.Component:
    """Session history panel with artifacts catalog."""
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Historial de Sesión",
                    font_size=Font.SIZE_LG,
                    font_weight=Font.WEIGHT_SEMIBOLD,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.text(
                    "Resultados guardados y estadísticas de uso.",
                    font_size=Font.SIZE_SM,
                    color=THEME.TEXT_SECONDARY,
                ),
                gap="2px",
                align="start",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon("download", size=14), rx.text("Exportar"), gap=Space.S2
                ),
                on_click=MedeXState.export_session,
                variant="outline",
                color_scheme="blue",
                size="2",
            ),
            width="100%",
            align="center",
        ),
        # Stats cards
        rx.hstack(
            rx.box(
                rx.vstack(
                    rx.icon("message-circle", size=20, color=THEME.PRIMARY_500),
                    rx.text(
                        MedeXState.total_queries,
                        font_size=Font.SIZE_2XL,
                        font_weight=Font.WEIGHT_BOLD,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Consultas", font_size=Font.SIZE_XS, color=THEME.TEXT_MUTED
                    ),
                    gap=Space.S1,
                    align="center",
                ),
                padding=Space.S4,
                background=THEME.BG_CARD,
                border=f"1px solid {THEME.BORDER_DEFAULT}",
                border_radius=Radius.MD,
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("clock", size=20, color=THEME.URGENT_500),
                    rx.text(
                        f"{MedeXState.session_duration_minutes} min",
                        font_size=Font.SIZE_2XL,
                        font_weight=Font.WEIGHT_BOLD,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.text("Duración", font_size=Font.SIZE_XS, color=THEME.TEXT_MUTED),
                    gap=Space.S1,
                    align="center",
                ),
                padding=Space.S4,
                background=THEME.BG_CARD,
                border=f"1px solid {THEME.BORDER_DEFAULT}",
                border_radius=Radius.MD,
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("package", size=20, color=THEME.EMERGENT_500),
                    rx.text(
                        MedeXState.total_artifacts,
                        font_size=Font.SIZE_2XL,
                        font_weight=Font.WEIGHT_BOLD,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Artefactos", font_size=Font.SIZE_XS, color=THEME.TEXT_MUTED
                    ),
                    gap=Space.S1,
                    align="center",
                ),
                padding=Space.S4,
                background=THEME.BG_CARD,
                border=f"1px solid {THEME.BORDER_DEFAULT}",
                border_radius=Radius.MD,
                flex="1",
            ),
            rx.box(
                rx.vstack(
                    rx.icon("messages-square", size=20, color=THEME.STABLE_500),
                    rx.text(
                        MedeXState.message_count,
                        font_size=Font.SIZE_2XL,
                        font_weight=Font.WEIGHT_BOLD,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.text("Mensajes", font_size=Font.SIZE_XS, color=THEME.TEXT_MUTED),
                    gap=Space.S1,
                    align="center",
                ),
                padding=Space.S4,
                background=THEME.BG_CARD,
                border=f"1px solid {THEME.BORDER_DEFAULT}",
                border_radius=Radius.MD,
                flex="1",
            ),
            gap=Space.S4,
            width="100%",
        ),
        rx.divider(margin=f"{Space.S4} 0"),
        # Artifacts section
        rx.vstack(
            rx.hstack(
                rx.text(
                    "📦 Catálogo de Artefactos",
                    font_size=Font.SIZE_MD,
                    font_weight=Font.WEIGHT_SEMIBOLD,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.spacer(),
                rx.badge(
                    f"{MedeXState.total_artifacts} guardados",
                    color_scheme="blue",
                    size="1",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                MedeXState.has_artifacts,
                rx.vstack(
                    rx.text(
                        f"Tienes {MedeXState.total_artifacts} artefactos guardados.",
                        font_size=Font.SIZE_SM,
                        color=THEME.TEXT_PRIMARY,
                    ),
                    rx.text(
                        "Los artefactos incluyen resultados de herramientas, investigaciones y consultas.",
                        font_size=Font.SIZE_XS,
                        color=THEME.TEXT_MUTED,
                    ),
                    gap=Space.S2,
                    width="100%",
                    padding=Space.S4,
                    background=THEME.BG_CARD,
                    border=f"1px solid {THEME.BORDER_DEFAULT}",
                    border_radius=Radius.MD,
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("package-open", size=40, color=THEME.TEXT_MUTED),
                        rx.text(
                            "No hay artefactos guardados",
                            font_size=Font.SIZE_SM,
                            color=THEME.TEXT_MUTED,
                        ),
                        rx.text(
                            "Los resultados de herramientas se guardarán aquí",
                            font_size=Font.SIZE_XS,
                            color=THEME.TEXT_MUTED,
                        ),
                        gap=Space.S2,
                        align="center",
                    ),
                    padding=Space.S8,
                    width="100%",
                ),
            ),
            gap=Space.S3,
            width="100%",
        ),
        rx.divider(margin=f"{Space.S4} 0"),
        # Recent messages section
        rx.cond(
            MedeXState.has_messages,
            rx.vstack(
                rx.text(
                    "💬 Mensajes Recientes",
                    font_size=Font.SIZE_MD,
                    font_weight=Font.WEIGHT_SEMIBOLD,
                    color=THEME.TEXT_PRIMARY,
                ),
                rx.foreach(
                    MedeXState.messages_as_dicts,
                    lambda msg: rx.box(
                        rx.hstack(
                            rx.badge(
                                msg["role"],
                                color_scheme=rx.cond(
                                    msg["role"] == "user", "blue", "gray"
                                ),
                                size="1",
                            ),
                            rx.text(
                                msg["content"],
                                font_size=Font.SIZE_SM,
                                color=THEME.TEXT_SECONDARY,
                                no_of_lines=2,
                            ),
                            gap=Space.S2,
                            align="start",
                            width="100%",
                        ),
                        padding=Space.S3,
                        background=THEME.BG_SECONDARY,
                        border_radius=Radius.DEFAULT,
                        width="100%",
                    ),
                ),
                gap=Space.S2,
                width="100%",
            ),
            rx.fragment(),
        ),
        gap=Space.S4,
        padding=Space.S6,
        width="100%",
        height="100%",
        overflow_y="auto",
    )


# =============================================================================
# MAIN CONTENT
# =============================================================================


def main_content() -> rx.Component:
    """Main content area with section switching."""
    return rx.box(
        rx.match(
            MedeXState.active_section,
            ("chat", chat_panel()),
            ("tools", tools_panel()),
            ("knowledge", knowledge_panel()),
            ("triage", triage_panel()),
            ("history", history_panel()),
            ("research", research_panel()),
            chat_panel(),
        ),
        flex="1",
        height="100%",
        overflow="hidden",
    )


# =============================================================================
# MAIN APPLICATION
# =============================================================================


def index() -> rx.Component:
    """Main application page."""
    return rx.el.div(
        sidebar(),
        rx.el.main(
            header(),
            main_content(),
            style={
                "display": "flex",
                "flex-direction": "column",
                "flex": "1",
                "height": "100vh",
                "overflow": "hidden",
                "background": THEME.BG_PRIMARY,
            },
        ),
        # Artifact modal overlay
        artifact_modal(),
        style={
            "display": "flex",
            "width": "100vw",
            "height": "100vh",
            "overflow": "hidden",
            "font-family": Font.FAMILY_PRIMARY,
        },
    )


# Create app
app = rx.App(
    theme=rx.theme(
        accent_color="blue",
        radius="medium",
    ),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ],
)

app.add_page(index, on_load=MedeXState.on_load)
