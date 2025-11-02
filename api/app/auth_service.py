"""
Authentication service for JWT token management and user authentication.

This module provides JWT token creation, validation, and user authentication
functionality. For the prototype, users are authenticated as "anonymous".
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import secrets

from api.app.config import get_settings
from api.models.database import User

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
settings = get_settings()
ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    """Authentication service for JWT token management."""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY or self._generate_secret_key()
        self.algorithm = ALGORITHM
        self.access_token_expire_minutes = ACCESS_TOKEN_EXPIRE_MINUTES
    
    def _generate_secret_key(self) -> str:
        """Generate a secure random secret key for JWT signing."""
        return secrets.token_urlsafe(32)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plain password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
    
    def create_user_token(self, user: User) -> str:
        """Create a JWT token for a user."""
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin
        }
        return self.create_access_token(data=token_data)
    
    def get_token_from_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Extract user information from JWT token."""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        return {
            "user_id": int(payload.get("sub", -1)),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "is_admin": payload.get("is_admin", False)
        }


# Global auth service instance
auth_service = AuthService()


# Anonymous user for prototype
ANONYMOUS_USER = User(
    id=1,
    username="anonymous",
    email="anonymous@archaeologist.local",
    hashed_password="no_password",
    is_active=True,
    is_admin=False
)


def get_anonymous_token() -> str:
    """Get a JWT token for the anonymous user."""
    return auth_service.create_user_token(ANONYMOUS_USER)


def authenticate_anonymous() -> tuple[User, str]:
    """Authenticate the anonymous user for prototype access."""
    return ANONYMOUS_USER, get_anonymous_token()