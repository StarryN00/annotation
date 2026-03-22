# 樟巢螟数据标注与模型训练系统 - 使用说明书

> **版本**: V1.0  
> **更新日期**: 2026-03-08  
> **适用对象**: 项目开发者、数据标注人员、模型训练工程师

---

## 目录

1. [系统概述](#一系统概述)
2. [环境准备](#二环境准备)
3. [快速开始](#三快速开始)
4. [详细使用指南](#四详细使用指南)
5. [配置文件说明](#五配置文件说明)
6. [CLI命令参考](#六cli命令参考)
7. [故障排除](#七故障排除)
8. [最佳实践](#八最佳实践)

---

## 一、系统概述

### 1.1 系统功能

本系统是一套端到端的**樟巢螟虫巢检测数据标注与模型训练工具链**，主要功能包括：

| 功能模块 | 说明 |
|---------|------|
| **AI自动标注** | 调用Claude/Kimi/OpenAI/Gemini等大模型，自动识别航拍图片中的虫巢位置 |
| **质量验证** | 可视化标注结果、统计分析、格式校验 |
| **数据集构建** | 自动划分训练/验证/测试集，生成YOLOv8配置文件 |
| **模型训练** | 基于YOLOv8的目标检测训练，支持数据增强 |
| **模型导出** | 导出PyTorch(.pt)和ONNX格式，便于部署 |

### 1.2 工作流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  原始图片   │ → │ AI自动标注  │ → │ 质量验证   │ → │ 数据集构建  │
│  (无人机)   │    │ (大模型API) │    │ (可视化)   │    │ (划分集合)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                               ↓
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  部署应用   │ ← │  模型导出   │ ← │ YOLOv8训练  │
│ (.pt/.onnx)│    │ (格式转换)  │    │ (目标检测)  │
└─────────────┘    └─────────────┘    └─────────────┘
```

---

## 二、环境准备

### 2.1 系统要求

- **操作系统**: Linux/macOS/Windows
- **Python版本**: Python 3.9+
- **GPU** (训练时推荐): NVIDIA GPU with CUDA 11.8+
- **内存**: 最低8GB，推荐16GB+
- **磁盘空间**: 预留50GB+（取决于数据集大小）

### 2.2 安装依赖

```bash
# 1. 克隆/进入项目目录
cd nest-labeling-pipeline

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或: venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt
```

**核心依赖清单**:
- `anthropic>=0.40.0` - Claude API客户端
- `openai>=1.50.0` - OpenAI API客户端  
- `httpx>=0.27.0` - HTTP客户端（Kimi/Gemini）
- `ultralytics>=8.1.0` - YOLOv8框架
- `torch>=2.0.0` - PyTorch深度学习框架
- `Pillow>=10.0.0` - 图像处理
- `PyYAML>=6.0` - YAML配置解析

### 2.3 配置API密钥

系统支持4种大模型，选择一种或多种配置：

```bash
# Claude (推荐，识图能力强)
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxx"

# Kimi (国内可用，性价比高)
export KIMI_API_KEY="sk-xxxxxxxx"

# OpenAI GPT-4o
export OPENAI_API_KEY="sk-xxxxxxxx"

# Google Gemini
export GOOGLE_API_KEY="xxxxxxxx"
```

**将上述命令添加到 `~/.bashrc` 或 `~/.zshrc` 实现永久配置。**

验证API配置：
```bash
echo $ANTHROPIC_API_KEY  # 应输出密钥值
```

---

## 三、快速开始

### 3.1 准备数据

将无人机航拍图片放入数据目录：

```bash
mkdir -p data/raw_images
cp /path/to/your/images/*.jpg data/raw_images/
```

**支持的图片格式**: `.jpg`, `.jpeg`, `.png`, `.webp`

### 3.2 选择模型

编辑 `config/config.yaml`，修改使用的模型：

```yaml
llm:
  provider: "claude"  # 可选: claude | kimi | openai | gemini
```

### 3.3 一键运行全流程

```bash
python scripts/run_full_pipeline.py --input data/raw_images/
```

运行完成后，产物位于：
- **标注数据**: `data/labels/`
- **质量报告**: `data/quality_reports/`
- **数据集**: `data/dataset/`
- **训练好的模型**: `outputs/models/nest_detector/weights/best.pt`
- **ONNX模型**: `outputs/models/best.onnx`

---

## 四、详细使用指南

### 4.1 分步执行（推荐用于调试）

#### Step 1: AI自动标注

```bash
python scripts/run_labeling.py \
    --input data/raw_images/ \
    --output data/labels/ \
    --provider claude \
    --verbose
```

**参数说明**:
- `--input`: 原始图片目录
- `--output`: 标注输出目录（默认使用配置文件中的路径）
- `--provider`: 覆盖配置，指定使用哪个模型
- `--verbose`: 显示详细日志

**输出**:
- `data/labels/*.txt` - YOLO格式标注文件
- `data/labels/classes.txt` - 类别定义
- `data/labels/labeling_report.json` - 标注统计报告

#### Step 2: 质量验证

```bash
python scripts/run_quality_check.py \
    --input data/raw_images/ \
    --labels data/labels/
```

**输出**:
- `data/quality_reports/statistics.json` - 统计数据
- `data/quality_reports/visualized/` - 可视化图片（带标注框）

**统计指标说明**:
- `total_images`: 总图片数
- `images_with_nests`: 含虫巢的图片数
- `nest_positive_rate`: 虫巢检出率
- `avg_nests_per_positive_image`: 每张阳性图片平均虫巢数

#### Step 3: 构建数据集

```bash
python scripts/run_build_dataset.py \
    --input data/raw_images/ \
    --labels data/labels/ \
    --output data/dataset/
```

**输出目录结构**:
```
data/dataset/
├── images/
│   ├── train/     # 70% 训练集
│   ├── val/       # 20% 验证集
│   └── test/      # 10% 测试集
├── labels/
│   ├── train/
│   ├── val/
│   └── test/
└── data.yaml      # YOLOv8数据集配置
```

#### Step 4: 训练模型

```bash
python scripts/run_training.py \
    --data data/dataset/data.yaml \
    --epochs 200 \
    --batch 16 \
    --device 0
```

**参数说明**:
- `--data`: 数据集配置文件路径
- `--epochs`: 训练轮数（默认200）
- `--batch`: 批大小（默认16，根据显存调整）
- `--device`: GPU设备号，`0`表示第一张GPU，`cpu`表示使用CPU

**训练过程输出**:
- 实时显示loss、mAP等指标
- 每10个epoch自动保存checkpoint
- 训练曲线图保存在 `outputs/models/nest_detector/`

#### Step 5: 模型评估与导出

训练脚本会自动执行评估和导出，如需手动操作：

```python
from src.training.train_yolo import evaluate_model
from src.training.export import export_model

# 评估模型
metrics = evaluate_model(
    model_path="outputs/models/nest_detector/weights/best.pt",
    data_yaml="data/dataset/data.yaml"
)
print(f"mAP@0.5: {metrics['mAP50']:.4f}")

# 导出ONNX
export_model(
    model_path="outputs/models/nest_detector/weights/best.pt",
    formats=["onnx", "engine"]  # engine为TensorRT格式
)
```

---

## 五、配置文件说明

### 5.1 主配置文件: `config/config.yaml`

```yaml
# ========== 大模型配置 ==========
llm:
  provider: "claude"  # 当前使用的模型
  
  claude:
    model: "claude-sonnet-4-20250514"
    api_key_env: "ANTHROPIC_API_KEY"
    max_tokens: 1024
    use_batch: false  # 是否使用Batch API（更便宜但慢）
  
  kimi:
    model: "moonshot-v1-128k"
    api_key_env: "KIMI_API_KEY"
    base_url: "https://api.moonshot.cn/v1"
    max_tokens: 1024

# ========== 标注配置 ==========
labeling:
  prompt_template: "config/prompts/nest_detection.txt"
  min_confidence: "low"      # 最低置信度: high/medium/low
  request_interval: 0.5      # API调用间隔（秒）
  max_retries: 3             # 失败重试次数
  supported_formats: [".jpg", ".jpeg", ".png", ".webp"]

# ========== 类别配置 ==========
classes:
  - name: "nest"
    id: 0
    description: "樟巢螟虫巢"

# ========== 数据集配置 ==========
dataset:
  train_ratio: 0.7   # 训练集比例
  val_ratio: 0.2     # 验证集比例
  test_ratio: 0.1    # 测试集比例
  seed: 42           # 随机种子（保证可复现）

# ========== 训练配置 ==========
training:
  yolo:
    model_size: "yolov8m"    # 模型大小: n/s/m/l/x
    pretrained: "yolov8m.pt" # 预训练权重
    epochs: 200
    batch_size: 16
    img_size: 640
    optimizer: "SGD"
    lr0: 0.01          # 初始学习率
    lrf: 0.01          # 最终学习率 = lr0 * lrf
    augment: true      # 启用数据增强
    device: "0"        # GPU编号

# ========== 路径配置 ==========
paths:
  raw_images: "data/raw_images"
  labels: "data/labels"
  quality_reports: "data/quality_reports"
  dataset: "data/dataset"
  models: "outputs/models"
  reports: "outputs/reports"
```

### 5.2 自定义提示词

编辑 `config/prompts/nest_detection.txt` 可修改LLM的检测指令。提示词必须包含：
- 虫巢的视觉特征描述
- 输出JSON格式要求（包含 `image_has_camphor_tree`, `detections`, `summary` 字段）
- 每个检测框的字段：`x_center`, `y_center`, `width`, `height`, `severity`, `confidence`

---

## 六、CLI命令参考

### 6.1 命令一览

| 命令 | 用途 | 常用参数 |
|------|------|----------|
| `run_labeling.py` | 自动标注 | `--input`, `--output`, `--provider` |
| `run_quality_check.py` | 质量验证 | `--input`, `--labels`, `--output` |
| `run_build_dataset.py` | 构建数据集 | `--input`, `--labels`, `--output` |
| `run_training.py` | 训练模型 | `--data`, `--epochs`, `--batch`, `--device` |
| `run_full_pipeline.py` | 一键全流程 | `--input`, `--skip-labeling` |

### 6.2 使用示例

**示例1: 使用Kimi进行标注（Claude额度不足时）**
```bash
python scripts/run_labeling.py \
    --input data/raw_images/ \
    --provider kimi \
    --verbose
```

**示例2: 跳过标注直接训练（已有标注数据）**
```bash
python scripts/run_full_pipeline.py \
    --input data/raw_images/ \
    --skip-labeling
```

**示例3: 减少训练轮数快速测试**
```bash
python scripts/run_training.py \
    --data data/dataset/data.yaml \
    --epochs 10 \
    --batch 8
```

**示例4: CPU训练（无GPU环境）**
```bash
python scripts/run_training.py \
    --data data/dataset/data.yaml \
    --device cpu
```

---

## 七、故障排除

### 7.1 常见问题

#### Q1: 导入错误 `ModuleNotFoundError: No module named 'anthropic'`

**原因**: 依赖未安装  
**解决**: 
```bash
pip install -r requirements.txt
```

#### Q2: API调用失败 `未设置 ANTHROPIC_API_KEY 环境变量`

**原因**: 环境变量未配置  
**解决**:
```bash
export ANTHROPIC_API_KEY="sk-xxx"
# 验证
echo $ANTHROPIC_API_KEY
```

#### Q3: 标注结果为空（所有图片都返回0个虫巢）

**可能原因**:
1. 提示词不清晰 → 检查 `config/prompts/nest_detection.txt`
2. 图片质量差 → 确保分辨率足够（建议>1024px）
3. API限流 → 增加 `request_interval` 到 1.0 或更高

**调试方法**:
```bash
python scripts/run_labeling.py --input data/raw_images/ --verbose
# 查看日志中的 raw_response 字段
```

#### Q4: 训练时报错 `CUDA out of memory`

**原因**: 显存不足  
**解决**: 减小批大小
```bash
python scripts/run_training.py --data data/dataset/data.yaml --batch 8  # 或更小
```

#### Q5: YOLO格式错误 `coordinates out of bounds`

**原因**: 标注坐标越界（不在0-1范围内）  
**解决**: 运行验证器检查并修复
```bash
python -c "
from src.quality.validator import validate_labels
results = validate_labels('data/labels/')
print(f'Invalid files: {results[\"errors\"]}')
"
```

#### Q6: 数据集划分后训练报错 `image not found`

**原因**: 图片与标注文件未对齐  
**解决**: 确保图片和标注文件名一致（除扩展名外）
```
image001.jpg  →  image001.txt
image002.png  →  image002.txt
```

### 7.2 调试模式

启用详细日志：
```bash
# 在Python代码中
import logging
logging.basicConfig(level=logging.DEBUG)

# 或在CLI命令中
python scripts/run_labeling.py --verbose
```

### 7.3 获取帮助

```bash
# 查看命令帮助
python scripts/run_labeling.py --help
python scripts/run_training.py --help
```

---

## 八、最佳实践

### 8.1 数据准备

1. **图片质量**: 建议分辨率≥1920x1080，格式统一为JPG
2. **数据量**: 至少100张以上图片用于训练，建议500+
3. **多样性**: 包含不同光照、角度、密度的虫巢样本
4. **命名规范**: 使用英文/数字命名，避免特殊字符

### 8.2 标注策略

1. **模型选择**: 
   - 精度优先: Claude/GPT-4o
   - 成本优先: Kimi/Gemini
   - 国内可用: Kimi

2. **置信度阈值**:
   - `high`: 只保留高置信度，用于高质量数据集
   - `medium`: 平衡质量和数量（推荐）
   - `low`: 保留所有结果，需人工复核

3. **人工抽检**: 即使使用AI标注，也建议抽检10-20%验证质量

### 8.3 训练优化

1. **预训练权重**: 始终使用预训练权重（yolov8m.pt）加速收敛
2. **数据增强**: 保持默认启用，提升泛化能力
3. **早停**: 默认patience=30，无需人工干预
4. **多GPU**: 多卡训练时修改 `device: "0,1"`

### 8.4 成本控制

| 模型 | 成本/千张 | 速度 | 建议场景 |
|------|-----------|------|----------|
| Claude | ~$5-10 | 中等 | 高精度需求 |
| Kimi | ~$2-5 | 快 | 大批量标注 |
| GPT-4o | ~$8-15 | 中等 | 复杂场景 |
| Gemini | ~$3-6 | 快 | 预算有限 |

**成本优化技巧**:
- 先用低成本模型（Kimi）标注，人工复核
- 使用 `use_batch: true` （Claude Batch API便宜50%）
- 小批量测试（50张）验证流程后再大批量处理

### 8.5 部署建议

训练好的模型部署：
```python
from ultralytics import YOLO

# 加载模型
model = YOLO('outputs/models/nest_detector/weights/best.pt')

# 推理
results = model('new_image.jpg')
for r in results:
    boxes = r.boxes  # 边界框
    print(f"检测到 {len(boxes)} 个虫巢")
```

---

## 附录

### A. YOLO格式说明

标注文件 `.txt` 格式：
```
<class_id> <x_center> <y_center> <width> <height>
```

示例：
```
0 0.553421 0.423156 0.082341 0.061234
0 0.712345 0.567890 0.054321 0.043210
```

- 所有值均为相对于图片宽高的比例（0-1）
- x_center, y_center: 边界框中心点坐标
- width, height: 边界框宽高

### B. 目录结构速查

```
nest-labeling-pipeline/
├── config/
│   ├── config.yaml
│   └── prompts/
│       ├── nest_detection.txt
│       └── tree_classification.txt
├── data/
│   ├── raw_images/        # 放入原始图片
│   ├── labels/            # 自动生成标注
│   ├── quality_reports/   # 自动生成报告
│   └── dataset/           # 自动生成数据集
├── outputs/
│   └── models/            # 训练好的模型
├── scripts/               # CLI脚本
├── src/                   # 源代码
└── tests/                 # 测试用例
```

### C. 更新日志

- **v1.0** (2026-03-08): 初始版本发布
  - 支持4种大模型适配器
  - 完整的标注→训练→导出流程
  - CLI一键运行支持

---

**文档维护**: 如有问题或建议，请提交Issue或联系开发团队。
