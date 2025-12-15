"""
重置admin用户密码的脚本
"""
import sys
import pymysql
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def reset_admin_password(username: str = "admin", new_password: str = "admin123"):
    """
    重置指定用户的密码
    
    Args:
        username: 用户名，默认为admin
        new_password: 新密码，默认为admin123
    """
    # 数据库连接配置（从.env文件读取或使用默认值）
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'root',
        'database': 'idp_platform',
        'charset': 'utf8mb4'
    }
    
    # 生成密码哈希
    password_hash = hash_password(new_password)
    
    print(f"正在重置用户 '{username}' 的密码...")
    print(f"新密码: {new_password}")
    print(f"密码哈希: {password_hash}")
    
    try:
        # 连接数据库
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        # 更新密码
        sql = "UPDATE users SET password_hash = %s WHERE username = %s"
        cursor.execute(sql, (password_hash, username))
        connection.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ 成功重置用户 '{username}' 的密码")
            print(f"\n请使用以下凭据登录：")
            print(f"  用户名: {username}")
            print(f"  密码: {new_password}")
        else:
            print(f"❌ 用户 '{username}' 不存在")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        print("\n请检查数据库连接配置是否正确")

if __name__ == "__main__":
    # 可以通过命令行参数指定用户名和密码
    username = sys.argv[1] if len(sys.argv) > 1 else "admin"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
    
    reset_admin_password(username, password)
