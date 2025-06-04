"""
login_interface.py - GPT Academic登录界面
提供用户登录、注册、登出功能的Gradio界面
"""

import gradio as gr
import time
from typing import Tuple, Optional, Dict, Any
from loguru import logger
from shared_utils.auth_integration import (
    authenticate_user, 
    register_user, 
    get_user_info, 
    logout_user,
    session_manager
)

# ----------------------------------------------------------------------
# 登录界面相关函数
# ----------------------------------------------------------------------

def handle_login(useremail: str, password: str, role: str, remember_me: bool = False) -> Tuple[str, dict, bool]:
    """
    处理用户登录
    Args:
        useremail: 用户邮箱
        password: 密码
        role: 用户角色
        remember_me: 是否记住登录状态
    Returns:
        (消息, 用户信息状态, 登录成功标志)
    """
    if not useremail or not password:
        return "请填写完整的登录信息", {}, False
    
    success, message, user_info = authenticate_user(useremail, password, role)
    
    if success and user_info:
        # 创建会话
        session_id = session_manager.create_session(user_info)
        
        # 构建返回的用户状态
        user_state = {
            "logged_in": True,
            "session_id": session_id,
            "useremail": user_info["useremail"],
            "username": user_info["username"],
            "role": user_info["role"],
            "token": user_info["token"],
            "login_time": time.time()
        }
        
        welcome_msg = f"欢迎，{user_info['username']}！您已成功登录到软工智能助手。"
        logger.info(f"用户登录成功: {useremail} ({role})")
        return welcome_msg, user_state, True
    else:
        logger.warning(f"用户登录失败: {useremail} - {message}")
        return f"登录失败: {message}", {}, False

def handle_register(useremail: str, username: str, password: str, confirm_password: str, role: str) -> str:
    """
    处理用户注册
    Args:
        useremail: 用户邮箱
        username: 用户名
        password: 密码
        confirm_password: 确认密码
        role: 用户角色
    Returns:
        注册结果消息
    """
    if not all([useremail, username, password, confirm_password]):
        return "请填写完整的注册信息"
    
    if password != confirm_password:
        return "两次输入的密码不一致"
    
    if len(password) < 6:
        return "密码长度至少6位"
    
    if "@" not in useremail:
        return "请输入有效的邮箱地址"
    
    success, message = register_user(useremail, username, password, role)
    
    if success:
        logger.info(f"新用户注册: {useremail} ({role})")
        return f"注册成功！请使用邮箱和密码登录。"
    else:
        logger.warning(f"用户注册失败: {useremail} - {message}")
        return f"注册失败: {message}"

def handle_logout(user_state: dict) -> Tuple[str, dict, bool]:
    """
    处理用户登出
    Args:
        user_state: 当前用户状态
    Returns:
        (消息, 空用户状态, 登出成功标志)
    """
    if user_state.get("logged_in") and user_state.get("useremail") and user_state.get("token"):
        # 从数据库清除token
        logout_user(user_state["useremail"], user_state["token"])
        # 删除会话
        if user_state.get("session_id"):
            session_manager.remove_session(user_state["session_id"])
        
        logger.info(f"用户登出: {user_state.get('useremail')}")
        return "您已成功登出", {}, True
    else:
        return "您尚未登录", {}, False

def check_login_status(user_state: dict) -> Tuple[bool, str]:
    """
    检查用户登录状态
    Args:
        user_state: 用户状态
    Returns:
        (是否已登录, 用户信息文本)
    """
    if not user_state.get("logged_in"):
        return False, "未登录"
    
    session_id = user_state.get("session_id")
    if session_id:
        session = session_manager.get_session(session_id)
        if session:
            username = session.get("username", "用户")
            role_text = "教师" if session.get("role") == "teacher" else "学生"
            return True, f"已登录: {username} ({role_text})"
    
    return False, "登录已过期，请重新登录"

def get_current_user(user_state: dict) -> Optional[Dict]:
    """
    获取当前登录用户信息
    Args:
        user_state: 用户状态
    Returns:
        用户信息字典或None
    """
    if not user_state.get("logged_in"):
        return None
    
    session_id = user_state.get("session_id")
    if session_id:
        return session_manager.get_session(session_id)
    
    return None

# ----------------------------------------------------------------------
# 登录界面构建函数
# ----------------------------------------------------------------------

