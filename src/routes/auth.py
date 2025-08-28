from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from ..utils.oauth import oauth_manager
from ..utils.config import FRONTEND_URL, SESSION_COOKIE_NAME, SESSION_COOKIE_MAX_AGE

router = APIRouter()

@router.get("/login")
async def login():
    """Generate OAuth authorization URL"""
    try:
        auth_url, state = oauth_manager.generate_auth_url()
        return JSONResponse({
            "auth_url": auth_url,
            "state": state
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate auth URL: {str(e)}")

@router.get("/callback")
async def oauth_callback(request: Request, response: Response):
    """Handle OAuth callback and create session"""
    try:
        # Get query parameters
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        
        # Check for OAuth errors
        if error:
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state parameter")
        
        # Validate CSRF state
        if not oauth_manager.validate_state(state):
            raise HTTPException(status_code=400, detail="Invalid or expired state parameter")
        
        # Exchange code for tokens
        tokens = await oauth_manager.exchange_code_for_tokens(code)
        
        # Get user info
        user_info = await oauth_manager.get_user_info(tokens['access_token'])
        user_email = user_info['email']
        
        # Store tokens and create session
        session_id = await oauth_manager.store_tokens_and_create_session(tokens, user_email)
        
        # Create secure session cookie
        response = RedirectResponse(url=f"{FRONTEND_URL}/dashboard")
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_id,
            max_age=SESSION_COOKIE_MAX_AGE,
            httponly=True,
            secure=True,  # Only over HTTPS
            samesite="lax"
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        # Redirect to frontend with error
        return RedirectResponse(url=f"{FRONTEND_URL}/error?message={str(e)}")

@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user and invalidate session"""
    try:
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if session_id:
            # Invalidate session in database using the proper method
            from ..utils.database import db
            await db.deactivate_session(session_id)
        
        # Clear cookie
        response = JSONResponse({"message": "Logged out successfully"})
        response.delete_cookie(key=SESSION_COOKIE_NAME)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")

@router.get("/me")
async def get_current_user(request: Request):
    """Get current user info from session"""
    try:
        session_id = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_id:
            raise HTTPException(status_code=401, detail="No session found")
        
        session_info = await oauth_manager.get_session_info(session_id)
        if not session_info:
            raise HTTPException(status_code=401, detail="Invalid session")
        
        return {
            "user_id": session_info['user_id'],
            "email": session_info['email'],
            "session_id": session_info['session_id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user info: {str(e)}")