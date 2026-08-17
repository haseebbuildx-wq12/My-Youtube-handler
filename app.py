"""
app.py
======
Sirf UI WIRING yahan hai — tabs generate karna, aur Google se
OAuth redirect ke baad wapas aane wale ?code=...&state=... ko
complete karna. Baaki sab logic core/ ke andar files mein hai.
"""

import streamlit as st
from urllib.parse import unquote 
from core import theme
from core import channel_manager
from core import youtube_auth
from core.ui_channel_form import render_add_channel_form, render_channel_tab

st.set_page_config(page_title="Multi-Channel YouTube Manager", page_icon="📺", layout="wide")

theme.inject()


# ============================================================
# OAuth redirect completion -- Google se wapas aane par
# ============================================================
   # top pe add karo

def _complete_oauth_if_needed():
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
            except Exception as e:
                st.session_state["oauth_error"] = str(e)

        st.query_params.clear()
        st.rerun()

_complete_oauth_if_needed()


# ============================================================
# HERO
# ============================================================
theme.hero(
    "📺 Multi-Channel YouTube Manager",
    "Apne saare YouTube channels ek hi jagah se manage karo — analytics, uploads aur research.",
)

if st.session_state.get("oauth_success_channel"):
    st.success(f"✅ '{st.session_state.pop('oauth_success_channel')}' Google se connect ho gaya!")
if st.session_state.get("oauth_error"):
    st.error(f"❌ Connect nahi ho paya: {st.session_state.pop('oauth_error')}")
if st.session_state.get("active_channel_deleted"):
    st.info(f"Channel delete ho gaya.")
    del st.session_state["active_channel_deleted"]


# ============================================================
# DYNAMIC CHANNEL TABS + "+ Add Channel" (hamesha last)
# ============================================================
channel_folders = channel_manager.list_channels()
tab_labels = [
    channel_manager.load_channel_config(f).get("channel_name", f) for f in channel_folders
] + ["➕ Add Channel"]

tabs = st.tabs(tab_labels)

for tab, folder in zip(tabs[:-1], channel_folders):
    with tab:
        render_channel_tab(folder)

with tabs[-1]:
    render_add_channel_form()
