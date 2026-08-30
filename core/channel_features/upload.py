"""
upload.py
=========
Video Upload Scheduler UI.

    Left   -- upload configuration + daily schedule + Save & Activate
    Right  -- profile-wise upload statistics
    Bottom -- upload activity/status table (permanent history)

Poora scheduling/upload engine core/uploader.py mein hai, ye file
sirf UI hai.
"""

from datetime import time as dtime

import pandas as pd
import streamlit as st

from core import theme
from core import uploader

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False


def _time_to_str(t: dtime) -> str:
    return f"{t.hour:02d}:{t.minute:02d}"


def _str_to_time(s: str) -> dtime:
    try:
        hh, mm = map(int, s.split(":"))
        return dtime(hh, mm)
    except Exception:
        return dtime(9, 0)


def render(channel_folder: str, channel_folder_path: str, config: dict):
    theme.feature_head(
        "⬆️", "Video Upload Scheduler",
        "Scraped videos ko automatically schedule ke hisaab se YouTube par upload karo.",
    )

    if not uploader.GOOGLE_API_AVAILABLE:
        st.warning(
            "⚠️ `google-api-python-client` install nahi hai -- upload kaam nahi karega. "
            "Terminal mein: `pip install google-api-python-client`",
            icon="⚠️",
        )

    # Background scheduler ko ensure karo (idempotent -- dobara start nahi hoga)
    uploader.ensure_scheduler(channel_folder, channel_folder_path)

    schedule = uploader.load_schedule(channel_folder_path)

    left, right = st.columns([1.2, 1])

    # ============================================================
    # LEFT -- Upload Configuration
    # ============================================================
    with left:
        with theme.card():
            status_badge = "🟢 Active" if schedule.get("active") else "⚪ Inactive"
            st.markdown(f"##### ⚙️ Upload Configuration &nbsp; `{status_badge}`", unsafe_allow_html=True)

            profiles = uploader.list_available_profiles(channel_folder_path)
            source_options = ["Random"] + profiles
            current_source = schedule.get("source_profile", "Random")
            if current_source not in source_options:
                current_source = "Random"

            source_profile = st.selectbox(
                "Upload From Profile", options=source_options,
                index=source_options.index(current_source),
                key=f"upl_source_{channel_folder}",
            )

            default_name = st.text_input(
                "Default Name", value=schedule.get("default_name", ""),
                placeholder="e.g. | Netflix Series",
                key=f"upl_defname_{channel_folder}",
            )
            default_description = st.text_area(
                "Default Description", value=schedule.get("default_description", ""),
                placeholder="Best Netflix series you should watch.",
                key=f"upl_defdesc_{channel_folder}", height=80,
            )
            default_tags = st.text_input(
                "Default Tags", value=schedule.get("default_tags", ""),
                placeholder="Netflix, Series, Entertainment, Trending",
                key=f"upl_deftags_{channel_folder}",
            )

            visibility_options = ["public", "unlisted", "private"]
            visibility = st.selectbox(
                "Visibility", options=visibility_options,
                index=visibility_options.index(schedule.get("visibility", "public")),
                format_func=lambda v: v.capitalize(),
                key=f"upl_vis_{channel_folder}",
            )

            videos_per_day = st.number_input(
                "Videos Per Day", min_value=1, max_value=50,
                value=int(schedule.get("videos_per_day", 5)),
                key=f"upl_perday_{channel_folder}",
            )

            st.markdown("**Upload Times**")
            st.caption("ℹ️ Videos Per Day ke hisaab se slots automatically ban/hat jate hain.")

            slots_key = f"upl_time_slots_{channel_folder}"
            init_key = f"upl_time_slots_init_{channel_folder}"
            if not st.session_state.get(init_key):
                st.session_state[slots_key] = [_str_to_time(t) for t in schedule.get("times", [])] or [dtime(9, 0)]
                st.session_state[init_key] = True

            slots = st.session_state[slots_key]

            # Videos Per Day badla ho to slots list ko usi count tak sync karo
            target_count = int(videos_per_day)
            if len(slots) < target_count:
                # naye slots default -- din mein barabar phaila ke suggest karo
                default_hours = [9, 12, 15, 18, 21, 8, 11, 14, 17, 20, 7, 10, 13, 16, 19]
                idx = 0
                while len(slots) < target_count:
                    h = default_hours[idx % len(default_hours)]
                    slots.append(dtime(h, 0))
                    idx += 1
            elif len(slots) > target_count:
                slots[:] = slots[:target_count]

            for i in range(len(slots)):
                slots[i] = st.time_input(f"Slot {i + 1}", value=slots[i], key=f"upl_slot_{channel_folder}_{i}")

            st.divider()

            btn_a, btn_b = st.columns(2)
            with btn_a:
                if st.button("💾 Save & Activate Schedule", type="primary", use_container_width=True, key=f"upl_save_{channel_folder}"):
                    new_config = {
                        "active": True,
                        "source_profile": source_profile,
                        "default_name": default_name,
                        "default_description": default_description,
                        "default_tags": default_tags,
                        "visibility": visibility,
                        "videos_per_day": int(videos_per_day),
                        "times": sorted({_time_to_str(t) for t in slots}),
                    }
                    uploader.save_schedule(channel_folder_path, new_config)
                    st.success("Schedule save + activate ho gaya. Ab automatically chalega -- koi button nahi dabana.")
                    st.rerun()
            with btn_b:
                if st.button("⏸ Deactivate", use_container_width=True, key=f"upl_deactivate_{channel_folder}"):
                    schedule["active"] = False
                    uploader.save_schedule(channel_folder_path, schedule)
                    st.info("Schedule deactivate ho gaya -- naye uploads nahi honge jab tak dobara activate na karo.")
                    st.rerun()

    # ============================================================
    # RIGHT -- Profile Upload Statistics
    # ============================================================
    with right:
        with theme.card():
            st.markdown("##### 📊 Profile Upload Stats")
            stats = uploader.profile_stats(channel_folder_path)
            if not stats:
                theme.empty_state("📁", "Abhi koi profile Videos folder mein nahi hai.")
            else:
                st.dataframe(pd.DataFrame(stats), use_container_width=True, hide_index=True)

    # ============================================================
    # BOTTOM -- Upload Activity / Status
    # ============================================================
    st.divider()
    header_a, header_b = st.columns([4, 1])
    with header_a:
        st.markdown("##### 📋 Upload Activity / Status")
    with header_b:
        if not AUTOREFRESH_AVAILABLE:
            if st.button("🔄 Refresh", key=f"upl_manual_refresh_{channel_folder}"):
                st.rerun()

    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=15_000, key=f"upl_autorefresh_{channel_folder}")
    else:
        st.caption("ℹ️ Auto-refresh ke liye: `pip install streamlit-autorefresh` -- abhi manual refresh use karo.")

    history = uploader.load_history(channel_folder_path)
    if not history:
        theme.empty_state("🕓", "Abhi koi upload activity nahi hui.")
    else:
        rows = []
        for rec in reversed(history[-100:]):  # sabse recent pehle, last 100
            rows.append({
                "Scheduled": rec.get("scheduled_time", "—"),
                "Profile": rec.get("profile") or "—",
                "Title": rec.get("title") or "—",
                "Status": rec.get("status", "—"),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)