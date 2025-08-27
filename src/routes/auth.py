from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from ..utils.google_oauth import build_authorization_url, exchange_code_for_tokens, verify_state
from ..utils.config import FRONTEND_REDIRECT_URL

router = APIRouter(tags=["auth"])

@router.get("/login")
async def login():
    auth_url, state = build_authorization_url()
    # Frontend can redirect user there; returns both for flexibility
    return {"authorization_url": auth_url, "state": state}

@router.get("/callback")
async def callback(code: str = Query(...), state: str = Query(...)):
    if not verify_state(state):
        raise HTTPException(status_code=400, detail="Invalid or expired state")
    try:
        await exchange_code_for_tokens(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {e}")
    # Redirect back to frontend (could append success flag)
    redirect_url = f"{FRONTEND_REDIRECT_URL}?success=1"
    return RedirectResponse(url=redirect_url, status_code=302)