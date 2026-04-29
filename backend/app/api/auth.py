"""Authentication API endpoints."""

from typing import Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..auth import create_access_token, get_current_user, verify_google_token


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class GoogleAuthRequest(BaseModel):
    id_token: str


@router.post("/google")
def auth_with_google(payload: GoogleAuthRequest):
    user = verify_google_token(payload.id_token)
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me")
def auth_me(user: Dict = Depends(get_current_user)):
    return user
