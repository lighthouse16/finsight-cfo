from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from app.core.config import settings

router = APIRouter(tags=["auth"])

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # In a real app, verify against DB using bcrypt.
    # For this demo, user acts as their role: 'admin', 'analyst', 'viewer'
    username = form_data.username.lower()
    if username not in ["admin", "analyst", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # We ignore the password for the mock provider to keep the demo simple
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Payload includes role and demo org
    access_token = create_access_token(
        data={
            "sub": username, 
            "role": username, 
            "org": "demo-org"
        }, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
