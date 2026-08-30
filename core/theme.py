"""
theme.py
========
Poori app ki THEME (colors, spacing, components) sirf isi file mein hai.
Baaki koi bhi file inline CSS/HTML NAHI likhegi -- sirf yahan ke reusable
functions call karegi. Naya feature banate waqt bhi pehle yahan check
karo ke koi helper already exist to nahi karta.

Naya color/spacing change karna ho -> sirf TOKENS dict edit karo,
poori app automatically update ho jayegi.
"""

import streamlit as st


TOKENS = {
    "bg":            "#F5F6FA",
    "surface":       "#FFFFFF",
    "surface_alt":   "#FAFBFD",
    "border":        "#E3E6ED",

    "text":          "#181B24",
    "text_muted":    "#6B7280",
    "text_faint":    "#9AA1AE",

    "brand_start":   "#FF4D5E",
    "brand_end":     "#7C3AED",

    "accent_blue":   "#2563EB",
    "accent_teal":   "#0D9488",
    "accent_amber":  "#F59E0B",
    "accent_purple": "#7C3AED",
    "accent_red":    "#EF4444",

    "heat_0":  "#EEF2FA",
    "heat_1":  "#C9DBF7",
    "heat_2":  "#93B9EF",
    "heat_3":  "#5A8FE0",
    "heat_4":  "#2E63C7",
    "heat_5":  "#173C8A",

    "gain":    "#16A34A",
    "gain_bg": "#E7F7ED",
    "loss":    "#DC2626",
    "loss_bg": "#FCEAEA",
    "flat_bg": "#EEF0F4",

    "success": "#16A34A",
    "warning": "#D97706",
    "danger":  "#DC2626",

    "radius":       "14px",
    "radius_sm":    "9px",
    "shadow":       "0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.06)",
    "shadow_hover": "0 4px 12px rgba(16,24,40,0.10)",

    # -- Sidebar (dark, professional) --
    "sidebar_bg":     "#14161F",
    "sidebar_bg_alt": "#1B1E2A",
    "sidebar_border": "#272B3A",
    "sidebar_text":   "#E5E7EF",
    "sidebar_muted":  "#8A8FA3",
}

T = TOKENS


