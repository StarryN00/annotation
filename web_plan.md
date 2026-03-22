# Web界面功能规划文档

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (React + Tailwind)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ 图片上传     │ │ 标注预览     │ │ 训练监控     │ │ 模型管理     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ HTTP/WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     后端 (FastAPI)                               │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                     API Router                               │ │
│  │  /api/upload    /api/label    /api/train    /api/models     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌─────────────┐   ┌─────────┴──────────┐   ┌─────────────┐     │
│  │ 标注服务     │   │    训练服务         │   │ 模型服务     │     │
│  │ (Labeler)   │   │   (YOLO Trainer)   │   │ (Export)    │     │
│  └─────────────┘   └────────────────────┘   └─────────────┘     │
│         │                   │                     │              │
│         └───────────────────┴─────────────────────┘              │
│                             │                                   │
│  ┌──────────────────────────┴──────────────────────────┐        │
│  │              任务队列 (AsyncIO Background Tasks)      │        │
│  │   - 标注任务队列                                      │        │
│  │   - 训练任务队列                                      │        │
│  │   - WebSocket 实时状态推送                            │        │
│  └──────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 页面设计

### 2.1 整体布局

```
┌──────────────────────────────────────────────────────────────────┐
│ 🌿 NestLabel                    [Dashboard] [Upload] [Train] [Models]│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│                    [主内容区域 - 根据路由切换]                      │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 页面路由

| 路由 | 名称 | 功能描述 |
|------|------|----------|
| `/` | Dashboard | 系统概览、统计卡片、最近任务 |
| `/upload` | 图片上传 | 批量上传图片、拖拽上传、上传进度 |
| `/label` | 自动标注 | 启动标注任务、实时进度、结果预览、人工修正 |
| `/dataset` | 数据集 | 训练/验证/测试集划分、数据增强配置 |
| `/train` | 模型训练 | 启动训练、实时监控训练曲线、早停控制 |
| `/models` | 模型管理 | 模型列表、性能对比、导出ONNX/TensorRT |
| `/visualize` | 可视化 | 查看标注结果、虫巢热力图、置信度分布 |

## 3. API 接口设计

### 3.1 图片管理
```yaml
POST /api/images/upload
  上传图片（支持多文件）
  Response: {image_ids: ["uuid1", "uuid2"], count: 2}

GET /api/images
  获取图片列表
  Query: ?page=1&limit=20&status=unlabeled|labeled|all
  Response: {items: [...], total: 100, page: 1}

GET /api/images/{image_id}
  获取单张图片详情
  Response: {id, filename, url, status, detections: [...]}

DELETE /api/images/{image_id}
  删除图片及其标注
```

### 3.2 标注任务
```yaml
POST /api/labeling/start
  启动标注任务
  Body: {image_ids: ["uuid1"], provider: "kimi", confidence: "medium"}
  Response: {task_id: "task_001", status: "pending"}

GET /api/labeling/tasks/{task_id}/status
  获取任务状态
  Response: {task_id, status, progress: 0.75, current_image: "xxx.jpg"}

WebSocket /ws/labeling/{task_id}
  实时标注进度推送
  Message: {type: "progress", current: 5, total: 20, image: "xxx.jpg", detections: 3}

POST /api/labeling/{image_id}/correct
  人工修正标注
  Body: {detections: [{x_center, y_center, width, height, severity}]}
```

### 3.3 数据集
```yaml
POST /api/dataset/build
  构建数据集
  Body: {train_ratio: 0.7, val_ratio: 0.2, test_ratio: 0.1, augment: true}
  Response: {dataset_id, splits: {train: 700, val: 200, test: 100}}

GET /api/dataset/{dataset_id}/preview
  预览数据集样本
  Response: {samples: [{split, image_url, label_count}]}
```

### 3.4 模型训练
```yaml
POST /api/training/start
  启动训练
  Body: {dataset_id, epochs: 200, batch_size: 16, device: "0", model_size: "m"}
  Response: {training_id, status: "starting"}

WebSocket /ws/training/{training_id}
  实时训练指标推送
  Message: {epoch: 10, loss: 2.3, mAP50: 0.65, lr: 0.01}

GET /api/training/{training_id}/status
  获取训练状态
  Response: {training_id, status: "running", epoch: 50/200, metrics: {...}}

POST /api/training/{training_id}/stop
  停止训练
```

### 3.5 模型管理
```yaml
GET /api/models
  获取模型列表
  Response: [{id, name, created_at, metrics: {mAP50, precision, recall}, status}]

