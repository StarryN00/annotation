import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.labeling.adapters.base import Detection, LabelingResult
from src.labeling.converter import save_yolo_label, generate_classes_file


class TestSaveYoloLabel:
    def test_save_empty_detections(self, tmp_path):
        result = LabelingResult(image_path="test.jpg")
        output_dir = tmp_path / "labels"

        path = save_yolo_label(result, str(output_dir))
        assert Path(path).exists()
        content = Path(path).read_text()
        assert content == ""

    def test_save_detections(self, tmp_path):
        result = LabelingResult(image_path="test.jpg")
        result.detections = [
            Detection(x_center=0.5, y_center=0.5, width=0.1, height=0.1),
            Detection(x_center=0.6, y_center=0.6, width=0.2, height=0.2),
        ]
        output_dir = tmp_path / "labels"

        path = save_yolo_label(result, str(output_dir))
        content = Path(path).read_text()
        lines = content.strip().split("\n")
        assert len(lines) == 2
        # Check format: class_id x_center y_center width height
        parts = lines[0].split()
        assert len(parts) == 5


class TestGenerateClassesFile:
    def test_generate_classes(self, tmp_path):
        classes = [{"id": 0, "name": "nest"}]
        output_dir = tmp_path / "labels"

        path = generate_classes_file(str(output_dir), classes)
        content = Path(path).read_text()
        assert "nest" in content
