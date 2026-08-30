"""
video_scraper.py
=================
TikTok video scraping ENGINE. "Profile Adder" tab jo profiles save
karta hai (tiktok_profiles list config.json mein), unhi profiles ki
videos yahan se scrape/download hoti hain.

Duplicate-prevention, folder-structure, aur sab persistent state ka
logic isi file mein hai. UI (channel_features/scraper.py) sirf isko
call karta hai -- koi bhi file seedha yt_dlp ya folder-writes na kare.

STORAGE:
--------
channels/<channel_folder>/Videos/<profile_name>/<safe_title>.<ext>
channels/<channel_folder>/scrape_state.json
    {
      "memepremeo": {
        "scraped_video_ids": ["111", "222", "333"],
        "last_scraped_video_id": "333",
        "last_scrape_time": "2026-08-18 05:30"
      }, ...
    }
"""

import json
import os
import re
from datetime import datetime

import yt_dlp

COOKIES_FILE = "cookies.txt"          # project root -- sab profiles ke liye common
VIDEOS_FOLDER_NAME = "Videos"
STATE_FILENAME = "scrape_state.json"
MAX_FILENAME_LEN = 450


# ============================================================
# Paths / filename safety
# ============================================================
def videos_root(channel_folder_path: str) -> str:
    return os.path.join(channel_folder_path, VIDEOS_FOLDER_NAME)


def _safe_folder_name(name: str) -> str:
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return name or "unknown"


def profile_folder(channel_folder_path: str, profile_name: str) -> str:
    return os.path.join(videos_root(channel_folder_path), _safe_folder_name(profile_name))


def sanitize_filename(title: str, max_len: int = MAX_FILENAME_LEN) -> str:
    """Caption/title ko safe filename mein convert karta hai."""
    title = (title or "video").strip()
    title = re.sub(r'[\\/:*?"<>|]', "_", title)   # invalid FS chars
    title = re.sub(r"\s+", " ", title).strip()
    if len(title) > max_len:
        title = title[:max_len].rstrip()
    return title or "video"


# ============================================================
# Video count -- "Total Available Videos" stat card ke liye
# ============================================================
def count_available_videos(channel_folder_path: str) -> int:
    """Videos/ ke andar sab profile-folders milaake total video files ginta hai."""
    root = videos_root(channel_folder_path)
    if not os.path.isdir(root):
        return 0
    total = 0
    for profile_dir in os.listdir(root):
        full = os.path.join(root, profile_dir)
        if os.path.isdir(full):
            total += sum(1 for f in os.listdir(full) if os.path.isfile(os.path.join(full, f)))
    return total


# ============================================================
# Persistent scrape-state (duplicate prevention)
# ============================================================
def _state_path(channel_folder_path: str) -> str:
    return os.path.join(channel_folder_path, STATE_FILENAME)


