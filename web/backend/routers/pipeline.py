from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict

from web.backend.services.pipeline_manager import pipeline_manager

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class PipelineStartRequest(BaseModel):
    provider: str = "kimi"
    confidence: str = "low"
    model_size: str = "m"
    epochs: int = 200
    batch_size: int = 8
    device: str = "mps"
    max_images: int = 0


@router.post("/start")
async def start_pipeline(request: PipelineStartRequest):
    if (
        pipeline_manager.active_pipeline
        and pipeline_manager.active_pipeline["status"] == "running"
    ):
        raise HTTPException(400, "已有流水线正在运行")

    import asyncio
    import uuid
    from datetime import datetime

    pipeline_id = str(uuid.uuid4())

    # 先初始化 pipeline 状态
    pipeline_manager.active_pipeline = {
        "id": pipeline_id,
        "status": "running",
        "current_stage": "labeling",
        "progress": 0,
        "message": "流水线初始化中...",
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "results": {},
    }

    pipeline_manager.should_stop = False

    # 启动后台任务
    asyncio.create_task(
        pipeline_manager.run_full_pipeline(
            provider=request.provider,
            confidence=request.confidence,
            max_images=request.max_images,
            train_config={
                "model_size": request.model_size,
                "epochs": request.epochs,
                "batch_size": request.batch_size,
                "device": request.device,
            },
        )
    )

    return {
        "message": "流水线已启动",
        "pipeline_id": pipeline_id,
    }


@router.get("/status")
async def get_pipeline_status():
    status = pipeline_manager.get_status()
    if not status:
        return {"status": "idle", "message": "没有正在运行的流水线"}

    # 如果是训练阶段，尝试读取实时epoch进度
    if status.get("current_stage") == "training":
        try:
            import json
            from pathlib import Path

            progress_file = Path(".training_progress.json")
            if progress_file.exists():
                data = json.loads(progress_file.read_text())
                status["training_progress"] = data
        except Exception:
            pass

    return status


@router.get("/training-progress")
async def get_training_progress():
    """获取实时训练进度（当前epoch）"""
    try:
        import json
        from pathlib import Path

        progress_file = Path(".training_progress.json")
        if progress_file.exists():
            data = json.loads(progress_file.read_text())
            return data
        return {"current_epoch": 0, "total_epochs": 0, "progress_percent": 0}
    except Exception:
        return {"current_epoch": 0, "total_epochs": 0, "progress_percent": 0}


@router.post("/stop")
async def stop_pipeline():
    pipeline_manager.stop_pipeline()
    return {"message": "流水线停止请求已发送"}
