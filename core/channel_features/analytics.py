"""
analytics.py
============
Channel Analytics ka poora UI. Data-fetching yahan NAHI hoti --
sab core.channel_features.analytics_data se aata hai. Ye file
sirf render karti hai.
"""

import calendar
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from core import theme
from core import youtube_auth
from core.channel_features import analytics_data as data


RANGE_OPTIONS = {
    "Pichle 2 mahine": 2,   # DEFAULT
    "Pichle 3 mahine": 3,
    "Pichle 6 mahine": 6,
    "Pichle 12 mahine": 12,
}


# ============================================================
# ENTRY POINT -- ui_channel_form.py isi ko call karta hai
# ============================================================
def render(channel_folder: str, channel_folder_path: str, config: dict):
    theme.feature_head(
        "📊", "Channel Analytics",
        "Views, subscribers aur video performance ka poora dashboard.",
    )

    creds = youtube_auth.load_credentials(channel_folder_path)
    cache = data.load_cache(channel_folder_path)
    demo_flag_key = f"{channel_folder}_show_demo"

    connected = creds is not None

    # ---------- STATE 1: Not connected ----------
    if not connected and not st.session_state.get(demo_flag_key):
        _render_not_connected(channel_folder, channel_folder_path, config, demo_flag_key)
        return

    # ---------- Demo mode (bina connect kiye preview) ----------
    if not connected and st.session_state.get(demo_flag_key):
        st.info("🎲 Ye DEMO data hai — real channel connect nahi hua.")
        if st.button("Demo band karo", key=f"{channel_folder}_stop_demo"):
            st.session_state[demo_flag_key] = False
            st.rerun()
        mock = data.fetch_mock_data()
        _render_dashboard(channel_folder, mock, is_mock=True)
        return

    # ---------- STATE 2: Connected but no cache yet ----------
    if connected and not cache:
        st.success("✅ Google se connected hai.")
        st.write("Dashboard dikhane ke liye pehli baar data fetch karo.")
        if st.button("🔄 Update Data", key=f"{channel_folder}_first_fetch"):
            _fetch_and_cache(channel_folder_path, config, creds, months=RANGE_OPTIONS["Pichle 2 mahine"])
            st.rerun()
        return

    # ---------- STATE 3: Data maujood hai ----------
    _render_top_bar(channel_folder, channel_folder_path, config, creds)
    cache = data.load_cache(channel_folder_path)  # refresh ke baad dobara load
    _render_dashboard(channel_folder, cache, is_mock=False)


# ============================================================
# STATE 1 helper
# ============================================================
def _render_not_connected(channel_folder, channel_folder_path, config, demo_flag_key):
    from core.ui_channel_form import render_connect_button  # local import: circular-import se bachne ke liye

    st.write("Is channel ka analytics dekhne ke liye pehle Google account connect karo.")
    render_connect_button(channel_folder, channel_folder_path, config, key=f"{channel_folder}_connect_analytics")

    with st.expander("🎲 Demo Data Dikhao (bina connect kiye preview)"):
        st.caption("Ye sirf sample/demo numbers hain, tumhare real channel ka data nahi.")
        if st.button("Demo Dashboard Dikhao", key=f"{channel_folder}_start_demo"):
            st.session_state[demo_flag_key] = True
            st.rerun()


# ============================================================
# STATE 3 top bar: range filter + Update Data button
# ============================================================
def _render_top_bar(channel_folder, channel_folder_path, config, creds):
    col_range, col_btn = st.columns([3, 1])
    range_key = f"{channel_folder}_range"
    with col_range:
        selected_label = st.selectbox(
            "Data Range", list(RANGE_OPTIONS.keys()),
            index=0, key=range_key,
            help="Zyada purana data sirf isi filter se select karne par fetch hota hai.",
        )
    months = RANGE_OPTIONS[selected_label]

    with col_btn:
        st.write("")
        st.write("")
        if st.button("🔄 Update Data", key=f"{channel_folder}_update"):
            _fetch_and_cache(channel_folder_path, config, creds, months=months)
            st.rerun()


def _fetch_and_cache(channel_folder_path, config, creds, months: int):
    """Overview + daily(range) + videos fetch karke cache mein merge karta hai."""
    with st.spinner("YouTube se data fetch ho raha hai..."):
        overview = data.fetch_channel_overview(creds)
        channel_id = overview.get("channel_id")

        end_date = datetime.now()
        start_date = end_date - timedelta(days=months * 30)
        daily = data.fetch_daily_analytics(
            creds, channel_id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )
        videos = data.fetch_all_videos(creds, channel_id)

        cache = data.merge_daily_into_cache(channel_folder_path, daily)
        cache["overview"] = overview
        cache["videos"] = videos
        data.save_cache(channel_folder_path, cache)
    st.success("Data update ho gaya!")


