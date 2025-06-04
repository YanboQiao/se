"""
db.py   —— 数据库相关工具
依赖：PyMySQL ≥ 1.1.0
"""

from __future__ import annotations

import json
import pathlib
import secrets
import time

import pymysql

# ----------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------
TOKEN_EXPIRE_SECONDS: int = 3600           # token 有效 1 小时
_CFG_PATH = pathlib.Path(__file__).parent.parent / "db_config.json"

# ----------------------------------------------------------------------
# 读取数据库配置
# ----------------------------------------------------------------------
with _CFG_PATH.open(encoding="utf-8") as fp:
    _cfg: dict[str, object] = json.load(fp)
_cfg["cursorclass"] = pymysql.cursors.DictCursor
DB_CONFIG: dict[str, object] = _cfg                  # 供外部查看

# ----------------------------------------------------------------------
# 连接函数
# ----------------------------------------------------------------------
def get_db_connection() -> pymysql.connections.Connection:
    """创建并返回数据库连接"""
    return pymysql.connect(**DB_CONFIG)

# ----------------------------------------------------------------------
# 业务函数
# ----------------------------------------------------------------------
def register_user(
    useremail: str,
    username: str,
    password: str,
    role: str,
) -> tuple[bool, str]:
    """注册新用户"""
    table = "student" if role == "student" else "teacher"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT 1 FROM {table} WHERE useremail=%s", (useremail,))
            if cur.fetchone():
                return False, "该邮箱已被注册"
            cur.execute(
                f"INSERT INTO {table} (useremail, username, password)"
                f" VALUES (%s, %s, %s)",
                (useremail, username, password),
            )
        conn.commit()
        return True, "注册成功"
    except Exception as exc:
        return False, f"注册失败: {exc}"
    finally:
        conn.close()


def login_user(
    useremail: str,
    password: str,
    role: str,
) -> tuple[bool, str, dict | None]:
    """登录并生成 token"""
    table = "student" if role == "student" else "teacher"
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM {table} WHERE useremail=%s", (useremail,))
            user = cur.fetchone()
            if not user:
                return False, "用户不存在", None
            if user["password"] != password:
                return False, "密码错误", None
            token = secrets.token_hex(16)
            expire_at = int(time.time()) + TOKEN_EXPIRE_SECONDS
            cur.execute(
                f"UPDATE {table} SET token=%s WHERE useremail=%s",
                (token, useremail),
            )
        conn.commit()
        return (
            True,
            "登录成功",
            {
                "token": token,
                "expire_at": expire_at,
                "username": user["username"],
                "role": role,
            },
        )
    except Exception as exc:
        return False, f"登录失败: {exc}", None
    finally:
        conn.close()

def check_user_credentials(useremail: str, password: str) -> bool:
    """Return True if the email/password matches a student or teacher"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for table in ("student", "teacher"):
                cur.execute(f"SELECT password FROM {table} WHERE useremail=%s", (useremail,))
                row = cur.fetchone()
                if row and row.get("password") == password:
                    return True
    except Exception:
        return False
    finally:
        conn.close()
    return False
