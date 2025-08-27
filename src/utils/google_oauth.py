import os, secrets, urllib.parse, httpx, time
from typing import Tuple, Dict
from .config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    OAUTH_SCOPES,
)

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# In-memory state & token store (replace with DB/redis in production)
_state_store: Dict[str, float] = {}
_token_store: Dict[str, Dict] = {}

STATE_TTL_SECONDS = 600

def build_authorization_url() -> Tuple[str, str]:
    state = secrets.token_urlsafe(24)
    _state_store[state] = time.time()
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(OAUTH_SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
        "state": state,
    }
    url = f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"
    return url, state

def _validate_state(state: str) -> bool:
    ts = _state_store.get(state)
    if not ts:
        return False
    if time.time() - ts > STATE_TTL_SECONDS:
        _state_store.pop(state, None)
        return False
    # one-time use
    _state_store.pop(state, None)
    return True

async def exchange_code_for_tokens(code: str) -> Dict:
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(TOKEN_ENDPOINT, data=data)
    resp.raise_for_status()
    token_data = resp.json()
    # Optionally store by some key (e.g., user id). Here we just keep last.
    _token_store["last"] = token_data
    return token_data

def get_last_tokens() -> Dict | None:
    return _token_store.get("last")

def verify_state(state: str) -> bool:
    return _validate_state(state)