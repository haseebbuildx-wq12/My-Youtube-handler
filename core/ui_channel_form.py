"""
ui_channel_form.py
===================
- render_add_channel_form()  -> "+ Add Channel" tab ka form
- render_channel_tab()        -> ek channel ke andar 4 sub-tabs
- render_connect_button()     -> shared "Connect with Google" UI
  (analytics.py aur settings.py dono isko use karte hain, taake
  OAuth-redirect wala UI code sirf ek hi jagah likha jaye)
"""
from urllib.parse import quote
import streamlit as st

from core import theme
from core import channel_manager
from core import youtube_auth
from core.channel_features import analytics, upload, scraper, settings


# ============================================================
# "+ Add Channel" tab
# ============================================================
def render_add_channel_form():
    theme.feature_head("➕", "Naya Channel Add Karo", "Google Cloud Console se apna OAuth Client ID/Secret yahan daalo.")

    with theme.card():
        with st.form(key="add_channel_form", clear_on_submit=True):
            channel_name = st.text_input("Channel Name", placeholder="e.g. My Gaming Channel")
            client_id = st.text_input("Client ID", placeholder="xxxxx.apps.googleusercontent.com")
            client_secret = st.text_input("Client Secret", type="password")
            submitted = st.form_submit_button("💾 Save Channel")

            if submitted:
                if not channel_name.strip() or not client_id.strip() or not client_secret.strip():
                    st.error("Sab fields fill karna zaroori hai.")
                else:
                    channel_manager.add_channel(channel_name, client_id, client_secret)
                    st.success(f"'{channel_name}' add ho gaya!")
                    st.rerun()

        st.caption(
            "ℹ️ Google Cloud Console mein OAuth Client type **Web application** "
            f"choose karo aur redirect URI `{youtube_auth.REDIRECT_URI}` "
            "Authorized redirect URIs mein add karo."
        )


# ============================================================
# Ek channel ke andar 4 sub-tabs
# ============================================================
def render_channel_tab(channel_folder: str):
    config = channel_manager.load_channel_config(channel_folder)
    if config is None:
        st.error("Channel config nahi mila.")
        return

    channel_folder_path = channel_manager.channel_dir(channel_folder)
    theme.channel_header(config.get("channel_name", channel_folder), config.get("created_at", ""))

    sub_tabs = st.tabs(["📊 Channel Analytics", "⬆️ Video Upload", "🕵️ Data Scraper", "⚙️ Settings"])

    with sub_tabs[0]:
        analytics.render(channel_folder, channel_folder_path, config)
    with sub_tabs[1]:
        upload.render(channel_folder, channel_folder_path, config)
    with sub_tabs[2]:
        scraper.render(channel_folder, channel_folder_path, config)
    with sub_tabs[3]:
        settings.render(channel_folder, channel_folder_path, config)


# ============================================================
# Shared "Connect with Google" button -- OAuth redirect shuru
# karta hai. app.py is redirect ke baad wapas aane wale
# ?code=...&state=... ko handle karta hai.
# ============================================================
# from urllib.parse import quote   # top pe add karo

def render_connect_button(channel_folder: str, channel_folder_path: str, config: dict, key: str):
    if st.button("🔗 Connect with Google", key=key):
        flow = youtube_auth.build_flow(config["client_id"], config["client_secret"])

        # channel_folder seedha OAuth "state" param mein bhej rahe hain --
        # redirect ke baad Streamlit session reset ho jata hai, isliye
        # session_state pe depend nahi kar sakte.
        auth_url, state = youtube_auth.get_authorization_url(
            flow, state=quote(channel_folder, safe="")
        )

        st.markdown(
            f'<meta http-equiv="refresh" content="0; url={auth_url}">'
            f'<p>Google consent screen par redirect ho raha hai... '
            f'agar automatically na ho to <a href="{auth_url}">yahan click karo</a>.</p>',
            unsafe_allow_html=True,
        )
        st.stop()