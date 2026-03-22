import time
import logging
from pathlib import Path

from .adapters.base import adapter_factory, LabelingResult
from .parser import parse_response
from .converter import save_yolo_label, generate_classes_file

logger = logging.getLogger(__name__)


class AutoLabeler:
    """
    自动标注主流程。

    职责:
    1. 遍历图片目录
    2. 调用大模型适配器获取检测结果
    3. 解析响应并验证
    4. 保存为YOLO格式标注文件
    5. 生成统计报告
    """

    def __init__(self, config: dict):
        self.config = config
        llm_config = config["llm"]
        provider = llm_config["provider"]
        provider_config = llm_config[provider]

        # 创建适配器（可替换，由配置决定）
        self.adapter = adapter_factory(provider, provider_config)
        self.provider = provider

        # 标注配置
        label_config = config.get("labeling", {})
        self.min_confidence = label_config.get("min_confidence", "low")
        self.request_interval = label_config.get("request_interval", 0.5)
        self.max_retries = label_config.get("max_retries", 3)
        self.supported_formats = set(
            label_config.get("supported_formats", [".jpg", ".jpeg", ".png"])
        )

        # 加载提示词模板
        prompt_path = label_config.get("prompt_template")
        if prompt_path and Path(prompt_path).exists():
            self.prompt = Path(prompt_path).read_text(encoding="utf-8")
        else:
            self.prompt = self._default_prompt()

    def run(self, input_dir: str, output_dir: str) -> list[LabelingResult]:
        """
        运行批量标注。

        参数:
            input_dir: 图片目录
            output_dir: 标注输出目录

        返回:
            所有图片的标注结果列表
        """
        input_dir = Path(input_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 收集图片
        images = sorted(
            [
                f
                for f in input_dir.iterdir()
                if f.suffix.lower() in self.supported_formats
            ]
        )

        if not images:
            logger.error(f"目录中未找到图片: {input_dir}")
            return []

        logger.info(f"使用模型: {self.provider}")
        logger.info(f"找到 {len(images)} 张图片，开始标注...")

        results = []
        stats = {
            "total": len(images),
            "success": 0,
            "error": 0,
            "with_nest": 0,
            "total_nests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
        }

        for i, img_path in enumerate(images, 1):
            logger.info(f"[{i}/{len(images)}] {img_path.name}")

            # 调用适配器（含重试）
            result = self._call_with_retry(str(img_path))

            # 解析响应
            if not result.error:
                result = parse_response(result, self.min_confidence)

            # 保存标注
            if not result.error:
                save_yolo_label(result, str(output_dir))
                stats["success"] += 1
                if result.detections:
                    stats["with_nest"] += 1
                    stats["total_nests"] += len(result.detections)
                logger.info(f"  → {len(result.detections)} 个虫巢")
            else:
                stats["error"] += 1
                logger.error(f"  ✗ {result.error}")

            stats["total_input_tokens"] += result.token_input
            stats["total_output_tokens"] += result.token_output
            results.append(result)

            # 请求间隔
            if i < len(images):
                time.sleep(self.request_interval)

        # 生成类别文件
        generate_classes_file(str(output_dir), self.config.get("classes", []))

        # 打印统计
        self._print_stats(stats)

        # 保存标注报告
        self._save_report(results, stats, str(output_dir))

        return results

    def _call_with_retry(self, image_path: str) -> LabelingResult:
        """带重试的API调用"""
        for attempt in range(self.max_retries):
            result = self.adapter.detect_nests(image_path, self.prompt)
            if not result.error:
                return result
            if attempt < self.max_retries - 1:
                wait = self.request_interval * (2**attempt)
                logger.warning(f"  重试 {attempt + 1}/{self.max_retries}，等待 {wait}s")
                time.sleep(wait)
        return result

    def _print_stats(self, stats: dict):
        """打印统计信息"""
        logger.info("\n" + "=" * 50)
        logger.info(f"标注完成 | 模型: {self.provider}")
        logger.info("=" * 50)
        logger.info(f"总图片数:    {stats['total']}")
        logger.info(f"成功标注:    {stats['success']}")
        logger.info(f"标注失败:    {stats['error']}")
        logger.info(f"含虫巢图片:  {stats['with_nest']}")
        logger.info(f"总虫巢数:    {stats['total_nests']}")
        logger.info(f"输入tokens:  {stats['total_input_tokens']:,}")
        logger.info(f"输出tokens:  {stats['total_output_tokens']:,}")

    def _save_report(self, results, stats, output_dir):
        """保存JSON格式的标注报告"""
        import json

        report = {
            "provider": self.provider,
            "stats": stats,
            "details": [
                {
                    "image": Path(r.image_path).name,
                    "nest_count": len(r.detections),
                    "has_camphor_tree": r.has_camphor_tree,
                    "summary": r.summary,
                    "error": r.error,
                }
                for r in results
            ],
        }
        report_path = Path(output_dir) / "labeling_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def _default_prompt(self) -> str:
        """默认提示词（当配置文件中的模板不存在时使用）"""
        return """请仔细分析这张无人机航拍图像，检测图中所有的樟巢螟虫巢。

樟巢螟虫巢的特征：
1. 颜色：棕褐色/暗褐色，与周围绿色树叶形成强烈对比
2. 形态：叶片卷缩、枯萎、缀叶成团，不规则团块状
3. 纹理：虫巢表面可见丝网结构
4. 位置：通常在树冠中上部

对于每个检测到的虫巢，返回：
- x_center, y_center: 中心点相对坐标 (0~1)，左上角为(0,0)
- width, height: 边界框相对宽高 (0~1)
- severity: 严重程度 "light" / "medium" / "severe"
- confidence: 置信度 "high" / "medium" / "low"

严格按以下JSON格式回复，不要有其他文字：
{
  "image_has_camphor_tree": true,
  "detections": [
    {
      "x_center": 0.55,
      "y_center": 0.42,
      "width": 0.08,
      "height": 0.06,
      "severity": "medium",
      "confidence": "high"
    }
  ],
  "summary": "简要描述"
}

如果没有检测到虫巢:
{
  "image_has_camphor_tree": false,
  "detections": [],
  "summary": "未检测到虫巢"
}"""
