from dotenv import load_dotenv
import os



load_dotenv()



# LLM API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# OAuth Scopes
OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets"
]

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Security
SECRET_KEY = os.getenv("SECRET_KEY")  # For encryption
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Session
SESSION_COOKIE_NAME = "session_id"
SESSION_COOKIE_MAX_AGE = 86400 * 7  # 7 days

# Google Sheets API
GOOGLE_SHEETS_API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
