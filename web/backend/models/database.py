"""
数据库模型定义
使用 SQLAlchemy 2.0 语法
"""

from datetime import datetime
from enum import Enum as PyEnum
from pathlib import Path
from typing import Optional, List

from sqlalchemy import create_engine, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


class Base(DeclarativeBase):
    pass


# ============== 枚举类型 ==============
class ImageStatus(str, PyEnum):
    PENDING = "pending"  # 待标注
    LABELING = "labeling"  # 标注中
    LABELED = "labeled"  # 已标注
    VERIFIED = "verified"  # 已验证
    ERROR = "error"  # 出错


class TaskStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class Severity(str, PyEnum):
    LIGHT = "light"
    MEDIUM = "medium"
    SEVERE = "severe"


# ============== 数据表 ==============
class Image(Base):
    """图片表"""

    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), index=True)
    path: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=ImageStatus.PENDING)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    width: Mapped[Optional[int]] = mapped_column(nullable=True)
    height: Mapped[Optional[int]] = mapped_column(nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(nullable=True)  # bytes

    # 关联
    detections: Mapped[List["Detection"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )


class Detection(Base):
    """检测结果表"""

    __tablename__ = "detections"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    image_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("images.id", ondelete="CASCADE")
    )
    x_center: Mapped[float] = mapped_column(Float)
    y_center: Mapped[float] = mapped_column(Float)
    width: Mapped[float] = mapped_column(Float)
    height: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(20), default=Severity.MEDIUM)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    is_manual: Mapped[bool] = mapped_column(default=False)  # 是否人工修正
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关联
    image: Mapped["Image"] = relationship(back_populates="detections")


class LabelingTask(Base):
    """标注任务表"""

    __tablename__ = "labeling_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.PENDING)
    provider: Mapped[str] = mapped_column(String(50))  # kimi/claude/openai/gemini
    confidence: Mapped[str] = mapped_column(String(20), default="medium")
    total_images: Mapped[int] = mapped_column(default=0)
    processed_images: Mapped[int] = mapped_column(default=0)
    success_count: Mapped[int] = mapped_column(default=0)
    error_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 存储关联的图片ID列表 (JSON)
    image_ids: Mapped[str] = mapped_column(Text, default="[]")


class TrainingTask(Base):
    """训练任务表"""

    __tablename__ = "training_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default=TaskStatus.PENDING)

    # 训练配置
    dataset_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    model_size: Mapped[str] = mapped_column(String(10), default="m")  # n/s/m/l/x
    epochs: Mapped[int] = mapped_column(default=200)
    batch_size: Mapped[int] = mapped_column(default=16)
    device: Mapped[str] = mapped_column(String(10), default="0")

    # 训练进度
    current_epoch: Mapped[int] = mapped_column(default=0)
    total_epochs: Mapped[int] = mapped_column(default=0)

    # 指标 (存储为JSON)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 模型路径
    best_model_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Model(Base):
    """训练好的模型表"""

    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    training_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    path: Mapped[str] = mapped_column(Text)
    metrics: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # mAP50, precision, recall
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    size_mb: Mapped[float] = mapped_column(default=0.0)
    format: Mapped[str] = mapped_column(String(20), default="pt")  # pt/onnx/engine


class Dataset(Base):
    """数据集表"""

    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(Text)
    train_count: Mapped[int] = mapped_column(default=0)
    val_count: Mapped[int] = mapped_column(default=0)
    test_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # 划分比例等


# ============== 数据库连接 ==============
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = BASE_DIR / "data" / "app.db"
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """获取数据库会话"""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
