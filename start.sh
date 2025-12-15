#!/bin/bash

# 智能文档处理中台 - 启动脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    echo "========================================"
    echo " 智能文档处理中台 - 启动脚本"
    echo "========================================"
    echo ""
    echo "用法: ./start.sh [dev|prod]"
    echo ""
    echo "  dev   - 启动开发环境 (本地服务)"
    echo "  prod  - 启动生产环境 (Docker Compose)"
    echo ""
    echo "示例:"
    echo "  ./start.sh dev"
    echo "  ./start.sh prod"
    echo ""
    exit 1
}

start_dev() {
    echo "========================================"
    echo " 智能文档处理中台 - 开发环境启动"
    echo "========================================"
    echo ""

    echo -e "${YELLOW}[0/5] 加载开发环境配置...${NC}"
    cp -f backend/.env.development backend/.env
    echo "已加载: backend/.env.development -> backend/.env"
    echo ""

    echo -e "${YELLOW}[1/5] 启动后端服务...${NC}"
    echo "端口: 8000"
    cd backend
    uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    echo "后端服务 PID: $BACKEND_PID"
    
    echo "等待后端服务启动..."
    sleep 5

    echo ""
    echo -e "${YELLOW}[2/5] 启动 OCR Worker...${NC}"
    cd backend
    python -m app.tasks.ocr_worker &
    OCR_PID=$!
    cd ..
    echo "OCR Worker PID: $OCR_PID"

    echo ""
    echo -e "${YELLOW}[3/5] 启动 Pipeline Worker...${NC}"
    cd backend
    python -m app.tasks.pipeline_worker &
    PIPELINE_PID=$!
    cd ..
    echo "Pipeline Worker PID: $PIPELINE_PID"

    echo ""
    echo -e "${YELLOW}[4/5] 启动 Push Worker...${NC}"
    cd backend
    python -m app.tasks.push_worker &
    PUSH_PID=$!
    cd ..
    echo "Push Worker PID: $PUSH_PID"

    echo ""
    echo "等待 Worker 服务启动..."
    sleep 3

    echo ""
    echo -e "${YELLOW}[5/5] 启动前端服务...${NC}"
    echo "端口: 5173"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo "前端服务 PID: $FRONTEND_PID"

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} 开发环境启动完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "后端服务: http://localhost:8000"
    echo "API 文档: http://localhost:8000/api/docs"
    echo "前端服务: http://localhost:5173"
    echo ""
    echo "Worker 服务:"
    echo "  - OCR Worker (处理OCR任务)"
    echo "  - Pipeline Worker (处理数据管道)"
    echo "  - Push Worker (处理Webhook推送)"
    echo ""
    echo "进程 PID:"
    echo "  Backend: $BACKEND_PID"
    echo "  OCR Worker: $OCR_PID"
    echo "  Pipeline Worker: $PIPELINE_PID"
    echo "  Push Worker: $PUSH_PID"
    echo "  Frontend: $FRONTEND_PID"
    echo ""
    echo "按 Ctrl+C 停止所有服务..."
    
    # 等待任意子进程结束
    wait
}

start_prod() {
    echo "========================================"
    echo " 智能文档处理中台 - 生产环境启动"
    echo "========================================"
    echo ""

    echo -e "${YELLOW}[1/2] 加载生产环境配置...${NC}"
    cp -f backend/.env.production backend/.env
    echo "已加载: backend/.env.production -> backend/.env"
    echo ""

    echo -e "${YELLOW}[2/2] 启动 Docker Compose 服务...${NC}"
    docker-compose up -d

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} 生产环境启动完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "查看服务状态: docker-compose ps"
    echo "查看服务日志: docker-compose logs -f"
    echo "停止所有服务: docker-compose down"
    echo ""
}

# 主逻辑
case "$1" in
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    *)
        usage
        ;;
esac
