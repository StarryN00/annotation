import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.labeling.adapters.base import Detection, LabelingResult
from src.labeling.parser import parse_response


class TestParseResponse:
    def test_parse_valid_response(self):
        result = LabelingResult(image_path="test.jpg")
        result.raw_response = """
        {
            "image_has_camphor_tree": true,
            "detections": [
                {
                    "x_center": 0.5,
                    "y_center": 0.5,
                    "width": 0.1,
                    "height": 0.1,
                    "severity": "medium",
                    "confidence": "high"
                }
            ],
            "summary": "检测到1个虫巢"
        }
        """

        parsed = parse_response(result, min_confidence="low")
        assert parsed.has_camphor_tree is True
        assert len(parsed.detections) == 1
        assert parsed.detections[0].x_center == 0.5

    def test_parse_with_markdown_code_block(self):
        result = LabelingResult(image_path="test.jpg")
        result.raw_response = """```json
        {
            "image_has_camphor_tree": false,
            "detections": [],
            "summary": "未检测到虫巢"
        }
        ```"""

        parsed = parse_response(result)
        assert parsed.has_camphor_tree is False
        assert len(parsed.detections) == 0

    def test_parse_invalid_json(self):
        result = LabelingResult(image_path="test.jpg")
        result.raw_response = "invalid json"

        parsed = parse_response(result)
        assert parsed.error is not None

    def test_confidence_filtering(self):
        result = LabelingResult(image_path="test.jpg")
        result.raw_response = """
        {
            "image_has_camphor_tree": true,
            "detections": [
                {"x_center": 0.5, "y_center": 0.5, "width": 0.1, "height": 0.1, 
                 "severity": "medium", "confidence": "low"},
                {"x_center": 0.6, "y_center": 0.6, "width": 0.1, "height": 0.1, 
                 "severity": "medium", "confidence": "high"}
            ],
            "summary": "检测到2个虫巢"
        }
        """

        # Filter for high confidence only
        parsed = parse_response(result, min_confidence="high")
        assert len(parsed.detections) == 1
        assert parsed.detections[0].confidence == "high"
