# from contextlib import asynccontextmanager
# from apscheduler.schedulers.asyncio import AsyncIOScheduler
# from fastapi import FastAPI
# from database import SessionLocal
# from sqlalchemy import select
# from .models import Item
# from .schema import ItemReadSchema
# from sqlalchemy.orm import selectinload
# from fastapi.encoders import jsonable_encoder
# import logging
# logging.basicConfig()
# logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# scheduler = AsyncIOScheduler()

# async def print_items():
#     async with SessionLocal() as db:
#         items = await db.execute(select(Item).options(selectinload(Item.user)))
#         print(jsonable_encoder([ItemReadSchema.model_validate(i) for i in items.scalars().all()]) if items else None)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # startup
#     scheduler.add_job(print_items, "cron", hour=14, minute=56)
#     scheduler.start()
#     yield
#     # shutdown
#     scheduler.shutdown()
    


# items/cron.py
import asyncio
from celery_app import celery_app
from celery.schedules import crontab
from database import SessionLocal
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.encoders import jsonable_encoder
from items.models import Item
from items.schema import ItemReadSchema

celery_app.conf.beat_schedule = {
    "print-items-daily": {
        "task": "items.cron.print_items_task",
        "schedule": crontab(hour=11, minute=28),
    },
}

async def _print_items():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as db:
            result = await db.execute(select(Item).options(selectinload(Item.user)))
            items = result.scalars().all()
            print(jsonable_encoder([ItemReadSchema.model_validate(i) for i in items]))
    finally:
        await engine.dispose()  # closes the pool cleanly before this event loop dies

@celery_app.task(name="items.cron.print_items_task")
def print_items_task():
    asyncio.run(_print_items())