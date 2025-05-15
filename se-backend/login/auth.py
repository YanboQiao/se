"""
auth.py —— 用户身份验证与权限控制
提供基于 token + useremail 的鉴权验证，以及按角色（教师/学生）权限控制的装饰器。
"""

from functools import wraps
from flask import request, jsonify, g
from db import get_db_connection


def verify_token(useremail: str, token: str, role_hint: str | None = None) -> str | None:
    """验证用户 token 是否有效。返回 'student' 或 'teacher'，若无效则返回 None。"""
    if not useremail or not token:
        return None
    # 确认角色提示，限定查询范围（仅接受 'student' 或 'teacher'）
    if role_hint not in ("student", "teacher"):
        tables_to_check = ["teacher", "student"]
    else:
        tables_to_check = [role_hint]
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for role in tables_to_check:
                cur.execute(f"SELECT 1 FROM {role} WHERE useremail=%s AND token=%s", (useremail, token))
                if cur.fetchone():
                    # 找到匹配的用户
                    return role
        return None
    except Exception:
        # 查询异常时视为验证失败
        return None
    finally:
        conn.close()


def _extract_token_and_user() -> tuple[str | None, str | None, str | None]:
    """从请求中提取 token、用户邮箱，以及角色提示"""
    token = None
    useremail = None
    role_hint = None
    json_data = None
    # 提取 token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):].strip()
    if not token:
        token = request.headers.get("token") or request.args.get("token")
    if not token:
        # 尝试从请求正文获取
        if request.form and "token" in request.form:
            token = request.form.get("token")
        else:
            if json_data is None:
                json_data = request.get_json(silent=True)
            if json_data:
                token = json_data.get("token")
    # 提取用户邮箱
    useremail = (request.headers.get("X-User-Email") or
                 request.args.get("useremail") or request.args.get("email") or request.args.get("userId") or
                 request.args.get("teacherId") or request.args.get("studentId"))
    if not useremail:
        if request.form and (request.form.get("useremail") or request.form.get("email") or request.form.get("userId") or
                             request.form.get("teacherId") or request.form.get("studentId")):
            useremail = (request.form.get("useremail") or request.form.get("email") or
                         request.form.get("userId") or request.form.get("teacherId") or request.form.get("studentId"))
        else:
            if json_data is None:
                json_data = request.get_json(silent=True)
            if json_data:
                useremail = (json_data.get("useremail") or json_data.get("email") or
                             json_data.get("userId") or json_data.get("teacherId") or json_data.get("studentId"))
    # 提取角色提示
    group = request.args.get("userGroup")
    if group:
        role_hint = "teacher" if str(group) == "2" else "student" if str(group) == "1" else None
    if role_hint is None:
        role_param = request.args.get("role") or (request.form.get("role") if request.form else None)
        if role_param:
            role_hint = role_param
        else:
            if json_data is None:
                json_data = request.get_json(silent=True)
            if json_data:
                # userGroup 可能出现在 JSON 请求体中
                if json_data.get("userGroup") is not None:
                    group_val = str(json_data.get("userGroup"))
                    if group_val.isdigit():
                        role_hint = "teacher" if group_val == "2" else "student" if group_val == "1" else None
                    else:
                        role_hint = json_data.get("role")
                else:
                    role_hint = json_data.get("role")
    # 规范化 role_hint 字符串
    if role_hint:
        rl = str(role_hint).lower()
        if rl not in ("student", "teacher"):
            if rl.isdigit():
                role_hint = "teacher" if rl == "2" else "student" if rl == "1" else None
            else:
                role_hint = "teacher" if "teacher" in rl else ("student" if "student" in rl else None)
    return token, useremail, role_hint


def login_required(f):
    """登录保护装饰器：验证请求中的 token 和用户身份"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        token, useremail, role_hint = _extract_token_and_user()
        if not token or not useremail:
            return jsonify(status="error", message="未登录，请先登录"), 401
        role = verify_token(useremail, token, role_hint)
        if role is None:
            return jsonify(status="error", message="登录已失效，请重新登录"), 401
        # 将用户信息保存到上下文，以便后续使用
        g.user = {"email": useremail, "role": role}
        return f(*args, **kwargs)

    return wrapper


def teacher_required(f):
    """教师权限装饰器：要求当前登录用户为教师"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        token, useremail, role_hint = _extract_token_and_user()
        if not token or not useremail:
            return jsonify(status="error", message="未登录，请先登录"), 401
        # 验证身份（不限制角色，以便区分权限）
        role = verify_token(useremail, token)
        if role is None:
            return jsonify(status="error", message="登录已失效，请重新登录"), 401
        if role != "teacher":
            return jsonify(status="error", message="权限不足"), 403
        g.user = {"email": useremail, "role": role}
        return f(*args, **kwargs)

    return wrapper


def student_required(f):
    """学生权限装饰器：要求当前登录用户为学生"""

    @wraps(f)
    def wrapper(*args, **kwargs):
        token, useremail, role_hint = _extract_token_and_user()
        if not token or not useremail:
            return jsonify(status="error", message="未登录，请先登录"), 401
        role = verify_token(useremail, token)
        if role is None:
            return jsonify(status="error", message="登录已失效，请重新登录"), 401
        if role != "student":
            return jsonify(status="error", message="权限不足"), 403
        g.user = {"email": useremail, "role": role}
        return f(*args, **kwargs)

    return wrapper
