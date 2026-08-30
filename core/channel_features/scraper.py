"""
scraper.py
==========
Data Scraper -- do sub-tabs:
  1. Profile Adder  -- TikTok profiles add karna (channel_id save karna)
  2. Video Scraper   -- unhi profiles se videos scrape/download karna

Poora scraping logic core/video_scraper.py mein hai, ye file sirf UI hai.
"""

import os

import pandas as pd
import streamlit as st
import yt_dlp

from core import theme
from core import channel_manager
from core import video_scraper

COOKIES_FILE = video_scraper.COOKIES_FILE


# ============================================================
# TikTok profile info fetch (Profile Adder ke liye)
# ============================================================
def _extract_tiktok_info(profile_input: str) -> dict:
    raw = profile_input.strip()
    url = raw if raw.startswith("http") else f"https://www.tiktok.com/@{raw.lstrip('@')}"

    ydl_opts = {
        "skip_download": True,
        "extract_flat": True,
    }
    if os.path.isfile(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return {
        "channel_id": info.get("channel_id") or info.get("uploader_id") or "",
        "uploader": info.get("uploader") or raw.lstrip("@"),
    }


def render(channel_folder: str, channel_folder_path: str, config: dict):
    theme.feature_head(
        "🕵️", "Data Scraper",
        "TikTok profiles add karo aur unse videos scrape karo.",
    )

    if not os.path.isfile(COOKIES_FILE):
        st.warning(
            f"⚠️ `{COOKIES_FILE}` project root mein nahi mili -- fetch/scrape "
            "reliable nahi rahega jab tak isko daal nahi dete.",
            icon="⚠️",
        )

    sub_tabs = st.tabs(["👤 Profile Adder", "🎥 Video Scraper"])

    with sub_tabs[0]:
        _render_profile_adder(channel_folder, channel_folder_path, config)

    with sub_tabs[1]:
        _render_video_scraper(channel_folder, channel_folder_path, config)


# ============================================================
# TAB 1 -- Profile Adder (pehle jaisa hi, koi change nahi)
# ============================================================
def _render_profile_adder(channel_folder: str, channel_folder_path: str, config: dict):
    profiles = config.get("tiktok_profiles", [])

    left, right = st.columns([1, 1.3])

    with left:
        with theme.card():
            st.markdown("##### ➕ Naya TikTok Profile")
            with st.form(key=f"add_tiktok_profile_{channel_folder}", clear_on_submit=True):
                profile_input = st.text_input(
                    "TikTok Username ya Profile URL",
                    placeholder="@memepremeo ya https://www.tiktok.com/@memepremeo",
                )
                submitted = st.form_submit_button("🔍 Fetch & Save")

            if submitted:
                cleaned = profile_input.strip().lstrip("@")
                if not cleaned:
                    st.error("Username ya URL daalo.")
                elif any(p["profile_name"].lower() == cleaned.lower() for p in profiles):
                    st.warning("Ye profile pehle se list mein hai.")
                else:
                    with st.spinner("yt-dlp se channel_id nikal raha hoon..."):
                        try:
                            info = _extract_tiktok_info(profile_input)
                            profiles.append({"profile_name": info["uploader"], "channel_id": info["channel_id"]})
                            channel_manager.update_channel_config(channel_folder, {"tiktok_profiles": profiles})
                            st.success(f"'{info['uploader']}' add ho gaya!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fetch nahi ho paya: {e}")

    with right:
        with theme.card():
            st.markdown("##### 📋 Saved Profiles")
            if not profiles:
                theme.empty_state("🕵️", "Abhi koi TikTok profile add nahi hua.")
            else:
                df = pd.DataFrame(profiles)[["profile_name", "channel_id"]]
                df.columns = ["Profile Name", "Channel ID"]
                st.dataframe(df, use_container_width=True, hide_index=True)

                to_delete = st.selectbox(
                    "Delete karna ho to profile select karo",
                    options=["-- Select --"] + [p["profile_name"] for p in profiles],
                    key=f"tiktok_del_select_{channel_folder}",
                )
                if to_delete != "-- Select --":
                    if st.button("🗑️ Delete", key=f"tiktok_del_btn_{channel_folder}"):
                        profiles = [p for p in profiles if p["profile_name"] != to_delete]
                        channel_manager.update_channel_config(channel_folder, {"tiktok_profiles": profiles})
                        st.rerun()


# ============================================================
# TAB 2 -- Video Scraper
# ============================================================
def _render_video_scraper(channel_folder: str, channel_folder_path: str, config: dict):
    profiles = config.get("tiktok_profiles", [])

    left, right = st.columns([1.1, 1])

    with left:
        # -------- Stats cards --------
        stat_a, stat_b = st.columns(2)
        with stat_a:
            theme.stat_card(
                "Total Available Videos",
                str(video_scraper.count_available_videos(channel_folder_path)),
                theme.T["accent_teal"],
            )
        with stat_b:
            theme.stat_card("Total Profiles", str(len(profiles)), theme.T["accent_blue"])

        st.caption("ℹ️ Count har page-load par live calculate hota hai.")
        st.divider()

        if not profiles:
            theme.empty_state("👤", "Pehle 'Profile Adder' tab se profiles add karo.")
            return

        # -------- Profile selection (Select All synced both directions) --------
        st.markdown("##### Select Profiles")

        select_all_key = f"select_all_{channel_folder}"
        cb_keys = [f"pf_cb_{channel_folder}_{p['profile_name']}" for p in profiles]

        all_checked = all(st.session_state.get(k, False) for k in cb_keys)
        if st.session_state.get(select_all_key) != all_checked:
            st.session_state[select_all_key] = all_checked

        def _toggle_all():
            new_val = st.session_state[select_all_key]
            for k in cb_keys:
                st.session_state[k] = new_val

        st.checkbox("Select All", key=select_all_key, on_change=_toggle_all)

        selected_profiles = []
        for p, k in zip(profiles, cb_keys):
            if st.checkbox(p["profile_name"], key=k):
                selected_profiles.append(p)

        st.divider()

        # -------- Minimum views filter --------
        min_views = st.number_input("Minimum Views", min_value=0, value=100000, step=1000)

        scrape_clicked = st.button(
            "🚀 Scrape Videos", type="primary",
            disabled=not selected_profiles, use_container_width=True,
        )
        if not selected_profiles:
            st.caption("Kam se kam ek profile select karo.")

    with right:
        with theme.card():
            st.markdown("##### 📋 Profiles Overview")
            scrape_state = video_scraper.load_scrape_state(channel_folder_path)
            rows = []
            for p in profiles:
                folder = video_scraper.profile_folder(channel_folder_path, p["profile_name"])
                count = len(os.listdir(folder)) if os.path.isdir(folder) else 0
                p_state = scrape_state.get(p["profile_name"], {})
                rows.append({
                    "Profile": p["profile_name"],
                    "Videos Saved": count,
                    "Last Scrape": p_state.get("last_scrape_time") or "—",
                    "Last Videos Scraped Count": p_state.get("last_run_downloaded", 0),
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            with st.expander("🩹 Smart Repair"):
                st.caption(
                    "Kisi profile ki actual downloaded files check karke, sirf un video IDs "
                    "ko 'un-mark' karta hai jinki file GAAYAB hai (jaise collision se overwrite "
                    "hui thi). Jo files mojood hain wo touch nahi hoti -- unnecessarily dobara "
                    "download nahi hongi."
                )
                repair_target = st.selectbox(
                    "Profile", options=["-- Select --"] + [p["profile_name"] for p in profiles],
                    key=f"repair_select_{channel_folder}",
                )
                if repair_target != "-- Select --":
                    if st.button("🩹 Check & Repair", key=f"repair_btn_{channel_folder}"):
                        profile_obj = next(p for p in profiles if p["profile_name"] == repair_target)
                        with st.spinner("Fresh video list fetch karke missing files check kar raha hoon..."):
                            result = video_scraper.repair_profile_state(channel_folder_path, profile_obj)
                        if result["unmarked"] > 0:
                            st.success(
                                f"✅ {result['unmarked']} missing video(s) mil gaye -- ab 'Scrape "
                                f"Videos' chalao, sirf yehi dobara download hongi."
                            )
                        else:
                            st.info("Koi missing video nahi mila -- sab theek hain.")

    # -------- Scraping run (full width, neeche) --------
    if scrape_clicked:
        st.divider()
        progress_box = st.container()
        status_rows = {p["profile_name"]: "Pending" for p in selected_profiles}
        status_placeholder = progress_box.empty()
        progress_bar = progress_box.progress(0)
        log_box = progress_box.expander("Live Log", expanded=True)

        def render_status():
            df = pd.DataFrame([{"Profile": n, "Status": s} for n, s in status_rows.items()])
            status_placeholder.dataframe(df, use_container_width=True, hide_index=True)

        render_status()
        totals = None

        for ev in video_scraper.scrape_profiles(channel_folder_path, selected_profiles, int(min_views)):
            etype = ev["event"]

            if etype == "profile_start":
                status_rows[ev["profile_name"]] = "Scraping"
                progress_box.info(f"Scraping Profile {ev['index']} of {ev['total']}: **{ev['profile_name']}**")
                render_status()
                progress_bar.progress((ev["index"] - 1) / ev["total"])

            elif etype == "video_start":
                log_box.write(f"⬇️ Downloading: {ev['title'][:60]} (views: {ev['views']})")

            elif etype == "video_done":
                if ev["status"] == "downloaded":
                    log_box.write(f"✅ Saved: {ev['title'][:60]}")
                else:
                    log_box.write(f"❌ Failed: {ev['title'][:60]} -- {ev.get('error', '')}")

            elif etype == "profile_result":
                status_rows[ev["profile_name"]] = ev["status"]
                render_status()
                if ev["status"] == "Failed":
                    log_box.write(f"❌ Profile '{ev['profile_name']}' failed: {ev.get('error', '')}")

            elif etype == "all_done":
                totals = ev["totals"]
                progress_bar.progress(1.0)

        if totals:
            st.success(
                f"**Done!** Profiles Processed: {totals['processed']} | "
                f"Completed: {totals['completed']} | Failed: {totals['failed']}  \n"
                f"New Videos Found: {totals['new_found']} | "
                f"Downloaded: {totals['downloaded']} | Skipped: {totals['skipped']}"
            )