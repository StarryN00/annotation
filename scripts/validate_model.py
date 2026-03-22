from ultralytics import YOLO
import json

model_path = "runs/detect/outputs/models/nest_detector5/weights/best.pt"
data_yaml = "web/backend/datasets/b6339600-96b9-4343-a81e-d2a967573116/data.yaml"

print("Loading model...")
model = YOLO(model_path)

print("Validating model on test set...")
metrics = model.val(data=data_yaml, split="test")

results = {
    "mAP50": float(metrics.box.map50),
    "mAP50-95": float(metrics.box.map),
    "precision": float(metrics.box.mp),
    "recall": float(metrics.box.mr),
}

print("\nValidation Results:")
print(f"  mAP50: {results['mAP50']:.4f}")
print(f"  mAP50-95: {results['mAP50-95']:.4f}")
print(f"  Precision: {results['precision']:.4f}")
print(f"  Recall: {results['recall']:.4f}")

with open("outputs/models/validation_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nResults saved to outputs/models/validation_results.json")
