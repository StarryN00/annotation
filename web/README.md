# Web 界面使用说明

## 功能概述

本 Web 界面为樟巢螟数据标注与模型训练系统提供图形化操作界面，包含以下功能模块：

- **概览 Dashboard** - 系统状态总览、统计卡片、最近任务
- **图片管理** - 批量上传、预览、删除图片
- **自动标注** - 调用大模型 API 自动检测虫巢位置
- **模型训练** - 数据集构建、YOLOv8 训练、实时监控
- **模型管理** - 模型列表、性能查看、导出 ONNX

## 架构说明

```
前端 (React + Tailwind CSS)  <->  后端 (FastAPI + SQLite)  <->  核心系统 (标注/训练模块)
```

## 快速开始

### 1. 安装依赖

```bash
# 安装 Web 后端依赖
pip install -r requirements_web.txt

# 安装前端依赖
cd web/frontend
npm install
```

### 2. 启动服务

**方式一：开发模式（推荐）**

终端 1 - 启动后端：
```bash
cd web/backend
python main.py
```

终端 2 - 启动前端：
```bash
cd web/frontend
npm run dev
```

访问 http://localhost:3000

**方式二：生产模式**

```bash
# 构建前端
cd web/frontend
npm run build

# 启动后端（会自动提供静态文件）
cd web/backend
python main.py
```

访问 http://localhost:8000

## 功能使用指南

### 图片上传

1. 进入"图片"页面
2. 点击"上传图片"按钮
3. 选择 JPG/PNG/WEBP 格式的图片
4. 支持批量上传（最多50张）

### 自动标注

1. 确保已有待标注的图片
2. 进入"标注"页面
3. 选择模型（Kimi/Claude/OpenAI/Gemini）
4. 选择置信度阈值
5. 点击"开始标注"
6. 通过 WebSocket 实时查看进度

### 模型训练

1. 先完成图片标注
2. 点击"构建新数据集"划分训练/验证/测试集
3. 配置训练参数（模型大小、轮数、批大小）
4. 点击"开始训练"
5. 实时监控训练进度和指标

### 模型导出

1. 训练完成后进入"模型"页面
2. 查看模型性能指标
3. 点击"下载 PyTorch"或"导出 ONNX"

## API 接口

所有 API 以 `/api` 为前缀：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/images` | GET/POST | 图片列表/上传 |
| `/api/images/{id}` | GET/DELETE | 图片详情/删除 |
| `/api/labeling/start` | POST | 开始标注任务 |
| `/api/labeling/tasks` | GET | 标注任务列表 |
| `/api/dataset/build` | POST | 构建数据集 |
| `/api/training/start` | POST | 开始训练任务 |
| `/api/training/tasks` | GET | 训练任务列表 |
| `/api/models` | GET | 模型列表 |
| `/api/models/{id}/export` | POST | 导出模型 |

WebSocket 接口：
- `/ws/labeling/{task_id}` - 标注进度实时推送
- `/ws/training/{task_id}` - 训练进度实时推送

## 配置说明

### 后端配置

环境变量：
- `ALLOWED_ORIGINS` - 允许的跨域来源，默认 `http://localhost:3000`
- `KIMI_API_KEY` / `ANTHROPIC_API_KEY` - API 密钥

数据库：
- SQLite 文件：`web/backend/data/app.db`

上传文件：
- 存储目录：`web/backend/uploads/`

### 前端配置

`vite.config.js`：
- 开发服务器端口：3000
- 代理配置：API 请求转发到 8000 端口

## 目录结构

```
web/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── data/                # SQLite 数据库
│   ├── uploads/             # 上传图片存储
│   ├── models/
│   │   ├── database.py      # SQLAlchemy 模型
│   │   └── schemas.py       # Pydantic 校验
│   ├── routers/
│   │   ├── images.py        # 图片 API
│   │   ├── labeling.py      # 标注 API
│   │   ├── training.py      # 训练 API
│   │   └── models.py        # 模型 API
│   └── services/
│       └── task_manager.py  # 任务管理器
├── frontend/
│   ├── src/
│   │   ├── main.jsx         # 入口
│   │   ├── App.jsx          # 主应用
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API 调用
│   │   └── styles/          # CSS 样式
│   └── package.json
└── README.md
```

## 注意事项

1. **API 密钥** - 确保已配置环境变量，否则标注功能无法使用
2. **GPU 训练** - 确保已安装 CUDA，否则训练会自动使用 CPU
3. **文件大小** - 单张图片最大 20MB，单次最多上传 50 张
4. **并发限制** - 同时只能运行一个标注任务和一个训练任务

## 故障排除

### 前端无法连接后端

检查 `vite.config.js` 中的 proxy 配置，确保指向正确的后端地址。

### 数据库错误

删除 `web/backend/data/app.db` 重新初始化。

### 标注任务卡住

检查 API 密钥是否正确配置，查看后端日志获取详细错误信息。

### 训练失败

- 检查是否有足够的已标注图片（至少 10 张）
- 检查 GPU 显存是否足够，可减小 batch_size
- 查看 `outputs/models/` 目录的日志文件
