"""
全自动流水线管理器
实现从标注到训练的无人值守流程
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from web.backend.models.database import (
    Image,
    ImageStatus,
    LabelingTask,
    TaskStatus,
    Dataset,
    TrainingTask,
    Model,
    async_session_maker,
)
from web.backend.services.task_manager import task_manager

logger = logging.getLogger(__name__)


class PipelineManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.active_pipeline = None
        self.should_stop = False

    async def run_full_pipeline(
        self,
        provider: str = "kimi",
        confidence: str = "low",
        max_images: int = 0,
        train_config: dict = None,
    ):
        pipeline_id = str(uuid.uuid4())
        self.active_pipeline = {
            "id": pipeline_id,
            "status": "running",
            "current_stage": "labeling",
            "progress": 0,
            "message": "开始全自动流水线",
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "results": {},
            "max_images": max_images,
        }

        try:
            async with async_session_maker() as db:
                await self._stage_labeling(db, provider, confidence)
                if self.should_stop:
                    return

                await self._stage_dataset_build(db, max_images)
                if self.should_stop:
                    return

                await self._stage_training(db, train_config)
                if self.should_stop:
                    return

                self.active_pipeline["status"] = "completed"
                self.active_pipeline["current_stage"] = "finished"
                self.active_pipeline["progress"] = 100
                self.active_pipeline["message"] = "流水线完成！"
                self.active_pipeline["completed_at"] = datetime.utcnow()

        except Exception as e:
            logger.exception("Pipeline failed")
            self.active_pipeline["status"] = "failed"
            self.active_pipeline["message"] = f"流水线失败: {str(e)}"
            self.active_pipeline["completed_at"] = datetime.utcnow()

    async def _stage_labeling(self, db: AsyncSession, provider: str, confidence: str):
        self.active_pipeline["current_stage"] = "labeling"
        self.active_pipeline["message"] = "正在检查待标注图片..."

        # 先检查已有的已标注图片
        result = await db.execute(
            select(Image).where(Image.status.in_(["labeled", "verified"]))
        )
        already_labeled = result.scalars().all()

        result = await db.execute(
            select(Image).where(Image.status == ImageStatus.PENDING)
        )
        pending_images = result.scalars().all()

        if not pending_images:
            self.active_pipeline["message"] = (
                f"所有图片已标注（共{len(already_labeled)}张），跳过标注阶段"
            )
            self.active_pipeline["results"]["labeled_count"] = len(already_labeled)
            self.active_pipeline["results"]["skipped_labeling"] = True
            self.active_pipeline["progress"] = 30
            return

        total = len(pending_images)
        self.active_pipeline["message"] = f"开始标注 {total} 张图片..."

        image_ids = [img.id for img in pending_images]

        labeling_task = LabelingTask(
            id=str(uuid.uuid4()),
            status=TaskStatus.PENDING,
            provider=provider,
            confidence=confidence,
            total_images=total,
            image_ids=str(image_ids),
        )
        db.add(labeling_task)
        await db.commit()

        await task_manager.run_labeling_task(
            task_id=labeling_task.id,
            image_ids=image_ids,
            provider=provider,
            confidence=confidence,
            db_session=db,
        )

        self.active_pipeline["results"]["labeled_count"] = total
        self.active_pipeline["progress"] = 30

    async def _stage_dataset_build(self, db: AsyncSession, max_images: int = 0):
        self.active_pipeline["current_stage"] = "dataset"
        self.active_pipeline["message"] = "正在构建数据集..."

        from src.dataset.splitter import build_yolo_dataset
        from web.backend.routers.training import build_dataset
        import random

        result = await db.execute(
            select(Image).where(Image.status.in_(["labeled", "verified"]))
        )
        labeled_images = list(result.scalars().all())

        if max_images > 0 and max_images < len(labeled_images):
            self.active_pipeline["message"] = (
                f"随机选择 {max_images} 张图片构建数据集..."
            )
            labeled_images = random.sample(labeled_images, max_images)
            self.active_pipeline["results"]["selected_images_count"] = len(
                labeled_images
            )
        else:
            self.active_pipeline["results"]["selected_images_count"] = len(
                labeled_images
            )

        if len(labeled_images) < 5:
            raise ValueError(
                f"已标注图片数量不足（{len(labeled_images)}张），至少需要5张"
            )

        dataset_id = str(uuid.uuid4())
        BASE_DIR = Path(__file__).resolve().parent.parent
        output_dir = BASE_DIR / "datasets" / dataset_id
        output_dir.mkdir(parents=True, exist_ok=True)

        PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
        label_dir = PROJECT_ROOT / "data" / "labels"
        label_dir.mkdir(parents=True, exist_ok=True)

        for image in labeled_images:
            from web.backend.models.database import Detection

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

        image_dir = BASE_DIR / "uploads"
        data_yaml = build_yolo_dataset(
            image_dir=str(image_dir),
            label_dir=str(label_dir),
            output_dir=str(output_dir),
            train_ratio=0.7,
            val_ratio=0.2,
            test_ratio=0.1,
        )

        dataset = Dataset(
            id=dataset_id,
            name=f"auto_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            path=str(output_dir),
            train_count=int(len(labeled_images) * 0.7),
            val_count=int(len(labeled_images) * 0.2),
            test_count=int(len(labeled_images) * 0.1),
            config={
                "train_ratio": 0.7,
                "val_ratio": 0.2,
                "test_ratio": 0.1,
                "augment": True,
            },
        )
        db.add(dataset)
        await db.commit()

        self.active_pipeline["results"]["dataset_id"] = dataset_id
        self.active_pipeline["progress"] = 40

    async def _stage_training(self, db: AsyncSession, train_config: dict):
        self.active_pipeline["current_stage"] = "training"
        self.active_pipeline["message"] = "开始训练模型..."

        dataset_id = self.active_pipeline["results"].get("dataset_id")
        if not dataset_id:
            raise ValueError("数据集ID不存在")

        config = train_config or {
            "model_size": "m",
            "epochs": 200,
            "batch_size": 16,
            "device": "0",
        }

        task_id = str(uuid.uuid4())
        task = TrainingTask(
            id=task_id,
            status=TaskStatus.PENDING,
            dataset_id=dataset_id,
            model_size=config["model_size"],
            epochs=config["epochs"],
            batch_size=config["batch_size"],
            device=config["device"],
            total_epochs=config["epochs"],
        )
        db.add(task)
        await db.commit()

        await task_manager.run_training_task(
            task_id=task_id,
            config={
                "dataset_id": dataset_id,
                "lr0": train_config.get("lr0", 0.02),
                **config,
            },
            db_session=db,
        )

        self.active_pipeline["results"]["training_task_id"] = task_id
        self.active_pipeline["current_stage"] = "finished"
        self.active_pipeline["status"] = "completed"
        self.active_pipeline["progress"] = 100
        self.active_pipeline["message"] = "训练完成！"
        self.active_pipeline["completed_at"] = datetime.utcnow()

    def stop_pipeline(self):
        self.should_stop = True
        self.active_pipeline["status"] = "stopped"
        self.active_pipeline["message"] = "流水线已停止"

    def get_status(self):
        return self.active_pipeline


pipeline_manager = PipelineManager()
