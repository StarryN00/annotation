#!/usr/bin/env python3

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, "/Users/starryn/project/annotation")

from web.backend.models.database import (
    async_session_maker,
    Image,
    ImageStatus,
    Detection,
)
from sqlalchemy import select


async def import_images():
    uploads_dir = Path("/Users/starryn/project/annotation/web/backend/uploads")
    labels_dir = Path("/Users/starryn/project/annotation/data/labels")

    image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    image_files = [
        f for f in uploads_dir.iterdir() if f.suffix.lower() in image_extensions
    ]

    print(f"找到 {len(image_files)} 张图片")
    print(f"前5个文件: {[f.name for f in image_files[:5]]}")

    async with async_session_maker() as db:
        imported = 0
        labeled = 0

        for img_path in image_files:
            image_id = img_path.stem

            result = await db.execute(select(Image).where(Image.id == image_id))
            if result.scalar_one_or_none():
                continue

            label_file = labels_dir / f"{image_id}.txt"
            has_label = label_file.exists() and label_file.stat().st_size > 0

            image = Image(
                id=image_id,
                filename=img_path.name,
                original_filename=img_path.name,
                status=ImageStatus.LABELED if has_label else ImageStatus.PENDING,
                uploaded_at=datetime.fromtimestamp(img_path.stat().st_mtime),
                width=0,
                height=0,
            )
            db.add(image)
            imported += 1

            if has_label:
                with open(label_file, "r") as f:
                    lines = f.readlines()

                for line in lines:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        det = Detection(
                            id=str(os.urandom(16).hex()),
                            image_id=image_id,
                            class_id=0,
                            x_center=float(parts[1]),
                            y_center=float(parts[2]),
                            width=float(parts[3]),
                            height=float(parts[4]),
                            confidence=0.9,
                            source="auto",
                        )
                        db.add(det)
                        labeled += 1

            if imported % 50 == 0:
                print(f"已导入 {imported} 张图片...")
                await db.commit()

        await db.commit()
        print(f"\n导入完成!")
        print(f"  - 图片总数: {imported}")
        print(f"  - 标注框数: {labeled}")


if __name__ == "__main__":
    asyncio.run(import_images())
