import shutil
import random
import yaml
from pathlib import Path


def build_yolo_dataset(
    image_dir: str,
    label_dir: str,
    output_dir: str,
    train_ratio: float = 0.7,
    val_ratio: float = 0.2,
    test_ratio: float = 0.1,
    seed: int = 42,
):
    """
    将图片和标注文件划分为训练/验证/测试集，
    生成 YOLOv8 所需的目录结构和 data.yaml 配置文件。

    输出目录结构:
        output_dir/
        ├── images/
        │   ├── train/
        │   ├── val/
        │   └── test/
        ├── labels/
        │   ├── train/
        │   ├── val/
        │   └── test/
        └── data.yaml
    """
    image_dir = Path(image_dir)
    label_dir = Path(label_dir)
    output_dir = Path(output_dir)

    # 创建目录
    for split in ["train", "val", "test"]:
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

    # 收集有标注的图片
    pairs = []
    for label_file in label_dir.glob("*.txt"):
        if label_file.name == "classes.txt":
            continue
        stem = label_file.stem
        # 查找对应图片
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            img_path = image_dir / f"{stem}{ext}"
            if img_path.exists():
                pairs.append((img_path, label_file))
                break

    # 打乱并划分
    random.seed(seed)
    random.shuffle(pairs)

    n = len(pairs)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    splits = {
        "train": pairs[:n_train],
        "val": pairs[n_train : n_train + n_val],
        "test": pairs[n_train + n_val :],
    }

    # 复制文件
    for split_name, split_pairs in splits.items():
        for img_path, label_path in split_pairs:
            shutil.copy2(img_path, output_dir / "images" / split_name / img_path.name)
            shutil.copy2(
                label_path, output_dir / "labels" / split_name / label_path.name
            )

    # 生成 data.yaml
    data_yaml = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {0: "nest"},
    }

    yaml_path = output_dir / "data.yaml"
    with open(yaml_path, "w") as f:
        yaml.dump(data_yaml, f, default_flow_style=False)

    print(f"数据集构建完成:")
    print(f"  训练集: {len(splits['train'])} 张")
    print(f"  验证集: {len(splits['val'])} 张")
    print(f"  测试集: {len(splits['test'])} 张")
    print(f"  配置文件: {yaml_path}")

    return str(yaml_path)
