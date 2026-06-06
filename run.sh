#!/bin/bash

# Wol_xyz 运行脚本
# 用法: ./run.sh {start|build|stop|restart|rebuild|status}

set -e

# 配置
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$PROJECT_DIR/.backend.pid"
LOG_FILE="$PROJECT_DIR/backend.log"
PORT=39090

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 构建前端
build_frontend() {
    echo -e "${YELLOW}构建前端...${NC}"
    cd "$PROJECT_DIR/frontend"

    if [ ! -d "node_modules" ]; then
        echo "安装前端依赖..."
        npm install
    fi

    npm run build
    echo -e "${GREEN}前端构建完成 ✓${NC}"
}

# 启动后端
start_backend() {
    echo -e "${YELLOW}启动后端...${NC}"
    cd "$PROJECT_DIR"

    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        echo "创建 Python 虚拟环境..."
        python3 -m venv .venv
        source .venv/bin/activate
        pip install -r backend/requirements.txt
    else
        source .venv/bin/activate
    fi

    # 检查是否已在运行
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${RED}后端已在运行 (PID: $pid)${NC}"
            return 1
        fi
    fi

    # 后台启动
    nohup uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"

    sleep 2

    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        echo -e "${GREEN}后端启动成功 (PID: $(cat "$PID_FILE"))${NC}"
    else
        echo -e "${RED}后端启动失败，请查看日志: $LOG_FILE${NC}"
        return 1
    fi
}

# 停止后端
stop_backend() {
    echo -e "${YELLOW}停止后端...${NC}"

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$PID_FILE"
            echo -e "${GREEN}后端已停止 ✓${NC}"
        else
            rm -f "$PID_FILE"
            echo -e "${YELLOW}进程不存在，已清理 PID 文件${NC}"
        fi
    else
        echo -e "${YELLOW}后端未在运行${NC}"
    fi
}

# 查看状态
show_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}后端运行中 (PID: $pid)${NC}"
            echo -e "访问地址: http://localhost:$PORT"
        else
            rm -f "$PID_FILE"
            echo -e "${RED}后端已停止${NC}"
        fi
    else
        echo -e "${YELLOW}后端未启动${NC}"
    fi
}

# 帮助信息
show_help() {
    echo "用法: ./run.sh {start|build|stop|restart|rebuild|status}"
    echo ""
    echo "命令说明:"
    echo "  start    - 直接启动后端（不构建前端）"
    echo "  build    - 构建前端并启动后端"
    echo "  stop     - 停止后端"
    echo "  restart  - 重启后端（不构建前端）"
    echo "  rebuild  - 重新构建前端并重启后端"
    echo "  status   - 查看运行状态"
}

# 主流程
case "${1:-help}" in
    start)
        echo "=== Wol_xyz 启动 ==="
        start_backend
        echo ""
        echo -e "${GREEN}启动完成${NC}"
        echo -e "访问地址: http://localhost:$PORT"
        ;;
    build)
        echo "=== Wol_xyz 构建并启动 ==="
        build_frontend
        start_backend
        echo ""
        echo -e "${GREEN}构建并启动完成${NC}"
        echo -e "访问地址: http://localhost:$PORT"
        ;;
    stop)
        stop_backend
        ;;
    restart)
        echo "=== Wol_xyz 重启 ==="
        stop_backend
        sleep 1
        start_backend
        echo ""
        echo -e "${GREEN}重启完成${NC}"
        echo -e "访问地址: http://localhost:$PORT"
        ;;
    rebuild)
        echo "=== Wol_xyz 重新构建并重启 ==="
        stop_backend
        sleep 1
        build_frontend
        start_backend
        echo ""
        echo -e "${GREEN}重新构建并重启完成${NC}"
        echo -e "访问地址: http://localhost:$PORT"
        ;;
    status)
        show_status
        ;;
    *)
        show_help
        exit 1
        ;;
esac
