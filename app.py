"""
app.py
======
Sirf UI WIRING yahan hai — sidebar navigation banana, aur Google se
OAuth redirect ke baad wapas aane wale ?code=...&state=... ko
complete karna. Baaki sab logic core/ ke andar files mein hai.
"""

import streamlit as st

from core import theme
from core import channel_manager
from core import youtube_auth
from core.ui_channel_form import render_add_channel_form, render_channel_tab

st.set_page_config(page_title="Multi-Channel YouTube Manager", page_icon="📺", layout="wide")

theme.inject()


# ============================================================
# OAuth redirect completion -- Google se wapas aane par
# ============================================================
def _complete_oauth_if_needed():
    from urllib.parse import unquote

    params = st.query_params
    code = params.get("code")
    state = params.get("state")
    pending_channel = unquote(state) if state else None

    if code and pending_channel:
        config = channel_manager.load_channel_config(pending_channel)
        if config:
            try:
                flow = youtube_auth.build_flow(config["client_id"], config["client_secret"])
                creds = youtube_auth.exchange_code_for_credentials(flow, code)
                youtube_auth.save_credentials(channel_manager.channel_dir(pending_channel), creds)
                st.session_state["oauth_success_channel"] = config.get("channel_name", pending_channel)
                st.session_state["active_channel"] = pending_channel
                st.session_state["show_add_channel"] = False
            except Exception as e:
                st.session_state["oauth_error"] = str(e)

        st.query_params.clear()
        st.rerun()


_complete_oauth_if_needed()


# ============================================================
# SIDEBAR -- title + channel list + add channel
# ============================================================
channel_folders = channel_manager.list_channels()
channel_names = {
    f: channel_manager.load_channel_config(f).get("channel_name", f) for f in channel_folders
}

# Agar active_channel set nahi hai ya delete ho chuka hai, to default pehla channel
if channel_folders and st.session_state.get("active_channel") not in channel_folders:
    st.session_state["active_channel"] = channel_folders[0]
    st.session_state["show_add_channel"] = False

with st.sidebar:
    st.markdown("### 📺 Multi-Channel\nYouTube Manager")
    st.caption("Apne saare YouTube channels ek hi jagah se manage karo.")
    st.divider()

    if not channel_folders:
        st.info("Abhi koi channel add nahi hua.")
    else:
        for folder in channel_folders:
            is_active = (
                st.session_state.get("active_channel") == folder
                and not st.session_state.get("show_add_channel")
            )
            if st.button(
                channel_names[folder],
                key=f"nav_{folder}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state["active_channel"] = folder
                st.session_state["show_add_channel"] = False
                st.rerun()

    st.divider()
    if st.button(
        "➕ Add Channel",
        use_container_width=True,
        type="primary" if st.session_state.get("show_add_channel") else "secondary",
    ):
        st.session_state["show_add_channel"] = True
        st.rerun()


# ============================================================
# TOP MESSAGES (success / error / delete notices)
# ============================================================
if st.session_state.get("oauth_success_channel"):
    st.success(f"✅ '{st.session_state.pop('oauth_success_channel')}' Google se connect ho gaya!")
if st.session_state.get("oauth_error"):
    st.error(f"❌ Connect nahi ho paya: {st.session_state.pop('oauth_error')}")
if st.session_state.get("active_channel_deleted"):
    st.info("Channel delete ho gaya.")
    del st.session_state["active_channel_deleted"]


# ============================================================
# MAIN AREA -- selected channel ka content, ya Add Channel form
# ============================================================
if st.session_state.get("show_add_channel") or not channel_folders:
    render_add_channel_form()
else:
    render_channel_tab(st.session_state["active_channel"])