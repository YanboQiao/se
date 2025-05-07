import pymysql
from flask import Flask, request, jsonify
from flask_cors import CORS
import secrets
import time
import random
import string
from db import register_user
from flask_mail import Mail, Message

# Global dictionary to store verification codes temporarily
verification_codes = {}

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '12345678',
    'database': 'se_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# 只定义一次Flask应用实例
app = Flask(__name__)
CORS(app)

# 邮件配置
app.config['MAIL_SERVER'] = 'smtp.qq.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = '2713250855@qq.com'  # 替换为你的邮箱
app.config['MAIL_PASSWORD'] = 'sipdxibzchypdeig'  # 替换为你的授权码

mail = Mail(app)

TOKEN_EXPIRE_SECONDS = 3600  # token有效期1小时


def send_verification_email(to, verify_code):
    try:
        msg = Message('您的验证码', sender=app.config['MAIL_USERNAME'], recipients=[to])
        msg.body = f'您的验证码是: {verify_code}'
        mail.send(msg)
        print(f"验证码 {verify_code} 已成功发送到 {to}")
    except Exception as e:
        print(f"邮件发送异常: {str(e)}")
        raise


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


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    print(data)  # 打印请求数据
    useremail = data.get('useremail')
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    if not all([useremail, username, password, role]):
        return jsonify({"status": "error", "message": "请填写完整信息"}), 400
    success, message = register_user(useremail, username, password, role)
    if success:
        return jsonify({"status": "success", "message": message}), 200
    else:
        return jsonify({"status": "error", "message": message}), 400


@app.route('/send-verify-code', methods=['POST'])
def send_verify_code():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"status": "error", "message": "邮箱不能为空"}), 400
    
    verify_code = ''.join(random.choices(string.digits, k=6))
    verification_codes[email] = verify_code
    
    try:
        send_verification_email(email, verify_code)
        return jsonify({"status": "success", "message": "验证码已发送"}), 200
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return jsonify({"status": "error", "message": f"邮件发送失败: {str(e)}"}), 500


@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    verify_code = data.get('verifyCode')
    new_password = data.get('newPassword')
    
    if not all([email, verify_code, new_password]):
        return jsonify({"status": "error", "message": "信息不完整"}), 400
    
    stored_code = verification_codes.get(email)
    if not stored_code or stored_code != verify_code:
        return jsonify({"status": "error", "message": "验证码错误或已过期"}), 400
    
    # TODO: 更新数据库中的密码
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 尝试更新学生表
            sql = "UPDATE student SET password = %s WHERE useremail = %s"
            result = cursor.execute(sql, (new_password, email))
            
            # 如果没有更新学生表，尝试更新教师表
            if result == 0:
                sql = "UPDATE teacher SET password = %s WHERE useremail = %s"
                result = cursor.execute(sql, (new_password, email))
            
            if result == 0:
                return jsonify({"status": "error", "message": "邮箱不存在"}), 404
                
            conn.commit()
            # 清除验证码
            if email in verification_codes:
                del verification_codes[email]
                
            return jsonify({"status": "success", "message": "密码重置成功"}), 200
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"密码重置失败: {str(e)}"}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1010)