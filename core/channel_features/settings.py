"""
settings.py
===========
Har channel ka Settings tab: client_id/secret dikhana + update
karna, Google connection status (Connected/Not Connected +
Disconnect), aur Delete channel button (confirmation checkbox
ke saath, warna disabled).
"""

import streamlit as st

from core import theme
from core import channel_manager
from core import youtube_auth


def render(channel_folder: str, channel_folder_path: str, config: dict):
    theme.feature_head("⚙️", "Settings", "Credentials, connection status aur channel management.")

    _render_connection_status(channel_folder, channel_folder_path, config)
    st.write("")
    _render_credentials(channel_folder, channel_folder_path, config)
    st.write("")
    _render_danger_zone(channel_folder, channel_folder_path, config)


# ============================================================
# Connection status + Disconnect
# ============================================================
def _render_connection_status(channel_folder, channel_folder_path, config):
    from core.ui_channel_form import render_connect_button

    with theme.card():
        st.markdown("**Google Connection**")
        connected = youtube_auth.is_connected(channel_folder_path)

        if connected:
            st.markdown(
                f'<span class="yt-pill ok">Connected</span>',
                unsafe_allow_html=True,
            )
            if st.button("🔌 Disconnect", key=f"{channel_folder}_disconnect"):
                youtube_auth.disconnect(channel_folder_path)
                st.success("Disconnect ho gaya.")
                st.rerun()
        else:
            st.markdown(
                f'<span class="yt-pill no">Not Connected</span>',
                unsafe_allow_html=True,
            )
            render_connect_button(channel_folder, channel_folder_path, config, key=f"{channel_folder}_connect_settings")


# ============================================================
# Client ID / Secret dikhana + update
# ============================================================
def _render_credentials(channel_folder, channel_folder_path, config):
    with theme.card():
        st.markdown("**OAuth Credentials**")
        with st.form(key=f"{channel_folder}_creds_form"):
            client_id = st.text_input("Client ID", value=config.get("client_id", ""))
            client_secret = st.text_input("Client Secret", value=config.get("client_secret", ""), type="password")
            submitted = st.form_submit_button("💾 Credentials Save Karo")
            if submitted:
                channel_manager.update_channel_credentials(channel_folder, client_id, client_secret)
                st.success("Credentials update ho gaye.")
                st.rerun()


# ============================================================
# Delete channel -- confirmation checkbox ke bina button disabled
# ============================================================
def _render_danger_zone(channel_folder, channel_folder_path, config):
    with theme.card():
        st.markdown(f"**⚠️ Danger Zone**")
        st.caption(f"Ye {config.get('channel_name')} channel ka config, token aur cached data hamesha ke liye delete kar dega.")

        confirm_key = f"{channel_folder}_delete_confirm"
        confirmed = st.checkbox("Haan, mujhe pata hai ye permanent hai — delete karo", key=confirm_key)

        if st.button("🗑️ Channel Delete Karo", key=f"{channel_folder}_delete_btn", disabled=not confirmed):
            channel_manager.delete_channel(channel_folder)
            st.session_state["active_channel_deleted"] = channel_folder
            st.rerun()
