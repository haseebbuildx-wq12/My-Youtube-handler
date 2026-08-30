"""
uploader.py
============
Video Upload Scheduler ENGINE. Scraper se independent hai:

    Scraper:  Profile -> Scrape -> Videos/<profile>/
    Uploader: Videos/<profile>/ -> pick eligible -> upload -> delete on success

STORAGE (per channel folder):
------------------------------
channels/<channel_folder>/upload_schedule.json
    {
      "active": true,
      "source_profile": "Random",
      "default_name": "| Netflix Series",
      "default_description": "...",
      "default_tags": "Netflix, Series",
      "visibility": "public",
      "videos_per_day": 5,
      "times": ["09:00", "12:00", "15:00", "18:00", "21:00"]
    }

channels/<channel_folder>/upload_history.json
    [ {scheduled_time, actual_time, profile, filename, title,
       status, error, video_id, file_deleted}, ... ]

SCHEDULER:
----------
Ek background daemon thread PER CHANNEL chalti hai (jab tak Streamlit
process zinda hai). Thread start hote hi "startup catch-up" karti hai:
aaj ke jo slots session-start se PEHLE guzar chuke the (aur unka koi
history record nahi hai) unhe turant "Skipped -- Scheduler was offline"
mark kar deti hai. Uske baad har future slot ka wait karti hai aur us
waqt automatically upload karti hai -- user ko koi button dabana nahi
padta.
"""

import json
import os
import random
import threading
import time
from datetime import datetime, timedelta

from core import youtube_auth
from core import video_scraper

try:
    from googleapiclient.discovery import build as _yt_build
    from googleapiclient.http import MediaFileUpload
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

SCHEDULE_FILENAME = "upload_schedule.json"
HISTORY_FILENAME = "upload_history.json"

DEFAULT_SCHEDULE = {
    "active": False,
    "source_profile": "Random",
    "default_name": "",
    "default_description": "",
    "default_tags": "",
    "visibility": "public",
    "videos_per_day": 5,
    "times": ["09:00", "12:00", "15:00", "18:00", "21:00"],
}


# ============================================================
# Schedule config -- load / save
# ============================================================
def _schedule_path(channel_folder_path: str) -> str:
    return os.path.join(channel_folder_path, SCHEDULE_FILENAME)


def load_schedule(channel_folder_path: str) -> dict:
    path = _schedule_path(channel_folder_path)
    if not os.path.isfile(path):
        return dict(DEFAULT_SCHEDULE)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = dict(DEFAULT_SCHEDULE)
    merged.update(data)
    return merged


def save_schedule(channel_folder_path: str, config: dict):
    with open(_schedule_path(channel_folder_path), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ============================================================
# Upload history -- persistent, permanent record
# ============================================================
def _history_path(channel_folder_path: str) -> str:
    return os.path.join(channel_folder_path, HISTORY_FILENAME)


def load_history(channel_folder_path: str) -> list[dict]:
    path = _history_path(channel_folder_path)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _append_history(channel_folder_path: str, record: dict):
    history = load_history(channel_folder_path)
    history.append(record)
    with open(_history_path(channel_folder_path), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


# ============================================================
# Profiles / eligible-video selection
# ============================================================
def list_available_profiles(channel_folder_path: str) -> list[str]:
    """Videos/ ke andar jitne profile-folders hain, unki list."""
    root = video_scraper.videos_root(channel_folder_path)
    if not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))


def pick_eligible_video(channel_folder_path: str, source_profile: str):
    """
    Ek eligible video chunta hai. Files khud hi "not yet uploaded" hain
    -- kyunki successful upload ke baad file DELETE ho jati hai (Golden
    Rule), folder mein jo bhi bacha hai wo automatically eligible hai.
    Return: (profile_name, filepath) ya (None, None).
    """
    profiles = list_available_profiles(channel_folder_path)
    if source_profile != "Random":
        profiles = [p for p in profiles if p == source_profile]

    random.shuffle(profiles)
    for profile in profiles:
        folder = os.path.join(video_scraper.videos_root(channel_folder_path), profile)
        if not os.path.isdir(folder):
            continue
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        if files:
            return profile, os.path.join(folder, files[0])
    return None, None


def profile_stats(channel_folder_path: str) -> list[dict]:
    """Har profile ka Uploaded (history se) + Ready to Upload (folder se)."""
    history = load_history(channel_folder_path)
    uploaded_counts = {}
    for rec in history:
        if rec.get("status") == "Successfully Uploaded" and rec.get("profile"):
            uploaded_counts[rec["profile"]] = uploaded_counts.get(rec["profile"], 0) + 1

    rows = []
    for profile in list_available_profiles(channel_folder_path):
        folder = os.path.join(video_scraper.videos_root(channel_folder_path), profile)
        ready = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]) if os.path.isdir(folder) else 0
        rows.append({
            "Profile": profile,
            "Uploaded": uploaded_counts.get(profile, 0),
            "Ready to Upload": ready,
        })
    return rows


def build_title(filename: str, default_name: str) -> str:
    """Filename (bina extension) + Default Name (jaisa likha waisa hi, bina koi extra separator)."""
    stem = os.path.splitext(filename)[0]
    default_name = (default_name or "").strip()
    if default_name:
        return f"{stem} {default_name}".strip()
    return stem


