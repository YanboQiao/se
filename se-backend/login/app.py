import pymysql
from flask import Flask, request, jsonify
from flask_cors import CORS
import secrets
import time

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': 'BITZZCnmsl2201?',
    'database': 'se_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

TOKEN_EXPIRE_SECONDS = 3600  # token有效期1小时


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


def generate_token():
    return secrets.token_hex(16)  # 32位随机字符串


def login_user(useremail, password, role):
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
            token = generate_token()
            expire_at = int(time.time()) + TOKEN_EXPIRE_SECONDS
            update_sql = f"UPDATE {table} SET token=%s WHERE useremail=%s"
            cursor.execute(update_sql, (token, useremail))
            conn.commit()
            return True, "登录成功", {"token": token, "expire_at": expire_at, "username": user["username"],
                                      "role": role}
    except Exception as e:
        return False, f"登录失败: {str(e)}", None
    finally:
        conn.close()


app = Flask(__name__)
CORS(app)


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    useremail = data.get('useremail')
    password = data.get('password')
    role = data.get('role')

    if not all([useremail, password, role]):
        return jsonify({"status": "error", "message": "请提供用户邮箱、密码和身份"}), 400

    success, message, info = login_user(useremail, password, role)

    if success:
        return jsonify({"status": "success", "message": message, "data": info}), 200
    else:
        return jsonify({"status": "error", "message": message}), 401


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1010)