from ultralytics import YOLO


def export_model(
    model_path: str,
    formats: list[str] = None,
    output_dir: str = "outputs/models",
):
    """
    将训练好的模型导出为多种格式。

    参数:
        model_path: .pt 模型路径
        formats: 导出格式列表，如 ["onnx", "engine"]
        output_dir: 输出目录
    """
    if formats is None:
        formats = ["onnx"]

    model = YOLO(model_path)

    exported_files = {}
    for fmt in formats:
        path = model.export(format=fmt)
        exported_files[fmt] = str(path)
        print(f"已导出 {fmt}: {path}")

    return exported_files
