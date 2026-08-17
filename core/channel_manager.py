"""
channel_manager.py
===================
Channel folders (channels/<naam>/) ka CRUD yahan hota hai:
add_channel, list_channels, load_channel_config, delete_channel.

Kisi bhi UI file ko seedha os.makedirs / json.load nahi karna --
sab isi module ke through.
"""

import json
import os
import re
import shutil
from datetime import datetime

CHANNELS_DIR = "channels"


def _ensure_channels_dir():
    """Root channels/ folder na ho to bana do."""
    os.makedirs(CHANNELS_DIR, exist_ok=True)


def slugify_channel_name(name: str) -> str:
    """
    Channel Name ko safe folder-name mein convert karta hai
    (spaces -> underscore, special chars strip) taake OS crash
    na kare.
    """
    name = name.strip()
    name = re.sub(r"[^\w\s-]", "", name)      # special chars hatao
    name = re.sub(r"[\s]+", "_", name)         # spaces -> underscore
    return name or "channel"


def _unique_folder_name(base_slug: str) -> str:
    """Agar naam already exist karta hai to _2, _3 laga do."""
    _ensure_channels_dir()
    candidate = base_slug
    counter = 2
    while os.path.isdir(os.path.join(CHANNELS_DIR, candidate)):
        candidate = f"{base_slug}_{counter}"
        counter += 1
    return candidate


def list_channels() -> list[str]:
    """
    channels/ ke andar jitne folders hain jinke andar config.json
    hai, unki list deta hai (folder names), created_at ke hisaab
    se sorted (purana pehle).
    """
    _ensure_channels_dir()
    valid = []
    for entry in os.listdir(CHANNELS_DIR):
        folder = os.path.join(CHANNELS_DIR, entry)
        if os.path.isdir(folder) and os.path.isfile(os.path.join(folder, "config.json")):
            valid.append(entry)

    def _created_at(folder_name):
        cfg = load_channel_config(folder_name) or {}
        return cfg.get("created_at", "")

    valid.sort(key=_created_at)
    return valid


def channel_dir(folder_name: str) -> str:
    """Given folder_name, uska full path deta hai."""
    return os.path.join(CHANNELS_DIR, folder_name)


def load_channel_config(folder_name: str) -> dict | None:
    """config.json read karke dict deta hai, na ho to None."""
    path = os.path.join(channel_dir(folder_name), "config.json")
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def add_channel(channel_name: str, client_id: str, client_secret: str) -> str:
    """
    Naya channel folder + config.json banata hai.
    Return: folder_name jo isko diya gaya.
    """
    _ensure_channels_dir()
    base_slug = slugify_channel_name(channel_name)
    folder_name = _unique_folder_name(base_slug)
    folder_path = channel_dir(folder_name)
    os.makedirs(folder_path, exist_ok=True)

    config = {
        "channel_name": channel_name.strip(),
        "client_id": client_id.strip(),
        "client_secret": client_secret.strip(),
        "created_at": datetime.now().strftime("%d %b %Y"),
    }
    with open(os.path.join(folder_path, "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return folder_name


def update_channel_credentials(folder_name: str, client_id: str, client_secret: str):
    """Settings tab se client_id/secret update karne ke liye."""
    config = load_channel_config(folder_name)
    if config is None:
        return
    config["client_id"] = client_id.strip()
    config["client_secret"] = client_secret.strip()
    with open(os.path.join(channel_dir(folder_name), "config.json"), "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def delete_channel(folder_name: str):
    """Poora channel folder (config, token, cache) delete kar deta hai."""
    folder_path = channel_dir(folder_name)
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
