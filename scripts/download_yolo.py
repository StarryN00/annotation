#!/usr/bin/env python3
import urllib.request
import os

url = "https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8m.pt"
output = "/Users/starryn/project/annotation/web/backend/yolov8m.pt"

print(f"Downloading YOLOv8m weights...")
print(f"URL: {url}")
print(f"Output: {output}")


def download_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = min(downloaded * 100 / total_size, 100)
    mb = downloaded / 1024 / 1024
    total_mb = total_size / 1024 / 1024
    print(
        f"\rProgress: {percent:.1f}% ({mb:.1f}MB / {total_mb:.1f}MB)",
        end="",
        flush=True,
    )


try:
    urllib.request.urlretrieve(url, output, reporthook=download_progress)
    print("\n✅ Download completed!")
except Exception as e:
    print(f"\n❌ Download failed: {e}")
