"""
auth_integration.py - GPT Academic与SE Backend的登录集成模块
通过HTTP API与后端进行用户认证，保持统一的用户登录验证
"""

import json
import secrets
import time
import requests
from loguru import logger
from typing import Tuple, Optional, Dict, Any
import uuid

# ----------------------------------------------------------------------
# 常量配置
# ----------------------------------------------------------------------
TOKEN_EXPIRE_SECONDS: int = 3600 * 24 * 7  # token 有效期 7 天（比backend更长，适合学术工具）
BACKEND_API_BASE_URL = "http://localhost:1010"  # SE Backend API地址

# ----------------------------------------------------------------------
# 数据库配置读取
# ----------------------------------------------------------------------
def get_db_config() -> Dict[str, Any]:
    """获取数据库配置"""
    try:
        if _BACKEND_CFG_PATH.exists():
            with _BACKEND_CFG_PATH.open(encoding="utf-8") as fp:
                cfg = json.load(fp)
                cfg["cursorclass"] = pymysql.cursors.DictCursor
                return cfg
        else:
            logger.warning("未找到backend数据库配置文件，使用默认配置")
            return {
                "host": "127.0.0.1",
                "port": 3306,
                "user": "root",
                "password": "BITZZCnmsl2201?",
                "database": "se_db_new",
                "charset": "utf8mb4",
                "cursorclass": pymysql.cursors.DictCursor
            }
    except Exception as e:
        logger.error(f"读取数据库配置失败: {e}")
        raise

def get_db_connection() -> pymysql.connections.Connection:
    """创建并返回数据库连接"""
    try:
        return pymysql.connect(**get_db_config())
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise

# ----------------------------------------------------------------------
# 用户认证函数
# ----------------------------------------------------------------------
def verify_user_token(useremail: str, token: str, role_hint: str = None) -> Optional[str]:
    """
    验证用户token是否有效
    Args:
        useremail: 用户邮箱
        token: 用户token
        role_hint: 角色提示，可以是 'student' 或 'teacher'
    Returns:
        用户角色('student' 或 'teacher')，无效时返回None
    """
    if not useremail or not token:
        return None
    
    # 确定要检查的表
    if role_hint and role_hint in ("student", "teacher"):
        tables_to_check = [role_hint]
    else:
        tables_to_check = ["teacher", "student"]
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            for role in tables_to_check:
                cur.execute(
                    f"SELECT username, token FROM {role} WHERE useremail=%s AND token=%s", 
                    (useremail, token)
                )
                result = cur.fetchone()
                if result:
                    return role
        return None
    except Exception as e:
        logger.error(f"Token验证失败: {e}")
        return None
    finally:
        conn.close()

