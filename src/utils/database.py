import asyncio
import os
import uuid
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from .config import SUPABASE_URL, SUPABASE_KEY
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseClient:
    def __init__(self):
        # Create Supabase client
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info(f"Supabase client initialized for: {SUPABASE_URL}")
    
    async def execute_query(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        logger.info(f"Executing query: {query}")
        logger.info(f"With args: {args}")
        
        try:
            # Use Supabase RPC for custom queries
            result = self.client.rpc('execute_sql', {'sql_query': query, 'params': list(args)})
            
            if result.data:
                logger.info(f"Query result: {result.data}")
                return result.data
            else:
                logger.warning(f"Query returned no data: {result}")
                return []
                
        except Exception as e:
            logger.error(f"Database query error: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Args: {args}")
            raise
    
    async def execute_command(self, command: str, *args) -> str:
        """Execute an INSERT/UPDATE/DELETE command"""
        logger.info(f"Executing command: {command}")
        logger.info(f"With args: {args}")
        
        try:
            # Use Supabase RPC for custom commands
            result = self.client.rpc('execute_sql', {'sql_query': command, 'params': list(args)})
            
            logger.info(f"Command result: {result}")
            return str(result)
            
        except Exception as e:
            logger.error(f"Database command error: {e}")
            logger.error(f"Command: {command}")
            logger.error(f"Args: {args}")
            raise
    
    # Helper methods for common operations using Supabase client
    async def insert_user(self, user_id: str, email: str) -> Dict[str, Any]:
        """Insert or update user using Supabase client"""
        try:
            result = self.client.table('users').upsert({
                'user_id': user_id,
                'email': email
            }, on_conflict='email').execute()
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting user: {e}")
            raise
    
    async def insert_oauth_tokens(self, user_id: str, access_token: str, 
                                access_token_expiry, refresh_token: str = None,
                                refresh_token_expiry=None, token_type: str = 'Bearer') -> Dict[str, Any]:
        """Insert OAuth tokens using Supabase client"""
        try:
            token_data = {
                'user_id': user_id,
                'access_token': access_token,
                'access_token_expiry': access_token_expiry.isoformat(),
                'token_type': token_type
            }
            
            if refresh_token:
                token_data['refresh_token'] = refresh_token
            if refresh_token_expiry:
                token_data['refresh_token_expiry'] = refresh_token_expiry.isoformat()
            
            result = self.client.table('oauth_tokens').insert(token_data).execute()
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting OAuth tokens: {e}")
            raise
    
    async def update_access_token(self, user_id: str, access_token: str, access_token_expiry) -> bool:
        """Update access token for a user"""
        try:
            result = self.client.table('oauth_tokens').update({
                'access_token': access_token,
                'access_token_expiry': access_token_expiry.isoformat()
            }).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error updating access token: {e}")
            raise
    
    async def insert_session(self, session_id: str, user_id: str, token_id: int, is_active: bool = True) -> Dict[str, Any]:
        """Insert session using Supabase client"""
        try:
            # Ensure session_id is a valid UUID string
            if not self._is_valid_uuid(session_id):
                session_id = str(uuid.uuid4())
                logger.warning(f"Invalid UUID provided, generated new one: {session_id}")
            
            result = self.client.table('sessions').insert({
                'session_id': session_id,
                'user_id': user_id,
                'token_id': token_id,
                'is_active': is_active
            }).execute()
            
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error(f"Error inserting session: {e}")
            raise
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information using Supabase client"""
        try:
            result = self.client.table('sessions').select(
                """
                session_id,
                user_id,
                is_active,
                users!inner(email),
                oauth_tokens!inner(access_token, refresh_token, access_token_expiry, token_type)
                """
            ).eq('session_id', session_id).eq('is_active', True).execute()
            
            if result.data:
                row = result.data[0]
                return {
                    'session_id': row['session_id'],
                    'user_id': row['user_id'],
                    'email': row['users']['email'],
                    'access_token': row['oauth_tokens']['access_token'],
                    'refresh_token': row['oauth_tokens']['refresh_token'],
                    'access_token_expiry': row['oauth_tokens']['access_token_expiry'],
                    'token_type': row['oauth_tokens']['token_type']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting session info: {e}")
            raise
    
    async def deactivate_session(self, session_id: str) -> bool:
        """Deactivate session using Supabase client"""
        try:
            result = self.client.table('sessions').update({
                'is_active': False
            }).eq('session_id', session_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error deactivating session: {e}")
            raise
    
    async def test_connection(self):
        """Test database connection"""
        try:
            # Simple test query
            result = self.client.table('users').select('count').execute()
            logger.info("Supabase connection successful!")
            return True
        except Exception as e:
            logger.error(f"Supabase connection failed: {e}")
            return False

db = SupabaseClient()