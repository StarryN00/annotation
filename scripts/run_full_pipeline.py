"""
一键运行完整管线:
  自动标注 → 质量验证 → 数据集构建 → 模型训练 → 模型评估
"""

import argparse
import logging
import yaml
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.labeling.labeler import AutoLabeler
from src.quality.visualizer import batch_visualize
from src.quality.statistics import generate_statistics
from src.dataset.splitter import build_yolo_dataset
from src.training.train_yolo import train_nest_detector, evaluate_model
from src.training.export import export_model


def main():
    parser = argparse.ArgumentParser(description="一键运行完整标注→训练管线")
    parser.add_argument("--config", default="config/config.yaml")
    parser.add_argument("--input", required=True, help="原始图片目录")
    parser.add_argument(
        "--skip-labeling",
        action="store_true",
        help="跳过标注步骤（已有标注数据时使用）",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    paths = config["paths"]

    # ========== Step 1-2: 自动标注 ==========
    if not args.skip_labeling:
        logger.info("=" * 50)
        logger.info("Step 2: AI自动标注")
        logger.info("=" * 50)
        labeler = AutoLabeler(config)
        labeler.run(args.input, paths["labels"])
    else:
        logger.info("跳过标注步骤")

    # ========== Step 3: 质量验证 ==========
    logger.info("=" * 50)
    logger.info("Step 3: 标注质量验证")
    logger.info("=" * 50)

    stats = generate_statistics(
        paths["labels"],
        report_path=str(Path(paths["quality_reports"]) / "statistics.json"),
    )
    logger.info(
        f"标注统计: {stats['total_images']} 张图, "
        f"{stats['images_with_nests']} 张含虫巢, "
        f"共 {stats['total_nests']} 个虫巢"
    )

    batch_visualize(
        args.input,
        paths["labels"],
        str(Path(paths["quality_reports"]) / "visualized"),
        sample_count=50,
    )

    # ========== Step 4: 数据集构建 ==========
    logger.info("=" * 50)
    logger.info("Step 4: 数据集构建")
    logger.info("=" * 50)

    ds_config = config["dataset"]
    data_yaml = build_yolo_dataset(
        image_dir=args.input,
        label_dir=paths["labels"],
        output_dir=paths["dataset"],
        train_ratio=ds_config["train_ratio"],
        val_ratio=ds_config["val_ratio"],
        test_ratio=ds_config["test_ratio"],
        seed=ds_config["seed"],
    )

    # ========== Step 5: 模型训练 ==========
    logger.info("=" * 50)
    logger.info("Step 5: YOLOv8 模型训练")
    logger.info("=" * 50)

    train_config = config["training"]["yolo"]
    best_model = train_nest_detector(
        data_yaml=data_yaml,
        output_dir=paths["models"],
        **train_config,
    )
    logger.info(f"最佳模型: {best_model}")

    # ========== Step 6: 评估与导出 ==========
    logger.info("=" * 50)
    logger.info("Step 6: 模型评估与导出")
    logger.info("=" * 50)

    metrics = evaluate_model(best_model, data_yaml)
    logger.info(
        f"评估结果: mAP@0.5={metrics['mAP50']:.4f}, "
        f"精确率={metrics['precision']:.4f}, "
        f"召回率={metrics['recall']:.4f}"
    )

    export_model(best_model, formats=["onnx"])

    logger.info("=" * 50)
    logger.info("全流程完成!")
    logger.info(f"模型权重: {best_model}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
