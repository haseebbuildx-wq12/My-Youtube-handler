"""
youtube_auth.py
================
Har channel apne khud ke client_id/client_secret se apna Google
account authorize karta hai.

IMPORTANT -- DEPLOYMENT NOTE:
------------------------------
Ye flow REDIRECT-BASED hai (InstalledAppFlow.run_local_server() nahi
use kiya), taake LOCAL machine aur CLOUD deployment dono pe bina code
badle kaam kare. Bas neeche REDIRECT_URI ek jagah set karo:

  - Local testing:  http://localhost:8501
  - Cloud deploy:   apni deployed app ki actual URL
                     (e.g. https://my-app.streamlit.app)

Google Cloud Console -> OAuth Client (Web application type) mein
ye SAME URI "Authorized redirect URIs" mein add karna zaroori hai,
warna "redirect_uri_mismatch" error aayega.

Flow: user "Connect with Google" dabata hai -> Google consent screen
par jata hai -> wapas isi app pe redirect hota hai with ?code=...
-> hum us code ko token mein exchange karke channel folder mein
token.json save kar dete hain.
"""

import json
import os

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

# Deployment ke waqt sirf isi ek line ko update karna hai.
REDIRECT_URI = os.environ.get("YOUTUBE_REDIRECT_URI", "http://localhost:8501")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.upload",  # future Video Upload feature ke liye
]

TOKEN_FILENAME = "token.json"


def _client_config(client_id: str, client_secret: str) -> dict:
    """Google client library ko chahiye is shape ka dict (client_secret.json jaisa)."""
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [REDIRECT_URI],
        }
    }


def build_flow(client_id: str, client_secret: str) -> Flow:
    """Ek naya OAuth Flow object banata hai given channel credentials se."""
    flow = Flow.from_client_config(
        _client_config(client_id, client_secret),
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
        autogenerate_code_verifier=False,
    )
    return flow


def get_authorization_url(flow: Flow, state: str | None = None) -> tuple[str, str]:
    """Consent-screen URL + state token deta hai."""
    kwargs = dict(
        access_type="offline",       # refresh_token bhi milega
        include_granted_scopes="true",
        prompt="consent",
    )
    if state:
        kwargs["state"] = state
    auth_url, state = flow.authorization_url(**kwargs)
    return auth_url, state


def exchange_code_for_credentials(flow: Flow, authorization_code: str) -> Credentials:
    """Google se mila 'code' ko access/refresh token mein exchange karta hai."""
    flow.fetch_token(code=authorization_code)
    return flow.credentials


def _token_path(channel_folder_path: str) -> str:
    return os.path.join(channel_folder_path, TOKEN_FILENAME)


def save_credentials(channel_folder_path: str, creds: Credentials):
    """token.json channel ke folder mein save karta hai."""
    data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }
    with open(_token_path(channel_folder_path), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_credentials(channel_folder_path: str) -> Credentials | None:
    """
    token.json se Credentials load karta hai. Agar expire ho gaya ho
    to auto-refresh karke wapas save bhi kar deta hai. Refresh fail
    ho jaye (revoke/expire) to None deta hai -- caller "Not Connected"
    dikhaye, crash na ho.
    """
    token_path = _token_path(channel_folder_path)
    if not os.path.isfile(token_path):
        return None

    with open(token_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    creds = Credentials(
        token=data.get("token"),
        refresh_token=data.get("refresh_token"),
        token_uri=data.get("token_uri"),
        client_id=data.get("client_id"),
        client_secret=data.get("client_secret"),
        scopes=data.get("scopes"),
    )

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            save_credentials(channel_folder_path, creds)
        except Exception:
            # Refresh token revoke/expire ho chuka -- reconnect chahiye
            return None

    return creds


def is_connected(channel_folder_path: str) -> bool:
    """Settings/Analytics tab mein connection status dikhane ke liye."""
    return load_credentials(channel_folder_path) is not None


def disconnect(channel_folder_path: str):
    """token.json delete kar deta hai -- channel dobara connect kar sake."""
    token_path = _token_path(channel_folder_path)
    if os.path.isfile(token_path):
        os.remove(token_path)
