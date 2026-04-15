from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

try:
    from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
    from .database import get_db
    from .models import User
except ImportError:
    from config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
    from database import get_db
    from models import User


security = HTTPBearer()
PBKDF2_ITERATIONS = 390000


def hash_password(raw_password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", raw_password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_b64}${digest_b64}"


def verify_password(raw_password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = hashed_password.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(digest_b64.encode("ascii"))
        calculated = hashlib.pbkdf2_hmac(
            "sha256", raw_password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(calculated, expected)
    except Exception:
        return False


def create_access_token(user_id: int, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_owner(user: User = Depends(get_current_user)) -> User:
    if not user.is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Owner only endpoint")
    return user
