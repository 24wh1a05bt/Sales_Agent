"""
theme.py
Shared design system for the app: one CSS injection function plus small
HTML component helpers, so every page shares the same look instead of
falling back to default Streamlit chrome.

Design language ("Beacon"): a sales-ops control tower. Indigo is the
working brand color, amber is reserved for the beacon mark and urgent
attention states, and everything else is quiet ink/cloud/paper neutrals
so the semantic Hot/Nurture/Disqualified colors keep their meaning.
"""

import html as _html

import streamlit as st

COLORS = {
    "ink": "#1E2233",
    "ink_muted": "#6B7280",
    "cloud": "#F5F5FB",
    "paper": "#FFFFFF",
    "border": "#E4E4F0",
    "primary": "#4F46E5",
    "primary_dark": "#3730A3",
    "primary_soft": "#EEF0FE",
    "beacon": "#F59E0B",
    "beacon_soft": "#FEF3E2",
    "hot": "#DC2626",
    "hot_soft": "#FDECEC",
    "nurture": "#D97706",
    "nurture_soft": "#FEF3E2",
    "disqualified": "#6B7280",
    "disqualified_soft": "#F1F1F5",
    "unscored": "#2563EB",
    "unscored_soft": "#EBF1FE",
    "success": "#059669",
    "success_soft": "#E7F6EF",
}

CLASS_STYLE = {
    "Hot": ("hot", "🔴"),
    "Nurture": ("nurture", "🟡"),
    "Disqualified": ("disqualified", "⚪"),
    "Unscored": ("unscored", "🔵"),
}

