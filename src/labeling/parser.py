import json
import logging
from .adapters.base import Detection, LabelingResult

logger = logging.getLogger(__name__)

CONFIDENCE_LEVELS = {"high": 3, "medium": 2, "low": 1}

MIN_CONFIDENCE_FILTER = {
    "high": 3,
    "medium": 2,
    "low": 1,
    "all": 0,
}


def parse_response(
    result: LabelingResult, min_confidence: str = "low"
) -> LabelingResult:
    """
    解析大模型返回的JSON，提取检测结果填充到 LabelingResult。

    此函数与具体的大模型无关，只处理统一的JSON格式。

    参数:
        result: 包含 raw_response 的 LabelingResult
        min_confidence: 最低置信度过滤阈值

    返回:
        填充了 detections 的 LabelingResult
    """
    if result.error or not result.raw_response:
        return result

    min_conf_level = CONFIDENCE_LEVELS.get(min_confidence, 1)

    try:
        text = result.raw_response.strip()

        # 处理可能的 markdown 代码块包裹
        if text.startswith("```"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[first_newline + 1 :]
            else:
                text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        data = json.loads(text)

        # 解析基础字段
        result.has_camphor_tree = data.get("image_has_camphor_tree", False)
        result.summary = data.get("summary", "")

        # 解析检测结果
        for det_data in data.get("detections", []):
            detection = Detection(
                x_center=float(det_data["x_center"]),
                y_center=float(det_data["y_center"]),
                width=float(det_data["width"]),
                height=float(det_data["height"]),
                severity=det_data.get("severity", "medium"),
                confidence=det_data.get("confidence", "medium"),
                class_id=0,
            )

            # 坐标合法性校验
            if not detection.is_valid():
                logger.warning(
                    f"坐标越界，跳过: "
                    f"({detection.x_center:.3f}, {detection.y_center:.3f})"
                )
                continue

            conf_level = CONFIDENCE_LEVELS.get(detection.confidence, 1)
            min_level = MIN_CONFIDENCE_FILTER.get(min_confidence, 1)
            if conf_level < min_level:
                continue

            result.detections.append(detection)

    except json.JSONDecodeError as e:
        result.error = f"JSON解析失败: {e}"
        logger.error(f"JSON解析失败: {result.raw_response[:200]}")
    except (KeyError, ValueError, TypeError) as e:
        result.error = f"数据格式错误: {e}"

    return result
