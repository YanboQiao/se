import pymysql
import secrets
import time

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '12345678',  
    'database': 'se_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

TOKEN_EXPIRE_SECONDS = 3600  # token有效期1小时

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def register_user(useremail, username, password, role):
    """注册新用户，role为'student'或'teacher'"""
    table = 'student' if role == 'student' else 'teacher'
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 检查邮箱是否已存在
            sql_check = f"SELECT * FROM {table} WHERE useremail=%s"
            cursor.execute(sql_check, (useremail,))
            if cursor.fetchone():
                return False, "该邮箱已被注册"
            # 插入新用户
            sql_insert = f"INSERT INTO {table} (useremail, username, password) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, (useremail, username, password))
        conn.commit()
        return True, "注册成功"
    except Exception as e:
        return False, f"注册失败: {str(e)}"
    finally:
        conn.close()

def login_user(useremail, password, role):
    """用户登录，支持学生和教师，登录成功生成token"""
    table = 'student' if role == 'student' else 'teacher'
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = f"SELECT * FROM {table} WHERE useremail=%s"
            cursor.execute(sql, (useremail,))
            user = cursor.fetchone()
            if not user:
                return False, "用户不存在", None
            if user['password'] != password:
                return False, "密码错误", None
            # 生成token和过期时间
            token = secrets.token_hex(16)
            expire_at = int(time.time()) + TOKEN_EXPIRE_SECONDS
            update_sql = f"UPDATE {table} SET token=%s WHERE useremail=%s"
            cursor.execute(update_sql, (token, useremail))
            conn.commit()
            return True, "登录成功", {
                "token": token,
                "expire_at": expire_at,
                "username": user["username"],
                "role": role
            }
    except Exception as e:
        return False, f"登录失败: {str(e)}", None
    finally:
        conn.close()