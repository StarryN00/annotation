#!/bin/bash

echo "=========================================="
echo "检查训练真实进度"
echo "=========================================="
echo ""

# 检查后端进程
echo "[1] 检查训练进程..."
if pgrep -f "python.*backend/main" > /dev/null; then
    echo "✅ 后端服务正在运行"
else
    echo "❌ 后端服务未运行"
fi

# 查看最新的训练日志
echo ""
echo "[2] 查看最新训练进度..."
echo "（显示最近3条训练记录）"
echo ""

tail -n 200 /tmp/nestlabel_backend.log 2>/dev/null | grep -E "^[[:space:]]*[0-9]+/[0-9]+" | tail -3

echo ""
echo "[3] 计算剩余时间..."

# 获取当前epoch和总epoch
CURRENT_EPOCH=$(tail -n 500 /tmp/nestlabel_backend.log 2>/dev/null | grep -E "^[[:space:]]*[0-9]+/[0-9]+" | tail -1 | awk '{print $1}' | cut -d'/' -f1)
TOTAL_EPOCH=200

if [ -n "$CURRENT_EPOCH" ] && [ "$CURRENT_EPOCH" -gt 0 ] 2>/dev/null; then
    REMAINING=$((TOTAL_EPOCH - CURRENT_EPOCH))
    # 假设每个epoch 8分钟
    REMAINING_MINUTES=$((REMAINING * 8))
    REMAINING_HOURS=$((REMAINING_MINUTES / 60))
    
    echo "当前进度: Epoch $CURRENT_EPOCH / $TOTAL_EPOCH"
    echo "已完成: $((CURRENT_EPOCH * 100 / TOTAL_EPOCH))%"
    echo "剩余: $REMAINING 个 epoch"
    echo "预估剩余时间: 约 $REMAINING_HOURS 小时"
    echo ""
    echo "说明: 每个epoch约7-8分钟（CPU训练）"
else
    echo "无法获取当前epoch，请检查日志"
fi

echo ""
echo "=========================================="
echo "提示: 训练正在进行中，请勿中断"
echo "可以关闭浏览器，但请保持终端运行"
echo "=========================================="
