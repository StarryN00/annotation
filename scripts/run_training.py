import argparse
import logging
import yaml
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.training.train_yolo import train_nest_detector, evaluate_model
from src.training.export import export_model


def main():
    parser = argparse.ArgumentParser(description="训练YOLOv8虫巢检测模型")
    parser.add_argument("--config", default="config/config.yaml", help="配置文件路径")
    parser.add_argument("--data", help="data.yaml路径")
    parser.add_argument("--output", help="模型输出目录")
    parser.add_argument("--epochs", type=int, help="训练轮数")
    parser.add_argument("--batch", type=int, help="批大小")
    parser.add_argument("--device", default="0", help="GPU设备")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    paths = config["paths"]
    data_yaml = args.data or str(Path(paths["dataset"]) / "data.yaml")
    output_dir = args.output or paths["models"]

    train_config = config["training"]["yolo"]

    # 命令行参数覆盖配置
    if args.epochs:
        train_config["epochs"] = args.epochs
    if args.batch:
        train_config["batch_size"] = args.batch
    if args.device:
        train_config["device"] = args.device

    logger.info("=" * 50)
    logger.info("开始训练 YOLOv8 模型")
    logger.info("=" * 50)

    best_model = train_nest_detector(
        data_yaml=data_yaml,
        output_dir=output_dir,
        **train_config,
    )

    logger.info(f"训练完成! 最佳模型: {best_model}")

    # 评估
    logger.info("=" * 50)
    logger.info("模型评估")
    logger.info("=" * 50)

    metrics = evaluate_model(best_model, data_yaml, device=train_config["device"])
    logger.info(f"mAP@0.5: {metrics['mAP50']:.4f}")
    logger.info(f"mAP@0.5:0.95: {metrics['mAP50-95']:.4f}")
    logger.info(f"精确率: {metrics['precision']:.4f}")
    logger.info(f"召回率: {metrics['recall']:.4f}")

    # 导出
    logger.info("=" * 50)
    logger.info("导出模型")
    logger.info("=" * 50)

    export_model(best_model, formats=["onnx"], output_dir=output_dir)

    logger.info("训练流程完成!")


if __name__ == "__main__":
    main()