def inject():
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {T['bg']}; }}
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                         Roboto, Helvetica, Arial, sans-serif;
            color: {T['text']};
        }}

        #MainMenu, footer {{visibility: hidden;}}

        header[data-testid="stHeader"] {{
            visibility: hidden;
            height: 0;
        }}
        div[data-testid="stToolbar"] {{ visibility: hidden; }}
        div[data-testid="stDecoration"] {{ visibility: hidden; }}

        /* ============================================================
           SIDEBAR -- dark, professional look, distinct from main area
           ============================================================ */
        section[data-testid="stSidebar"] {{
            min-width: 260px !important;
            max-width: 260px !important;
            background: {T['sidebar_bg']} !important;
            border-right: 1px solid {T['sidebar_border']};
        }}
        section[data-testid="stSidebar"] > div {{
            padding-top: 1.4rem;
        }}
        /* Sidebar text (markdown titles/captions) */
        section[data-testid="stSidebar"] h3 {{
            color: {T['sidebar_text']} !important;
            font-size: 1.02rem;
            margin-bottom: 2px;
        }}
        section[data-testid="stSidebar"] p, 
        section[data-testid="stSidebar"] .stCaption,
        section[data-testid="stSidebar"] small {{
            color: {T['sidebar_muted']} !important;
        }}
        section[data-testid="stSidebar"] hr {{
            border-color: {T['sidebar_border']} !important;
            margin: 14px 0;
        }}

        /* Sidebar nav buttons -- inactive: flat/ghost, active: gradient */
        section[data-testid="stSidebar"] .stButton > button {{
            background: transparent;
            color: {T['sidebar_muted']};
            border: 1px solid transparent;
            box-shadow: none;
            font-weight: 600;
            font-size: 0.88rem;
            text-align: left;
            justify-content: flex-start;
            padding: 0.55rem 0.85rem;
            border-radius: {T['radius_sm']};
            transition: background 0.12s ease, color 0.12s ease;
        }}
        section[data-testid="stSidebar"] .stButton > button:hover {{
            background: {T['sidebar_bg_alt']};
            color: {T['sidebar_text']};
            transform: none;
            box-shadow: none;
        }}
        section[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: linear-gradient(90deg, {T['brand_start']}, {T['brand_end']});
            color: #FFFFFF;
            box-shadow: {T['shadow']};
        }}
        section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(90deg, {T['brand_start']}, {T['brand_end']});
            color: #FFFFFF;
            box-shadow: {T['shadow_hover']};
        }}
        /* "+ Add Channel" ko thoda outlined/dashed rakho taake nav list se
           visually alag rahe (action vs navigation) */
        section[data-testid="stSidebar"] .stButton:last-of-type > button {{
            border: 1px dashed {T['sidebar_border']};
            background: transparent;
            color: {T['sidebar_text']};
        }}
        section[data-testid="stSidebar"] .stButton:last-of-type > button:hover {{
            border-color: {T['brand_end']};
            color: #FFFFFF;
            background: {T['sidebar_bg_alt']};
        }}

        .block-container {{
            padding-top: 0.5rem;
            padding-bottom: 3rem;
            padding-left: 1rem;
            padding-right: 2rem;
            max-width: 100%;
        }}

        h1, h2, h3, h4 {{ color: {T['text']}; font-weight: 700; }}

        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px;
            border-bottom: 1px solid {T['border']};
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 42px;
            background: transparent;
            color: {T['text_muted']};
            font-weight: 600;
            font-size: 0.92rem;
            border-radius: 8px 8px 0 0;
            padding: 0 16px;
        }}
        .stTabs [aria-selected="true"] {{
            color: {T['text']} !important;
            border-bottom: 3px solid {T['brand_end']} !important;
            background: {T['surface_alt']};
        }}

        .stButton > button, .stDownloadButton > button {{
            background: linear-gradient(90deg, {T['brand_start']}, {T['brand_end']});
            color: #FFFFFF;
            border: none;
            border-radius: {T['radius_sm']};
            padding: 0.5rem 1.15rem;
            font-weight: 600;
            box-shadow: {T['shadow']};
            transition: transform 0.12s ease, box-shadow 0.12s ease;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: {T['shadow_hover']};
            color: #FFFFFF;
        }}
        .stButton > button:disabled {{
            background: {T['flat_bg']};
            color: {T['text_faint']};
            box-shadow: none;
            transform: none;
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid {T['border']};
            border-radius: {T['radius']};
            background: {T['surface']};
        }}

        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
            border-radius: {T['radius_sm']} !important;
            border: 1px solid {T['border']} !important;
            background: {T['surface']} !important;
        }}

        .yt-hero {{
            background: linear-gradient(120deg, {T['brand_start']} 0%, {T['brand_end']} 100%);
            border-radius: {T['radius']};
            padding: 26px 30px;
            margin-bottom: 20px;
            box-shadow: {T['shadow_hover']};
        }}
        .yt-hero h1 {{ color: #FFFFFF !important; font-size: 1.55rem; margin: 0 0 4px 0; }}
        .yt-hero p {{ color: rgba(255,255,255,0.9) !important; margin: 0; font-size: 0.94rem; }}

        .yt-card {{
            background: {T['surface']};
            border: 1px solid {T['border']};
            border-radius: {T['radius']};
            padding: 18px 20px;
            box-shadow: {T['shadow']};
            margin-bottom: 16px;
        }}

        .yt-channel-header {{
            display: flex; align-items: center; gap: 14px;
            padding: 14px 18px;
            background: {T['surface']};
            border: 1px solid {T['border']};
            border-radius: {T['radius']};
            margin-bottom: 18px;
        }}
        .yt-avatar {{
            width: 46px; height: 46px; border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            color: #fff; font-weight: 700; font-size: 1.1rem;
            background: linear-gradient(135deg, {T['brand_start']}, {T['brand_end']});
            flex-shrink: 0;
        }}
        .yt-channel-name {{ font-size: 1.05rem; font-weight: 700; margin: 0; }}
        .yt-channel-sub {{ font-size: 0.8rem; color: {T['text_muted']}; margin: 0; }}

        .yt-feature-head {{ display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }}
        .yt-feature-icon {{ font-size: 1.5rem; }}
        .yt-feature-title {{ font-size: 1.15rem; font-weight: 700; margin: 0; }}
        .yt-feature-desc {{ color: {T['text_muted']}; font-size: 0.9rem; margin: 2px 0 14px 0; }}

        .yt-bullet {{ display: flex; gap: 10px; align-items: flex-start; padding: 7px 0; font-size: 0.92rem; }}
        .yt-bullet-arrow {{ color: {T['brand_end']}; font-weight: 700; }}

        .yt-pill {{
            display: inline-block; background: {T['flat_bg']}; color: {T['text_muted']};
            font-size: 0.72rem; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
            padding: 3px 10px; border-radius: 999px; margin-bottom: 10px;
        }}
        .yt-pill.soon {{ background: #FFF3E0; color: {T['warning']}; }}
        .yt-pill.ok   {{ background: {T['gain_bg']}; color: {T['gain']}; }}
        .yt-pill.no   {{ background: {T['loss_bg']}; color: {T['loss']}; }}

        .yt-stat {{
            background: {T['surface']};
            border: 1px solid {T['border']};
            border-left: 4px solid var(--stat-color, {T['accent_blue']});
            border-radius: {T['radius_sm']};
            padding: 14px 16px;
        }}
        .yt-stat-value {{ font-size: 1.7rem; font-weight: 800; line-height: 1.1; margin: 0; }}
        .yt-stat-label {{
            font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em;
            text-transform: uppercase; color: {T['text_muted']}; margin: 4px 0 0 0;
        }}

        .yt-cal-grid {{ display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; }}
        .yt-cal-grid.compact {{ gap: 4px; }}
        .yt-cal-dow {{
            text-align: center; font-size: 0.7rem; font-weight: 700;
            color: {T['text_faint']}; text-transform: uppercase; padding-bottom: 2px;
        }}
        .yt-cal-cell {{
            border-radius: 8px; padding: 8px 4px 6px 4px; text-align: center;
            min-height: 58px; display: flex; flex-direction: column; justify-content: space-between;
        }}
        .yt-cal-cell.compact {{ min-height: 38px; padding: 5px 3px 4px 3px; }}
        .yt-cal-cell.empty {{ background: transparent; }}
        .yt-cal-value {{ font-size: 0.95rem; font-weight: 800; }}
        .yt-cal-cell.compact .yt-cal-value {{ font-size: 0.78rem; }}
        .yt-cal-date {{ font-size: 0.68rem; color: {T['text_faint']}; align-self: flex-end; }}

        .yt-empty {{ text-align: center; padding: 40px 20px; color: {T['text_muted']}; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str = ""):
    st.markdown(f'<div class="yt-hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


def channel_header(channel_name: str, created_at: str = ""):
    initial = channel_name.strip()[0].upper() if channel_name.strip() else "?"
    sub = f"Channel &bull; Added {created_at}" if created_at else "Channel"
    st.markdown(
        f"""
        <div class="yt-channel-header">
            <div class="yt-avatar">{initial}</div>
            <div>
                <p class="yt-channel-name">{channel_name}</p>
                <p class="yt-channel-sub">{sub}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_head(icon: str, title: str, description: str, pill: str = None, pill_kind: str = "soon"):
    pill_html = f'<span class="yt-pill {pill_kind}">{pill}</span>' if pill else ""
    st.markdown(
        f"""
        {pill_html}
        <div class="yt-feature-head">
            <span class="yt-feature-icon">{icon}</span>
            <p class="yt-feature-title">{title}</p>
        </div>
        <p class="yt-feature-desc">{description}</p>
        """,
        unsafe_allow_html=True,
    )


def bullet_list(items):
    rows = "".join(
        f'<div class="yt-bullet"><span class="yt-bullet-arrow">&rarr;</span><span>{item}</span></div>'
        for item in items
    )
    st.markdown(f"<div>{rows}</div>", unsafe_allow_html=True)


class card:
    """Context manager: with theme.card(): ..."""
    def __enter__(self):
        st.markdown('<div class="yt-card">', unsafe_allow_html=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        st.markdown("</div>", unsafe_allow_html=True)


def stat_card(label: str, value: str, color: str = None):
    color = color or T["accent_blue"]
    st.markdown(
        f"""
        <div class="yt-stat" style="--stat-color:{color};">
            <p class="yt-stat-value">{value}</p>
            <p class="yt-stat-label">{label}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(icon: str, message: str):
    st.markdown(f'<div class="yt-empty"><div style="font-size:2rem;">{icon}</div><p>{message}</p></div>', unsafe_allow_html=True)


def heat_color(value: float, max_value: float) -> str:
    if max_value <= 0:
        return T["heat_0"]
    ratio = min(value / max_value, 1.0)
    scale = [T["heat_0"], T["heat_1"], T["heat_2"], T["heat_3"], T["heat_4"], T["heat_5"]]
    idx = min(int(ratio * (len(scale) - 1)), len(scale) - 1)
    return scale[idx]


def heat_text_color(value: float, max_value: float) -> str:
    if max_value <= 0:
        return T["text"]
    ratio = min(value / max_value, 1.0) if max_value else 0
    return "#FFFFFF" if ratio > 0.55 else T["text"]


def diverging_bg(value: float) -> str:
    if value > 0:
        return T["gain_bg"]
    if value < 0:
        return T["loss_bg"]
    return T["flat_bg"]


def diverging_text(value: float) -> str:
    if value > 0:
        return T["gain"]
    if value < 0:
        return T["loss"]
    return T["text_muted"]