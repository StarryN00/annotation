import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from web.backend.models.database import get_db, Dataset, TrainingTask, TaskStatus
from web.backend.models.schemas import (
    DatasetSchema,
    BuildDatasetRequest,
    TrainingTaskSchema,
    StartTrainingRequest,
    TrainingProgressMessage,
)
from web.backend.services.task_manager import task_manager
from src.dataset.splitter import build_yolo_dataset

router = APIRouter(tags=["dataset", "training"])


@router.post("/api/dataset/build", response_model=DatasetSchema)
async def build_dataset(
    request: BuildDatasetRequest, db: AsyncSession = Depends(get_db)
):
    total_ratio = request.train_ratio + request.val_ratio + request.test_ratio
    if abs(total_ratio - 1.0) > 0.001:
        raise HTTPException(400, "划分比例之和必须等于1")

    from web.backend.models.database import Image

    result = await db.execute(select(Image))
    images = result.scalars().all()

    labeled_images = [img for img in images if img.status in ("labeled", "verified")]
    if len(labeled_images) < 10:
        raise HTTPException(400, "已标注图片数量不足（至少需要10张）")

    dataset_id = str(uuid.uuid4())
    output_dir = Path(f"web/backend/datasets/{dataset_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    label_dir = Path("data/labels")
    label_dir.mkdir(parents=True, exist_ok=True)

    from web.backend.models.database import Detection

    for image in labeled_images:
        det_result = await db.execute(
            select(Detection).where(Detection.image_id == image.id)
        )
        detections = det_result.scalars().all()

        label_file = label_dir / f"{image.id}.txt"
        with open(label_file, "w") as f:
            for det in detections:
                f.write(
                    f"0 {det.x_center:.6f} {det.y_center:.6f} {det.width:.6f} {det.height:.6f}\n"
                )

    image_dir = Path("web/backend/uploads")
    data_yaml = build_yolo_dataset(
        image_dir=str(image_dir),
        label_dir=str(label_dir),
        output_dir=str(output_dir),
        train_ratio=request.train_ratio,
        val_ratio=request.val_ratio,
        test_ratio=request.test_ratio,
    )

    dataset = Dataset(
        id=dataset_id,
        name=f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        path=str(output_dir),
        train_count=int(len(labeled_images) * request.train_ratio),
        val_count=int(len(labeled_images) * request.val_ratio),
        test_count=int(len(labeled_images) * request.test_ratio),
        config={
            "train_ratio": request.train_ratio,
            "val_ratio": request.val_ratio,
            "test_ratio": request.test_ratio,
            "augment": request.augment,
        },
    )
    db.add(dataset)
    await db.commit()

    return DatasetSchema.model_validate(dataset)


@router.get("/api/datasets", response_model=List[DatasetSchema])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    datasets = result.scalars().all()
    return [DatasetSchema.model_validate(d) for d in datasets]


@router.get("/api/datasets/{dataset_id}", response_model=DatasetSchema)
async def get_dataset(dataset_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "数据集不存在")
    return DatasetSchema.model_validate(dataset)


@router.post("/api/training/start", response_model=TrainingTaskSchema)
async def start_training(
    request: StartTrainingRequest, db: AsyncSession = Depends(get_db)
):
    if request.dataset_id:
        result = await db.execute(
            select(Dataset).where(Dataset.id == request.dataset_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(404, "数据集不存在")

    task_id = str(uuid.uuid4())
    task = TrainingTask(
        id=task_id,
        status=TaskStatus.PENDING,
        dataset_id=request.dataset_id,
        model_size=request.model_size,
        epochs=request.epochs,
        batch_size=request.batch_size,
        device=request.device,
        total_epochs=request.epochs,
    )
    db.add(task)
    await db.commit()

    import asyncio
    from web.backend.models.database import async_session_maker

    async def run_task():
        async with async_session_maker() as session:
            await task_manager.run_training_task(
                task_id=task_id,
                config={
                    "dataset_id": request.dataset_id,
                    "model_size": request.model_size,
                    "epochs": request.epochs,
                    "batch_size": request.batch_size,
                    "device": request.device,
                },
                db_session=session,
            )

    asyncio.create_task(run_task())

    return TrainingTaskSchema.model_validate(task)


@router.get("/api/training/tasks", response_model=List[TrainingTaskSchema])
async def list_training_tasks(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingTask).order_by(TrainingTask.created_at.desc()).limit(limit)
    )
    tasks = result.scalars().all()
    return [TrainingTaskSchema.model_validate(t) for t in tasks]


@router.get("/api/training/tasks/{task_id}", response_model=TrainingTaskSchema)
async def get_training_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingTask).where(TrainingTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "任务不存在")
    return TrainingTaskSchema.model_validate(task)


@router.post("/api/training/tasks/{task_id}/stop")
async def stop_training(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrainingTask).where(TrainingTask.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "任务不存在")

    if task.status != TaskStatus.RUNNING:
        raise HTTPException(400, "任务不在运行中")

    success = task_manager.stop_training_task(task_id)
    if success:
        task.status = TaskStatus.STOPPED
        await db.commit()
        return {"message": "训练已停止"}
    else:
        raise HTTPException(500, "停止训练失败")


@router.websocket("/ws/training/{task_id}")
async def training_websocket(websocket: WebSocket, task_id: str):
    await websocket.accept()
    await task_manager.register_training_websocket(task_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            pass
    except WebSocketDisconnect:
        await task_manager.unregister_training_websocket(task_id, websocket)
