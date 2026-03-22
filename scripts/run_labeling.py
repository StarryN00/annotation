import argparse
import logging
import yaml
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.labeling.labeler import AutoLabeler


def main():
    parser = argparse.ArgumentParser(description="樟巢螟虫巢自动标注")
    parser.add_argument("--config", default="config/config.yaml", help="配置文件路径")
    parser.add_argument("--input", required=True, help="图片目录")
    parser.add_argument("--output", default=None, help="标注输出目录")
    parser.add_argument(
        "--provider", default=None, help="覆盖配置中的模型: claude/kimi/openai/gemini"
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # 命令行参数覆盖配置
    if args.provider:
        config["llm"]["provider"] = args.provider

    output_dir = args.output or config["paths"]["labels"]

    labeler = AutoLabeler(config)
    labeler.run(args.input, output_dir)


if __name__ == "__main__":
    main()
