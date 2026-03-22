import os
import sys
from pathlib import Path

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from web.backend.models.database import init_db
from web.backend.routers import images, labeling, training, models, pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="樟巢螟数据标注与模型训练系统",
    description="基于多模态大模型的自动化虫巢检测数据标注与 YOLOv8 模型训练 Web 界面",
    version="1.0.0",
    lifespan=lifespan,
)

import os

ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(images.router)
app.include_router(labeling.router)
app.include_router(training.router)
app.include_router(models.router)
app.include_router(pipeline.router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/app", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/api/health")
async def health_check():
    try:
        import torch

        gpu_available = torch.cuda.is_available()
    except ImportError:
        gpu_available = False

    return {
        "status": "ok",
        "version": "1.0.0",
        "gpu_available": gpu_available,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
