#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py —— GPT-Academic + 登录 / 注册集成版
后端认证接口： http://127.0.0.1:1010/api/login  /register
"""

import os, sys, time, threading, webbrowser, requests, gradio as gr
from loguru import logger

# ------------------------------------------------------------------- #
#  配置 & 常量
# ------------------------------------------------------------------- #
os.environ['no_proxy'] = '*'                  # 避免代理污染
BACKEND = "http://127.0.0.1:1010/api"        # Flask 后端地址

# ------------------------------------------------------------------- #
#  认证接口封装
# ------------------------------------------------------------------- #
def _post_api(path: str, payload: dict) -> tuple[bool, str, dict]:
    """向后端发送 JSON POST 请求并统一返回 (ok, msg, data)"""
    try:
        r = requests.post(BACKEND + path, json=payload, timeout=8)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        logger.error(f"认证接口异常: {e}")
        return False, "无法连接认证服务", {}
    ok = (j.get("status") == "success")
    return ok, j.get("message", "未知错误"), j.get("data", {})

def login_api(email, pwd, role):
    return _post_api("/login", {"useremail": email, "password": pwd, "role": role})

def register_api(email, name, pwd, role):
    return _post_api("/register", {"useremail": email, "username": name,
                                   "password": pwd, "role": role})

# ------------------------------------------------------------------- #
#  插件信息编码函数（从main.py复制）
# ------------------------------------------------------------------- #
def encode_plugin_info(k, plugin)->str:
    import copy
    from themes.theme import to_cookie_str
    plugin_ = copy.copy(plugin)
    plugin_.pop("Function", None)
    plugin_.pop("Class", None)
    plugin_.pop("Button", None)
    plugin_["Info"] = plugin.get("Info", k)
    if plugin.get("AdvancedArgs", False):
        plugin_["Label"] = f"插件[{k}]的高级参数说明：" + plugin.get("ArgsReminder", f"没有提供高级参数功能说明")
    else:
        plugin_["Label"] = f"插件[{k}]不需要高级参数。"
    return to_cookie_str(plugin_)

# ------------------------------------------------------------------- #
#  认证中间件 - 包装predict函数以携带认证信息
# ------------------------------------------------------------------- #
class AuthenticatedPredict:
    """认证包装器，为predict函数添加认证上下文"""
    
    def __init__(self, original_predict):
        self.original_predict = original_predict
        self.current_token = ""
        self.current_useremail = ""
        self.current_role = ""
    
    def set_auth_context(self, token: str, useremail: str, role: str):
        """设置当前的认证上下文"""
        self.current_token = token
        self.current_useremail = useremail
        self.current_role = role
        logger.info(f"认证上下文已设置: {useremail} ({role})")
    
    def clear_auth_context(self):
        """清除认证上下文"""
        self.current_token = ""
        self.current_useremail = ""
        self.current_role = ""
        logger.info("认证上下文已清除")
    
    def __call__(self, *args, **kwargs):
        """包装原始predict函数调用"""
        # 在调用predict前注入认证信息到环境变量
        if self.current_token and self.current_useremail:
            os.environ['AUTH_TOKEN'] = self.current_token
            os.environ['AUTH_USEREMAIL'] = self.current_useremail
            os.environ['AUTH_ROLE'] = self.current_role
            logger.debug(f"注入认证信息到predict调用: {self.current_useremail}")
        
        try:
            # 调用原始predict函数
            return self.original_predict(*args, **kwargs)
        finally:
            # 清理环境变量（可选）
            for key in ['AUTH_TOKEN', 'AUTH_USEREMAIL', 'AUTH_ROLE']:
                if key in os.environ:
                    del os.environ[key]

# 全局认证predict包装器实例
authenticated_predict = None

# ------------------------------------------------------------------- #
#  HTTP请求认证补丁 - 为所有LLM请求注入认证头
# ------------------------------------------------------------------- #
def patch_requests_for_auth():
    """补丁requests库，为所有POST请求自动添加认证头"""
    import requests
    
    # 保存原始的post方法
    original_post = requests.post
    original_session_post = requests.Session.post
    
    def add_auth_headers(headers=None):
        """添加认证头到请求头中"""
        if headers is None:
            headers = {}
        
        # 从环境变量获取认证信息
        token = os.environ.get('AUTH_TOKEN')
        useremail = os.environ.get('AUTH_USEREMAIL') 
        role = os.environ.get('AUTH_ROLE')
        
        if token and useremail:
            # 按照auth.py的要求添加认证头
            headers['Authorization'] = f'Bearer {token}'
            headers['X-User-Email'] = useremail
            if role:
                headers['X-User-Role'] = role
            logger.debug(f"添加认证头到请求: {useremail}")
        
        return headers
    
    def patched_post(url, **kwargs):
        """补丁后的requests.post方法"""
        # 只对特定的LLM API端点添加认证头
        if any(endpoint in str(url) for endpoint in [
            'api.openai.com', 'api.anthropic.com', 'api.cohere.ai',
            'dashscope.aliyuncs.com', 'api.moonshot.cn', 'spark-api.xf-yun.com',
            'localhost', '127.0.0.1'  # 包含本地开发环境
        ]):
            kwargs['headers'] = add_auth_headers(kwargs.get('headers'))
        
        return original_post(url, **kwargs)
    
    def patched_session_post(self, url, **kwargs):
        """补丁后的session.post方法"""
        # 只对特定的LLM API端点添加认证头
        if any(endpoint in str(url) for endpoint in [
            'api.openai.com', 'api.anthropic.com', 'api.cohere.ai',
            'dashscope.aliyuncs.com', 'api.moonshot.cn', 'spark-api.xf-yun.com',
            'localhost', '127.0.0.1'  # 包含本地开发环境
        ]):
            kwargs['headers'] = add_auth_headers(kwargs.get('headers'))
        
        return original_session_post(self, url, **kwargs)
    
    # 应用补丁
    requests.post = patched_post
    requests.Session.post = patched_session_post
    logger.info("HTTP请求认证补丁已应用")

# ------------------------------------------------------------------- #
#  主程序
# ------------------------------------------------------------------- #
def _make_title(name: str, role: str) -> str:
    """生成标题HTML"""
    from check_proxy import get_current_version
    from themes.theme import theme_declaration
    if not name:  # 未登录
        return f"<h1 align='center'>软工智能助手 {get_current_version()}</h1>{theme_declaration}"
    disp = f"👤 <span style='color:#28a745'>{name}</span> ({role})"
    return f"<h1 align='center'>软工智能助手 {get_current_version()}</h1>{theme_declaration}" \
           f"<div align='center' style='margin:10px;padding:10px;background:rgba(40,167,69,.1);border-radius:5px;'>已登录用户: {disp}</div>"

def main() -> None:
    global authenticated_predict
    
    # 应用HTTP请求认证补丁
    patch_requests_for_auth()
    
    # ============= 读取 GPT-Academic 原始配置 =============
    from toolbox import (format_io, find_free_port, on_file_uploaded,
                         on_report_generated, get_conf, ArgsGeneralWrapper,
                         DummyWith)
    from shared_utils.logging import setup_logging
    setup_logging(get_conf("PATH_LOGGING"))
    from request_llms.bridge_all import predict
    
    # 创建认证包装器
    authenticated_predict = AuthenticatedPredict(predict)

    (proxies, WEB_PORT, LLM_MODEL, CONCURRENT_COUNT,
     AUTHENTICATION)                           = get_conf('proxies','WEB_PORT','LLM_MODEL','CONCURRENT_COUNT','AUTHENTICATION')
    (CHATBOT_HEIGHT, LAYOUT, AVAIL_LLM_MODELS,
     AUTO_CLEAR_TXT)                           = get_conf('CHATBOT_HEIGHT','LAYOUT','AVAIL_LLM_MODELS','AUTO_CLEAR_TXT')
    (ENABLE_AUDIO, _, AVAIL_FONTS, AVAIL_THEMES,
     THEME, ADD_WAIFU)                         = get_conf('ENABLE_AUDIO','AUTO_CLEAR_TXT','AVAIL_FONTS','AVAIL_THEMES','THEME','ADD_WAIFU')
    (NUM_CUSTOM_BASIC_BTN, SSL_KEYFILE,
     SSL_CERTFILE)                             = get_conf('NUM_CUSTOM_BASIC_BTN','SSL_KEYFILE','SSL_CERTFILE')
    (DARK_MODE, INIT_SYS_PROMPT, _, TTS_TYPE)  = get_conf('DARK_MODE','INIT_SYS_PROMPT','ADD_WAIFU','TTS_TYPE')
    if LLM_MODEL not in AVAIL_LLM_MODELS:
        AVAIL_LLM_MODELS += [LLM_MODEL]

    from check_proxy import get_current_version
    PORT = find_free_port() if WEB_PORT <= 0 else WEB_PORT

    from themes.theme import (adjust_theme, advanced_css, theme_declaration,
                              js_code_clear, js_code_show_or_hide,
                              js_code_for_toggle_darkmode, load_dynamic_theme,
                              to_cookie_str, from_cookie_str, assign_user_uuid)
    set_theme = adjust_theme()

    # ---------------------------------------------------------------- #
    #  Gradio 组件 & 全局 State（将在gr.Blocks内部创建）
    # ---------------------------------------------------------------- #

    HELP_MENU = \
    """
    </br></br>普通对话使用说明: 1. 输入问题; 2. 点击提交
    </br></br>基础功能区使用说明: 1. 输入文本; 2. 点击任意基础功能区按钮
    </br></br>函数插件区使用说明: 1. 输入路径/问题, 或者上传文件; 2. 点击任意函数插件区按钮
    </br></br>虚空终端使用说明: 点击虚空终端, 然后根据提示输入指令, 再次点击虚空终端
    </br></br>如何保存对话: 点击保存当前的对话按钮
    </br></br>如何语音对话: 请阅读Wiki
    </br></br>如何临时更换API_KEY: 在输入区输入临时API_KEY后提交（网页刷新后失效）
    """

    # ---------------------------------------------------------------- #
    #  构建界面
    # ---------------------------------------------------------------- #
    with gr.Blocks(title="软件工程智能助手", theme=set_theme,
                   analytics_enabled=False, css=advanced_css) as app:
        
        # 创建状态管理组件
        token_state = gr.State("")      # 保存当前登录 token
        username_state = gr.State("")   # 用户名
        useremail_state = gr.State("")  # 用户邮箱 (用于认证)
        role_state = gr.State("")       # student / teacher

        # ======= 登录 / 注册 面板 =======
        with gr.Column(visible=True) as login_panel:
            gr.Markdown("## 🔐 登录软件工程智能助手")
            in_email  = gr.Textbox(label="邮箱")
            in_pwd    = gr.Textbox(label="密码", type="password")
            in_role   = gr.Radio(["student", "teacher"], value="student", label="身份")
            btn_login = gr.Button("登录", variant="primary")
            msg_login = gr.Markdown()

            gr.Markdown("---")
            gr.Markdown("### 注册新账号")
            r_email = gr.Textbox(label="邮箱")
            r_name  = gr.Textbox(label="用户名")
            r_pwd1  = gr.Textbox(label="密码", type="password")
            r_pwd2  = gr.Textbox(label="确认密码", type="password")
            r_role  = gr.Radio(["student","teacher"], value="student", label="身份")
            btn_reg = gr.Button("注册", variant="secondary")
            msg_reg = gr.Markdown()

        with gr.Column(visible=False) as main_panel:
            # ---------- 标题 ----------
            title_html = gr.HTML(_make_title("", ""))

            # ============= 以下保留 GPT-Academic 原始 UI =============
            from core_functional import get_core_functions
            from crazy_functional import get_crazy_functions, get_multiplex_button_functions
            functional = get_core_functions()
            plugins = get_crazy_functions()
            DEFAULT_FN_GROUPS = get_conf('DEFAULT_FN_GROUPS')
            all_plugin_groups = list(set([g for _,p in plugins.items() for g in p['Group'].split('|')]))
            match_group = lambda tags, groups: any(g in groups for g in tags.split('|'))

            gr.Chatbot.postprocess = format_io
            from check_proxy import check_proxy, auto_update, warm_up_modules
            proxy_info = check_proxy(proxies)

            gr_L1 = lambda: gr.Row().style()
            gr_L2 = lambda scale, elem_id: gr.Column(scale=scale, elem_id=elem_id, min_width=400)
            if LAYOUT == "TOP-DOWN":
                gr_L1 = lambda: DummyWith()
                gr_L2 = lambda scale, elem_id: gr.Row()
                CHATBOT_HEIGHT /= 2

            cancel_handles, customize_btns, predefined_btns = [], {}, {}
            from shared_utils.cookie_manager import make_cookie_cache, make_history_cache
            cookies, web_cookie_cache = make_cookie_cache()

            with gr_L1():
                with gr_L2(scale=2, elem_id="gpt-chat"):
                    chatbot = gr.Chatbot(label=f"当前模型：{LLM_MODEL}", elem_id="gpt-chatbot")
                    if LAYOUT == "TOP-DOWN": chatbot.style(height=CHATBOT_HEIGHT)
                    history, _, _ = make_history_cache()
                with gr_L2(scale=1, elem_id="gpt-panel"):
                    with gr.Accordion("输入区", open=True, elem_id="input-panel") as area_input_primary:
                        with gr.Row():
                            txt = gr.Textbox(show_label=False, placeholder="Input question here.", elem_id='user_input_main').style(container=False)
                        with gr.Row(elem_id="gpt-submit-row"):
                            multiplex_submit_btn = gr.Button("提交", elem_id="elem_submit_visible", variant="primary")
                            multiplex_sel = gr.Dropdown(choices=get_multiplex_button_functions().keys(), value="常规对话",
                                                        interactive=True, label='', show_label=False,
                                                        elem_classes='normal_mut_select', elem_id="gpt-submit-dropdown").style(container=False)
                            submit_btn = gr.Button("提交", elem_id="elem_submit", variant="primary", visible=False)
                        with gr.Row():
                            resetBtn = gr.Button("重置", elem_id="elem_reset", variant="secondary").style(size="sm")
                            stopBtn  = gr.Button("停止", elem_id="elem_stop", variant="secondary").style(size="sm")
                            clearBtn = gr.Button("清除", elem_id="elem_clear", variant="secondary", visible=False).style(size="sm")
                        if ENABLE_AUDIO:
                            with gr.Row():
                                audio_mic = gr.Audio(source="microphone", type="numpy", elem_id="elem_audio",
                                                     streaming=True, show_label=False).style(container=False)
                        with gr.Row():
                            status = gr.Markdown("Tip: 按Enter提交, 按Shift+Enter换行。支持将文件直接粘贴到输入区。", elem_id="state-panel")

                    # ---- 基础功能区 ----
                    with gr.Accordion("基础功能区", open=True, elem_id="basic-panel") as area_basic_fn:
                        with gr.Row():
                            for k in range(NUM_CUSTOM_BASIC_BTN):
                                btn = gr.Button(f"自定义按钮{k+1}", visible=False, variant="secondary",
                                                info_str='基础功能区: 自定义按钮').style(size="sm")
                                customize_btns[f"自定义按钮{k+1}"] = btn
                            for k in functional:
                                if ("Visible" in functional[k]) and (not functional[k]["Visible"]): continue
                                variant = functional[k].get("Color", "secondary")
                                functional[k]["Button"] = gr.Button(k, variant=variant,
                                                                    info_str=f'基础功能区: {k}').style(size="sm")
                                predefined_btns[k] = functional[k]["Button"]

                    # ---- 函数插件区 ----
                    with gr.Accordion("函数插件区", open=True, elem_id="plugin-panel") as area_crazy_fn:
                        with gr.Row():
                            gr.Markdown("<small>插件可读取“输入区”文本 / 路径作为参数（上传文件自动修正路径）</small>")
                        with gr.Row(elem_id="input-plugin-group"):
                            plugin_group_sel = gr.Dropdown(choices=all_plugin_groups, label='', show_label=False,
                                                           value=DEFAULT_FN_GROUPS, multiselect=True,
                                                           interactive=True, elem_classes='normal_mut_select').style(container=False)
                        with gr.Row():
                            for idx, (name, plugin) in enumerate(plugins.items()):
                                if not plugin.get("AsButton", True): continue
                                visible = match_group(plugin['Group'], DEFAULT_FN_GROUPS)
                                variant = plugin.get("Color", "secondary")
                                info    = plugin.get("Info", name)
                                btn_id  = f"plugin_btn_{idx}"
                                plugin['Button'] = gr.Button(name, variant=variant, visible=visible,
                                                             info_str=f'函数插件区: {info}', elem_id=btn_id).style(size="sm")
                                plugin['ButtonElemId'] = btn_id
                        with gr.Row():
                            with gr.Accordion("更多函数插件", open=True):
                                dropdown_fn_list = []
                                for name,plugin in plugins.items():
                                    if match_group(plugin['Group'], DEFAULT_FN_GROUPS) and \
                                       (not plugin.get("AsButton",True) or plugin.get("AdvancedArgs",False)):
                                        dropdown_fn_list.append(name)
                                dropdown = gr.Dropdown(dropdown_fn_list,
                                                       value="点击这里输入「关键词」搜索插件",
                                                       label="", show_label=False).style(container=False)
                                plugin_advanced_arg = gr.Textbox(show_label=True, label="高级参数输入区",
                                                                 visible=False, elem_id="advance_arg_input_legacy",
                                                                 placeholder="这里是特殊函数插件的高级参数输入区").style(container=False)
                                switchy_bt = gr.Button("请先从插件列表中选择", variant="secondary",
                                                       elem_id="elem_switchy_bt").style(size="sm")
                        with gr.Row():
                            with gr.Accordion("点击展开“文件下载区”。", open=False):
                                file_upload = gr.Files(label="任何文件, 推荐上传压缩文件(zip, tar)",
                                                       file_count="multiple", elem_id="elem_upload")

            # ---- 顶部工具栏 & 浮动菜单 （原逻辑照搬） ----
            from themes.gui_toolbar import define_gui_toolbar
            checkboxes, checkboxes_2, max_length_sl, theme_dropdown, system_prompt, file_upload_2, \
                md_dropdown, top_p, temperature = define_gui_toolbar(
                    AVAIL_LLM_MODELS, LLM_MODEL, INIT_SYS_PROMPT, THEME,
                    AVAIL_THEMES, AVAIL_FONTS, ADD_WAIFU, HELP_MENU,
                    js_code_for_toggle_darkmode)

            from themes.gui_floating_menu import define_gui_floating_menu
            area_input_secondary, txt2, area_customize, _, resetBtn2, clearBtn2, stopBtn2 = \
                define_gui_floating_menu(customize_btns, functional, predefined_btns, cookies, web_cookie_cache)

            from themes.gui_advanced_plugin_class import define_gui_advanced_plugin_class
            new_plugin_callback, route_switchy_bt_with_arg, usr_confirmed_arg = \
                define_gui_advanced_plugin_class(plugins)

            # ---- 功能区显隐联动 ----
            def fn_area_visibility(a):
                ret = {area_input_primary:   gr.update(visible=("浮动输入区" not in a)),
                       area_input_secondary: gr.update(visible=("浮动输入区"     in a)),
                       plugin_advanced_arg:  gr.update(visible=("插件参数区"     in a))}
                if "浮动输入区" in a: ret[txt] = gr.update(value="")
                return ret
            checkboxes.select(fn_area_visibility, [checkboxes],
                              [area_basic_fn, area_crazy_fn, area_input_primary, area_input_secondary,
                               txt, txt2, plugin_advanced_arg])
            checkboxes.select(None, [checkboxes], None, _js=js_code_show_or_hide)
            def fn_area_visibility_2(a): return {area_customize: gr.update(visible=("自定义菜单" in a))}
            checkboxes_2.select(fn_area_visibility_2, [checkboxes_2], [area_customize])
            checkboxes_2.select(None, [checkboxes_2], None, _js="apply_checkbox_change_for_group2")

            # ---- 组合输入 / 输出 ----
            input_combo = [cookies, max_length_sl, md_dropdown, txt, txt2,
                           top_p, temperature, chatbot, history, system_prompt, plugin_advanced_arg]
            input_combo_order = ["cookies","max_length_sl","md_dropdown","txt","txt2",
                                 "top_p","temperature","chatbot","history",
                                 "system_prompt","plugin_advanced_arg"]
            output_combo = [cookies, chatbot, history, status]
            predict_args = dict(fn=ArgsGeneralWrapper(authenticated_predict),
                                inputs=input_combo + [gr.State(True)],
                                outputs=output_combo)

            multiplex_submit_btn.click(None, [multiplex_sel], None,
                                       _js="(s)=>multiplex_function_begin(s)")
            txt.submit(None, [multiplex_sel], None, _js="(s)=>multiplex_function_begin(s)")
            multiplex_sel.select(None, [multiplex_sel], None, _js="(s)=>run_multiplex_shift(s)")
            cancel_handles.append(submit_btn.click(**predict_args))
            resetBtn.click(None, None, [chatbot, history, status], _js="clear_conversation")
            resetBtn2.click(None, None, [chatbot, history, status], _js="clear_conversation")
            clearBtn.click(None, None, [txt, txt2], _js=js_code_clear)
            clearBtn2.click(None, None, [txt, txt2], _js=js_code_clear)
            if AUTO_CLEAR_TXT:
                cancel_handles.append(submit_btn.click(**predict_args).then(
                    lambda: ("", ""), inputs=[], outputs=[txt, txt2]))

            # ---- 基础功能按钮绑定 ----
            for k in functional:
                if ("Visible" in functional[k]) and (not functional[k]["Visible"]): continue
                h = functional[k]["Button"].click(
                    fn=ArgsGeneralWrapper(authenticated_predict),
                    inputs=input_combo + [gr.State(True), gr.State(k)],
                    outputs=output_combo)
                cancel_handles.append(h)
            for btn in customize_btns.values():
                h = btn.click(fn=ArgsGeneralWrapper(authenticated_predict),
                              inputs=input_combo + [gr.State(True), gr.State(btn.value)],
                              outputs=output_combo)
                cancel_handles.append(h)

            # ---- 文件上传 ----
            file_upload.upload(on_file_uploaded,
                               [file_upload, chatbot, txt, txt2, checkboxes, cookies],
                               [chatbot, txt, txt2, cookies]).then(None,None,None,
                               _js="()=>{toast_push('上传完毕 ...'); cancel_loading_status();}")
            file_upload_2.upload(on_file_uploaded,
                                 [file_upload_2, chatbot, txt, txt2, checkboxes, cookies],
                                 [chatbot, txt, txt2, cookies]).then(None,None,None,
                                 _js="()=>{toast_push('上传完毕 ...'); cancel_loading_status();}")

            # ---- 插件按钮绑定（修复：使用JavaScript方式，与main.py一致）----
            register_advanced_plugin_init_arr = ""
            for k in plugins:
                register_advanced_plugin_init_arr += f"""register_plugin_init("{k}","{encode_plugin_info(k, plugins[k])}");"""
                if plugins[k].get("Class", None):
                    plugins[k]["JsMenu"] = plugins[k]["Class"]().get_js_code_for_generating_menu(k)
                    register_advanced_plugin_init_arr += """register_advanced_plugin_init_code("{k}","{gui_js}");""".format(k=k, gui_js=plugins[k]["JsMenu"])
                if not plugins[k].get("AsButton", True): continue
                if plugins[k].get("Class", None) is None:
                    assert plugins[k].get("Function", None) is not None
                    click_handle = plugins[k]["Button"].click(None, inputs=[], outputs=None, _js=f"""()=>run_classic_plugin_via_id("{plugins[k]["ButtonElemId"]}")""")
                else:
                    click_handle = plugins[k]["Button"].click(None, inputs=[], outputs=None, _js=f"""()=>run_advanced_plugin_launch_code("{k}")""")

            # 注册switchy_bt的JavaScript回调
            switchy_bt.click(None, [switchy_bt], None, _js="(switchy_bt)=>on_flex_button_click(switchy_bt)")
            
            # 随变按钮的回调函数注册
            def route(request: gr.Request, k, *args, **kwargs):
                if k in [r"未选定任何插件", r""]: return
                yield from ArgsGeneralWrapper(plugins[k]["Function"])(request, *args, **kwargs)
                
            # 旧插件的高级参数区确认按钮（隐藏）
            old_plugin_callback = gr.Button(r"未选定任何插件", variant="secondary", visible=False, elem_id="old_callback_btn_for_plugin_exe")
            click_handle_ng = old_plugin_callback.click(route, [switchy_bt, *input_combo], output_combo)
            cancel_handles.append(click_handle_ng)
            
            # 新一代插件的高级参数区确认按钮（隐藏）
            click_handle_ng = new_plugin_callback.click(route_switchy_bt_with_arg,
                [
                    gr.State(["new_plugin_callback", "usr_confirmed_arg"] + input_combo_order),
                    new_plugin_callback, usr_confirmed_arg, *input_combo
                ], output_combo)
            cancel_handles.append(click_handle_ng)

            # ---- 停止按钮 ----
            stopBtn.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)
            stopBtn2.click(fn=None, inputs=None, outputs=None, cancels=cancel_handles)

            # ---- 插件组切换 ----
            def on_group_change(groups):
                btn_updates, dd = [], []
                for n,p in plugins.items():
                    if not p.get("AsButton",True): continue
                    show = match_group(p['Group'], groups) if groups else False
                    btn_updates.append(p['Button'].update(visible=show))
                    if p.get("AdvancedArgs",False) and show: dd.append(n)
                return [*btn_updates, gr.Dropdown.update(choices=dd)]
            plugin_group_sel.select(on_group_change, [plugin_group_sel],
                                    [*[plugins[n]['Button'] for n in plugins if plugins[n].get("AsButton",True)],
                                     dropdown])

            # ---- 主题切换 ----
            secret_css = gr.Textbox(visible=False, elem_id="secret_css")
            def on_theme_change(t, css_holder):
                adj, css1, _, dyn = load_dynamic_theme(t)
                css2 = dyn._get_theme_css() if dyn else adj()._get_theme_css()
                return css2 + css1
            theme_dropdown.select(on_theme_change, [theme_dropdown, secret_css],
                                  [secret_css]).then(None,[theme_dropdown, secret_css],
                                  None,_js="change_theme")

            # ---- 模型切换 ----
            md_dropdown.select(lambda m:{chatbot: gr.update(label="当前模型："+m)},
                               [md_dropdown], [chatbot])

            # ---- Cookie / uuid ----
            from shared_utils.cookie_manager import load_web_cookie_cache__fn_builder
            load_web_cookie_cache = load_web_cookie_cache__fn_builder(customize_btns, cookies, predefined_btns)
            app.load(assign_user_uuid, inputs=[cookies], outputs=[cookies])
            app.load(load_web_cookie_cache, inputs=[web_cookie_cache, cookies],
                     outputs=[web_cookie_cache, cookies, *customize_btns.values(),
                              *predefined_btns.values()], _js="persistent_cookie_init")
            app.load(None, inputs=[], outputs=None,
                     _js=f"()=>GptAcademicJavaScriptInit('{DARK_MODE}','{INIT_SYS_PROMPT}','{ADD_WAIFU}','{LAYOUT}','{TTS_TYPE}')")
            app.load(None, inputs=[], outputs=None, _js=f"""()=>{{{register_advanced_plugin_init_arr}}}""")

            # ---- 语音（可选） ----
            if ENABLE_AUDIO:
                from crazy_functions.live_audio.audio_io import RealtimeAudioDistribution
                rad = RealtimeAudioDistribution()
                def deal_audio(audio, ck): rad.feed(ck['uuid'].hex, audio)
                audio_mic.stream(deal_audio, inputs=[audio_mic, cookies])

            # ---- 登出按钮 ----
            btn_logout = gr.Button("🚪 登出", variant="secondary")

            # ---- 认证状态显示 ----
            auth_status = gr.Markdown("🔒 未登录", elem_id="auth-status")

            def update_auth_status(token, username, role):
                """更新认证状态显示"""
                if token and username and role:
                    return f"🔐 已登录: {username} ({role})"
                return "🔒 未登录"

        # ----------------------------------------------------------------
        #  登录 / 注册 / 登出 回调
        # ----------------------------------------------------------------
        def do_login(email, pwd, role):
            ok, msg, data = login_api(email, pwd, role)
            if ok:
                authenticated_predict.set_auth_context(data["token"], email, role)
                return (
                    gr.update(visible=False),
                    gr.update(visible=True),
                    data["token"],
                    data["username"],
                    email,
                    role,
                    f"✅ 登录成功，欢迎 {data['username']}！",
                    _make_title(data["username"], role),
                )
            return (
                gr.update(),
                gr.update(),
                "",
                "",
                "",
                "",
                f"❌ 登录失败: {msg}",
                _make_title("", ""),
            )

        def do_register(email, name, p1, p2, role):
            if p1 != p2: return "❌ 两次密码不一致"
            ok, msg, _ = register_api(email, name, p1, role)
            return "✅ 注册成功，请登录" if ok else f"❌ 注册失败: {msg}"

        def do_logout():
            # 清除认证上下文
            if authenticated_predict:
                authenticated_predict.clear_auth_context()
            return (gr.update(visible=True), gr.update(visible=False),
                    "", "", "", "", "", _make_title("", ""))

        # 绑定按钮
        btn_login.click(do_login,
                        inputs=[in_email, in_pwd, in_role],
                        outputs=[login_panel, main_panel,
                                 token_state, username_state, useremail_state, role_state,
                                 msg_login, title_html],
                        queue=True)

        btn_reg.click(do_register,
                      inputs=[r_email, r_name, r_pwd1, r_pwd2, r_role],
                      outputs=[msg_reg], queue=False)

        btn_logout.click(do_logout,
                         inputs=[],
                         outputs=[login_panel, main_panel,
                                  token_state, username_state, useremail_state, role_state,
                                  msg_login, title_html],
                         queue=False)

        # ---- 登录状态恢复功能 ----
        def restore_login_state(token, username, useremail, role):
            """恢复登录状态（页面刷新后）"""
            if token and username and useremail and role:
                # 验证token是否仍然有效
                try:
                    # 这里可以添加token验证逻辑
                    if authenticated_predict:
                        # 使用正确的email进行认证
                        authenticated_predict.set_auth_context(token, useremail, role)
                    return (_make_title(username, role), f"🔄 登录状态已恢复: {username}")
                except Exception as e:
                    logger.error(f"恢复登录状态失败: {e}")
                    return (_make_title("", ""), "")
            return (_make_title("", ""), "")

        # 在应用加载时尝试恢复登录状态
        app.load(restore_login_state, 
                inputs=[token_state, username_state, useremail_state, role_state],
                outputs=[title_html, msg_login])

    # ------------------------------------------------------------------
    #  异步任务：自动更新 / 打开浏览器
    # ------------------------------------------------------------------
    from check_proxy import auto_update, warm_up_modules
    def delayed():
        logger.info(f"如果浏览器未自动打开，请访问: http://localhost:{PORT}")
        threading.Thread(target=lambda:(time.sleep(0),auto_update()),
                         name="auto-update",daemon=True).start()
        threading.Thread(target=lambda:(time.sleep(6),warm_up_modules()),
                         name="warm-up",daemon=True).start()
        if get_conf('AUTO_OPEN_BROWSER'):
            threading.Thread(target=lambda:(time.sleep(2),
                             webbrowser.open_new_tab(f"http://localhost:{PORT}/llms")),
                             name="open-browser",daemon=True).start()
    delayed()

    # ------------------------------------------------------------------
    #  启动 FastAPI Server
    # ------------------------------------------------------------------
    from shared_utils.fastapi_server import start_app
    logger.info(f"启动服务器: http://localhost:{PORT}")
    start_app(app, CONCURRENT_COUNT, AUTHENTICATION, PORT,
              SSL_KEYFILE, SSL_CERTFILE)

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