# ============================================================
# DASHBOARD LAYOUT
# ============================================================
def _render_dashboard(channel_folder: str, cache: dict, is_mock: bool):
    overview = cache.get("overview", {})
    daily = cache.get("daily", {})
    videos = cache.get("videos", [])
    last_updated = cache.get("last_updated", "abhi" if is_mock else "—")

    # ---- Top stat row ----
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.3])
    with c1:
        theme.stat_card("Subscribers", f"{overview.get('subscribers', 0):,}", theme.T["accent_blue"])
    with c2:
        theme.stat_card("Total Views", f"{overview.get('total_views', 0):,}", theme.T["accent_teal"])
    with c3:
        theme.stat_card("Total Videos", f"{overview.get('total_videos', 0):,}", theme.T["accent_amber"])
    with c4:
        st.markdown(
            f"<div style='padding-top:10px;color:{theme.T['text_muted']};font-size:0.85rem;'>"
            f"🕒 Last updated<br><b style='color:{theme.T['text']};'>{last_updated}</b></div>",
            unsafe_allow_html=True,
        )

    st.write("")

    month_key = f"{channel_folder}_cal_month"
    if month_key not in st.session_state:
        st.session_state[month_key] = datetime.now().replace(day=1)

    left, right = st.columns([1.15, 1])

    with left:
        _render_month_nav(month_key)
        with theme.card():
            st.markdown("**Views**")
            _render_calendar(daily, st.session_state[month_key], mode="views", compact=False)
        with theme.card():
            st.markdown("**Subscribers gained / lost**")
            _render_calendar(daily, st.session_state[month_key], mode="subs", compact=True)

    with right:
        with theme.card():
            _render_video_table(channel_folder, videos)


def _render_month_nav(month_key: str):
    current = st.session_state[month_key]
    c1, c2, c3 = st.columns([1, 3, 1])
    with c1:
        if st.button("◀", key=f"{month_key}_prev"):
            prev_month_last_day = current - timedelta(days=1)
            st.session_state[month_key] = prev_month_last_day.replace(day=1)
            st.rerun()
    with c2:
        st.markdown(
            f"<h4 style='text-align:center;margin:6px 0;'>{current.strftime('%B %Y')}</h4>",
            unsafe_allow_html=True,
        )
    with c3:
        if st.button("▶", key=f"{month_key}_next"):
            days_in_month = calendar.monthrange(current.year, current.month)[1]
            next_month_first = current + timedelta(days=days_in_month)
            st.session_state[month_key] = next_month_first.replace(day=1)
            st.rerun()


# ============================================================
# CALENDAR HEATMAP RENDER (HTML string, ek hi markdown call)
# ============================================================
def _render_calendar(daily: dict, month_date: datetime, mode: str, compact: bool):
    year, month = month_date.year, month_date.month
    cal = calendar.Calendar(firstweekday=6)  # Sunday se start
    weeks = cal.monthdayscalendar(year, month)

    dow_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    grid_class = "yt-cal-grid compact" if compact else "yt-cal-grid"
    cell_class = "yt-cal-cell compact" if compact else "yt-cal-cell"

    max_views = max((v.get("views", 0) for v in daily.values()), default=0)

    html = [f'<div class="yt-cal-wrap"><div class="{grid_class}">']
    for label in dow_labels:
        html.append(f'<div class="yt-cal-dow">{label}</div>')

    for week in weeks:
        for day_num in week:
            if day_num == 0:
                html.append(f'<div class="{cell_class} empty"></div>')
                continue
            date_key = f"{year:04d}-{month:02d}-{day_num:02d}"
            entry = daily.get(date_key)

            if mode == "views":
                views = entry.get("views", 0) if entry else 0
                bg = theme.heat_color(views, max_views)
                fg = theme.heat_text_color(views, max_views)
                value_display = f"{views:,}" if entry else "—"
                html.append(
                    f'<div class="{cell_class}" style="background:{bg};">'
                    f'<span class="yt-cal-value" style="color:{fg};">{value_display}</span>'
                    f'<span class="yt-cal-date" style="color:{fg};opacity:0.75;">{day_num}</span>'
                    f'</div>'
                )
            else:  # subs
                change = entry.get("subs_change", 0) if entry else 0
                bg = theme.diverging_bg(change)
                fg = theme.diverging_text(change)
                value_display = (f"+{change}" if change > 0 else str(change)) if entry else "—"
                html.append(
                    f'<div class="{cell_class}" style="background:{bg};">'
                    f'<span class="yt-cal-value" style="color:{fg};">{value_display}</span>'
                    f'<span class="yt-cal-date" style="color:{theme.T["text_faint"]};">{day_num}</span>'
                    f'</div>'
                )
    html.append("</div></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


# ============================================================
# VIDEO TABLE -- search + sort (views/likes) + load-all toggle
# ============================================================
def _render_video_table(channel_folder: str, videos: list[dict]):
    st.markdown("**Videos**")

    if not videos:
        theme.empty_state("🎬", "Abhi koi video data nahi mila.")
        return

    df = pd.DataFrame(videos)

    search_col, sort_col = st.columns([2, 1])
    with search_col:
        query = st.text_input("🔍 Title se search karo", key=f"{channel_folder}_video_search", placeholder="Video title...")
    with sort_col:
        sort_by = st.selectbox("Sort by", ["Views", "Likes"], key=f"{channel_folder}_video_sort")

    if query:
        df = df[df["title"].str.contains(query, case=False, na=False)]

    sort_col_name = "views" if sort_by == "Views" else "likes"
    df = df.sort_values(sort_col_name, ascending=False).reset_index(drop=True)

    show_all_key = f"{channel_folder}_show_all_videos"
    show_all = st.session_state.get(show_all_key, False)

    display_df = df if show_all else df.head(10)
    display_df = display_df.rename(columns={
        "title": "Video Title", "views": "Views", "likes": "Likes", "comments": "Comments",
    })

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    if len(df) > 10:
        if not show_all:
            if st.button(f"⬇️ Saari {len(df)} videos load karo", key=f"{channel_folder}_load_all"):
                st.session_state[show_all_key] = True
                st.rerun()
        else:
            if st.button("⬆️ Wapas 10 dikhao", key=f"{channel_folder}_collapse"):
                st.session_state[show_all_key] = False
                st.rerun()
