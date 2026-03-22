#!/bin/bash

# NestLabel Web 启动脚本
# 一键启动前后端服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="$SCRIPT_DIR/.service_pids"

# 加载环境变量文件（如果存在）
if [ -f "$PROJECT_ROOT/.env" ]; then
    export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
fi

# 检查必需的 API Key
if [ -z "$KIMI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$OPENAI_API_KEY" ] && [ -z "$GEMINI_API_KEY" ]; then
    echo "警告：未设置任何 API Key 环境变量"
    echo "请设置以下环境变量之一："
    echo "  - KIMI_API_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - OPENAI_API_KEY"
    echo "  - GEMINI_API_KEY"
    echo ""
    echo "可以通过以下方式设置："
    echo "  1. 在当前 shell 中：export KIMI_API_KEY='your-key'"
    echo "  2. 创建 .env 文件：echo 'KIMI_API_KEY=your-key' > .env"
    echo ""
    read -p "是否继续启动？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "检查依赖环境..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "未找到 Python3，请先安装 Python 3.9+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    log_info "Python 版本: $PYTHON_VERSION"
    
    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "未找到 Node.js，请先安装 Node.js 16+"
        exit 1
    fi
    
    NODE_VERSION=$(node --version)
    log_info "Node.js 版本: $NODE_VERSION"
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        log_error "未找到 pip3"
        exit 1
    fi
    
    log_info "依赖检查通过"
}

# 安装后端依赖
install_backend_deps() {
    log_step "安装后端依赖..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "requirements_web.txt" ]; then
        pip3 install -r requirements_web.txt 2>&1 | grep -v "already satisfied" || true
        if [ $? -eq 0 ]; then
            log_info "后端依赖安装完成"
        else
            log_error "后端依赖安装失败"
            exit 1
        fi
    else
        log_warn "未找到 requirements_web.txt"
    fi
}

# 安装前端依赖
install_frontend_deps() {
    log_step "安装前端依赖..."
    
    cd "$PROJECT_ROOT/web/frontend"
    
    if [ ! -d "node_modules" ]; then
        log_info "首次安装前端依赖，这可能需要几分钟..."
        npm install
        if [ $? -eq 0 ]; then
            log_info "前端依赖安装完成"
        else
            log_error "前端依赖安装失败"
            exit 1
        fi
    else
        log_info "前端依赖已安装"
    fi
}

# 初始化数据库
init_database() {
    log_step "初始化数据库..."
    
    cd "$PROJECT_ROOT"
    
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from web.backend.models.database import init_db
asyncio.run(init_db())
"
    
    if [ $? -eq 0 ]; then
        log_info "数据库初始化完成"
    else
        log_warn "数据库初始化可能已存在"
    fi
}

# 启动后端服务
start_backend() {
    log_step "启动后端服务..."
    
    cd "$PROJECT_ROOT"
    
    # 检查端口是否被占用
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warn "端口 8000 已被占用，尝试停止旧服务..."
        kill $(lsof -Pi :8000 -sTCP:LISTEN -t) 2>/dev/null || true
        sleep 1
    fi
    
    # 启动后端
    python3 web/backend/main.py > /tmp/nestlabel_backend.log 2>&1 &
    BACKEND_PID=$!
    
    # 等待后端启动
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            log_info "后端服务已启动 (PID: $BACKEND_PID)"
            echo "backend:$BACKEND_PID" >> "$PID_FILE"
            return 0
        fi
        sleep 0.5
    done
    
    log_error "后端服务启动失败，查看日志: /tmp/nestlabel_backend.log"
    exit 1
}

