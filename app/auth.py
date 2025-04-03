import os
from datetime import timedelta, datetime

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing_extensions import deprecated

from app.database import get_db
from app.models import User

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
security = HTTPBearer()

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    password_hash = pwd_context.hash(password)
    return password_hash

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")])
        print(payload)
        return payload
    except jwt.ExpiredSignatureError:
        print("JWT has expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    token = credentials.credentials

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    username = payload.get("sub")  # `sub` is the username

    if not username:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch the user from the database using the username (sub)
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user

