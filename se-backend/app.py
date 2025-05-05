import pymysql
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
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
    return pymysql.connect(**DB_CONFIG)

def generate_token():
    return secrets.token_hex(16)  # 32位随机字符串

def login_user(username, password, role):
    table = 'student' if role == 'student' else 'teacher'
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 查找用户
            sql = f"SELECT * FROM {table} WHERE username=%s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            if not user:
                return False, "用户不存在", None
            # 校验密码（如有hash则用check_password_hash，否则直接比对）
            if not check_password_hash(user['password'], password) and user['password'] != password:
                return False, "密码错误", None
            # 生成token和过期时间
            token = generate_token()
            expire_at = int(time.time()) + TOKEN_EXPIRE_SECONDS
            update_sql = f"UPDATE {table} SET token=%s WHERE username=%s"
            cursor.execute(update_sql, (token, username))
            conn.commit()
            return True, "登录成功", {"token": token, "expire_at": expire_at, "username": user["username"], "role": role}
    except Exception as e:
        return False, f"登录失败: {str(e)}", None
    finally:
        conn.close()

app = Flask(__name__)
CORS(app)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    # 兼容前端的 useremail 字段
    username = data.get('username') or data.get('useremail')
    password = data.get('password')
    role = data.get('role')
    if not all([username, password, role]):
        return jsonify({"status": "error", "message": "请提供用户名、密码和身份"}), 400
    success, message, info = login_user(username, password, role)
    if success:
        return jsonify({"status": "success", "message": message, "data": info}), 200
    else:
        return jsonify({"status": "error", "message": message}), 401

# 你可以根据需要补充注册、token校验等接口

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)