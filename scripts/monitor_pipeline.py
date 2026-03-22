#!/usr/bin/env python3
import requests
import time
import json
from datetime import datetime

API_BASE = "http://localhost:8000"
LOG_FILE = "/tmp/pipeline_monitor.log"


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {msg}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def check_status():
    try:
        resp = requests.get(f"{API_BASE}/api/pipeline/status", timeout=10)
        return resp.json()
    except Exception as e:
        log(f"获取状态失败: {e}")
        return None


def check_training_progress():
    try:
        resp = requests.get(f"{API_BASE}/api/pipeline/training-progress", timeout=10)
        return resp.json()
    except Exception as e:
        return None


def main():
    log("=" * 60)
    log("开始监控流水线...")
    log("配置: YOLOv8m, 200 epochs, batch_size=8, MPS, max_images=200")
    log("=" * 60)

    last_stage = None
    last_progress = 0
    start_time = time.time()

    while True:
        status = check_status()
        if not status:
            time.sleep(30)
            continue

        current_stage = status.get("current_stage", "unknown")
        current_status = status.get("status", "unknown")
        progress = status.get("progress", 0)
        message = status.get("message", "")

        if current_stage != last_stage or progress != last_progress:
            elapsed = time.time() - start_time
            elapsed_str = f"{int(elapsed // 3600)}h{int((elapsed % 3600) // 60)}m"
            log(
                f"[{current_status.upper()}] 阶段: {current_stage} | 进度: {progress}% | 用时: {elapsed_str}"
            )
            log(f"  消息: {message}")

            if current_stage == "training":
                train_progress = check_training_progress()
                if train_progress and train_progress.get("total_epochs", 0) > 0:
                    epoch = train_progress.get("current_epoch", 0)
                    total = train_progress.get("total_epochs", 0)
                    pct = train_progress.get("progress_percent", 0)
                    log(f"  训练详情: Epoch {epoch}/{total} ({pct}%)")

            last_stage = current_stage
            last_progress = progress

        if current_status in ["completed", "failed", "stopped"]:
            log("=" * 60)
            log(f"流水线结束! 状态: {current_status}")
            if status.get("results"):
                log(f"结果: {json.dumps(status['results'], indent=2)}")
            break

        time.sleep(30)


if __name__ == "__main__":
    main()
