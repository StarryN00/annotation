"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DetectionSchema(BaseModel):
    id: str
    image_id: str
    x_center: float = Field(..., ge=0, le=1)
    y_center: float = Field(..., ge=0, le=1)
    width: float = Field(..., ge=0, le=1)
    height: float = Field(..., ge=0, le=1)
    severity: str
    confidence: float = Field(..., ge=0, le=1)
    is_manual: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ImageSchema(BaseModel):
    id: str
    filename: str
    path: str
    status: str
    uploaded_at: datetime
    width: Optional[int]
    height: Optional[int]
    file_size: Optional[int]
    detections: List[DetectionSchema] = []

    class Config:
        from_attributes = True


class ImageListResponse(BaseModel):
    items: List[ImageSchema]
    total: int
    page: int
    limit: int


class UploadResponse(BaseModel):
    image_ids: List[str]
    count: int
    message: Optional[str] = None


class LabelingTaskSchema(BaseModel):
    id: str
    status: str
    provider: str
    confidence: str
    total_images: int
    processed_images: int
    success_count: int
    error_count: int
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True


class StartLabelingRequest(BaseModel):
    image_ids: List[str]
    provider: str = Field(default="kimi", pattern="^(kimi|claude|openai|gemini)$")
    confidence: str = Field(default="medium", pattern="^(low|medium|high)$")


class LabelingProgressMessage(BaseModel):
    type: str = "progress"
    task_id: str
    current: int
    total: int
    image_name: str
    detections_count: int


class TrainingTaskSchema(BaseModel):
    id: str
    status: str
    dataset_id: Optional[str]
    model_size: str
    epochs: int
    batch_size: int
    device: str
    current_epoch: int
    total_epochs: int
    metrics: Optional[dict]
    created_at: datetime
    completed_at: Optional[datetime]
    best_model_path: Optional[str]

    class Config:
        from_attributes = True


class StartTrainingRequest(BaseModel):
    dataset_id: Optional[str] = None
    model_size: str = Field(default="m", pattern="^(n|s|m|l|x)$")
    epochs: int = Field(default=200, ge=1, le=1000)
    batch_size: int = Field(default=16, ge=1, le=128)
    device: str = Field(default="0")


class TrainingProgressMessage(BaseModel):
    type: str = "training_progress"
    task_id: str
    epoch: int
    total_epochs: int
    loss: Optional[float]
    mAP50: Optional[float]
    lr: Optional[float]


class DatasetSchema(BaseModel):
    id: str
    name: str
    path: str
    train_count: int
    val_count: int
    test_count: int
    created_at: datetime
    config: Optional[dict]

    class Config:
        from_attributes = True


class BuildDatasetRequest(BaseModel):
    train_ratio: float = Field(default=0.7, ge=0, le=1)
    val_ratio: float = Field(default=0.2, ge=0, le=1)
    test_ratio: float = Field(default=0.1, ge=0, le=1)
    augment: bool = True


class ModelSchema(BaseModel):
    id: str
    name: str
    training_id: Optional[str]
    path: str
    metrics: Optional[dict]
    created_at: datetime
    size_mb: float
    format: str

    class Config:
        from_attributes = True


class ExportModelRequest(BaseModel):
    format: str = Field(pattern="^(onnx|tensorrt|torchscript)$")


class ExportModelResponse(BaseModel):
    download_url: str
    format: str
    size_mb: float


class CorrectionRequest(BaseModel):
    detections: List[dict]


class HealthResponse(BaseModel):
    status: str
    version: str
    gpu_available: bool
