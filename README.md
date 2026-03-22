# 樟巢螟数据标注与模型训练系统

基于多模态大模型的自动化虫巢检测数据标注与 YOLOv8 模型训练管线。

## 系统架构

```
原始航拍图片
    │
    ▼
┌─────────────────────────────────────┐
│ Step 1: AI自动标注 (Claude/Kimi/    │  调用大模型识别虫巢位置
│          OpenAI/Gemini)             │  输出 YOLO 格式标注文件
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ Step 2: 标注质量验证                │  可视化抽检 + 统计分析
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ Step 3: 数据集构建                  │  划分训练/验证/测试集
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ Step 4: YOLOv8 模型训练             │  目标检测训练
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ Step 5: 模型评估与导出              │  评估指标验证 → 导出ONNX
└─────────────────────────────────────┘
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
export ANTHROPIC_API_KEY="sk-xxx"       # 如果用 Claude
export KIMI_API_KEY="sk-xxx"            # 如果用 Kimi
export OPENAI_API_KEY="sk-xxx"          # 如果用 OpenAI
export GOOGLE_API_KEY="xxx"             # 如果用 Gemini
```

### 3. 修改配置（可选）

编辑 `config/config.yaml` 选择模型和调整参数：

```yaml
llm:
  provider: "claude"  # 或 kimi / openai / gemini
```

### 4. 一键运行全流程

```bash
python scripts/run_full_pipeline.py --input data/raw_images/
```

或分步运行：

```bash
# 仅运行自动标注
python scripts/run_labeling.py --input data/raw_images/ --provider claude

# 质量检查
python scripts/run_quality_check.py

# 构建数据集
python scripts/run_build_dataset.py

# 训练模型
python scripts/run_training.py
```

### 5. 交付产物

训练完成后，模型权重位于：
- `outputs/models/nest_detector/weights/best.pt` - PyTorch 格式
- `outputs/models/best.onnx` - ONNX 格式

## 项目结构

```
nest-labeling-pipeline/
├── config/
│   ├── config.yaml              # 全局配置
│   └── prompts/
│       └── nest_detection.txt   # LLM提示词模板
├── src/
│   ├── labeling/                # 自动标注模块
│   │   ├── adapters/            # 多模型适配器（Claude/Kimi/OpenAI/Gemini）
│   │   ├── parser.py            # JSON响应解析
│   │   ├── converter.py         # YOLO格式转换
│   │   └── labeler.py           # 标注主流程
│   ├── quality/                 # 质量验证模块
│   │   ├── visualizer.py        # 标注可视化
│   │   ├── statistics.py        # 统计分析
│   │   └── validator.py         # 格式验证
│   ├── dataset/                 # 数据集构建模块
│   │   └── splitter.py          # 训练/验证/测试集划分
│   ├── training/                # 模型训练模块
│   │   ├── train_yolo.py        # YOLOv8训练
│   │   └── export.py            # 模型导出
│   └── utils/                   # 工具函数
├── scripts/                     # 命令行入口
│   ├── run_labeling.py
│   ├── run_quality_check.py
│   ├── run_build_dataset.py
│   ├── run_training.py
│   └── run_full_pipeline.py
├── data/                        # 数据目录
│   ├── raw_images/              # 原始航拍图片
│   ├── labels/                  # 自动标注输出
│   ├── quality_reports/         # 质量检查报告
│   └── dataset/                 # 构建好的数据集
└── outputs/                     # 训练输出
    ├── models/                  # 训练好的模型权重
    └── reports/                 # 训练报告
```

## 核心特性

### 多模型适配器架构

通过适配器模式支持多种大模型，切换模型只需修改配置：

```python
# config.yaml
llm:
  provider: "claude"  # 或 kimi / openai / gemini
```

新增适配器仅需：
1. 继承 `BaseLLMAdapter`
2. 实现 `detect_nests()` 方法
3. 在工厂函数中注册

### 标注质量验证

- **可视化检查**: 在图片上绘制标注框，人工抽检
- **统计分析**: 虫巢分布、检出率、边界框大小统计
- **格式验证**: 自动检查坐标越界、格式错误

### 数据集划分

支持自定义划分比例（默认 70% / 20% / 10%）：

```yaml
dataset:
  train_ratio: 0.7
  val_ratio: 0.2
  test_ratio: 0.1
  seed: 42  # 可复现
```

### YOLOv8 训练

自动化训练流程：
- 预训练权重加载
- 数据增强（mosaic, mixup, flip等）
- 早停机制
- 自动保存最佳模型
- 训练可视化

## 配置说明

详见 `config/config.yaml`：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `llm.provider` | 使用的大模型 | `claude` |
| `labeling.min_confidence` | 最低置信度过滤 | `low` |
| `labeling.request_interval` | API调用间隔(秒) | `0.5` |
| `dataset.train_ratio` | 训练集比例 | `0.7` |
| `training.yolo.epochs` | 训练轮数 | `200` |
| `training.yolo.batch_size` | 批大小 | `16` |
| `training.yolo.img_size` | 输入图像尺寸 | `640` |

## 开发说明

### 运行测试

```bash
pytest tests/ -v
```

### 添加新的LLM适配器

1. 创建 `src/labeling/adapters/new_adapter.py`:

```python
from .base import BaseLLMAdapter, LabelingResult

class NewAdapter(BaseLLMAdapter):
    def detect_nests(self, image_path: str, prompt: str) -> LabelingResult:
        result = LabelingResult(image_path=image_path)
        # 实现API调用逻辑
        return result
```

2. 在 `adapters/base.py` 的 `adapter_factory()` 中注册

3. 在 `config.yaml` 中添加配置

## 依赖项

- Python 3.9+
- anthropic - Claude API
- openai - OpenAI API
- httpx - HTTP客户端
- Pillow - 图像处理
- PyYAML - 配置文件
- ultralytics - YOLOv8
- torch - PyTorch

## 许可证

MIT License
