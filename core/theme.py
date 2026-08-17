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


# ============================================================
# DESIGN TOKENS -- sab kuch yahan se nikalta hai. Yahi ek jagah
# hai jo tumhe rangon/spacing ke liye edit karni padegi.
# ============================================================
TOKENS = {
    # -- Base surfaces (LIGHT theme) --
    "bg":            "#F5F6FA",   # page background
    "surface":       "#FFFFFF",   # card background
    "surface_alt":   "#FAFBFD",   # subtle alternate surface (headers, inputs)
    "border":        "#E3E6ED",   # card / divider border

    # -- Text --
    "text":          "#181B24",   # primary text -- dark, high contrast on white
    "text_muted":    "#6B7280",   # secondary text
    "text_faint":    "#9AA1AE",   # tertiary / placeholder

    # -- Brand gradient (buttons, hero, accents) --
    "brand_start":   "#FF4D5E",   # red
    "brand_end":     "#7C3AED",   # purple

    # -- Stat-card accent colors (rotate through these) --
    "accent_blue":   "#2563EB",
    "accent_teal":   "#0D9488",
    "accent_amber":  "#F59E0B",
    "accent_purple": "#7C3AED",
    "accent_red":    "#EF4444",

    # -- Heatmap (views) -- sequential scale, light -> dark --
    "heat_0":  "#EEF2FA",
    "heat_1":  "#C9DBF7",
    "heat_2":  "#93B9EF",
    "heat_3":  "#5A8FE0",
    "heat_4":  "#2E63C7",
    "heat_5":  "#173C8A",

    # -- Diverging (subscribers gained/lost) --
    "gain":    "#16A34A",
    "gain_bg": "#E7F7ED",
    "loss":    "#DC2626",
    "loss_bg": "#FCEAEA",
    "flat_bg": "#EEF0F4",

    # -- Status --
    "success": "#16A34A",
    "warning": "#D97706",
    "danger":  "#DC2626",

    # -- Radius / shadow --
    "radius":       "14px",
    "radius_sm":    "9px",
    "shadow":       "0 1px 2px rgba(16,24,40,0.04), 0 1px 3px rgba(16,24,40,0.06)",
    "shadow_hover": "0 4px 12px rgba(16,24,40,0.10)",
}

T = TOKENS  # short alias used everywhere below


# ============================================================
# 1) inject() -- ek hi baar app.py ke shuru mein call karo.
#    Poori app ki base CSS yahan se aati hai.
# ============================================================
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
        .block-container {{
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            max-width: 1320px;
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
    """Views heatmap: value ko sequential-scale color mein badalta hai."""
    if max_value <= 0:
        return T["heat_0"]
    ratio = min(value / max_value, 1.0)
    scale = [T["heat_0"], T["heat_1"], T["heat_2"], T["heat_3"], T["heat_4"], T["heat_5"]]
    idx = min(int(ratio * (len(scale) - 1)), len(scale) - 1)
    return scale[idx]


def heat_text_color(value: float, max_value: float) -> str:
    """Dark cell pe likha number white honi chahiye, halke cell pe dark."""
    if max_value <= 0:
        return T["text"]
    ratio = min(value / max_value, 1.0) if max_value else 0
    return "#FFFFFF" if ratio > 0.55 else T["text"]


def diverging_bg(value: float) -> str:
    """Subscribers gained/lost calendar ke liye background."""
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
