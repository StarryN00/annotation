from pathlib import Path
from .adapters.base import LabelingResult


def save_yolo_label(result: LabelingResult, output_dir: str) -> str:
    """
    将标注结果保存为YOLO格式的 .txt 文件。

    YOLO格式: 每行一个目标
    class_id x_center y_center width height

    参数:
        result: 标注结果
        output_dir: 标注文件输出目录

    返回:
        保存的标注文件路径
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_stem = Path(result.image_path).stem
    label_path = output_dir / f"{image_stem}.txt"

    with open(label_path, "w") as f:
        for det in result.detections:
            f.write(det.to_yolo_line() + "\n")

    return str(label_path)


def generate_classes_file(output_dir: str, classes: list[dict]) -> str:
    """
    生成 classes.txt 文件。

    参数:
        output_dir: 输出目录
        classes: 类别列表 [{"id": 0, "name": "nest"}, ...]
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    classes_path = output_dir / "classes.txt"
    sorted_classes = sorted(classes, key=lambda c: c["id"])

    with open(classes_path, "w") as f:
        for cls in sorted_classes:
            f.write(cls["name"] + "\n")

    return str(classes_path)
