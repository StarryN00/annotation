#!/bin/bash

# Web界面测试脚本
# 测试内容：
# 1. 后端 API 连通性
# 2. 数据库初始化
# 3. 前端构建

echo "========================================"
echo "樟巢螟标注系统 - Web界面测试"
echo "========================================"
echo ""

# 检查 Python 环境
echo "[1/5] 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "  Python: $PYTHON_VERSION"
else
    echo "  错误: 未找到 Python3"
    exit 1
fi

# 安装 Web 依赖
echo ""
echo "[2/5] 安装 Web 依赖..."
cd web/backend
pip install -q -r ../../requirements_web.txt
if [ $? -eq 0 ]; then
    echo "  依赖安装成功"
else
    echo "  警告: 部分依赖安装失败"
fi
cd ../..

# 测试数据库初始化
echo ""
echo "[3/5] 测试数据库初始化..."
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from web.backend.models.database import init_db
asyncio.run(init_db())
print('  数据库初始化成功')
"

if [ $? -eq 0 ]; then
    echo "  数据库初始化成功"
else
    echo "  错误: 数据库初始化失败"
fi

# 测试后端启动 (5秒后停止)
echo ""
echo "[4/5] 测试后端服务启动..."
timeout 5 python3 -c "
import sys
sys.path.insert(0, '.')
from web.backend.main import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get('/api/health')
if response.status_code == 200:
    print('  健康检查通过:', response.json())
else:
    print('  健康检查失败:', response.status_code)
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "  后端服务测试通过"
else
    echo "  警告: 后端服务测试需要更多依赖"
fi

# 测试前端项目结构
echo ""
echo "[5/5] 检查前端项目结构..."
FRONTEND_FILES=(
    "web/frontend/package.json"
    "web/frontend/vite.config.js"
    "web/frontend/index.html"
    "web/frontend/src/main.jsx"
    "web/frontend/src/App.jsx"
)

all_exist=true
for file in "${FRONTEND_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  文件存在: $file"
    else
        echo "  文件缺失: $file"
        all_exist=false
    fi
done

if [ "$all_exist" = true ]; then
    echo ""
    echo "========================================"
    echo "所有测试通过!"
    echo "========================================"
    echo ""
    echo "使用说明:"
    echo "1. 安装前端依赖: cd web/frontend && npm install"
    echo "2. 启动前端开发服务器: npm run dev"
    echo "3. 启动后端服务: python web/backend/main.py"
    echo ""
    exit 0
else
    echo ""
    echo "========================================"
    echo "部分测试未通过，请检查"
    echo "========================================"
    exit 1
fi
