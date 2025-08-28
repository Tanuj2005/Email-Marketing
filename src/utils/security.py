import secrets
import hashlib
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from .config import SECRET_KEY

class SecurityManager:
    def __init__(self):
        self.key = self._derive_key(SECRET_KEY.encode())
        self.fernet = Fernet(self.key)
    
    def _derive_key(self, password: bytes) -> bytes:
        """Derive a Fernet key from password"""
        salt = b'oauth_salt_12345'  # In production, use random salt per encryption
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt sensitive tokens"""
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt sensitive tokens"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()
    
    def hash_user_id(self, email: str) -> str:
        """Create a hashed user ID from email"""
        return hashlib.sha256(f"{email}{SECRET_KEY}".encode()).hexdigest()
    
    def generate_session_id(self) -> str:
        """Generate a secure session ID as UUID"""
        return str(uuid.uuid4())

security = SecurityManager()