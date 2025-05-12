"""
app.py —— Flask 3.x 主程序
依赖：
    Flask          ≥ 3.1.0
    Werkzeug       ≥ 3.1.2
    Flask-Mailman  ≥ 1.1.1
    Flask-Cors     ≥ 4.0.0
"""
from __future__ import annotations

import random, string, time, ssl
from typing import Final

from flask import Flask, jsonify, request, redirect, url_for
from flask_cors import CORS
from flask_mailman import EmailMessage, Mail

from db import get_db_connection, login_user, register_user  # 本地模块

# ----------------------------------------------------------------------
# 常量 & 全局缓存
# ----------------------------------------------------------------------
CODE_LIFETIME_SEC: Final[int] = 300  # 5 min
verification_codes: dict[str, tuple[str, float]] = {}  # {email: (code, ts)}

VALID_EMAIL_DOMAINS: Final[list[str]] = [
    "qq.com", "163.com", "gmail.com", "outlook.com", "126.com", "foxmail.com"
]

# ----------------------------------------------------------------------
# Flask 应用
# ----------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

app.config.update(
    MAIL_SERVER="smtp.qq.com",
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME="2713250855@qq.com",
    MAIL_PASSWORD="sipdxibzchypdeig",
    MAIL_DEFAULT_SENDER=("SE 助手", "2713250855@qq.com"),
)
mail = Mail(app)


# ============================= 工具函数 ============================= #
def _send_email_code(to_addr: str, code: str) -> None:
    """实际发送邮件（抛出异常由上层捕捉）"""
    msg = EmailMessage(
        subject="SE 助手邮箱验证码",
        body=(
            f"您好！\n\n本次操作验证码：{code}\n"
            f"请在 {CODE_LIFETIME_SEC // 60} 分钟内完成验证。\n\n"
            f"若非本人操作可忽略。"
        ),
        to=[to_addr],
    )
    with mail.get_connection() as conn:
        conn.send_messages([msg])
    app.logger.info("Mail code %s -> %s", code, to_addr)


def _code_valid(email: str, code: str) -> bool:
    tup = verification_codes.get(email)
    if not tup:
        return False
    saved, ts = tup
    if time.time() - ts > CODE_LIFETIME_SEC:
        verification_codes.pop(email, None)
        return False
    return saved == code


# ============================= Auth 路由 ============================ #
@app.post("/api/register")
def api_register():
    data = request.get_json(silent=True) or {}
    useremail, username = data.get("useremail"), data.get("username")
    password, role = data.get("password"), data.get("role")

    if not all([useremail, username, password, role]):
        return jsonify(status="error", message="信息不完整"), 400

    if useremail.split("@")[-1] not in VALID_EMAIL_DOMAINS:
        return jsonify(status="error",
                       message=f"仅支持：{', '.join(VALID_EMAIL_DOMAINS)}"), 400

    ok, msg = register_user(useremail, username, password, role)
    return jsonify(status="success" if ok else "error", message=msg), (200 if ok else 400)


@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    useremail, password, role = data.get("useremail"), data.get("password"), data.get("role")
    if not all([useremail, password, role]):
        return jsonify(status="error", message="缺少字段"), 400

    ok, msg, info = login_user(useremail, password, role)
    return jsonify(status="success" if ok else "error", message=msg, data=info), (200 if ok else 401)


# ======================== 邮箱验证码相关 ============================ #
@app.post("/api/reset-password/send-code")
def api_send_code():
    """发送验证码：前端 ResetPasswordView.vue 调用"""
    data = request.get_json(silent=True) or {}
    email, role = data.get("email"), data.get("role")
    if not email or not role:
        return jsonify(status="error", message="缺少邮箱或身份"), 400

    # 可选：检查邮箱是否存在
    table = "student" if role == "student" else "teacher"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {table} WHERE useremail=%s", (email,))
            if not cur.fetchone():
                return jsonify(status="error", message="邮箱未注册"), 404
    finally:
        conn.close()

    code = "".join(random.choices(string.digits, k=6))
    verification_codes[email] = (code, time.time())

    try:
        _send_email_code(email, code)
        return jsonify(status="success", message="验证码已发送"), 200
    except Exception as exc:
        return jsonify(status="error", message=f"邮件发送失败: {exc}"), 500


@app.post("/api/reset-password/email")
def api_reset_pwd_by_email():
    """邮箱验证码 + 新密码一次性提交"""
    data = request.get_json(silent=True) or {}
    email = data.get("useremail") or data.get("email")
    role = data.get("role")
    code = data.get("emailCode") or data.get("verifyCode")
    new_pass = data.get("newPassword")

    if not all([email, role, code, new_pass]):
        return jsonify(status="error", message="信息不完整"), 400
    if not _code_valid(email, code):
        return jsonify(status="error", message="验证码错误或已过期"), 400

    table = "student" if role == "student" else "teacher"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            rows = cur.execute(
                f"UPDATE {table} SET password=%s WHERE useremail=%s", (new_pass, email)
            )
        conn.commit()
    except Exception as exc:
        return jsonify(status="error", message=f"密码重置失败: {exc}"), 500
    finally:
        conn.close()
        verification_codes.pop(email, None)

    if rows:
        return jsonify(status="success", message="密码已重置"), 200
    return jsonify(status="error", message="未找到账号"), 404


# ---------------- 兼容旧路径 (可在完成迁移后删除) ---------------- #
@app.post("/api/send-verify-code")
def legacy_send_verify_code():
    return redirect(url_for("api_send_code"), code=307)  # 307 保留 POST


@app.post("/api/reset-password")
def legacy_reset_password():
    return redirect(url_for("api_reset_pwd_by_email"), code=307)


# ----------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=1010)
