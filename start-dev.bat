@echo off
chcp 65001 >nul
echo ========================================
echo  Enterprise IDP Platform - 开发环境启动
echo ========================================
echo.

echo [0/5] 加载开发环境配置...
copy /Y "backend\.env.development" "backend\.env" >nul
echo 已加载: backend\.env.development -^> backend\.env
echo.

echo [1/5] 启动后端服务...
echo 端口: 8000
echo.
start "Backend Server" cmd /k "cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo 等待后端服务启动...
timeout /t 5 /nobreak >nul

echo.
echo [2/5] 启动 OCR Worker...
start "OCR Worker" cmd /k "cd backend && python -m app.tasks.ocr_worker"

echo.
echo [3/5] 启动 Pipeline Worker...
start "Pipeline Worker" cmd /k "cd backend && python -m app.tasks.pipeline_worker"

echo.
echo [4/5] 启动 Push Worker...
start "Push Worker" cmd /k "cd backend && python -m app.tasks.push_worker"

echo 等待 Worker 服务启动...
timeout /t 3 /nobreak >nul

echo.
echo [5/5] 启动前端服务...
echo 端口: 5173
echo.
start "Frontend Server" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo  服务启动完成！
echo ========================================
echo.
echo 当前环境: 开发环境 (development)
echo.
echo 后端服务: http://localhost:8000
echo API 文档: http://localhost:8000/api/docs
echo 前端服务: http://localhost:5173
echo.
echo Worker 服务:
echo   - OCR Worker (处理OCR任务)
echo   - Pipeline Worker (处理数据管道)
echo   - Push Worker (处理Webhook推送)
echo.
echo 按任意键关闭此窗口...
pause >nul
