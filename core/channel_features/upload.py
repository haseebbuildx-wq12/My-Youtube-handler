"""
upload.py
=========
Video Upload -- ABHI PLACEHOLDER hai. Future mein sirf isi file
ke andar ka logic replace karna hoga (YouTube Data API v3
videos.insert call), baaki poori app (tabs, theme, caching
pattern) touch nahi karni padegi. Upload scope already
youtube_auth.py mein authorize ho chuka hai.
"""

import streamlit as st

from core import theme


def render(channel_folder: str, channel_folder_path: str, config: dict):
    theme.feature_head(
        "⬆️", "Video Upload",
        "Seedha is channel par video publish karo — jald aa raha hai.",
        pill="Coming Soon", pill_kind="soon",
    )

    with theme.card():
        st.markdown("Ye feature ban jaane par is tarah kaam karega:")
        theme.bullet_list([
            "Video file select karna (local computer se upload)",
            "Title, description, tags aur category set karna",
            "Custom thumbnail upload karna",
            "Privacy setting choose karna — Public / Unlisted / Private",
            "Scheduling — video ko future date/time par publish karna",
            "Upload YouTube Data API v3 se hoga, is channel ke connected "
            "Google account se (upload permission pehle se authorize hai)",
        ])
