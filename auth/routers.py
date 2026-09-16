from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.encoders import jsonable_encoder
from utils import response
from database import get_db
from auth.schema import UserRegistrationSchema, UserLoginSchema, UserProfileSchema
from auth.models import User
from sqlalchemy.orm import Session
from auth.  auth import *
from utils import response
from config import settings
import os
import uuid
from pathlib import PurePosixPath
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

router = APIRouter()

@router.post('/register')
async def register_user(user: UserRegistrationSchema, db: AsyncSession = Depends(get_db)):
    hashed_password = hash_password(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return response(
    status=201,
    message="User created successfully",
    data={
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        }
    }
)

@router.post('/login')
async def login_user(cred: UserLoginSchema, db: AsyncSession = Depends(get_db)):
    username = cred.username
    password = cred.password
    result = await db.execute(select(User).filter(User.username == username))
    db_user_instance = result.scalar_one_or_none()
    if not db_user_instance:
        return response(status=400, message='Incorrect username/password')
    if not verify_password(password, db_user_instance.hashed_password):
        return response(status=400, message='Incorrect username or password')
    access_token = create_access_token({"sub": db_user_instance.username})
    refresh_token = create_refresh_token({"sub": db_user_instance.username})
    return response(status=200, message='Login successful', data={
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    })

@router.post('/refresh')
def refresh_access_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return response(status=401, message="Invalid token type")
        username = payload.get("sub")
    except jwt.ExpiredSignatureError:
        return response(status=401, message="Refresh token expired, please log in again")
    except jwt.InvalidTokenError:
        return response(status=401, message="Invalid refresh token")

    new_access_token = create_access_token({"sub": username})
    return response(status=200, message="Token refreshed", data={"access_token": new_access_token})

@router.get('/profile')
async def get_user_profile(username: str = Depends(verify_token), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        return response(status=404, message="User not found")
    
    return response(status=200, message="Profile fetched", data={
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "profile_picture": user.profile_picture
    })

@router.post('/profile/picture/')
def upload_profile_picture(file: UploadFile= File(...), username:str= Depends(verify_token), db: Session = Depends(get_db)):
    if file.content_type not in settings.ALLOWED_PROFILE_PICTURE_TYPE:
        raise HTTPException(status_code=400, detail="Only JPG/PNG allowed")

    contents = file.file.read()
    if len(contents) > settings.MAX_PROFILE_PICTURE_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_picture = user.profile_picture
    ext = file.filename.split(".")[-1]
    filename = f"{username}_{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)
    user.profile_picture=str(PurePosixPath(settings.UPLOAD_DIR) / filename)
    db.commit()
    if old_picture and os.path.exists(old_picture):
        os.remove(old_picture)
    data = UserProfileSchema.model_validate(user)
    return response(
        status=200,
        message= 'Profile picture updated successfully',
        data=jsonable_encoder(data)
    )