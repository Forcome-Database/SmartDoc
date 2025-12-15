#!/usr/bin/env python3
"""
生成Alembic迁移脚本的辅助工具
"""
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """执行命令并返回结果"""
    print(f"执行命令: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0

def main():
    """主函数"""
    # 获取backend目录路径
    backend_dir = Path(__file__).parent.parent
    
    print("=" * 60)
    print("生成初始数据库迁移脚本")
    print("=" * 60)
    
    # 生成迁移脚本
    print("\n步骤 1: 生成迁移脚本...")
    success = run_command(
        'alembic revision --autogenerate -m "Initial migration: create all tables"',
        cwd=backend_dir
    )
    
    if not success:
        print("❌ 生成迁移脚本失败")
        return 1
    
    print("✅ 迁移脚本生成成功")
    
    print("\n" + "=" * 60)
    print("下一步操作:")
    print("=" * 60)
    print("1. 检查生成的迁移脚本: backend/alembic/versions/")
    print("2. 确保数据库服务已启动")
    print("3. 执行迁移: alembic upgrade head")
    print("4. 执行初始化数据: mysql < scripts/init.sql")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
