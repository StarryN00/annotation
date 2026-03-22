import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.labeling.adapters.base import Detection, LabelingResult, adapter_factory


class TestDetection:
    def test_detection_creation(self):
        det = Detection(x_center=0.5, y_center=0.5, width=0.1, height=0.1)
        assert det.x_center == 0.5
        assert det.class_id == 0
        assert det.is_valid()

    def test_invalid_coordinates(self):
        det = Detection(x_center=1.5, y_center=0.5, width=0.1, height=0.1)
        assert not det.is_valid()

    def test_to_yolo_line(self):
        det = Detection(x_center=0.5, y_center=0.5, width=0.1, height=0.1, class_id=0)
        line = det.to_yolo_line()
        parts = line.split()
        assert len(parts) == 5
        assert float(parts[0]) == 0


class TestLabelingResult:
    def test_result_creation(self):
        result = LabelingResult(image_path="test.jpg")
        assert result.image_path == "test.jpg"
        assert result.detections == []
        assert result.error is None


class TestAdapterFactory:
    def test_factory_raises_on_invalid_provider(self):
        with pytest.raises(ValueError):
            adapter_factory("invalid_provider", {})