def load_scrape_state(channel_folder_path: str) -> dict:
    path = _state_path(channel_folder_path)
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_scrape_state(channel_folder_path: str, state: dict):
    with open(_state_path(channel_folder_path), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _profile_state(state: dict, profile_name: str) -> dict:
    return state.setdefault(profile_name, {
        "scraped_video_ids": [],
        "last_scraped_video_id": None,
        "last_scrape_time": None,
    })


def reset_profile_state(channel_folder_path: str, profile_name: str):
    """
    Profile ki scraped-video-IDs history clear kar deta hai -- agli
    scrape run par sab videos "naya" treat hongi (min-views filter
    ke hisaab se dobara download hongi). Actual downloaded FILES
    (Videos/<profile>/ ke andar) ko ye function touch nahi karta.
    """
    state = load_scrape_state(channel_folder_path)
    if profile_name in state:
        del state[profile_name]
        save_scrape_state(channel_folder_path, state)


def repair_profile_state(channel_folder_path: str, profile: dict) -> dict:
    """
    SMART repair -- puri history reset NAHI karta. Sirf unhi video IDs ko
    "un-mark" karta hai jinki file actually GAAYAB hai (jaise purane
    filename-collision bug ki wajah se overwrite ho gayi thi). Baaki sab
    (jinki file mojood hai) waise hi "scraped" rehte hain -- dobara
    download nahi hongi.

    Logic: profile ki fresh video list fetch karo, unke titles ko group
    karo (collision-detection), aur har group mein jitni files ACTUALLY
    disk par hain us se zyada IDs "scraped" mark hain to utni IDs ko
    un-mark kar do (arbitrary choice -- konsi exact ID missing thi pata
    nahi chalta, lekin sahi COUNT unmark hoga, jo agli scrape par sahi
    videos khud download kar dega).

    Return: {"checked": n, "unmarked": n} summary.
    """
    state = load_scrape_state(channel_folder_path)
    profile_name = profile["profile_name"]
    p_state = _profile_state(state, profile_name)
    scraped_ids = set(p_state["scraped_video_ids"])

    if not scraped_ids:
        return {"checked": 0, "unmarked": 0}

    dest_folder = profile_folder(channel_folder_path, profile_name)
    existing_files = set(os.listdir(dest_folder)) if os.path.isdir(dest_folder) else set()
    existing_stems = {os.path.splitext(f)[0] for f in existing_files}

    try:
        videos = fetch_profile_videos(profile["channel_id"])
    except Exception:
        return {"checked": 0, "unmarked": 0}

    # sirf un videos ko consider karo jo "scraped" mark hain
    relevant = [v for v in videos if v.get("id") in scraped_ids]

    # title ke hisaab se group karo (collision detect karne ke liye)
    groups: dict[str, list[str]] = {}
    for v in relevant:
        title_key = sanitize_filename(v["title"])
        groups.setdefault(title_key, []).append(v["id"])

    unmarked_total = 0
    for title_key, ids_in_group in groups.items():
        # is title (aur "Title Part 2", "Title Part 3"...) se kitni files disk par hain
        actual_count = sum(
            1 for stem in existing_stems
            if stem == title_key or stem.startswith(f"{title_key} Part ")
        )
        missing_count = len(ids_in_group) - actual_count
        if missing_count > 0:
            for vid in ids_in_group[:missing_count]:
                scraped_ids.discard(vid)
                unmarked_total += 1

    p_state["scraped_video_ids"] = list(scraped_ids)
    save_scrape_state(channel_folder_path, state)

    return {"checked": len(relevant), "unmarked": unmarked_total}


# ============================================================
# Fetch profile's recent videos (list only -- koi download nahi)
# ============================================================
def fetch_profile_videos(channel_id: str) -> list[dict]:
    # EXACT same options as the working demo script -- yt-dlp ka TikTok
    # extractor in extra flags (quiet/no_warnings) se kabhi kabhi ajeeb
    # behave karta hai, isliye minimal pattern hi use karo.
    list_opts = {
        "cookiefile": COOKIES_FILE,
        "extract_flat": False,
        "ignoreerrors": True,
    }
    with yt_dlp.YoutubeDL(list_opts) as ydl:
        info = ydl.extract_info(f"tiktokuser:{channel_id}", download=False)

    entries = (info or {}).get("entries", []) or []
    videos = []
    for entry in entries:
        if entry is None:
            continue
        videos.append({
            "id": entry.get("id"),
            "title": entry.get("title") or "video",
            "views": entry.get("view_count", 0) or 0,
            "url": entry.get("webpage_url") or entry.get("url"),
        })
    return videos


# ============================================================
# Scrape ONE profile -- generator, progress events yield karta hai
# ============================================================
def scrape_profile(channel_folder_path: str, profile: dict, min_views: int, state: dict):
    """
    Events:
      {"event": "listing"}
      {"event": "profile_failed", "error": ...}          -- listing hi fail ho gayi
      {"event": "video_start", "title": ..., "views": ...}
      {"event": "video_done", "status": "downloaded"/"failed", "title": ..., "error"?: ...}
      {"event": "profile_done", "summary": {...}}
    """
    profile_name = profile["profile_name"]
    channel_id = profile["channel_id"]
    p_state = _profile_state(state, profile_name)
    scraped_ids = set(p_state["scraped_video_ids"])

    summary = {"new_found": 0, "downloaded": 0, "skipped": 0, "failed_videos": 0}

    yield {"event": "listing"}
    try:
        videos = fetch_profile_videos(channel_id)
    except Exception as e:
        yield {"event": "profile_failed", "error": str(e)}
        return

    dest_folder = profile_folder(channel_folder_path, profile_name)
    os.makedirs(dest_folder, exist_ok=True)   # Videos/<profile>/ agar nahi hai to ban jayega

    for v in videos:
        vid = v["id"]
        if not vid:
            continue
        if v["views"] < min_views:
            continue  # Minimum Views filter
        if vid in scraped_ids:
            summary["skipped"] += 1
            continue

        summary["new_found"] += 1
        yield {"event": "video_start", "title": v["title"], "views": v["views"]}

        safe_title = sanitize_filename(v["title"])

        # Pehle clean title try karo. Collision hone par (do videos ka
        # caption same truncate ho gaya) "Part 2", "Part 3"... lagao --
        # video ID kabhi bhi filename mein nahi aani.
        existing_names = {os.path.splitext(f)[0] for f in os.listdir(dest_folder)} if os.path.isdir(dest_folder) else set()
        final_name = safe_title
        if final_name in existing_names:
            part_num = 2
            while f"{safe_title} Part {part_num}" in existing_names:
                part_num += 1
            final_name = f"{safe_title} Part {part_num}"

        dl_opts = {
            "outtmpl": os.path.join(dest_folder, f"{final_name}.%(ext)s"),
            "format": "h264_540p_554275/best[vcodec^=h264]/best",
            "cookiefile": COOKIES_FILE,
            "ignoreerrors": True,
            "retries": 5,
            "sleep_interval": 3,
            "max_sleep_interval": 8,
            "windowsfilenames": True,
        }
        try:
            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.download([v["url"]])

            # Video ID turant persist karo -- taake beech mein app crash/close
            # ho jaye to bhi ab tak downloaded videos dobara scrape na hon.
            scraped_ids.add(vid)
            p_state["scraped_video_ids"] = list(scraped_ids)
            p_state["last_scraped_video_id"] = vid
            p_state["last_scrape_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            p_state.setdefault("video_files", {})[vid] = final_name
            save_scrape_state(channel_folder_path, state)

            summary["downloaded"] += 1
            yield {"event": "video_done", "status": "downloaded", "title": v["title"]}
        except Exception as e:
            summary["failed_videos"] += 1
            yield {"event": "video_done", "status": "failed", "title": v["title"], "error": str(e)}

    yield {"event": "profile_done", "summary": summary}

    # Is run mein kitni nayi videos download hui, wo bhi state mein save karo
    # -- "Last Videos Scraped Count" column ke liye (UI overview table)
    p_state["last_run_downloaded"] = summary["downloaded"]
    save_scrape_state(channel_folder_path, state)


# ============================================================
# Scrape MULTIPLE profiles, ek-ek karke (sequential, parallel nahi
# -- rate-limit issues se bachne ke liye)
# ============================================================
def scrape_profiles(channel_folder_path: str, profiles: list[dict], min_views: int):
    """
    Events:
      {"event": "profile_start", "index": i, "total": n, "profile_name": ...}
      video_start / video_done -- scrape_profile se pass-through
      {"event": "profile_result", "profile_name": ..., "status": "Completed"/"Failed", ...}
      {"event": "all_done", "totals": {...}}
    """
    state = load_scrape_state(channel_folder_path)
    total = len(profiles)
    totals = {"processed": 0, "completed": 0, "failed": 0,
              "new_found": 0, "downloaded": 0, "skipped": 0}

    for i, profile in enumerate(profiles, start=1):
        yield {"event": "profile_start", "index": i, "total": total, "profile_name": profile["profile_name"]}

        profile_summary = {"new_found": 0, "downloaded": 0, "skipped": 0, "failed_videos": 0}
        profile_failed = False
        error_msg = None

        for ev in scrape_profile(channel_folder_path, profile, min_views, state):
            if ev["event"] == "profile_failed":
                profile_failed = True
                error_msg = ev["error"]
            elif ev["event"] == "profile_done":
                profile_summary = ev["summary"]
            else:
                yield ev  # listing / video_start / video_done -- UI ko pass through

        totals["processed"] += 1
        if profile_failed:
            totals["failed"] += 1
            yield {"event": "profile_result", "profile_name": profile["profile_name"],
                   "status": "Failed", "error": error_msg}
        else:
            totals["completed"] += 1
            totals["new_found"] += profile_summary["new_found"]
            totals["downloaded"] += profile_summary["downloaded"]
            totals["skipped"] += profile_summary["skipped"]
            yield {"event": "profile_result", "profile_name": profile["profile_name"],
                   "status": "Completed", "summary": profile_summary}

    yield {"event": "all_done", "totals": totals}