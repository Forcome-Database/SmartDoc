# 环境配置指南

## OpenMP 库冲突问题

### 问题描述

```
OMP: Error #15: Initializing libiomp5md.dll, but found libiomp5md.dll already initialized.
```

PaddlePaddle 和其他库（NumPy、MKL）都链接了 OpenMP 运行时库，导致冲突。

### 解决方案

**方案1：代码中设置（已自动修复）**

```python
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
```

**方案2：系统环境变量（永久解决）**

Windows:
1. 右键"此电脑" → "属性" → "高级系统设置"
2. 点击"环境变量"
3. 新建用户变量：`KMP_DUPLICATE_LIB_OK` = `TRUE`

Linux/macOS:
```bash
echo 'export KMP_DUPLICATE_LIB_OK=TRUE' >> ~/.bashrc
source ~/.bashrc
```

## Conda 环境配置

```bash
# 创建环境
conda create -n SmartDoc python=3.11
conda activate SmartDoc

# 安装依赖
cd backend
pip install -r requirements.txt
```

## 环境变量配置

在 `backend/.env` 中配置：

```bash
# 数据库
DATABASE_URL=mysql+aiomysql://root:password@localhost:3306/smartdoc

# Redis
REDIS_URL=redis://localhost:6379/0

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Tesseract（可选）
TESSERACT_CMD=D:/Work/software/Tesseract/tesseract.exe
TESSDATA_PREFIX=D:/Work/software/Tesseract/tessdata

# LLM（可选）
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-3.5-turbo
```

## 常见环境问题

### Python 版本不兼容

```bash
python --version  # 应该是 3.11.x
conda create -n SmartDoc python=3.11
```

### CUDA 相关错误

```bash
pip uninstall paddlepaddle-gpu
pip install paddlepaddle==3.0.0  # CPU版本
```

### Tesseract 未找到

1. 下载安装: https://github.com/UB-Mannheim/tesseract/wiki
2. 添加到 PATH 环境变量
3. 配置 `TESSDATA_PREFIX`

### 端口被占用

```bash
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F
```

## 验证清单

- [ ] Python 3.11 已安装
- [ ] Conda 环境已创建
- [ ] 所有依赖已安装
- [ ] OpenMP 环境变量已设置
- [ ] Tesseract 已安装（可选）
- [ ] 数据库连接正常
- [ ] 后端服务可以启动
