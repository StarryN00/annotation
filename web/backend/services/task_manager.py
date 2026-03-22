import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import uuid

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class TaskManager:
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
        self.active_labeling_tasks: Dict[str, dict] = {}
        self.active_training_tasks: Dict[str, dict] = {}
        self.labeling_websockets: Dict[str, List[WebSocket]] = {}
        self.training_websockets: Dict[str, List[WebSocket]] = {}

    async def register_labeling_websocket(self, task_id: str, websocket: WebSocket):
        if task_id not in self.labeling_websockets:
            self.labeling_websockets[task_id] = []
        self.labeling_websockets[task_id].append(websocket)

    async def unregister_labeling_websocket(self, task_id: str, websocket: WebSocket):
        if task_id in self.labeling_websockets:
            if websocket in self.labeling_websockets[task_id]:
                self.labeling_websockets[task_id].remove(websocket)

    async def broadcast_labeling_progress(self, task_id: str, data: dict):
        if task_id in self.labeling_websockets:
            dead_sockets = []
            for ws in self.labeling_websockets[task_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.labeling_websockets[task_id].remove(ws)

    async def register_training_websocket(self, task_id: str, websocket: WebSocket):
        if task_id not in self.training_websockets:
            self.training_websockets[task_id] = []
        self.training_websockets[task_id].append(websocket)

    async def unregister_training_websocket(self, task_id: str, websocket: WebSocket):
        if task_id in self.training_websockets:
            if websocket in self.training_websockets[task_id]:
                self.training_websockets[task_id].remove(websocket)

    async def broadcast_training_progress(self, task_id: str, data: dict):
        if task_id in self.training_websockets:
            dead_sockets = []
            for ws in self.training_websockets[task_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.training_websockets[task_id].remove(ws)

    async def run_labeling_task(
        self,
        task_id: str,
        image_ids: List[str],
        provider: str,
        confidence: str,
        db_session,
    ):
        from sqlalchemy import select
        from web.backend.models.database import (
            Image,
            Detection,
            LabelingTask,
            ImageStatus,
            TaskStatus,
        )
        from src.labeling.labeler import AutoLabeler
        import yaml

        logger.info(f"Starting labeling task {task_id} with {len(image_ids)} images")

        try:
            task_result = await db_session.execute(
                select(LabelingTask).where(LabelingTask.id == task_id)
            )
            task = task_result.scalar_one()
            task.status = TaskStatus.RUNNING
            await db_session.commit()

            config_path = Path("config/config.yaml")
            with open(config_path) as f:
                config = yaml.safe_load(f)

            config["llm"]["provider"] = provider
            config["labeling"]["min_confidence"] = confidence

            labeler = AutoLabeler(config)

            processed = 0
            success_count = 0
            error_count = 0

            for idx, image_id in enumerate(image_ids):
                try:
                    image_result = await db_session.execute(
                        select(Image).where(Image.id == image_id)
                    )
                    image = image_result.scalar_one()

                    await self.broadcast_labeling_progress(
                        task_id,
                        {
                            "type": "progress",
                            "task_id": task_id,
                            "current": idx + 1,
                            "total": len(image_ids),
                            "image_name": image.filename,
                            "detections_count": 0,
                        },
                    )

                    image.status = ImageStatus.LABELING
                    await db_session.commit()

                    result = labeler._call_with_retry(image.path)

                    if result.error:
                        logger.error(
                            f"Labeling failed for {image.filename}: {result.error}"
                        )
                        image.status = ImageStatus.ERROR
                        error_count += 1
                    else:
                        from src.labeling.parser import parse_response

                        result = parse_response(result, confidence)

                        for det_data in result.detections:
                            detection = Detection(
                                id=str(uuid.uuid4()),
                                image_id=image_id,
                                x_center=det_data.x_center,
                                y_center=det_data.y_center,
                                width=det_data.width,
                                height=det_data.height,
                                severity=det_data.severity,
                                confidence=0.8
                                if det_data.confidence == "high"
                                else (0.5 if det_data.confidence == "medium" else 0.3),
                                is_manual=False,
                            )
                            db_session.add(detection)

                        image.status = ImageStatus.LABELED
                        success_count += 1

                        await self.broadcast_labeling_progress(
                            task_id,
                            {
                                "type": "progress",
                                "task_id": task_id,
                                "current": idx + 1,
                                "total": len(image_ids),
                                "image_name": image.filename,
                                "detections_count": len(result.detections),
                            },
                        )

                    processed += 1
                    task.processed_images = processed
                    task.success_count = success_count
                    task.error_count = error_count
                    await db_session.commit()

                    await asyncio.sleep(
                        config.get("labeling", {}).get("request_interval", 0.5)
                    )

                except Exception as e:
                    logger.exception(f"Error processing image {image_id}")
                    error_count += 1
                    task.error_count = error_count
                    await db_session.commit()

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            await db_session.commit()

            await self.broadcast_labeling_progress(
                task_id,
                {
                    "type": "completed",
                    "task_id": task_id,
                    "total": len(image_ids),
                    "success": success_count,
                    "error": error_count,
                },
            )

        except Exception as e:
            logger.exception(f"Labeling task {task_id} failed")
            task_result = await db_session.execute(
                select(LabelingTask).where(LabelingTask.id == task_id)
            )
            task = task_result.scalar_one()
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            await db_session.commit()

            await self.broadcast_labeling_progress(
                task_id, {"type": "error", "task_id": task_id, "error": str(e)}
            )

    async def run_training_task(self, task_id: str, config: dict, db_session):
        from sqlalchemy import select
        from web.backend.models.database import TrainingTask, TaskStatus, Model
        from src.training.train_yolo import train_nest_detector
        import sys
        from pathlib import Path
        import asyncio
        import os

        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

        logger.info(f"Starting training task {task_id}")

        try:
            task_result = await db_session.execute(
                select(TrainingTask).where(TrainingTask.id == task_id)
            )
            task = task_result.scalar_one()
            task.status = TaskStatus.RUNNING
            task.total_epochs = config["epochs"]
            await db_session.commit()

            dataset_id = config.get("dataset_id")
            if not dataset_id:
                raise ValueError("Dataset ID is required")

            from web.backend.models.database import Dataset

            dataset_result = await db_session.execute(
                select(Dataset).where(Dataset.id == dataset_id)
            )
            dataset = dataset_result.scalar_one()
            data_yaml = str(Path(dataset.path) / "data.yaml")

            if not Path(data_yaml).exists():
                raise FileNotFoundError(f"Dataset config not found: {data_yaml}")

            logger.info(f"Starting training in background thread for task {task_id}")
            loop = asyncio.get_event_loop()

            def train_wrapper():
                return train_nest_detector(
                    data_yaml=data_yaml,
                    model_size=config["model_size"],
                    epochs=config["epochs"],
                    batch_size=config["batch_size"],
                    device=config["device"],
                    output_dir="outputs/models",
                )

            best_model_path, train_metrics = await loop.run_in_executor(
                None, train_wrapper
            )

            task.status = TaskStatus.COMPLETED
            task.current_epoch = config["epochs"]
            task.best_model_path = best_model_path
            task.completed_at = datetime.utcnow()

            model_size_mb = 0
            if best_model_path and Path(best_model_path).exists():
                model_size_mb = Path(best_model_path).stat().st_size / (1024 * 1024)

            task.metrics = train_metrics
            await db_session.commit()

            model = Model(
                id=str(uuid.uuid4()),
                name=f"nest_detector_{task_id}",
                training_id=task_id,
                path=best_model_path or "",
                metrics=task.metrics,
                size_mb=model_size_mb,
                format="pt",
            )
            db_session.add(model)
            await db_session.commit()

            await self.broadcast_training_progress(
                task_id,
                {
                    "type": "completed",
                    "task_id": task_id,
                    "best_model_path": best_model_path,
                },
            )

        except Exception as e:
            logger.exception(f"Training task {task_id} failed")
            task_result = await db_session.execute(
                select(TrainingTask).where(TrainingTask.id == task_id)
            )
            task = task_result.scalar_one()
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            await db_session.commit()

            await self.broadcast_training_progress(
                task_id, {"type": "error", "task_id": task_id, "error": str(e)}
            )

    def stop_training_task(self, task_id: str) -> bool:
        if task_id in self.active_training_tasks:
            self.active_training_tasks[task_id]["should_stop"] = True
            return True
        return False


task_manager = TaskManager()
