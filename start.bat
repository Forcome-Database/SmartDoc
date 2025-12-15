@echo off
chcp 65001 >nul

:: 检查参数
if "%1"=="" goto :usage
if "%1"=="dev" goto :dev
if "%1"=="prod" goto :prod
goto :usage

:usage
echo ========================================
echo  智能文档处理中台 - 启动脚本
echo ========================================
echo.
echo 用法: start.bat [dev^|prod]
echo.
echo   dev   - 启动开发环境 (本地服务)
echo   prod  - 启动生产环境 (Docker Compose)
echo.
echo 示例:
echo   start.bat dev
echo   start.bat prod
echo.
goto :eof

:dev
echo ========================================
echo  智能文档处理中台 - 开发环境启动
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
echo  开发环境启动完成！
echo ========================================
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
goto :eof

:prod
echo ========================================
echo  智能文档处理中台 - 生产环境启动
echo ========================================
echo.

echo [1/2] 加载生产环境配置...
copy /Y "backend\.env.production" "backend\.env" >nul
echo 已加载: backend\.env.production -^> backend\.env
echo.

echo [2/2] 启动 Docker Compose 服务...
docker-compose up -d

echo.
echo ========================================
echo  生产环境启动完成！
echo ========================================
echo.
echo 查看服务状态: docker-compose ps
echo 查看服务日志: docker-compose logs -f
echo 停止所有服务: docker-compose down
echo.
goto :eof
