import json
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from web.backend.models.database import get_db, LabelingTask, TaskStatus
from web.backend.models.schemas import (
    LabelingTaskSchema,
    StartLabelingRequest,
    LabelingProgressMessage,
)
from web.backend.services.task_manager import task_manager

router = APIRouter(prefix="/api/labeling", tags=["labeling"])


@router.post("/start", response_model=LabelingTaskSchema)
async def start_labeling(
    request: StartLabelingRequest, db: AsyncSession = Depends(get_db)
):
    from web.backend.models.database import Image

    for image_id in request.image_ids:
        result = await db.execute(select(Image).where(Image.id == image_id))
        if not result.scalar_one_or_none():
            raise HTTPException(404, f"图片不存在: {image_id}")

    task_id = str(uuid.uuid4())
    task = LabelingTask(
        id=task_id,
        status=TaskStatus.PENDING,
        provider=request.provider,
        confidence=request.confidence,
        total_images=len(request.image_ids),
        image_ids=json.dumps(request.image_ids),
    )
    db.add(task)
    await db.commit()

    import asyncio
    from web.backend.models.database import async_session_maker

    async def run_task():
        async with async_session_maker() as session:
            await task_manager.run_labeling_task(
                task_id=task_id,
                image_ids=request.image_ids,
                provider=request.provider,
                confidence=request.confidence,
                db_session=session,
            )

    asyncio.create_task(run_task())

    return LabelingTaskSchema.model_validate(task)


@router.get("/tasks", response_model=List[LabelingTaskSchema])
async def list_labeling_tasks(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LabelingTask).order_by(LabelingTask.created_at.desc()).limit(limit)
    )
    tasks = result.scalars().all()
    return [LabelingTaskSchema.model_validate(t) for t in tasks]


@router.get("/tasks/{task_id}", response_model=LabelingTaskSchema)
async def get_labeling_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LabelingTask).where(LabelingTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "任务不存在")
    return LabelingTaskSchema.model_validate(task)


@router.websocket("/ws/{task_id}")
async def labeling_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    await task_manager.register_labeling_websocket(task_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            pass
    except WebSocketDisconnect:
        await task_manager.unregister_labeling_websocket(task_id, websocket)
