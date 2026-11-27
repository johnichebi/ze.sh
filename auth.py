from jose import jwt, JWTError
from datetime import datetime, timedelta
from pwdlib import PasswordHash
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from database import execute_query
import os

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/account/login")
password_hash = PasswordHash.recommended()

def hash_password(password):
    hashed_password = password_hash.hash(password)
    return hashed_password

def verify_hash_password(plain, hashed_password):
    return password_hash.verify(plain, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()

    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(
            to_encode, 
            SECRET_KEY,
            algorithm=ALGORITHM
            )
    return encoded_jwt

def verify_access_token(token: str):
    try:
        payload =jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM]
                )
        username = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")
        return username
    except JWTError as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token")


def get_current_user(token: str = Depends(oauth2_scheme)):
    #print({"TOKEN":token})
    query = "SELECT * FROM users WHERE user_name=:username"
    user = execute_query(query, {"username":verify_access_token(token)}).mappings().first()
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")
