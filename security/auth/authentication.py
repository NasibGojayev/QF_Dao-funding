"""
Authentication Module for DonCoin DAO Security
JWT-based authentication for admin endpoints.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import AUTH_CONFIG, DEFAULT_ADMIN, LOGS_DIR

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
security = HTTPBearer()

# =============================================================================
# MODELS
# =============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: list = []


class User(BaseModel):
    username: str
    email: str
    is_admin: bool = False
    disabled: bool = False


class UserInDB(User):
    hashed_password: str


class LoginRequest(BaseModel):
    username: str
    password: str


# =============================================================================
# USER DATABASE (In production, use actual database)
# =============================================================================

# Simple in-memory user store (replace with database in production)
USERS_DB: Dict[str, dict] = {
    DEFAULT_ADMIN['username']: {
        'username': DEFAULT_ADMIN['username'],
        'email': DEFAULT_ADMIN['email'],
        'hashed_password': pwd_context.hash(DEFAULT_ADMIN['password']),
        'is_admin': True,
        'disabled': False,
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    if username in USERS_DB:
        user_dict = USERS_DB[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=AUTH_CONFIG['access_token_expire_minutes'])
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode, 
        AUTH_CONFIG['secret_key'], 
        algorithm=AUTH_CONFIG['algorithm']
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token, 
            AUTH_CONFIG['secret_key'], 
            algorithms=[AUTH_CONFIG['algorithm']]
        )
        username: str = payload.get("sub")
        if username is None:
            return None
        token_scopes = payload.get("scopes", [])
        return TokenData(username=username, scopes=token_scopes)
    except JWTError:
        return None


# =============================================================================
# ADMIN ACCESS LOGGING
# =============================================================================

def log_admin_access(
    username: str,
    action: str,
    resource: str,
    ip_address: str,
    success: bool = True,
    details: Optional[dict] = None
):
    """Log admin access for audit trail"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "username": username,
        "action": action,
        "resource": resource,
        "ip_address": ip_address,
        "success": success,
        "details": details or {}
    }
    
    log_file = LOGS_DIR / "admin_access.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


def log_auth_event(
    event_type: str,  # 'login_success', 'login_failure', 'logout', 'token_refresh'
    username: str,
    ip_address: str,
    user_agent: Optional[str] = None,
    details: Optional[dict] = None
):
    """Log authentication events"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "username": username,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "details": details or {}
    }
    
    log_file = LOGS_DIR / "auth_events.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


# =============================================================================
# DEPENDENCIES
# =============================================================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Dependency to get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = decode_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return User(
        username=user.username,
        email=user.email,
        is_admin=user.is_admin,
        disabled=user.disabled
    )


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Dependency to get current admin user"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# =============================================================================
# LOGIN / LOGOUT FUNCTIONS
# =============================================================================

def login(
    username: str,
    password: str,
    ip_address: str,
    user_agent: Optional[str] = None
) -> Optional[Token]:
    """Perform login and return token"""
    user = authenticate_user(username, password)
    
    if not user:
        log_auth_event(
            event_type="login_failure",
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"reason": "invalid_credentials"}
        )
        return None
    
    access_token_expires = timedelta(minutes=AUTH_CONFIG['access_token_expire_minutes'])
    access_token = create_access_token(
        data={"sub": user.username, "scopes": ["admin"] if user.is_admin else []},
        expires_delta=access_token_expires
    )
    
    log_auth_event(
        event_type="login_success",
        username=username,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return Token(
        access_token=access_token,
        expires_in=AUTH_CONFIG['access_token_expire_minutes'] * 60
    )


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    Returns (is_valid, message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if not (has_upper and has_lower):
        return False, "Password must contain both uppercase and lowercase letters"
    
    if not has_digit:
        return False, "Password must contain at least one number"
    
    if not has_special:
        return False, "Password must contain at least one special character"
    
    return True, "Password meets requirements"
