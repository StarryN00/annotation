from ultralytics import YOLO
from pathlib import Path
import json
import os


def train_nest_detector(
    data_yaml: str,
    model_size: str = "yolov8m",
    pretrained: str = "yolov8m.pt",
    epochs: int = 200,
    batch_size: int = 16,
    img_size: int = 640,
    device: str = "0",
    output_dir: str = "outputs/models",
    progress_file: str = ".training_progress.json",
    **kwargs,
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    progress_path = Path(progress_file)

    def save_progress(current, total):
        try:
            data = {
                "current_epoch": current,
                "total_epochs": total,
                "progress_percent": round((current / total * 100), 1)
                if total > 0
                else 0,
            }
            progress_path.write_text(json.dumps(data))
        except Exception:
            pass

    save_progress(0, epochs)

    model = YOLO(pretrained)

    def epoch_callback(trainer):
        if hasattr(trainer, "epoch"):
            save_progress(trainer.epoch + 1, trainer.epochs)

    # 添加训练回调
    try:
        model.add_callback("on_train_epoch_start", epoch_callback)
    except Exception:
        pass

    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        project=str(output_dir),
        name="nest_detector",
        optimizer=kwargs.get("optimizer", "SGD"),
        lr0=kwargs.get("lr0", 0.01),
        lrf=kwargs.get("lrf", 0.01),
        augment=kwargs.get("augment", True),
        mosaic=1.0,
        mixup=0.1,
        flipud=0.5,
        fliplr=0.5,
        degrees=15.0,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        patience=30,
        save_period=10,
        plots=True,
        verbose=True,
    )

    save_progress(epochs, epochs)

    best_path = None
    weights_dir = output_dir / "nest_detector" / "weights"
    if not weights_dir.exists():
        for subdir in output_dir.glob("nest_detector*"):
            potential_weights = subdir / "weights"
            if potential_weights.exists():
                weights_dir = potential_weights
                break

    if weights_dir.exists():
        best_pt = weights_dir / "best.pt"
        if best_pt.exists():
            best_path = best_pt

    if best_path is None:
        best_path = output_dir / "nest_detector" / "weights" / "best.pt"

    metrics = {
        "mAP50": float(results.results_dict.get("metrics/mAP50(B)", 0.0))
        if hasattr(results, "results_dict")
        else 0.0,
        "mAP50_95": float(results.results_dict.get("metrics/mAP50-95(B)", 0.0))
        if hasattr(results, "results_dict")
        else 0.0,
        "precision": float(results.results_dict.get("metrics/precision(B)", 0.0))
        if hasattr(results, "results_dict")
        else 0.0,
        "recall": float(results.results_dict.get("metrics/recall(B)", 0.0))
        if hasattr(results, "results_dict")
        else 0.0,
    }

    try:
        progress_path.unlink()
    except Exception:
        pass

    return str(best_path), metrics


def evaluate_model(model_path: str, data_yaml: str, device: str = "0") -> dict:
    model = YOLO(model_path)
    metrics = model.val(data=data_yaml, device=device, split="test")

    return {
        "mAP50": float(metrics.box.map50),
        "mAP50-95": float(metrics.box.map),
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
    }
