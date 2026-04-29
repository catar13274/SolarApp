"""Authentication helpers for Google Workspace login."""

import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


security = HTTPBearer(auto_error=False)


def _allowed_domains() -> List[str]:
    raw = os.getenv("ALLOWED_GOOGLE_DOMAINS", "freevoltsrl.ro,energoteamconect.ro")
    return [domain.strip().lower() for domain in raw.split(",") if domain.strip()]


def _allowed_emails() -> List[str]:
    raw = os.getenv("ALLOWED_GOOGLE_EMAILS", "")
    return [email.strip().lower() for email in raw.split(",") if email.strip()]


def _jwt_secret() -> str:
    secret = os.getenv("APP_JWT_SECRET", "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="APP_JWT_SECRET is not configured.",
        )
    return secret


def verify_google_token(token: str) -> Dict:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured.",
        )

    try:
        info = id_token.verify_oauth2_token(token, google_requests.Request(), client_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token.")

    email = str(info.get("email", "")).lower()
    domain = email.split("@")[-1] if "@" in email else ""
    allowed_emails = _allowed_emails()

    if allowed_emails and email not in allowed_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Email '{email}' is not in the allowlist.",
        )

    if domain not in _allowed_domains():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Email domain '{domain}' is not allowed.",
        )

    return {
        "email": email,
        "name": info.get("name", ""),
        "picture": info.get("picture", ""),
        "domain": domain,
    }


def create_access_token(user: Dict) -> str:
    expires_minutes = int(os.getenv("APP_JWT_EXPIRES_MINUTES", "480"))
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["email"],
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
        "domain": user.get("domain", ""),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token.")

    try:
        payload = jwt.decode(credentials.credentials, _jwt_secret(), algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")

    return {
        "email": payload.get("sub", ""),
        "name": payload.get("name", ""),
        "picture": payload.get("picture", ""),
        "domain": payload.get("domain", ""),
    }
