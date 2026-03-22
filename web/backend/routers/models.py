import os
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from web.backend.models.database import get_db, Model
from web.backend.models.schemas import (
    ModelSchema,
    ExportModelRequest,
    ExportModelResponse,
)

router = APIRouter(prefix="/api/models", tags=["models"])


@router.get("", response_model=List[ModelSchema])
async def list_models(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Model).order_by(Model.created_at.desc()))
    models = result.scalars().all()
    return [ModelSchema.model_validate(m) for m in models]


@router.get("/{model_id}", response_model=ModelSchema)
async def get_model(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "模型不存在")
    return ModelSchema.model_validate(model)


@router.post("/{model_id}/export", response_model=ExportModelResponse)
async def export_model(
    model_id: str, request: ExportModelRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "模型不存在")

    if not os.path.exists(model.path):
        raise HTTPException(404, "模型文件不存在")

    if request.format == "onnx":
        from src.training.export import export_model

        export_paths = export_model(model.path, formats=["onnx"])
        if export_paths and "onnx" in export_paths:
            export_path = export_paths["onnx"]
            size_mb = os.path.getsize(export_path) / (1024 * 1024)
            return ExportModelResponse(
                download_url=f"/api/models/{model_id}/download?format=onnx",
                format="onnx",
                size_mb=round(size_mb, 2),
            )

    raise HTTPException(400, f"不支持的导出格式: {request.format}")


@router.get("/{model_id}/download")
async def download_model(
    model_id: str, format: str = "pt", db: AsyncSession = Depends(get_db)
):
    from fastapi.responses import FileResponse

    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "模型不存在")

    if format == "pt":
        file_path = model.path
    elif format == "onnx":
        file_path = model.path.replace(".pt", ".onnx")
    else:
        raise HTTPException(400, f"不支持的格式: {format}")

    if not os.path.exists(file_path):
        raise HTTPException(404, "文件不存在")

    return FileResponse(
        file_path,
        filename=f"{model.name}.{format}",
        media_type="application/octet-stream",
    )


@router.delete("/{model_id}")
async def delete_model(model_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Model).where(Model.id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(404, "模型不存在")

    if os.path.exists(model.path):
        os.remove(model.path)

    onnx_path = model.path.replace(".pt", ".onnx")
    if os.path.exists(onnx_path):
        os.remove(onnx_path)

    await db.delete(model)
    await db.commit()
    return {"message": "删除成功"}
