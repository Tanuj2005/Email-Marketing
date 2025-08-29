import secrets
import time
import httpx
from typing import Tuple, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
from .config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    OAUTH_SCOPES,
    GOOGLE_AUTH_URI,
    TOKEN_ENDPOINT
)
from .database import db
from .security import security

# In-memory state store for CSRF protection
_state_store: Dict[str, float] = {}
STATE_TTL_SECONDS = 600

class OAuthManager:
    
    def generate_auth_url(self) -> Tuple[str, str]:
        """Generate Google OAuth authorization URL with CSRF protection"""
        # Generate random state for CSRF protection
        state = secrets.token_urlsafe(32)
        _state_store[state] = time.time()
        
        query_params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(OAUTH_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        auth_url = f"{GOOGLE_AUTH_URI}?{urlencode(query_params)}"
        return auth_url, state
    
    def validate_state(self, state: str) -> bool:
        """Validate CSRF state token"""
        ts = _state_store.get(state)
        if not ts:
            return False
        if time.time() - ts > STATE_TTL_SECONDS:
            _state_store.pop(state, None)
            return False
        # One-time use
        _state_store.pop(state, None)
        return True
    
    async def exchange_code_for_tokens(self, code: str) -> Dict:
        """Exchange authorization code for tokens"""
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
        return resp.json()
    
    async def refresh_access_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        data = {
            "refresh_token": refresh_token,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "grant_type": "refresh_token",
        }
        
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(TOKEN_ENDPOINT, data=data)
        resp.raise_for_status()
        return resp.json()
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user info from Google"""
        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers=headers
            )
        resp.raise_for_status()
        return resp.json()
    
    async def store_tokens_and_create_session(self, tokens: Dict, user_email: str) -> str:
        """Store tokens in database and create session"""
        
        # Create or get user
        user_id = security.hash_user_id(user_email)
        
        # Insert or update user using Supabase client
        await db.insert_user(user_id, user_email)
        
        # Calculate expiry times
        access_token_expiry = datetime.utcnow() + timedelta(seconds=int(tokens.get('expires_in', 3600)))
        refresh_token_expiry = datetime.utcnow() + timedelta(days=90) if tokens.get('refresh_token') else None
        
        # Encrypt sensitive tokens
        encrypted_access_token = security.encrypt_token(tokens['access_token'])
        encrypted_refresh_token = security.encrypt_token(tokens['refresh_token']) if tokens.get('refresh_token') else None
        
        # Store tokens using Supabase client
        token_result = await db.insert_oauth_tokens(
            user_id, encrypted_access_token, access_token_expiry, 
            encrypted_refresh_token, refresh_token_expiry, tokens.get('token_type', 'Bearer')
        )
        
        token_id = token_result.get('token_id') or token_result.get('id')
        
        # Create session
        session_id = security.generate_session_id()
        
        await db.insert_session(session_id, user_id, token_id, True)
        
        return session_id
    
    async def get_valid_access_token(self, session_id: str) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        session_info = await db.get_session_info(session_id)
        
        if not session_info:
            return None
        
        # Decrypt tokens
        access_token = security.decrypt_token(session_info['access_token'])
        refresh_token = security.decrypt_token(session_info['refresh_token']) if session_info['refresh_token'] else None
        
        # Check if access token is expired
        access_token_expiry = datetime.fromisoformat(session_info['access_token_expiry'].replace('Z', '+00:00'))
        if datetime.utcnow() > access_token_expiry.replace(tzinfo=None):
            if not refresh_token:
                return None  # Can't refresh without refresh token
            
            # Refresh the token
            try:
                new_tokens = await self.refresh_access_token(refresh_token)
                
                # Update tokens in database
                new_access_token_expiry = datetime.utcnow() + timedelta(seconds=int(new_tokens.get('expires_in', 3600)))
                encrypted_new_access_token = security.encrypt_token(new_tokens['access_token'])
                
                await db.update_access_token(session_info['user_id'], encrypted_new_access_token, new_access_token_expiry)
                
                return new_tokens['access_token']
            except Exception as e:
                # Refresh failed
                return None
        
        return access_token
    
    async def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get session information"""
        session_info = await db.get_session_info(session_id)
        
        if not session_info:
            return None
        
        # Decrypt tokens
        session_info['access_token'] = security.decrypt_token(session_info['access_token'])
        if session_info['refresh_token']:
            session_info['refresh_token'] = security.decrypt_token(session_info['refresh_token'])
        
        return session_info

oauth_manager = OAuthManager()