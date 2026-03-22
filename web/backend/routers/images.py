import os
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from web.backend.models.database import get_db, Image, Detection, ImageStatus
from web.backend.models.schemas import (
    ImageSchema,
    ImageListResponse,
    UploadResponse,
    CorrectionRequest,
)

router = APIRouter(prefix="/api/images", tags=["images"])

UPLOAD_DIR = Path("web/backend/uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_FILES_PER_UPLOAD = 500


@router.post("/upload", response_model=UploadResponse)
async def upload_images(
    files: List[UploadFile] = File(...), db: AsyncSession = Depends(get_db)
):
    if len(files) > MAX_FILES_PER_UPLOAD:
        raise HTTPException(400, f"一次最多上传 {MAX_FILES_PER_UPLOAD} 个文件")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    image_ids = []
    for file in files:
        if not file.filename:
            continue
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(400, f"不支持的文件格式: {ext}")

        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(400, f"文件过大: {file.filename}")

        image_id = str(uuid.uuid4())
        new_filename = f"{image_id}{ext}"
        file_path = UPLOAD_DIR / new_filename

        with open(file_path, "wb") as f:
            f.write(contents)

        try:
            from PIL import Image as PILImage

            with PILImage.open(file_path) as img:
                width, height = img.size
        except Exception:
            width, height = None, None

        image = Image(
            id=image_id,
            filename=file.filename,
            path=str(file_path),
            status=ImageStatus.PENDING,
            width=width,
            height=height,
            file_size=len(contents),
        )
        db.add(image)
        image_ids.append(image_id)

    await db.commit()
    return UploadResponse(image_ids=image_ids, count=len(image_ids))


@router.get("", response_model=ImageListResponse)
async def list_images(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    search: str = Query(None, description="搜索文件名"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Image).options(selectinload(Image.detections))
    if status:
        query = query.where(Image.status == status)
    if search:
        query = query.where(Image.filename.ilike(f"%{search}%"))

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0

    query = query.offset((page - 1) * limit).limit(limit)
    result = await db.execute(query)
    images = result.scalars().all()

    return ImageListResponse(
        items=[ImageSchema.model_validate(img) for img in images],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{image_id}", response_model=ImageSchema)
async def get_image(image_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Image)
        .where(Image.id == image_id)
        .options(selectinload(Image.detections))
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, "图片不存在")
    return ImageSchema.model_validate(image)


@router.get("/{image_id}/file")
async def get_image_file(image_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, "图片不存在")

    if not os.path.exists(image.path):
        raise HTTPException(404, "图片文件不存在")

    return FileResponse(image.path, filename=image.filename)


@router.delete("/{image_id}")
async def delete_image(image_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, "图片不存在")

    if os.path.exists(image.path):
        os.remove(image.path)

    await db.delete(image)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/{image_id}/correct")
async def correct_detections(
    image_id: str, request: CorrectionRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(404, "图片不存在")

    await db.execute(select(Detection).where(Detection.image_id == image_id))

    for det_data in request.detections:
        detection = Detection(
            id=str(uuid.uuid4()),
            image_id=image_id,
            x_center=det_data.get("x_center", 0),
            y_center=det_data.get("y_center", 0),
            width=det_data.get("width", 0),
            height=det_data.get("height", 0),
            severity=det_data.get("severity", "medium"),
            confidence=det_data.get("confidence", 1.0),
            is_manual=True,
        )
        db.add(detection)

    image.status = ImageStatus.VERIFIED
    await db.commit()
    return {"message": "修正成功"}


@router.post("/scan-directory", response_model=UploadResponse)
async def scan_directory(directory_path: str, db: AsyncSession = Depends(get_db)):
    """
    扫描指定目录，将图片直接导入系统（不复制文件，只创建数据库记录）。
    用于大批量图片的快速导入。
    """
    from pathlib import Path
    import glob

    path = Path(directory_path)
    if not path.exists():
        raise HTTPException(400, f"目录不存在: {directory_path}")
    if not path.is_dir():
        raise HTTPException(400, f"路径不是目录: {directory_path}")

    # 查找所有支持的图片格式
    image_paths = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.webp"]:
        image_paths.extend(path.glob(ext))
        image_paths.extend(path.glob(ext.upper()))

    if not image_paths:
        raise HTTPException(400, f"目录中没有找到支持的图片文件")

    if len(image_paths) > 2000:
        raise HTTPException(
            400, f"图片数量过多（{len(image_paths)}张），最多支持2000张"
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    image_ids = []
    processed = 0
    errors = []

    for img_path in image_paths:
        try:
            ext = img_path.suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue

            # 获取图片尺寸
            try:
                from PIL import Image as PILImage

                with PILImage.open(img_path) as img:
                    width, height = img.size
            except Exception:
                width, height = None, None

            image_id = str(uuid.uuid4())

            # 创建软链接或复制文件到上传目录
            new_filename = f"{image_id}{ext}"
            target_path = UPLOAD_DIR / new_filename

            # 复制文件（软链接可能在不同文件系统上不可用）
            shutil.copy2(img_path, target_path)

            image = Image(
                id=image_id,
                filename=img_path.name,
                path=str(target_path),
                status=ImageStatus.PENDING,
                width=width,
                height=height,
                file_size=img_path.stat().st_size if img_path.exists() else 0,
            )
            db.add(image)
            image_ids.append(image_id)
            processed += 1

            # 每50张提交一次，避免内存问题
            if processed % 50 == 0:
                await db.commit()

        except Exception as e:
            errors.append(f"{img_path.name}: {str(e)}")
            continue

    await db.commit()

    return UploadResponse(
        image_ids=image_ids,
        count=len(image_ids),
        message=f"成功导入 {len(image_ids)} 张图片"
        + (f"，{len(errors)} 张失败" if errors else ""),
    )
