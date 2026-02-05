class AuraTheme:
    # Derived from provided design tokens
    DARK = {
        "font_sans": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji'",
        "bg_base": "#0b1020",
        "surface": "#101426",
        "sidebar_bg": "#101426",
        "card_bg": "#101426",
        "text_primary": "#e5e7eb",
        "text_secondary": "#cbd5e1",
        "border": "#1f2937",
        "color_primary": "#3b82f6",
        "color_secondary": "#8b5cf6",
        "color_accent": "#fbbf24",
        "color_success": "#22c55e",
        "color_warning": "#f59e0b",
        "color_error": "#ef4444",
        "mesh_opacity": 60,
    }

    LIGHT = {
        "font_sans": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, 'Apple Color Emoji', 'Segoe UI Emoji'",
        "bg_base": "#f8fafc",
        "surface": "#ffffff",
        "sidebar_bg": "#ffffff",
        "card_bg": "#ffffff",
        "text_primary": "#0f172a",
        "text_secondary": "#334155",
        "border": "#e2e8f0",
        "color_primary": "#2563eb",
        "color_secondary": "#7c3aed",
        "color_accent": "#f59e0b",
        "color_success": "#22c55e",
        "color_warning": "#f59e0b",
        "color_error": "#ef4444",
        "mesh_opacity": 30,
    }


def get_qss(theme):
    """
    Generate QSS from the design tokens to keep PySide6 widgets consistent
    with the provided light/dark web theme.
    """

    border_rgba = f"rgba(31, 41, 55, 0.6)" if theme == AuraTheme.DARK else f"rgba(226, 232, 240, 0.9)"
    hover_overlay = "rgba(255, 255, 255, 0.06)" if theme == AuraTheme.DARK else "rgba(15, 23, 42, 0.05)"
    pressed_overlay = "rgba(0, 0, 0, 0.08)" if theme == AuraTheme.DARK else "rgba(0, 0, 0, 0.06)"

    return f"""
    * {{
        font-family: {theme['font_sans']};
        color: {theme['text_primary']};
    }}

    QWidget#CentralWidget {{
        background-color: transparent;
        border-radius: 30px;
    }}

    QWidget#Sidebar {{
        background-color: {theme['sidebar_bg']};
        border-top-left-radius: 30px;
        border-bottom-left-radius: 30px;
        border-right: 1px solid {theme['border']};
    }}

    QLabel#Logo {{
        color: {theme['text_primary']};
        font-size: 22px;
        font-weight: 800;
        letter-spacing: 1px;
    }}

    QPushButton#SidebarButton {{
        text-align: left;
        padding: 12px 18px;
        border: 1px solid transparent;
        border-radius: 12px;
        color: {theme['text_secondary']};
        font-size: 14px;
        font-weight: 700;
        background-color: transparent;
        margin: 4px 12px;
    }}

    QPushButton#SidebarButton:hover {{
        background-color: {hover_overlay};
        color: {theme['text_primary']};
    }}

    QPushButton#SidebarButton:checked {{
        background-color: {theme['color_primary']};
        border-color: {theme['color_primary']};
        color: #ffffff;
    }}

    QFrame#MetricCard, QFrame#ContentCard, QFrame#RuleCard {{
        background-color: {theme['card_bg']};
        border-radius: 16px;
        border: 1px solid {theme['border']};
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }}

    QLabel#PageTitle {{
        color: {theme['text_primary']};
        font-size: 30px;
        font-weight: 800;
    }}

    QLabel#SectionTitle {{
        color: {theme['text_primary']};
        font-size: 18px;
        font-weight: 700;
    }}

    QLabel#BodySecondary {{
        color: {theme['text_secondary']};
        font-size: 15px;
        font-weight: 500;
    }}

    QLabel#StatusLabel[status="Active"] {{
        color: {theme['color_success']};
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}

    QLabel#StatusLabel[status="Inactive"] {{
        color: {theme['text_secondary']};
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}

    QLabel#MetricValue {{
        color: {theme['text_primary']};
        font-size: 26px;
        font-weight: 800;
    }}

    QLabel#MetricLabel {{
        color: {theme['text_secondary']};
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    /* Base button styling similar to web .btn */
    QPushButton {{
        background-color: {theme['surface']};
        color: {theme['text_primary']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 600;
        transition: all 120ms ease-out;
    }}

    QPushButton:hover {{
        background-color: {hover_overlay};
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }}

    QPushButton:pressed {{
        background-color: {pressed_overlay};
    }}

    QPushButton:disabled {{
        opacity: 0.6;
        box-shadow: none;
    }}

    /* Primary action */
    QPushButton#GlowBtn {{
        background-color: {theme['color_primary']};
        color: #ffffff;
        border: 1px solid {theme['color_primary']};
        border-radius: 12px;
        padding: 12px 22px;
        font-weight: 700;
    }}

    QPushButton#GlowBtn:hover {{
        filter: brightness(0.97);
        box-shadow: 0 4px 12px rgba(0,0,0,0.18);
    }}

    QPushButton#GlowBtn:pressed {{
        transform: translateY(1px);
    }}

    /* Table/secondary action */
    QPushButton#TableActionBtn {{
        background-color: transparent;
        color: {theme['color_primary']};
        border: 1px solid {theme['border']};
        border-radius: 8px;
        padding: 6px 12px;
        font-weight: 700;
    }}

    QPushButton#TableActionBtn:hover {{
        background-color: {hover_overlay};
    }}

    QTableWidget {{
        background-color: transparent;
        border: none;
        color: {theme['text_primary']};
        gridline-color: {theme['border']};
        alternate-background-color: {hover_overlay};
    }}

    QHeaderView::section {{
        background-color: {theme['surface']};
        color: {theme['text_primary']};
        font-size: 11px;
        font-weight: 800;
        border: none;
        border-bottom: 1px solid {theme['border']};
        padding: 10px 8px;
    }}

    QLineEdit, QComboBox {{
        background-color: {theme['surface']};
        border: 1px solid {theme['border']};
        border-radius: 10px;
        padding: 9px 10px;
        color: {theme['text_primary']};
    }}

    QComboBox::drop-down {{
        border: none;
    }}
    """
