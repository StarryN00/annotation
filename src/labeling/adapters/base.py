from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import base64
from pathlib import Path


@dataclass
class Detection:
    """单个虫巢检测结果"""

    x_center: float  # 0~1, 相对图片宽度
    y_center: float  # 0~1, 相对图片高度
    width: float  # 0~1
    height: float  # 0~1
    severity: str = "medium"  # light / medium / severe
    confidence: str = "medium"  # high / medium / low
    class_id: int = 0

    def is_valid(self) -> bool:
        """坐标合法性检查"""
        return (
            0 <= self.x_center <= 1
            and 0 <= self.y_center <= 1
            and 0 < self.width <= 1
            and 0 < self.height <= 1
            and self.x_center - self.width / 2 >= -0.01
            and self.x_center + self.width / 2 <= 1.01
            and self.y_center - self.height / 2 >= -0.01
            and self.y_center + self.height / 2 <= 1.01
        )

    def to_yolo_line(self) -> str:
        """转为YOLO格式: class_id x_center y_center width height"""
        return f"{self.class_id} {self.x_center:.6f} {self.y_center:.6f} {self.width:.6f} {self.height:.6f}"


@dataclass
class LabelingResult:
    """单张图片的标注结果"""

    image_path: str
    has_camphor_tree: bool = False
    detections: list = field(default_factory=list)  # List[Detection]
    summary: str = ""
    error: Optional[str] = None
    raw_response: str = ""
    token_input: int = 0
    token_output: int = 0


class BaseLLMAdapter(ABC):
    """
    大模型适配器基类。

    所有适配器必须实现 detect_nests() 方法，
    接收图片路径，返回统一的 LabelingResult。

    新增适配器只需:
    1. 继承此类
    2. 实现 detect_nests() 方法
    3. 在 adapter_factory() 中注册
    """

    def __init__(self, config: dict):
        """
        参数:
            config: 该适配器对应的配置字典
                    如 config['llm']['claude'] 的内容
        """
        self.config = config

    @abstractmethod
    def detect_nests(self, image_path: str, prompt: str) -> LabelingResult:
        """
        调用大模型分析图片，检测虫巢。

        参数:
            image_path: 图片文件路径
            prompt: 用户提示词（描述任务和输出格式）

        返回:
            LabelingResult 统一结构
        """
        pass

    def encode_image_base64(self, image_path: str) -> tuple[str, str]:
        """将图片编码为base64，返回 (data, media_type)"""
        path = Path(image_path)
        media_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
        }
        media_type = media_map.get(path.suffix.lower(), "image/jpeg")
        with open(image_path, "rb") as f:
            data = base64.standard_b64encode(f.read()).decode("utf-8")
        return data, media_type


def adapter_factory(provider: str, config: dict) -> BaseLLMAdapter:
    """
    适配器工厂函数。根据 provider 名称返回对应的适配器实例。

    参数:
        provider: "claude" / "kimi" / "openai" / "gemini"
        config: 对应模型的配置字典
    """
    # 延迟导入，避免导入错误影响其他适配器
    if provider == "claude":
        from .claude_adapter import ClaudeAdapter

        return ClaudeAdapter(config)
    elif provider == "kimi":
        from .kimi_adapter import KimiAdapter

        return KimiAdapter(config)
    elif provider == "openai":
        from .openai_adapter import OpenAIAdapter

        return OpenAIAdapter(config)
    elif provider == "gemini":
        from .gemini_adapter import GeminiAdapter

        return GeminiAdapter(config)
    else:
        raise ValueError(
            f"不支持的模型: {provider}。支持: claude, kimi, openai, gemini"
        )
