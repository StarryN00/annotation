# NestLabel 部署笔记

## 服务器信息
- **IP**: 101.42.171.63 (即将销毁)
- **系统**: Ubuntu 24.04 LTS
- **规格**: 8核32GB + NVIDIA GPU
- **部署日期**: 2026-03-22

---

## 快速部署指南

### 1. 系统依赖安装
```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-pip python3-venv nodejs npm nginx
```

### 2. 克隆项目
```bash
cd /home/ubuntu
git clone https://github.com/StarryN00/annotation.git
cd annotation
```

### 3. 配置环境变量
创建 `.env` 文件：
```bash
cat > .env << 'EOF'
KIMI_API_KEY=sk-CViBA55KahBvMQmzjD8ZZQYrbPLMPVvTNQFe6QfUfIc7BSKY
EOF
```

### 4. Python 虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install ultralytics opencv-python-headless Pillow numpy pandas pyyaml requests aiohttp
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic python-multipart
```

### 5. 构建前端
```bash
cd web/frontend
npm install
npm run build
cd ../..
```

### 6. 配置 Systemd 服务
使用项目中的模板：
```bash
sudo cp nestlabel.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nestlabel
sudo systemctl start nestlabel
```

### 7. 配置 Nginx
```bash
sudo tee /etc/nginx/sites-available/nestlabel << 'EOF'
server {
    listen 80;
    server_name YOUR_SERVER_IP;

    client_max_body_size 1024M;

    location / {
        root /home/ubuntu/annotation/web/backend/static;
        index index.html;
        try_files $uri $uri/ =404;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    location /assets {
        alias /home/ubuntu/annotation/web/backend/static/assets;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/nestlabel /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

### 8. 设置权限
```bash
chmod 755 /home/ubuntu
chmod -R 755 /home/ubuntu/annotation/web/backend/static/
```

---

## 重要配置项

### 上传限制
- Nginx: `client_max_body_size 1024M`
- 前端: 每批10张图片
- 单文件: 最大20MB

### API Key
- 必须设置 `KIMI_API_KEY` 环境变量
- 在服务文件中添加: `EnvironmentFile=/home/ubuntu/annotation/.env`

### 工作目录
- Systemd 工作目录: `/home/ubuntu/annotation`
- 启动命令: `uvicorn web.backend.main:app --host 0.0.0.0 --port 8000`

---

## 已知问题与修复

### 1. 扫描导入路径问题
**现象**: 扫描导入提示"找不到路径"
**原因**: 必须输入服务器本地绝对路径
**解决**: 在前端提示中明确说明

### 2. 图片上传100张报错
**现象**: 批量上传大量图片失败
**原因**: Nginx 默认 body 大小限制
**解决**: 设置 `client_max_body_size 1024M`

### 3. 模型路径错误
**现象**: 标注失败，找不到图片
**原因**: 工作目录配置错误
**解决**: 服务文件设置正确工作目录

### 4. ONNX 导出报错
**现象**: 导出 ONNX 时 KeyError
**原因**: 代码bug，字典访问方式错误
**解决**: 修复为 `export_paths["onnx"]`

---

## 服务管理命令

```bash
# 查看状态
sudo systemctl status nestlabel

# 查看日志
sudo journalctl -u nestlabel -f

# 重启服务
sudo systemctl restart nestlabel

# 停止服务
sudo systemctl stop nestlabel
```

---

## 项目统计

### 本次部署成果
- 图片总数: 731张
- 标注完成: 651张
- 检测框总数: 447个
- 训练轮数: 200 epochs
- 模型大小: 50MB (YOLOv8m)

### 模型下载
- PyTorch: `http://YOUR_IP/api/models/MODEL_ID/download?format=pt`
- ONNX: `http://YOUR_IP/api/models/MODEL_ID/download?format=onnx`

---

## GitHub 仓库
- **地址**: https://github.com/StarryN00/annotation
- **分支**: main
- **提交数**: 11次

---

## 注意事项

1. **GPU 支持**: 训练需要 NVIDIA GPU，标注只需要 CPU
2. **API Key**: Kimi API Key 是必需的，否则标注会失败
3. **存储空间**: 731张图片约占用 7-8GB 空间
4. **内存**: 建议至少 16GB 内存，32GB更佳
5. **备份**: 定期备份 `web/backend/uploads/` 和数据库

---

## 联系
- 创建者: StarryN00
- 项目: 樟巢螟数据标注与模型训练系统
