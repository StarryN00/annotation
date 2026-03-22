import argparse
import logging
import yaml
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dataset.splitter import build_yolo_dataset


def main():
    parser = argparse.ArgumentParser(description="构建YOLO数据集")
    parser.add_argument("--config", default="config/config.yaml", help="配置文件路径")
    parser.add_argument("--input", help="原始图片目录")
    parser.add_argument("--labels", help="标注文件目录")
    parser.add_argument("--output", help="数据集输出目录")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    paths = config["paths"]
    input_dir = args.input or paths["raw_images"]
    label_dir = args.labels or paths["labels"]
    output_dir = args.output or paths["dataset"]

    ds_config = config["dataset"]

    data_yaml = build_yolo_dataset(
        image_dir=input_dir,
        label_dir=label_dir,
        output_dir=output_dir,
        train_ratio=ds_config["train_ratio"],
        val_ratio=ds_config["val_ratio"],
        test_ratio=ds_config["test_ratio"],
        seed=ds_config["seed"],
    )

    print(f"\n数据集构建完成: {data_yaml}")


if __name__ == "__main__":
    main()
