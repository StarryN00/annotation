import argparse
import logging
import yaml
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.quality.statistics import generate_statistics
from src.quality.visualizer import batch_visualize
from src.quality.validator import validate_labels


def main():
    parser = argparse.ArgumentParser(description="标注质量检查")
    parser.add_argument("--config", default="config/config.yaml", help="配置文件路径")
    parser.add_argument("--input", help="原始图片目录（用于可视化）")
    parser.add_argument("--labels", help="标注文件目录")
    parser.add_argument("--output", help="质量报告输出目录")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    paths = config["paths"]
    input_dir = args.input or paths["raw_images"]
    label_dir = args.labels or paths["labels"]
    output_dir = args.output or paths["quality_reports"]

    # 统计分析
    logger.info("=" * 50)
    logger.info("标注统计分析")
    logger.info("=" * 50)

    stats = generate_statistics(
        label_dir,
        report_path=str(Path(output_dir) / "statistics.json"),
    )

    logger.info(f"总图片数: {stats['total_images']}")
    logger.info(f"含虫巢图片: {stats['images_with_nests']}")
    logger.info(f"总虫巢数: {stats['total_nests']}")
    logger.info(f"虫巢检出率: {stats['nest_positive_rate']:.2%}")

    # 验证
    logger.info("\n" + "=" * 50)
    logger.info("标注格式验证")
    logger.info("=" * 50)

    validation = validate_labels(label_dir, image_dir=input_dir)
    summary = validation["summary"]
    logger.info(f"验证通过: {summary['valid_files']} / {summary['total_label_files']}")
    if summary["invalid_files"] > 0:
        logger.warning(f"验证失败: {summary['invalid_files']} 个文件")
        invalid_files = [f for f in validation["files"] if not f["valid"]]
        for f in invalid_files[:5]:
            logger.warning(f"  {f['path']}: {f['issues'][:2]}")

    # 可视化
    logger.info("\n" + "=" * 50)
    logger.info("生成可视化样本")
    logger.info("=" * 50)

    vis_dir = Path(output_dir) / "visualized"
    batch_visualize(input_dir, label_dir, str(vis_dir), sample_count=50)
    logger.info(f"可视化结果保存到: {vis_dir}")

    logger.info("\n质量检查完成!")


if __name__ == "__main__":
    main()
