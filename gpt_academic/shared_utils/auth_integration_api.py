"""
auth_integration_api.py - GPT Academic与SE Backend的API登录集成模块
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
# 认证函数
# ----------------------------------------------------------------------
def authenticate_user(email: str, password: str, role: str) -> Tuple[bool, str, Optional[Dict]]:
    """
    通过SE Backend API进行用户认证
    
    Args:
        email: 用户邮箱
        password: 密码
        role: 用户角色 ('student' 或 'teacher')
    
    Returns:
        Tuple[bool, str, Optional[Dict]]: (成功标志, 消息, 用户信息)
    """
    try:
        # 调用后端登录API
        response = requests.post(
            f"{BACKEND_API_BASE_URL}/api/login",
            json={
                "useremail": email,
                "password": password,
                "role": role
            },
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        data = response.json()
        
        if response.status_code == 200 and data.get("status") == "success":
            user_info = data.get("data", {})
            # 确保用户信息包含必要字段
            if not user_info.get("useremail"):
                user_info["useremail"] = email
            if not user_info.get("role"):
                user_info["role"] = role
                
            logger.info(f"用户 {email} ({role}) 通过API认证成功")
            return True, "登录成功", user_info
        else:
            message = data.get("message", "登录失败")
            logger.warning(f"用户 {email} ({role}) 登录失败: {message}")
            return False, message, None
            
    except requests.exceptions.ConnectionError:
        logger.error(f"无法连接到后端API: {BACKEND_API_BASE_URL}")
        return False, "无法连接到认证服务器，请确保后端服务已启动", None
    except requests.exceptions.Timeout:
        logger.error("后端API请求超时")
        return False, "请求超时，请稍后重试", None
    except requests.exceptions.RequestException as e:
        logger.error(f"登录API请求失败: {e}")
        return False, "网络连接错误，请稍后重试", None
    except Exception as e:
        logger.error(f"登录过程发生错误: {e}")
        return False, "系统错误，请稍后重试", None


def register_user(email: str, username: str, password: str, role: str) -> Tuple[bool, str]:
    """
    通过SE Backend API进行用户注册
    
    Args:
        email: 用户邮箱
        username: 用户名
        password: 密码
        role: 用户角色 ('student' 或 'teacher')
    
    Returns:
        Tuple[bool, str]: (成功标志, 消息)
    """
    try:
        # 调用后端注册API
        response = requests.post(
            f"{BACKEND_API_BASE_URL}/api/register",
            json={
                "useremail": email,
                "username": username,
                "password": password,
                "role": role
            },
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        data = response.json()
        
        if response.status_code == 200 and data.get("status") == "success":
            message = data.get("message", "注册成功")
            logger.info(f"用户 {email} ({role}) 注册成功")
            return True, message
        else:
            message = data.get("message", "注册失败")
            logger.warning(f"用户 {email} ({role}) 注册失败: {message}")
            return False, message
            
    except requests.exceptions.ConnectionError:
        logger.error(f"无法连接到后端API: {BACKEND_API_BASE_URL}")
        return False, "无法连接到认证服务器，请确保后端服务已启动"
    except requests.exceptions.Timeout:
        logger.error("后端API请求超时")
        return False, "请求超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        logger.error(f"注册API请求失败: {e}")
        return False, "网络连接错误，请稍后重试"
    except Exception as e:
        logger.error(f"注册过程发生错误: {e}")
        return False, "系统错误，请稍后重试"


def test_backend_connection() -> bool:
    """
    测试与后端API的连接
    
    Returns:
        bool: 连接成功标志
    """
    try:
        response = requests.get(f"{BACKEND_API_BASE_URL}/", timeout=5)
        return response.status_code in [200, 404]  # 404也说明服务在运行
    except:
        return False


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
        logger.info(f"创建会话: {session_id} for {user_info.get('useremail')}")
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
            user_info = self.sessions[session_id]
            del self.sessions[session_id]
            logger.info(f"删除会话: {session_id} for {user_info.get('useremail')}")
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
        if expired_sessions:
            logger.info(f"清理了 {len(expired_sessions)} 个过期会话")

# 全局会话管理器
session_manager = UserSession()

# ----------------------------------------------------------------------
# 系统初始化函数
# ----------------------------------------------------------------------
def initialize_auth_system() -> bool:
    """
    初始化认证系统
    检查后端API连接
    Returns:
        初始化成功标志
    """
    try:
        logger.info("正在初始化API认证系统...")
        
        # 测试后端连接
        if not test_backend_connection():
            logger.error(f"无法连接到后端API: {BACKEND_API_BASE_URL}")
            logger.error("请确保SE Backend服务在1010端口运行")
            return False
        
        logger.info("后端API连接测试成功")
        
        # 清理过期会话
        session_manager.cleanup_expired_sessions()
        
        logger.info("API认证系统初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"API认证系统初始化失败: {e}")
        return False

def check_auth_dependencies() -> bool:
    """
    检查认证系统依赖项
    Returns:
        依赖检查成功标志
    """
    try:
        import requests
        import loguru
        logger.info("API认证系统依赖项检查通过")
        return True
    except ImportError as e:
        logger.error(f"缺少必要依赖: {e}")
        logger.error("请运行: pip install requests loguru")
        return False