# ============================================================
# YouTube Data API v3 upload
# ============================================================
def upload_to_youtube(channel_folder_path: str, filepath: str, title: str,
                       description: str, tags: str, visibility: str) -> str:
    if not GOOGLE_API_AVAILABLE:
        raise RuntimeError(
            "google-api-python-client install nahi hai. "
            "Terminal mein: pip install google-api-python-client"
        )
    creds = youtube_auth.load_credentials(channel_folder_path)
    if creds is None:
        raise RuntimeError("Ye channel Google se connected nahi hai -- Settings tab se pehle connect karo.")

    youtube = _yt_build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": title[:100],  # YouTube ka title max length 100 chars
            "description": description or "",
            "tags": [t.strip() for t in tags.split(",") if t.strip()] if tags else [],
            "categoryId": "22",  # People & Blogs -- default, chaho to badal sakte ho
        },
        "status": {"privacyStatus": visibility},
    }
    media = MediaFileUpload(filepath, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _status, response = request.next_chunk()
    return response["id"]


# ============================================================
# SCHEDULER -- background thread, per channel
# ============================================================
_scheduler_threads: dict[str, threading.Thread] = {}
_scheduler_lock = threading.Lock()


def ensure_scheduler(channel_folder: str, channel_folder_path: str):
    """
    Idempotent -- ek hi background thread per channel chalti hai.
    Streamlit reruns par (jab bhi page reload/interact ho) dobara call
    hoti hai, lekin agar thread pehle se zinda hai to kuch nahi hota.
    """
    with _scheduler_lock:
        existing = _scheduler_threads.get(channel_folder_path)
        if existing and existing.is_alive():
            return
        t = threading.Thread(
            target=_scheduler_loop,
            args=(channel_folder, channel_folder_path),
            daemon=True,
        )
        _scheduler_threads[channel_folder_path] = t
        t.start()


def is_scheduler_running(channel_folder_path: str) -> bool:
    t = _scheduler_threads.get(channel_folder_path)
    return bool(t and t.is_alive())


def _today_slot_datetimes(times_list: list[str], on_date) -> list[datetime]:
    result = []
    for t_str in times_list:
        try:
            hh, mm = map(int, t_str.split(":"))
            result.append(datetime(on_date.year, on_date.month, on_date.day, hh, mm))
        except Exception:
            continue
    return sorted(result)


def _already_recorded(history: list[dict], scheduled_dt: datetime) -> bool:
    tag = scheduled_dt.strftime("%Y-%m-%d %H:%M")
    return any(rec.get("scheduled_time") == tag for rec in history)


def _startup_catchup(channel_folder_path: str, session_start: datetime):
    """App start hote hi -- aaj ke jo slots guzar chuke hain (aur unka
    record nahi hai), unhe turant 'Skipped -- offline' mark karo."""
    config = load_schedule(channel_folder_path)
    today_slots = _today_slot_datetimes(config.get("times", []), session_start.date())
    for slot in today_slots:
        history = load_history(channel_folder_path)
        if slot < session_start and not _already_recorded(history, slot):
            _append_history(channel_folder_path, {
                "scheduled_time": slot.strftime("%Y-%m-%d %H:%M"),
                "actual_time": session_start.strftime("%Y-%m-%d %H:%M:%S"),
                "profile": None,
                "filename": None,
                "title": None,
                "status": "Skipped — Scheduler was offline at the scheduled time",
                "error": None,
                "video_id": None,
                "file_deleted": False,
            })


def _next_upcoming_slot(channel_folder_path: str, session_start: datetime):
    config = load_schedule(channel_folder_path)
    history = load_history(channel_folder_path)
    now = datetime.now()

    today_slots = _today_slot_datetimes(config.get("times", []), now.date())
    for slot in today_slots:
        if slot >= session_start and not _already_recorded(history, slot):
            return slot

    check_date = now.date() + timedelta(days=1)
    for _ in range(7):  # safety cap
        day_slots = _today_slot_datetimes(config.get("times", []), check_date)
        if day_slots:
            return day_slots[0]
        check_date += timedelta(days=1)
    return None


def _attempt_upload_slot(channel_folder_path: str, scheduled_dt: datetime):
    config = load_schedule(channel_folder_path)
    profile, filepath = pick_eligible_video(channel_folder_path, config.get("source_profile", "Random"))

    record = {
        "scheduled_time": scheduled_dt.strftime("%Y-%m-%d %H:%M"),
        "actual_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "profile": profile,
        "filename": None,
        "title": None,
        "status": None,
        "error": None,
        "video_id": None,
        "file_deleted": False,
    }

    if not filepath:
        record["status"] = "Skipped — No eligible video available"
        _append_history(channel_folder_path, record)
        return

    filename = os.path.basename(filepath)
    title = build_title(filename, config.get("default_name", ""))
    record["filename"] = filename
    record["title"] = title

    try:
        video_id = upload_to_youtube(
            channel_folder_path, filepath, title,
            config.get("default_description", ""),
            config.get("default_tags", ""),
            config.get("visibility", "public"),
        )
        record["status"] = "Successfully Uploaded"
        record["video_id"] = video_id
        os.remove(filepath)  # GOLDEN RULE -- sirf SUCCESS ke baad delete
        record["file_deleted"] = True
    except Exception as e:
        record["status"] = "Upload Failed"
        record["error"] = str(e)
        record["file_deleted"] = False  # retry ke liye file safe rehti hai

    _append_history(channel_folder_path, record)


def _scheduler_loop(channel_folder: str, channel_folder_path: str):
    session_start = datetime.now()
    _startup_catchup(channel_folder_path, session_start)

    while True:
        config = load_schedule(channel_folder_path)
        if not config.get("active"):
            time.sleep(30)
            continue

        nxt = _next_upcoming_slot(channel_folder_path, session_start)
        if nxt is None:
            time.sleep(60)
            continue

        wait_seconds = (nxt - datetime.now()).total_seconds()
        if wait_seconds > 1:
            time.sleep(min(wait_seconds, 60))  # har 60s config-changes ke liye check karo
            continue

        _attempt_upload_slot(channel_folder_path, nxt)
        time.sleep(2)
