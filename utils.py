from typing import Any
from fastapi.responses import JSONResponse
from fastapi import Depends, HTTPException
from database import get_db
from auth.auth import verify_token
from auth.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


def response(status: int, message: str, data: Any = None, error: str | None = None):
    resp = {'status': status, 'message': message}
    if data is not None:
        resp['data'] = data
    if error is not None:
        resp['error'] = error
    return JSONResponse(content=resp, status_code=status)

async def get_current_active_user(username: str = Depends(verify_token), db: AsyncSession=Depends(get_db)):
    user = await db.execute(select(User).filter(User.username==username))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')
    return user