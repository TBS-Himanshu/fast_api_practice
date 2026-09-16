from fastapi import APIRouter,Depends
from .models import Item
from database import get_db
from auth.auth import verify_token
from auth.models import User
from utils import response, get_current_active_user
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .schema import ItemReadSchema, ItemCreateSchema
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import selectinload
from fastapi import BackgroundTasks

router = APIRouter(dependencies=[Depends(get_current_active_user)])

@router.post('/item')
async def create_item(item:ItemCreateSchema, db: AsyncSession =Depends(get_db), username: str = Depends(verify_token)):
    result = await db.execute(select(User).filter(User.username == username))
    user = result.scalar_one_or_none()
    new_item = Item(name=item.name, user_id=user.id)
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return response(
        status=201,
        message='Item created successfully',
        data={"name": new_item.name, "user_id": new_item.user_id}
    )

@router.get('/item')
async def get_all_user_items(db: AsyncSession=Depends(get_db), user: User = Depends(get_current_active_user)):
    items = await db.execute(select(Item).filter(Item.user_id==user.id))
    items = [jsonable_encoder(ItemReadSchema.model_validate(i)) for i in items.scalars()]
    return response(
        status=200,
        message='items received successfully',
        data={'items': items}
    )

@router.get('/item/{item_id}')
async def get_user_item(item_id: int, db: AsyncSession=Depends(get_db), user: User = Depends(get_current_active_user)):
    item = await db.execute(select(Item).filter(Item.user_id==user.id, Item.id==item_id))
    item = item.scalar_one_or_none()
    if not item:
        return response(
            status=404,
            message='Item not found.'
        )
    return response(
        status=200,
        message='item received successfully',
        data={'item': item.name}
    )

@router.patch('/item/{item_id}')
async def update_user_item(item_id:int, item_name:str, db: AsyncSession=Depends(get_db), user: User= Depends(get_current_active_user)):
    item = await db.execute(select(Item).filter(Item.user_id==user.id, Item.id==item_id))
    item = item.scalar_one_or_none()
    if not item:
        return response(
            status=404,
            message='Item not found.'
        )
    item.name = item_name
    await db.commit()
    await db.refresh(item)
    return response(
        status=200,
        message='Item updated successfully.',
        data={'item': item.name}
    )

@router.get('/all_items')
async def get_all_items(db: AsyncSession=Depends(get_db)):
    users = await db.execute(select(User))
    users = users.scalars()
    items:dict = {}
    for user in users:
        try:
            user_items = await db.execute(select(Item).filter(Item.user_id==user.id))
            items[user.id] = [ItemReadSchema.model_validate(item) for item in user_items.scalars()]
        except Exception as e:
            print(f'e:{e}')
    return response(
        status = 200,
        message="User wise items retrieved successfully.",
        data={
            "items": jsonable_encoder(items)
        }
    )

@router.get('/all_items/optimized')
async def get_all_items(db: AsyncSession=Depends(get_db)):
    users = await db.execute(select(User).options(selectinload(User.items)))
    users = users.scalars()
    items:dict = {}
    for user in users:
        try:
            items[user.id] = [ItemReadSchema.model_validate(item) for item in user.items]
        except Exception as e:
            print(f'e:{e}')
    return response(
        status = 200,
        message="User wise items retrieved successfully.",
        data={
            "items": jsonable_encoder(items)
        }
    )

@router.get('/schedule_itmes/')
async def schedule_items( background_task: BackgroundTasks, time: int = 10, db: AsyncSession=Depends(get_db)):
    background_task.add_task(print_items, time)
    return response(
        status=200,
        message="Items print scheduled successfully"
    )

from items.cron import print_items_task
@router.get('/schedule_items/celery/')
async def schedule_items(time: int = 10):
    print_items_task.apply_async(countdown=time)
    return response(
        status=200,
        message="Items print scheduled successfully"
    )

async def print_items(delay: int):
    import asyncio
    await asyncio.sleep(delay)
    from database import SessionLocal

    async with SessionLocal() as db:
        result = await db.execute(select(Item).options(selectinload(Item.user)))
        items = result.scalars().all()
        for item in items:
            print('item:', jsonable_encoder(ItemReadSchema.model_validate(item)))
    return response(
        status=200,
        message='Items will be printed soon. please check terminal'
    )