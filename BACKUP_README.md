# 数据备份清单

## 备份时间
2026-03-22

## 备份内容

### ✅ 已下载到本地 (/Users/starryn/project/annotation/backup/)

| 文件 | 大小 | 说明 |
|------|------|------|
| `app.db` | 484KB | SQLite 数据库，包含所有图片元数据、标注结果、检测框 |
| `best.pt` | 50MB | 最佳模型权重（推荐使用的模型）|
| `last.pt` | 50MB | 最后 epoch 的模型权重 |

**数据库内容包含：**
- 731 张图片的元数据（文件名、路径、尺寸、状态）
- 651 张已标注图片的标注结果
- 447 个检测框的详细信息（位置、置信度、严重程度）
- 训练任务记录
- 数据集划分信息

---

### ⚠️ 服务器上未下载的大文件

#### 1. 原始图片（7.7GB）
```
位置: /home/ubuntu/annotation/web/backend/uploads/
数量: 731 张
大小: 7.7 GB
```

**备份建议：**
- 这些是你上传的原始图片
- 如果本地还有这些图片的副本，可以不需要备份
- 如果需要备份，使用以下命令：

```bash
# 在服务器上压缩
mkdir -p /home/ubuntu/backup_images
tar -czf /home/ubuntu/backup_images/uploads.tar.gz -C /home/ubuntu/annotation/web/backend uploads/

# 下载到本地（这可能需要很长时间）
scp -i ssh/test.pem ubuntu@101.42.171.63:/home/ubuntu/backup_images/uploads.tar.gz ./
```

#### 2. 完整备份包（8.2GB）
```
位置: /home/ubuntu/backup/nestlabel_data_20260322.tar.gz
包含: 数据库 + 图片 + 所有模型（包括中间epoch）
```

如果需要完整备份，下载这个文件即可。

---

## 数据恢复方法

### 恢复数据库
```bash
# 将备份的数据库复制到项目目录
cp backup/app.db web/backend/data/
```

### 恢复模型
```bash
# 将备份的模型复制到项目目录
cp backup/best.pt runs/detect/outputs/models/nest_detector/weights/
```

### 恢复图片
```bash
# 解压图片备份
tar -xzf uploads.tar.gz -C web/backend/
```

---

## 重要提示

1. **数据库是核心**：`app.db` 包含了所有的标注结果，务必妥善保存
2. **模型权重**：`best.pt` 是训练好的模型，可用于推理
3. **原始图片**：如果本地还有原始图片，可以不备份服务器上的
4. **下次部署**：使用 DEPLOYMENT_NOTES.md 部署后，恢复数据库即可看到所有标注数据

---

## 备份文件位置

本地备份路径：
```
/Users/starryn/project/annotation/backup/
├── app.db      (数据库)
└── best.pt     (最佳模型)
```
