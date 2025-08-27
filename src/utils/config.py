from dotenv import load_dotenv
import os



load_dotenv()



# LLM API Key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")



# Google OAuth2
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_REDIRECT_URL = os.getenv("FRONTEND_REDIRECT_URL")



OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.send",
]



