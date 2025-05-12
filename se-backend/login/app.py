"""
app.py —— Flask 3.x 主程序
依赖：
    Flask          ≥ 3.1.0
    Werkzeug       ≥ 3.1.2
    Flask-Mailman  ≥ 1.1.1
    Flask-Cors     ≥ 4.0.0
"""

from __future__ import annotations

import random
import string
import time
from typing import Final

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_mailman import EmailMessage, Mail

from db import get_db_connection, login_user, register_user  # 本地模块
import ssl

# ----------------------------------------------------------------------
# 全局常量与变量
# ----------------------------------------------------------------------
CODE_LIFETIME_SEC: Final[int] = 300  # 验证码 5 分钟有效
verification_codes: dict[str, tuple[str, float]] = {}  # {email: (code, timestamp)}

VALID_EMAIL_DOMAINS: Final[list[str]] = [
    "qq.com", "163.com", "gmail.com", "outlook.com", "126.com", "foxmail.com"
]

# ----------------------------------------------------------------------
# 创建 Flask 应用
# ----------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# ----------------------------- 邮件配置 ------------------------------
app.config.update(
    MAIL_SERVER="smtp.qq.com",
    MAIL_PORT=465,
    MAIL_USE_SSL=True,  # SSL 465
    MAIL_USE_TLS=False,
    MAIL_USERNAME="2713250855@qq.com",  # 换成自己的邮箱
    MAIL_PASSWORD="sipdxibzchypdeig",  # 换成 QQ SMTP 授权码
    MAIL_DEFAULT_SENDER=("SE 助手", "2713250855@qq.com"),
)

mail = Mail(app)


# ----------------------------------------------------------------------
# 工具函数
# ----------------------------------------------------------------------
def _send_verification_email(recipient: str, code: str) -> None:
    """发送 6 位邮箱验证码"""
    msg = EmailMessage(
        subject="SE 助手邮箱验证码",
        body=(
            f"您好！\n\n"
            f"您本次操作的验证码为：{code}\n"
            f"请在 {CODE_LIFETIME_SEC // 60} 分钟内完成验证。\n\n"
            f"（如非本人操作，请忽略此邮件）"
        ),
        to=[recipient],
    )

    # 显式获取 SMTP 连接，失败会抛出真实的 SMTP 异常
    with mail.get_connection() as conn:
        conn.send_messages([msg])

    app.logger.info("Verification code %s sent to %s", code, recipient)


def _verify_code(email: str, code: str) -> bool:
    """校验验证码是否正确且未过期"""
    if email not in verification_codes:
        return False
    saved_code, ts = verification_codes[email]
    if time.time() - ts > CODE_LIFETIME_SEC:  # 超时
        verification_codes.pop(email, None)
        return False
    return saved_code == code


# ----------------------------------------------------------------------
# 路由
# ----------------------------------------------------------------------
@app.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    useremail, username = data.get("useremail"), data.get("username")
    password, role = data.get("password"), data.get("role")

    if not all([useremail, username, password, role]):
        return jsonify(status="error", message="请填写完整信息"), 400

    domain = useremail.split("@")[-1] if "@" in useremail else ""
    if domain not in VALID_EMAIL_DOMAINS:
        return jsonify(
            status="error",
            message=f"目前只支持：{', '.join(VALID_EMAIL_DOMAINS)}"
        ), 400

    ok, msg = register_user(useremail, username, password, role)
    return jsonify(status="success" if ok else "error", message=msg), (200 if ok else 400)


@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    useremail, password = data.get("useremail"), data.get("password")
    role = data.get("role")

    if not all([useremail, password, role]):
        return jsonify(status="error", message="请提供邮箱、密码和角色"), 400

    ok, msg, info = login_user(useremail, password, role)
    return jsonify(status="success" if ok else "error", message=msg, data=info), (200 if ok else 401)


@app.post("/send-verify-code")
def send_verify_code():
    from traceback import format_exc

    data = request.get_json(silent=True) or {}
    email = data.get("email")
    if not email:
        return jsonify(status="error", message="邮箱不能为空"), 400

    code = "".join(random.choices(string.digits, k=6))
    verification_codes[email] = (code, time.time())

    try:
        _send_verification_email(email, code)
        return jsonify(status="success", message="验证码已发送"), 200
    except Exception:
        # 返回完整 traceback 便于调试，生产环境可改为只返回简短信息
        return jsonify(
            status="error",
            message="邮件发送失败：\n" + format_exc()
        ), 500


@app.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    email, role = data.get("email"), data.get("role")
    code, new_pass = data.get("verifyCode"), data.get("newPassword")

    if not all([email, role, code, new_pass]):
        return jsonify(status="error", message="信息不完整"), 400
    if not _verify_code(email, code):
        return jsonify(status="error", message="验证码错误或已过期"), 400

    table = "student" if role == "student" else "teacher"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            res = cur.execute(
                f"UPDATE {table} SET password=%s WHERE useremail=%s",
                (new_pass, email),
            )
        conn.commit()
    except Exception as exc:
        return jsonify(status="error", message=f"密码重置失败: {exc}"), 500
    finally:
        conn.close()
        verification_codes.pop(email, None)

    if res:
        return jsonify(status="success", message="密码重置成功"), 200
    return jsonify(status="error", message=f"未找到该邮箱的 {role} 账号"), 404


@app.post("/check-email")
def check_email():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    role = data.get("role")

    if not email or not role:
        return jsonify(status="error", message="请提供邮箱和角色"), 400

    table = "student" if role == "student" else "teacher"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {table} WHERE useremail=%s", (email,))
            exists = bool(cur.fetchone())
    except Exception as exc:
        return jsonify(status="error", message=str(exc)), 500
    finally:
        conn.close()

    if exists:
        return jsonify(status="success", message="该邮箱已注册"), 200
    return jsonify(status="error", message="该邮箱未注册"), 404


@app.post("/check-verify-code")
def check_verify_code():
    data = request.get_json(silent=True) or {}
    email = data.get("email")
    code = data.get("verifyCode")

    if not email or not code:
        return jsonify(status="error", message="请提供邮箱和验证码"), 400
    if _verify_code(email, code):
        return jsonify(status="success", message="验证码正确"), 200
    return jsonify(status="error", message="验证码错误或已过期"), 400


# ----------------------------------------------------------------------
# 应用入口
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1010)
