#!/usr/bin/env python3

import asyncio
import sys

sys.path.insert(0, "/Users/starryn/project/annotation")

from web.backend.models.database import async_session_maker, Image
from sqlalchemy import select, func


async def check_db():
    async with async_session_maker() as db:
        result = await db.execute(select(func.count()).select_from(Image))
        count = result.scalar()
        print(f"数据库中图片数量: {count}")

        if count > 0:
            result = await db.execute(select(Image).limit(3))
            images = result.scalars().all()
            for img in images:
                print(f"  - {img.id}: {img.status}")


if __name__ == "__main__":
    asyncio.run(check_db())
