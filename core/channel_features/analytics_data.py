"""
analytics_data.py
==================
DATA-LAYER sirf yahan hai -- koi UI code nahi. analytics.py sirf
in functions ko call karta hai aur result render karta hai.

- fetch_channel_overview()   -> subscribers/views/video count (real)
- fetch_daily_analytics()    -> per-day views + subs gained/lost (real)
- fetch_all_videos()         -> saari videos ki list + stats (real, batched)
- fetch_mock_data()          -> bina connect kiye demo data
- load_cache() / save_cache()-> channels/<naam>/analytics_cache.json
"""

import json
import os
import random
from datetime import datetime, timedelta

from googleapiclient.discovery import build

CACHE_FILENAME = "analytics_cache.json"
DEFAULT_RANGE_MONTHS = 2  # by default sirf pichle 2 mahine ka data fetch hota hai


# ============================================================
# CACHE (channels/<naam>/analytics_cache.json)
# ============================================================
def _cache_path(channel_folder_path: str) -> str:
    return os.path.join(channel_folder_path, CACHE_FILENAME)


def load_cache(channel_folder_path: str) -> dict | None:
    path = _cache_path(channel_folder_path)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cache(channel_folder_path: str, data: dict):
    data["last_updated"] = datetime.now().strftime("%d %b %Y, %I:%M %p")
    with open(_cache_path(channel_folder_path), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_daily_into_cache(channel_folder_path: str, new_daily: dict):
    """
    Naya date-range fetch hua daily data purane cache ke 'daily' dict
    mein merge kar deta hai (taake ek baar fetch kiya mahina dobara
    quota na khaye jab user usi mahine par wapas aaye).
    """
    cache = load_cache(channel_folder_path) or {}
    daily = cache.get("daily", {})
    daily.update(new_daily)
    cache["daily"] = daily
    save_cache(channel_folder_path, cache)
    return cache


# ============================================================
# REAL API -- Channel overview (subscribers / views / videos)
# ============================================================
def fetch_channel_overview(creds) -> dict:
    youtube = build("youtube", "v3", credentials=creds)
    resp = youtube.channels().list(part="snippet,statistics", mine=True).execute()
    items = resp.get("items", [])
    if not items:
        return {}
    item = items[0]
    stats = item.get("statistics", {})
    return {
        "channel_id": item.get("id"),
        "title": item.get("snippet", {}).get("title", ""),
        "subscribers": int(stats.get("subscriberCount", 0)),
        "total_views": int(stats.get("viewCount", 0)),
        "total_videos": int(stats.get("videoCount", 0)),
    }


# ============================================================
# REAL API -- Daily views + subscribers gained/lost
# (YouTube Analytics API v2, quota-cheap: ek hi call poore range ke liye)
# ============================================================
def fetch_daily_analytics(creds, channel_id: str, start_date: str, end_date: str) -> dict:
    """
    start_date/end_date format: 'YYYY-MM-DD'
    Return: {"2026-06-01": {"views": 120, "subs_change": 3}, ...}
    """
    yt_analytics = build("youtubeAnalytics", "v2", credentials=creds)
    resp = yt_analytics.reports().query(
        ids=f"channel=={channel_id}",
        startDate=start_date,
        endDate=end_date,
        metrics="views,subscribersGained,subscribersLost",
        dimensions="day",
    ).execute()

    daily = {}
    for row in resp.get("rows", []):
        day, views, gained, lost = row
        daily[day] = {"views": int(views), "subs_change": int(gained) - int(lost)}
    return daily


# ============================================================
# REAL API -- Saari videos ki list (title, views, likes, comments)
# Quota-friendly: playlistItems se video IDs nikalte hain, phir
# videos.list ko 50-50 ke BATCH mein call karte hain (poore
# channel ke liye ek-ek video call karne ke bajaye).
# ============================================================
def fetch_all_videos(creds, channel_id: str) -> list[dict]:
    youtube = build("youtube", "v3", credentials=creds)

    # Channel ki "uploads" playlist ID nikalo
    ch_resp = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    items = ch_resp.get("items", [])
    if not items:
        return []
    uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # Uploads playlist se saari video IDs nikalo (pagination)
    video_ids = []
    page_token = None
    while True:
        pl_resp = youtube.playlistItems().list(
            part="contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=50,
            pageToken=page_token,
        ).execute()
        video_ids.extend(i["contentDetails"]["videoId"] for i in pl_resp.get("items", []))
        page_token = pl_resp.get("nextPageToken")
        if not page_token:
            break

    # Stats 50-50 ke batch mein fetch karo (quota-efficient)
    videos = []
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i + 50]
        v_resp = youtube.videos().list(
            part="snippet,statistics",
            id=",".join(batch_ids),
        ).execute()
        for v in v_resp.get("items", []):
            stats = v.get("statistics", {})
            videos.append({
                "title": v.get("snippet", {}).get("title", "Untitled"),
                "views": int(stats.get("viewCount", 0)),
                "likes": int(stats.get("likeCount", 0)),
                "comments": int(stats.get("commentCount", 0)),
            })

    return videos


# ============================================================
# MOCK DATA -- bina connect kiye realistic demo (testing/preview)
# ============================================================
def fetch_mock_data(months: int = DEFAULT_RANGE_MONTHS) -> dict:
    random.seed(42)  # taake demo data har baar consistent rahe

    today = datetime.now()
    start = today - timedelta(days=months * 30)

    daily = {}
    day = start
    while day <= today:
        key = day.strftime("%Y-%m-%d")
        views = random.randint(50, 4500)
        subs_change = random.randint(-15, 40)
        daily[key] = {"views": views, "subs_change": subs_change}
        day += timedelta(days=1)

    video_titles = [
        "Kaise Banayein Perfect Thumbnail?", "Ye Trick Views 10x Kar Degi",
        "Vlog: Ek Din Studio Mein", "Top 5 Editing Software 2026",
        "Live Q&A Highlights", "Behind The Scenes",
        "Tutorial: Beginners Guide", "Reaction Video Special",
        "Collab With Friends", "Shorts Compilation #12",
    ]
    videos = [
        {
            "title": t,
            "views": random.randint(500, 250000),
            "likes": random.randint(20, 15000),
            "comments": random.randint(2, 900),
        }
        for t in video_titles
    ]

    overview = {
        "title": "Demo Channel",
        "subscribers": sum(d["subs_change"] for d in daily.values()) + 12000,
        "total_views": sum(d["views"] for d in daily.values()),
        "total_videos": len(videos),
    }

    return {"overview": overview, "daily": daily, "videos": videos, "is_mock": True}
