"""
scraper.py
==========
Data Scraper -- ABHI PLACEHOLDER hai. Future mein sirf isi file
ke andar ka logic replace karna hoga, baaki poori app touch
nahi karni padegi.
"""

import streamlit as st

from core import theme


def render(channel_folder: str, channel_folder_path: str, config: dict):
    theme.feature_head(
        "🕵️", "Data Scraper",
        "Competitors aur trends research karo — jald aa raha hai.",
        pill="Coming Soon", pill_kind="soon",
    )

    with theme.card():
        st.markdown("Ye feature ban jaane par is tarah kaam karega:")
        theme.bullet_list([
            "Competitor channels ke stats scrape karna (subscribers, views, upload frequency)",
            "Trending videos aur tags nikalna",
            "Keyword research — konse keywords zyada search hote hain",
            "Comments aur titles se naye content ideas nikalna",
        ])
