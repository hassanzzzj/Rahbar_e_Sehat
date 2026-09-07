"""
Security utilities including authentication, hashing, and encryption helpers.
Implements JWT-based auth, password hashing, and field-level encryption for PII.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.core.exceptions import AuthenticationError

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityManager:
    """Manages security operations including JWT, hashing, and encryption."""

    def __init__(self) -> None:
        settings = get_settings()
        self.jwt_secret = settings.jwt_secret_key
        self.jwt_algorithm = settings.jwt_algorithm
        self.jwt_expiration_hours = settings.jwt_expiration_hours
        self.encryption_key = settings.encryption_key.encode()
        self._fernet = Fernet(self.encryption_key)

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(hours=self.jwt_expiration_hours)
        )
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)

    def decode_access_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate a JWT access token."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
            )
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}") from e

    def encrypt_field(self, plaintext: str) -> str:
        """Encrypt a sensitive field using Fernet symmetric encryption."""
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt_field(self, ciphertext: str) -> str:
        """Decrypt a sensitive field using Fernet symmetric encryption."""
        return self._fernet.decrypt(ciphertext.encode()).decode()

    def generate_session_token(self, phone_number: str) -> str:
        """
        Generate a tokenized session identifier from phone number.
        This decouples PII from clinical data in storage.
        """
        import hashlib
        import secrets

        salt = secrets.token_hex(16)
        hash_input = f"{phone_number}:{salt}:{self.jwt_secret}"
        token_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        return f"{salt}:{token_hash}"


_security_manager_instance: Optional["SecurityManager"] = None


def get_security_manager() -> "SecurityManager":
    """Return the singleton SecurityManager, creating it on first access."""
    global _security_manager_instance
    if _security_manager_instance is None:
        _security_manager_instance = SecurityManager()
    return _security_manager_instance