# 启动前端服务
start_frontend() {
    log_step "启动前端服务..."
    
    cd "$PROJECT_ROOT/web/frontend"
    
    # 检查端口是否被占用
    if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warn "端口 3000 已被占用，尝试停止旧服务..."
        kill $(lsof -Pi :3000 -sTCP:LISTEN -t) 2>/dev/null || true
        sleep 1
    fi
    
    # 启动前端
    npm run dev > /tmp/nestlabel_frontend.log 2>&1 &
    FRONTEND_PID=$!
    
    # 等待前端启动
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            log_info "前端服务已启动 (PID: $FRONTEND_PID)"
            echo "frontend:$FRONTEND_PID" >> "$PID_FILE"
            return 0
        fi
        sleep 0.5
    done
    
    log_error "前端服务启动失败，查看日志: /tmp/nestlabel_frontend.log"
    exit 1
}

# 停止服务
stop_services() {
    log_step "停止服务..."
    
    if [ -f "$PID_FILE" ]; then
        while IFS=: read -r service pid; do
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null || true
                log_info "已停止 $service (PID: $pid)"
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    
    # 确保端口释放
    kill $(lsof -Pi :8000 -sTCP:LISTEN -t) 2>/dev/null || true
    kill $(lsof -Pi :3000 -sTCP:LISTEN -t) 2>/dev/null || true
    
    log_info "所有服务已停止"
}

# 查看状态
show_status() {
    log_step "服务状态检查..."
    
    BACKEND_RUNNING=false
    FRONTEND_RUNNING=false
    
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        BACKEND_RUNNING=true
        BACKEND_STATUS=$(curl -s http://localhost:8000/api/health | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null || echo "unknown")
    fi
    
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        FRONTEND_RUNNING=true
    fi
    
    echo ""
    echo "========================================"
    echo "服务状态"
    echo "========================================"
    echo -e "后端服务 (http://localhost:8000): $([ "$BACKEND_RUNNING" = true ] && echo -e "${GREEN}运行中${NC} [$BACKEND_STATUS]" || echo -e "${RED}未运行${NC}")"
    echo -e "前端服务 (http://localhost:3000): $([ "$FRONTEND_RUNNING" = true ] && echo -e "${GREEN}运行中${NC}" || echo -e "${RED}未运行${NC}")"
    echo "========================================"
    echo ""
    
    if [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
        log_info "所有服务正常运行！"
        log_info "请在浏览器中访问: http://localhost:3000"
    else
        log_warn "部分服务未运行"
    fi
}

# 显示日志
show_logs() {
    echo "========================================"
    echo "后端日志 (最近 20 行)"
    echo "========================================"
    tail -n 20 /tmp/nestlabel_backend.log 2>/dev/null || echo "暂无日志"
    
    echo ""
    echo "========================================"
    echo "前端日志 (最近 20 行)"
    echo "========================================"
    tail -n 20 /tmp/nestlabel_frontend.log 2>/dev/null || echo "暂无日志"
}

# 启动所有服务
start_all() {
    # 清理旧的 PID 文件
    rm -f "$PID_FILE"
    
    check_dependencies
    install_backend_deps
    install_frontend_deps
    init_database
    start_backend
    start_frontend
    
    echo ""
    log_info "🚀 所有服务启动成功！"
    log_info ""
    log_info "访问地址:"
    log_info "  - Web 界面: http://localhost:3000"
    log_info "  - API 文档: http://localhost:8000/docs"
    log_info ""
    log_info "常用命令:"
    log_info "  - 查看状态: $0 status"
    log_info "  - 查看日志: $0 logs"
    log_info "  - 停止服务: $0 stop"
    log_info ""
    
    show_status
    
    # 保持脚本运行
    log_info "按 Ctrl+C 停止所有服务..."
    trap stop_services EXIT
    wait
}

# 帮助信息
show_help() {
    echo "NestLabel Web 启动脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start    启动所有服务 (默认)"
    echo "  stop     停止所有服务"
    echo "  status   查看服务状态"
    echo "  logs     查看服务日志"
    echo "  restart  重启所有服务"
    echo "  help     显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0           # 启动所有服务"
    echo "  $0 start     # 启动所有服务"
    echo "  $0 stop      # 停止所有服务"
    echo "  $0 status    # 查看运行状态"
    echo "  $0 logs      # 查看日志"
}

# 主逻辑
case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    restart)
        stop_services
        sleep 2
        start_all
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac
