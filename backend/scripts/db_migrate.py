#!/usr/bin/env python3
"""
数据库迁移管理脚本
提供生成、执行、回滚等数据库迁移操作
"""
import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime


class Colors:
    """终端颜色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """打印标题"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text):
    """打印成功信息"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """打印错误信息"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text):
    """打印警告信息"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text):
    """打印信息"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def run_command(cmd, cwd=None, check=True):
    """执行命令"""
    print_info(f"执行命令: {cmd}")
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
    
    if check and result.returncode != 0:
        print_error(f"命令执行失败，退出码: {result.returncode}")
        return False
    
    return True


def generate_migration(message):
    """生成迁移脚本"""
    print_header("生成数据库迁移脚本")
    
    backend_dir = Path(__file__).parent.parent
    
    if not message:
        message = f"Migration at {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    cmd = f'alembic revision --autogenerate -m "{message}"'
    
    if run_command(cmd, cwd=backend_dir):
        print_success("迁移脚本生成成功")
        print_info("请检查生成的迁移脚本: backend/alembic/versions/")
        return True
    else:
        print_error("迁移脚本生成失败")
        return False


def upgrade_database(revision="head"):
    """升级数据库"""
    print_header(f"升级数据库到版本: {revision}")
    
    backend_dir = Path(__file__).parent.parent
    
    # 显示当前版本
    print_info("当前数据库版本:")
    run_command("alembic current", cwd=backend_dir, check=False)
    
    # 执行升级
    cmd = f"alembic upgrade {revision}"
    
    if run_command(cmd, cwd=backend_dir):
        print_success(f"数据库升级成功到版本: {revision}")
        
        # 显示新版本
        print_info("升级后数据库版本:")
        run_command("alembic current", cwd=backend_dir, check=False)
        return True
    else:
        print_error("数据库升级失败")
        return False


def downgrade_database(revision="-1"):
    """降级数据库"""
    print_header(f"降级数据库到版本: {revision}")
    
    print_warning("警告: 此操作将回滚数据库变更，可能导致数据丢失！")
    confirm = input("确认继续? (yes/no): ")
    
    if confirm.lower() != "yes":
        print_info("操作已取消")
        return False
    
    backend_dir = Path(__file__).parent.parent
    
    # 显示当前版本
    print_info("当前数据库版本:")
    run_command("alembic current", cwd=backend_dir, check=False)
    
    # 执行降级
    cmd = f"alembic downgrade {revision}"
    
    if run_command(cmd, cwd=backend_dir):
        print_success(f"数据库降级成功到版本: {revision}")
        
        # 显示新版本
        print_info("降级后数据库版本:")
        run_command("alembic current", cwd=backend_dir, check=False)
        return True
    else:
        print_error("数据库降级失败")
        return False


def show_history():
    """显示迁移历史"""
    print_header("数据库迁移历史")
    
    backend_dir = Path(__file__).parent.parent
    
    print_info("当前版本:")
    run_command("alembic current", cwd=backend_dir, check=False)
    
    print_info("\n迁移历史:")
    run_command("alembic history --verbose", cwd=backend_dir, check=False)


def show_sql(direction="upgrade", revision="head"):
    """显示SQL语句（不执行）"""
    print_header(f"显示{direction}的SQL语句")
    
    backend_dir = Path(__file__).parent.parent
    
    if direction == "upgrade":
        cmd = f"alembic upgrade {revision} --sql"
    else:
        cmd = f"alembic downgrade {revision} --sql"
    
    run_command(cmd, cwd=backend_dir, check=False)


def init_data():
    """执行初始化数据脚本"""
    print_header("执行初始化数据脚本")
    
    backend_dir = Path(__file__).parent.parent
    init_sql = backend_dir / "scripts" / "init.sql"
    
    if not init_sql.exists():
        print_error(f"初始化脚本不存在: {init_sql}")
        return False
    
    print_info("请手动执行以下命令来导入初始化数据:")
    print(f"\n  mysql -u <username> -p <database> < {init_sql}")
    print(f"\n或使用Docker:")
    print(f"  docker-compose exec mysql mysql -u idp_user -p idp_platform < scripts/init.sql\n")
    
    print_warning("注意: 默认管理员账号 admin / admin123")
    print_warning("生产环境请务必修改默认密码！")
    
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据库迁移管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成迁移脚本
  python db_migrate.py generate -m "Add user table"
  
  # 升级到最新版本
  python db_migrate.py upgrade
  
  # 升级到特定版本
  python db_migrate.py upgrade abc123
  
  # 回滚一个版本
  python db_migrate.py downgrade
  
  # 回滚到特定版本
  python db_migrate.py downgrade abc123
  
  # 查看迁移历史
  python db_migrate.py history
  
  # 查看升级SQL（不执行）
  python db_migrate.py sql
  
  # 执行初始化数据
  python db_migrate.py init
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # generate命令
    generate_parser = subparsers.add_parser("generate", help="生成迁移脚本")
    generate_parser.add_argument("-m", "--message", help="迁移描述信息")
    
    # upgrade命令
    upgrade_parser = subparsers.add_parser("upgrade", help="升级数据库")
    upgrade_parser.add_argument("revision", nargs="?", default="head", help="目标版本（默认: head）")
    
    # downgrade命令
    downgrade_parser = subparsers.add_parser("downgrade", help="降级数据库")
    downgrade_parser.add_argument("revision", nargs="?", default="-1", help="目标版本（默认: -1）")
    
    # history命令
    subparsers.add_parser("history", help="显示迁移历史")
    
    # sql命令
    sql_parser = subparsers.add_parser("sql", help="显示SQL语句（不执行）")
    sql_parser.add_argument("--direction", choices=["upgrade", "downgrade"], default="upgrade", help="方向")
    sql_parser.add_argument("--revision", default="head", help="目标版本")
    
    # init命令
    subparsers.add_parser("init", help="执行初始化数据脚本")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # 执行对应命令
    if args.command == "generate":
        success = generate_migration(args.message)
    elif args.command == "upgrade":
        success = upgrade_database(args.revision)
    elif args.command == "downgrade":
        success = downgrade_database(args.revision)
    elif args.command == "history":
        success = show_history()
        success = True  # history命令总是成功
    elif args.command == "sql":
        success = show_sql(args.direction, args.revision)
        success = True  # sql命令总是成功
    elif args.command == "init":
        success = init_data()
    else:
        parser.print_help()
        return 0
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