def authenticate_user(useremail: str, password: str, role: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    用户登录认证
    Args:
        useremail: 用户邮箱
        password: 用户密码
        role: 用户角色 ('student' 或 'teacher')
    Returns:
        (成功标志, 消息, 用户信息字典)
    """
    if role not in ("student", "teacher"):
        return False, "无效的用户角色", None
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 检查用户是否存在
            cur.execute(f"SELECT * FROM {role} WHERE useremail=%s", (useremail,))
            user = cur.fetchone()
            
            if not user:
                return False, "用户不存在", None
            
            if user["password"] != password:
                return False, "密码错误", None
            
            # 生成新的token (使用较短的token以适应数据库字段长度)
            token = secrets.token_hex(16)  # 32字符的随机token
            expire_at = int(time.time()) + TOKEN_EXPIRE_SECONDS
            
            # 更新用户token
            cur.execute(
                f"UPDATE {role} SET token=%s WHERE useremail=%s",
                (token, useremail)
            )
        
        conn.commit()
        
        user_info = {
            "useremail": useremail,
            "username": user["username"],
            "role": role,
            "token": token,
            "expire_at": expire_at,
        }
        
        logger.info(f"用户 {useremail} ({role}) 登录成功")
        return True, "登录成功", user_info
    
    except Exception as e:
        logger.error(f"用户登录失败: {e}")
        return False, f"登录失败: {str(e)}", None
    finally:
        conn.close()

def register_user(useremail: str, username: str, password: str, role: str) -> Tuple[bool, str]:
    """
    注册新用户
    Args:
        useremail: 用户邮箱
        username: 用户名
        password: 密码
        role: 角色 ('student' 或 'teacher')
    Returns:
        (成功标志, 消息)
    """
    if role not in ("student", "teacher"):
        return False, "无效的用户角色"
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 检查邮箱是否已注册
            cur.execute(f"SELECT 1 FROM {role} WHERE useremail=%s", (useremail,))
            if cur.fetchone():
                return False, "该邮箱已被注册"
            
            # 插入新用户
            cur.execute(
                f"INSERT INTO {role} (useremail, username, password) VALUES (%s, %s, %s)",
                (useremail, username, password)
            )
        
        conn.commit()
        logger.info(f"新用户注册成功: {useremail} ({role})")
        return True, "注册成功"
    
    except Exception as e:
        logger.error(f"用户注册失败: {e}")
        return False, f"注册失败: {str(e)}"
    finally:
        conn.close()

def get_user_info(useremail: str, token: str) -> Optional[Dict]:
    """
    根据邮箱和token获取用户信息
    Args:
        useremail: 用户邮箱
        token: 用户token
    Returns:
        用户信息字典，失败时返回None
    """
    role = verify_user_token(useremail, token)
    if not role:
        return None
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT useremail, username FROM {role} WHERE useremail=%s AND token=%s",
                (useremail, token)
            )
            user = cur.fetchone()
            if user:
                return {
                    "useremail": user["useremail"],
                    "username": user["username"],
                    "role": role
                }
        return None
    except Exception as e:
        logger.error(f"获取用户信息失败: {e}")
        return None
    finally:
        conn.close()

def logout_user(useremail: str, token: str) -> bool:
    """
    用户登出，清除token
    Args:
        useremail: 用户邮箱
        token: 用户token
    Returns:
        成功标志
    """
    role = verify_user_token(useremail, token)
    if not role:
        return False
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE {role} SET token=NULL WHERE useremail=%s AND token=%s",
                (useremail, token)
            )
        conn.commit()
        logger.info(f"用户 {useremail} ({role}) 已登出")
        return True
    except Exception as e:
        logger.error(f"用户登出失败: {e}")
        return False
    finally:
        conn.close()

# ----------------------------------------------------------------------
# Session管理
# ----------------------------------------------------------------------
class UserSession:
    """用户会话管理类"""
    
    def __init__(self):
        self.sessions = {}  # session_id -> user_info
    
    def create_session(self, user_info: Dict) -> str:
        """创建用户会话"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            **user_info,
            "created_at": time.time(),
            "last_activity": time.time()
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话信息"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # 检查会话是否过期
            if time.time() - session["created_at"] > TOKEN_EXPIRE_SECONDS:
                del self.sessions[session_id]
                return None
            # 更新最后活动时间
            session["last_activity"] = time.time()
            return session
        return None
    
    def remove_session(self, session_id: str) -> bool:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if current_time - session["created_at"] > TOKEN_EXPIRE_SECONDS
        ]
        for session_id in expired_sessions:
            del self.sessions[session_id]

# 全局会话管理器
session_manager = UserSession()

# ----------------------------------------------------------------------
# 系统初始化函数
# ----------------------------------------------------------------------
def initialize_auth_system() -> bool:
    """
    初始化认证系统
    检查数据库连接和表结构
    Returns:
        初始化成功标志
    """
    try:
        logger.info("正在初始化认证系统...")
        
        # 测试数据库连接
        conn = get_db_connection()
        if not conn:
            logger.error("数据库连接失败")
            return False
        
        try:
            with conn.cursor() as cur:
                # 检查必要的表是否存在
                tables_to_check = ["student", "teacher"]
                for table in tables_to_check:
                    cur.execute(f"SHOW TABLES LIKE '{table}'")
                    if not cur.fetchone():
                        logger.error(f"数据库表 {table} 不存在")
                        return False
                
                # 检查表结构是否包含必要字段
                required_fields = ["useremail", "username", "password", "token"]
                for table in tables_to_check:
                    cur.execute(f"DESCRIBE {table}")
                    fields = [row["Field"] for row in cur.fetchall()]
                    missing_fields = [field for field in required_fields if field not in fields]
                    if missing_fields:
                        logger.error(f"表 {table} 缺少必要字段: {missing_fields}")
                        return False
                
                logger.info("数据库表结构检查通过")
                
        finally:
            conn.close()
        
        # 清理过期会话
        session_manager.cleanup_expired_sessions()
        
        logger.info("认证系统初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"认证系统初始化失败: {e}")
        return False

def check_auth_dependencies() -> bool:
    """
    检查认证系统依赖项
    Returns:
        依赖检查成功标志
    """
    try:
        import pymysql
        import loguru
        logger.info("认证系统依赖项检查通过")
        return True
    except ImportError as e:
        logger.error(f"缺少必要依赖: {e}")
        logger.error("请运行: pip install PyMySQL loguru")
        return False