POST /api/models/{model_id}/export
  导出模型
  Body: {format: "onnx|tensorrt|torchscript"}
  Response: {download_url, format, size}

DELETE /api/models/{model_id}
  删除模型

POST /api/models/{model_id}/evaluate
  在测试集上评估模型
  Response: {mAP50, precision, recall, confusion_matrix}
```

### 3.6 系统状态
```yaml
GET /api/health
  健康检查
  Response: {status: "ok", version: "1.0.0", gpu_available: true}

GET /api/config
  获取当前配置
  Response: {llm: {provider, model}, training: {...}}

PUT /api/config
  更新配置
  Body: {llm: {provider: "claude"}}
```

## 4. 数据模型

### 4.1 核心实体

```python
# 图片
class Image(BaseModel):
    id: str  # UUID
    filename: str
    path: str
    status: Literal["pending", "labeled", "verified", "error"]
    uploaded_at: datetime
    width: int
    height: int

# 检测结果
class Detection(BaseModel):
    id: str
    image_id: str
    x_center: float  # 0-1
    y_center: float
    width: float
    height: float
    severity: Literal["light", "medium", "severe"]
    confidence: float  # 0-1
    is_manual: bool  # 是否人工修正

# 标注任务
class LabelingTask(BaseModel):
    id: str
    status: Literal["pending", "running", "completed", "failed"]
    provider: str
    total_images: int
    processed_images: int
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]

# 训练任务
class TrainingTask(BaseModel):
    id: str
    dataset_id: str
    status: Literal["pending", "running", "completed", "stopped", "failed"]
    config: TrainingConfig
    metrics: Dict[str, float]  # mAP50, loss, etc.
    current_epoch: int
    total_epochs: int
    created_at: datetime
    best_model_path: Optional[str]

# 模型
class Model(BaseModel):
    id: str
    name: str
    training_id: str
    path: str
    metrics: Dict[str, float]
    created_at: datetime
    size_mb: float
```

## 5. 技术栈选择

### 5.1 后端
- **FastAPI**: 高性能异步框架
- **SQLAlchemy + SQLite**: 轻量级数据持久化
- **WebSocket**: 实时任务状态推送
- **Background Tasks**: 异步任务处理
- **Pydantic**: 数据验证

### 5.2 前端
- **React 18**: 组件化框架
- **Tailwind CSS**: 原子化样式
- **Vite**: 构建工具
- **Axios**: HTTP客户端
- **Recharts**: 图表可视化
- **React Query**: 数据获取和缓存

### 5.3 设计方向
- **Tone**: 专业工具感 + 林业自然主题
- **Color**: 深绿(#1a472a) + 暖金(#d4a574) + 米白(#faf8f5)
- **Typography**: 中文优先，清晰可读
- **Layout**: 左侧导航 + 主内容区

## 6. 任务队列设计

使用 FastAPI 的 BackgroundTasks 实现轻量级队列：

```python
class TaskManager:
    """管理标注和训练任务的执行"""
    
    async def start_labeling_task(self, task_id: str, image_ids: List[str]):
        # 异步执行标注
        # 通过 WebSocket 推送进度
        pass
    
    async def start_training_task(self, task_id: str, config: TrainingConfig):
        # 异步执行训练
        # 通过 WebSocket 推送训练指标
        pass
```

## 7. 安全考虑

1. **文件上传**: 限制文件类型(jpg/png/webp)、大小(<20MB)、文件名安全检查
2. **路径遍历**: 所有路径操作使用 Path 对象，禁止用户输入直接拼接到路径
3. **资源限制**: 限制并发任务数，防止资源耗尽
4. **CORS**: 配置允许的域名

## 8. 实施计划

| 阶段 | 任务 | 预计时间 |
|------|------|----------|
| 1 | FastAPI后端基础框架 + API路由 | 2h |
| 2 | 数据库模型 + 图片管理API | 2h |
| 3 | 标注任务API + WebSocket | 3h |
| 4 | 训练任务API + WebSocket | 2h |
| 5 | 前端React项目搭建 | 1h |
| 6 | 前端页面开发（上传/标注/训练） | 4h |
| 7 | 前端页面开发（可视化/模型管理） | 2h |
| 8 | 集成测试 + Bug修复 | 2h |
| 9 | 代码审计 + 文档 | 1h |

**总计: 约19小时**

---

*规划完成，准备进入开发阶段*
