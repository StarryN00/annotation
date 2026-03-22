from ultralytics import YOLO
import os
import shutil

model_path = "runs/detect/outputs/models/nest_detector5/weights/best.pt"
output_dir = "outputs/models"

os.makedirs(output_dir, exist_ok=True)

print(f"Loading model from {model_path}...")
model = YOLO(model_path)

print("Exporting to ONNX format...")
model.export(format="onnx", imgsz=640, half=False, simplify=True)

onnx_path = model_path.replace(".pt", ".onnx")
if os.path.exists(onnx_path):
    final_path = os.path.join(output_dir, "best.onnx")
    shutil.copy(onnx_path, final_path)
    print(f"ONNX model exported to: {final_path}")
    size_mb = os.path.getsize(final_path) / (1024 * 1024)
    print(f"Size: {size_mb:.2f} MB")
else:
    print("Export failed")
