"""
Authentication Utilities
========================
JWT token generation/validation and password hashing for API authentication.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

# Configuration
SECRET_KEY = "dam-secret-key-2025-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token extraction (auto_error=False allows guest access)
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: User's database ID
        
    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[int]:
    """
    Dependency to extract user_id from JWT token in Authorization header.
    
    This is used as a FastAPI dependency:
        @app.get("/endpoint")
        def my_endpoint(user_id: Optional[int] = Depends(get_current_user_id)):
            ...
    
    Args:
        credentials: HTTPBearer credentials (automatically extracted from Authorization header)
        
    Returns:
        User ID if valid token provided, None if no token (guest mode)
        
    Notes:
        - Returns None for invalid/expired tokens (allows guest access)
        - Frontend should check for 401 errors and prompt login if needed
    """
    if not credentials:
        return None  # No Authorization header = guest mode
    
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        
        if user_id_str is None:
            return None
        
        return int(user_id_str)
        
    except JWTError:
        # Invalid or expired token = treat as guest
        return None


def require_auth(user_id: Optional[int] = Depends(get_current_user_id)) -> int:
    """
    Dependency that REQUIRES authentication (raises 401 if not logged in).
    
    Use this for endpoints that absolutely require a logged-in user:
        @app.get("/protected")
        def protected_endpoint(user_id: int = Depends(require_auth)):
            ...
    
    Args:
        user_id: User ID from token (extracted by get_current_user_id)
        
    Returns:
        User ID (guaranteed to be non-None)
        
    Raises:
        HTTPException 401 if no valid token provided
    """
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user_id