def create_login_interface():
    """
    创建登录界面
    Returns:
        (login_interface, user_state, login_status)
    """
    with gr.Blocks(title="用户登录") as login_interface:
        
        # 用户状态存储
        user_state = gr.State({})
        
        # 登录状态显示
        login_status = gr.Markdown("请登录以使用软工智能助手", elem_id="login-status")
        
        with gr.Tab("登录", elem_id="login-tab"):
            with gr.Row():
                with gr.Column():
                    login_email = gr.Textbox(
                        label="邮箱地址",
                        placeholder="请输入您的邮箱地址",
                        elem_id="login-email"
                    )
                    login_password = gr.Textbox(
                        label="密码",
                        type="password",
                        placeholder="请输入密码",
                        elem_id="login-password"
                    )
                    login_role = gr.Radio(
                        choices=["student", "teacher"],
                        value="student",
                        label="身份",
                        info="选择您的身份：学生或教师"
                    )
                    remember_me = gr.Checkbox(
                        label="记住登录状态",
                        value=False
                    )
                    
                    with gr.Row():
                        login_btn = gr.Button("登录", variant="primary", elem_id="login-button")
                        logout_btn = gr.Button("登出", variant="secondary", visible=False, elem_id="logout-button")
            
            login_message = gr.Markdown("", elem_id="login-message")
        
        with gr.Tab("注册", elem_id="register-tab"):
            with gr.Row():
                with gr.Column():
                    reg_email = gr.Textbox(
                        label="邮箱地址",
                        placeholder="请输入邮箱地址",
                        elem_id="reg-email"
                    )
                    reg_username = gr.Textbox(
                        label="用户名",
                        placeholder="请输入用户名",
                        elem_id="reg-username"
                    )
                    reg_password = gr.Textbox(
                        label="密码",
                        type="password",
                        placeholder="请输入密码（至少6位）",
                        elem_id="reg-password"
                    )
                    reg_confirm_password = gr.Textbox(
                        label="确认密码",
                        type="password",
                        placeholder="请再次输入密码",
                        elem_id="reg-confirm-password"
                    )
                    reg_role = gr.Radio(
                        choices=["student", "teacher"],
                        value="student",
                        label="身份",
                        info="选择您要注册的身份"
                    )
                    
                    register_btn = gr.Button("注册", variant="primary", elem_id="register-button")
            
            register_message = gr.Markdown("", elem_id="register-message")
        
        # 事件处理
        def update_login_ui(message, user_state_new, success):
            if success:
                return {
                    login_message: gr.update(value=f"✅ {message}"),
                    login_status: gr.update(value=f"✅ {message}"),
                    login_btn: gr.update(visible=False),
                    logout_btn: gr.update(visible=True),
                    user_state: user_state_new
                }
            else:
                return {
                    login_message: gr.update(value=f"❌ {message}"),
                    login_status: gr.update(value="❌ 登录失败，请重试"),
                    login_btn: gr.update(visible=True),
                    logout_btn: gr.update(visible=False),
                    user_state: {}
                }
        
        def update_logout_ui(message, user_state_new, success):
            return {
                login_message: gr.update(value=f"ℹ️ {message}"),
                login_status: gr.update(value="请登录以使用软工智能助手"),
                login_btn: gr.update(visible=True),
                logout_btn: gr.update(visible=False),
                user_state: user_state_new
            }
        
        def update_register_ui(message):
            if "成功" in message:
                return gr.update(value=f"✅ {message}")
            else:
                return gr.update(value=f"❌ {message}")
        
        # 绑定事件
        login_btn.click(
            handle_login,
            inputs=[login_email, login_password, login_role, remember_me],
            outputs=[login_message, user_state, gr.State()]
        ).then(
            update_login_ui,
            inputs=[login_message, user_state, gr.State()],
            outputs=[login_message, login_status, login_btn, logout_btn, user_state]
        )
        
        logout_btn.click(
            handle_logout,
            inputs=[user_state],
            outputs=[login_message, user_state, gr.State()]
        ).then(
            update_logout_ui,
            inputs=[login_message, user_state, gr.State()],
            outputs=[login_message, login_status, login_btn, logout_btn, user_state]
        )
        
        register_btn.click(
            handle_register,
            inputs=[reg_email, reg_username, reg_password, reg_confirm_password, reg_role],
            outputs=[register_message]
        ).then(
            update_register_ui,
            inputs=[register_message],
            outputs=[register_message]
        )
    
    return login_interface, user_state, login_status
