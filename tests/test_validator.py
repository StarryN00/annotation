import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.quality.validator import validate_label_file, validate_labels


class TestValidateLabelFile:
    def test_valid_label_file(self, tmp_path):
        label_file = tmp_path / "test.txt"
        label_file.write_text("0 0.5 0.5 0.1 0.1\n")

        errors = validate_label_file(str(label_file))
        assert errors == []

    def test_empty_file_is_valid(self, tmp_path):
        label_file = tmp_path / "test.txt"
        label_file.write_text("")

        errors = validate_label_file(str(label_file))
        assert errors == []

    def test_invalid_format(self, tmp_path):
        label_file = tmp_path / "test.txt"
        label_file.write_text("0 0.5 0.5\n")  # Missing height

        errors = validate_label_file(str(label_file))
        assert len(errors) > 0

    def test_out_of_bounds(self, tmp_path):
        label_file = tmp_path / "test.txt"
        label_file.write_text("0 1.5 0.5 0.1 0.1\n")  # x_center > 1

        errors = validate_label_file(str(label_file))
        assert len(errors) > 0
        assert any("x坐标" in e for e in errors)


class TestValidateLabels:
    def test_validate_directory(self, tmp_path):
        # Create test label files
        (tmp_path / "valid.txt").write_text("0 0.5 0.5 0.1 0.1\n")
        (tmp_path / "invalid.txt").write_text("invalid content\n")
        (tmp_path / "classes.txt").write_text("nest\n")  # Should be ignored

        results = validate_labels(str(tmp_path))
        assert results["total"] == 2  # classes.txt ignored
        assert results["valid"] == 1
        assert results["invalid"] == 1