STATUS_STYLE = {
    "Pending Review": ("nurture", "⏳"),
    "Approved": ("success", "✅"),
    "Rejected": ("hot", "✕"),
    "Sent": ("unscored", "📤"),
    "Archived": ("disqualified", "🗄"),
    "New": ("unscored", "🆕"),
    "Scored": ("success", "✓"),
    "Enriched": ("primary", "🧬"),
}


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, sans-serif;
        }}

        #MainMenu, footer, header[data-testid="stHeader"] {{ background: transparent; }}
        .stApp {{ background: {COLORS['cloud']}; }}

        h1, h2, h3 {{
            font-family: 'Space Grotesk', 'Inter', sans-serif !important;
            color: {COLORS['ink']} !important;
            letter-spacing: -0.01em;
        }}

        div[data-testid="stMetric"] {{
            background: {COLORS['paper']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 14px 18px;
            box-shadow: 0 1px 2px rgba(30,34,51,0.04);
        }}
        div[data-testid="stMetricValue"] {{
            font-family: 'JetBrains Mono', monospace;
            color: {COLORS['ink']};
        }}

        section[data-testid="stSidebar"] {{
            background: {COLORS['ink']};
            border-right: 1px solid {COLORS['border']};
        }}
        section[data-testid="stSidebar"] * {{ color: #E7E8F5 !important; }}
        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {{
            border-radius: 8px;
            margin-bottom: 2px;
        }}
        section[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {{
            background: rgba(255,255,255,0.08);
        }}

        .stButton > button, .stFormSubmitButton > button {{
            border-radius: 8px;
            font-weight: 600;
            border: 1px solid {COLORS['border']};
        }}
        .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
            background: {COLORS['primary']};
            border-color: {COLORS['primary']};
        }}
        .stButton > button[kind="primary"]:hover {{
            background: {COLORS['primary_dark']};
            border-color: {COLORS['primary_dark']};
        }}

        div[data-testid="stTabs"] button[role="tab"] {{
            font-weight: 600;
            font-family: 'Inter', sans-serif;
        }}

        div[data-testid="stExpander"] {{
            background: {COLORS['paper']};
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
        }}

        div[data-testid="stDataFrame"] {{
            border: 1px solid {COLORS['border']};
            border-radius: 10px;
            overflow: hidden;
        }}

        .beacon-header {{
            display: flex; align-items: center; gap: 12px;
            padding: 4px 0 18px 0;
        }}
        .beacon-mark {{
            position: relative; width: 34px; height: 34px; flex-shrink: 0;
        }}
        .beacon-mark .ring {{
            position: absolute; inset: 0; border-radius: 50%;
            border: 2px solid {COLORS['beacon']}; opacity: 0;
            animation: beacon-pulse 2.4s ease-out infinite;
        }}
        .beacon-mark .dot {{
            position: absolute; top: 11px; left: 11px; width: 12px; height: 12px;
            border-radius: 50%; background: {COLORS['beacon']};
        }}
        @keyframes beacon-pulse {{
            0% {{ transform: scale(0.4); opacity: 0.9; }}
            100% {{ transform: scale(1.6); opacity: 0; }}
        }}
        .beacon-wordmark {{
            font-family: 'Space Grotesk', sans-serif; font-weight: 700;
            font-size: 22px; color: {COLORS['ink']}; line-height: 1;
        }}
        .beacon-tagline {{
            font-size: 12px; color: {COLORS['ink_muted']}; margin-top: 2px;
        }}

        .card {{
            background: {COLORS['paper']};
            border: 1px solid {COLORS['border']};
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 1px 2px rgba(30,34,51,0.04);
            margin-bottom: 14px;
        }}
        .kpi-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 6px; }}
        .kpi-card {{
            background: {COLORS['paper']}; border: 1px solid {COLORS['border']};
            border-radius: 12px; padding: 16px 18px;
            box-shadow: 0 1px 2px rgba(30,34,51,0.04);
        }}
        .kpi-label {{ font-size: 12px; color: {COLORS['ink_muted']}; font-weight: 600;
                       text-transform: uppercase; letter-spacing: 0.04em; }}
        .kpi-value {{ font-family: 'JetBrains Mono', monospace; font-size: 26px;
                       font-weight: 600; color: {COLORS['ink']}; margin-top: 4px; }}
        .kpi-sub {{ font-size: 12px; color: {COLORS['ink_muted']}; margin-top: 2px; }}

        .badge {{
            display: inline-flex; align-items: center; gap: 5px;
            padding: 3px 10px; border-radius: 999px;
            font-size: 12px; font-weight: 600; white-space: nowrap;
        }}

        .chip {{
            display: inline-flex; padding: 3px 10px; margin: 2px 4px 2px 0;
            border-radius: 6px; background: {COLORS['primary_soft']};
            color: {COLORS['primary_dark']}; font-size: 12px; font-weight: 500;
        }}

        .avatar {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 36px; height: 36px; border-radius: 50%;
            background: {COLORS['primary']}; color: white; font-weight: 700;
            font-family: 'Space Grotesk', sans-serif; font-size: 14px; flex-shrink: 0;
        }}

        .timeline-item {{ border-left: 2px solid {COLORS['border']}; padding: 0 0 14px 16px; margin-left: 6px; position: relative; }}
        .timeline-item::before {{
            content: ""; position: absolute; left: -7px; top: 2px;
            width: 12px; height: 12px; border-radius: 50%;
            background: {COLORS['primary']}; border: 2px solid {COLORS['paper']};
        }}
        .timeline-time {{ font-family: 'JetBrains Mono', monospace; font-size: 11px; color: {COLORS['ink_muted']}; }}
        .timeline-action {{ font-weight: 600; color: {COLORS['ink']}; }}

        .empty-state {{
            text-align: center; padding: 48px 20px; color: {COLORS['ink_muted']};
            background: {COLORS['paper']}; border: 1px dashed {COLORS['border']}; border-radius: 12px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand_header(tagline: str = "AI Lead Qualification & Outreach"):
    st.markdown(
        f"""
        <div class="beacon-header">
            <div class="beacon-mark">
                <div class="ring"></div>
                <div class="dot"></div>
            </div>
            <div>
                <div class="beacon-wordmark">Beacon</div>
                <div class="beacon-tagline">{_html.escape(tagline)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def badge(text: str, kind: str) -> str:
    color = COLORS.get(kind, COLORS["primary"])
    soft = COLORS.get(f"{kind}_soft", COLORS["primary_soft"])
    return f'<span class="badge" style="color:{color};background:{soft};">{_html.escape(text)}</span>'


def classification_badge(classification: str) -> str:
    kind, icon = CLASS_STYLE.get(classification, ("primary", "•"))
    return badge(f"{icon} {classification}", kind)


def status_badge(status: str) -> str:
    kind, icon = STATUS_STYLE.get(status, ("primary", "•"))
    return badge(f"{icon} {status}", kind)


def avatar_initials(name: str, size: int = 36) -> str:
    parts = [p for p in (name or "?").split(" ") if p]
    initials = "".join(p[0].upper() for p in parts[:2]) or "?"
    font_size = max(12, int(size * 0.4))
    return (f'<div class="avatar" style="width:{size}px;height:{size}px;'
            f'font-size:{font_size}px;">{initials}</div>')


def kpi_card(label: str, value, sub: str = "") -> str:
    return f"""
    <div class="kpi-card">
        <div class="kpi-label">{_html.escape(label)}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{_html.escape(sub)}</div>
    </div>
    """


def kpi_row(items: list):
    """items: list of (label, value, sub) tuples, rendered as a responsive grid."""
    cards = "".join(kpi_card(l, v, s) for l, v, s in items)
    st.markdown(f'<div class="kpi-grid">{cards}</div>', unsafe_allow_html=True)


def chip(text: str) -> str:
    return f'<span class="chip">{_html.escape(str(text))}</span>'


def page_sidebar(user, logout_fn=None):
    """Renders the shared branded sidebar nav. Pass logout_fn to show a
    log-out button (app.py does; sub-pages just link back to Home)."""
    with st.sidebar:
        brand_header("Control Tower")
        if user:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:14px;">'
                f'{avatar_initials(user["name"])}'
                f'<div><div style="font-weight:600;">{_html.escape(user["name"])}</div>'
                f'<div style="font-size:12px;opacity:0.7;">{_html.escape(user["role"])}</div></div></div>',
                unsafe_allow_html=True,
            )
            if logout_fn and st.button("↩ Log out", use_container_width=True):
                logout_fn()
                st.rerun()
            st.divider()
        st.page_link("app.py", label="🏠 Home")
        st.page_link("pages/1_Lead_Intake.py", label="📥 Lead Intake")
        st.page_link("pages/2_Lead_List.py", label="📋 Lead List")
        st.page_link("pages/3_Lead_Details.py", label="🔍 Lead Details")
        st.page_link("pages/4_Email_Approval.py", label="✉️ Email Approval")
        st.page_link("pages/5_Analytics.py", label="📊 Analytics")
        st.page_link("pages/6_Audit_Logs.py", label="📜 Audit Logs")
        st.page_link("pages/7_Settings.py", label="⚙️ Settings")
        st.divider()
        st.caption("Beacon v1.0 · SOC2-style audit trail\nNo email ever sends without approval.")


def empty_state(message: str, icon: str = "🔍"):
    st.markdown(
        f'<div class="empty-state"><div style="font-size:28px;">{icon}</div>'
        f'<div style="margin-top:8px;">{_html.escape(message)}</div></div>',
        unsafe_allow_html=True,
    )