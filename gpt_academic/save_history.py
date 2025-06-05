from flask import Flask, request, jsonify
from flask_cors import CORS  # 用于处理跨域请求
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许所有来源的跨域请求，生产环境中应配置得更严格

# 基本配置
BASE_LOG_DIR = os.path.join(os.getcwd(), 'se', 'gpt_log')  # 日志存储基础路径


def get_safe_user_email(user_email_input: str) -> str | None:
    """清理并验证用户邮箱字符串作为安全的文件名一部分。"""
    if not user_email_input:
        return None
    safe_email = "".join(c for c in user_email_input if c.isalnum() or c in ('_', '-')).strip()
    return safe_email if safe_email else None


@app.route('/api/save_chat_history', methods=['POST'])
def save_chat_history_route():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"detail": "请求体必须是JSON格式"}), 400

        user_email_input = data.get('user_email')
        chat_html_content = data.get('chat_html')  # 这是单个对话会话的HTML片段

        if not user_email_input:
            return jsonify({"detail": "用户邮箱不能为空"}), 400
        if not chat_html_content:
            return jsonify({"detail": "对话内容不能为空"}), 400

        safe_user_email = get_safe_user_email(user_email_input)
        if not safe_user_email:
            return jsonify({"detail": "无效的用户邮箱格式"}), 400

        user_log_dir = os.path.join(BASE_LOG_DIR, safe_user_email)
        os.makedirs(user_log_dir, exist_ok=True)

        log_file_path = os.path.join(user_log_dir, 'chat_secrets.log')  # 使用.log后缀

        # 以追加模式写入，每个对话片段后加一个分隔符
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(chat_html_content)  # chat_html_content 已经包含了时间戳和包裹的 div
            f.write("\n<hr style='border:0; border-top: 1px dashed #ccc; margin: 20px 0;'>\n")

        return jsonify({"message": f"对话已追加到 {log_file_path}"}), 200
    except Exception as e:
        print(f"Flask - 保存对话历史时发生错误: {e}")
        return jsonify({"detail": f"服务器内部错误: {str(e)}"}), 500


@app.route('/api/load_chat_history', methods=['GET'])
def load_chat_history_route():
    user_email_input = request.args.get('user_email')  # 从URL查询参数获取

    if not user_email_input:
        # 返回JSON，其中包含要显示的HTML
        return jsonify({"html_content": "<p style='color:orange;'>需要提供用户邮箱以加载历史记录。</p>"}), 400

    safe_user_email = get_safe_user_email(user_email_input)
    if not safe_user_email:
        return jsonify({"html_content": "<p style='color:red;'>无效的用户邮箱格式。</p>"}), 400

    log_file_path = os.path.join(BASE_LOG_DIR, safe_user_email, 'chat_secrets.log')
    html_to_display = ""

    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                history_content = f.read()
            if history_content.strip():
                html_to_display = f"""
                <div class="chat-history-container" style="max-height: 400px; overflow-y: auto; border: 1px solid #e0e0e0; padding: 15px; background-color: #f9f9f9; border-radius: 5px;">
                    <h3 style="margin-top:0; color:#333;">用户 '{safe_user_email}' 的历史对话:</h3>
                    {history_content}
                </div>
                """
            else:
                html_to_display = f"<p>用户 '{safe_user_email}' 的历史记录为空。</p>"
            return jsonify({"html_content": html_to_display}), 200
        except Exception as e:
            print(f"Flask - 读取历史记录文件 '{log_file_path}' 时出错: {e}")
            html_to_display = f"<p style='color:red;'>读取历史记录文件时出错: {str(e)}</p>"
            return jsonify({"html_content": html_to_display}), 500
    else:
        html_to_display = f"<p>未找到用户 '{safe_user_email}' 的历史记录文件。</p>"
        return jsonify({"html_content": html_to_display}), 200  # 仍然是200，但内容表明未找到


if __name__ == '__main__':
    # 确保 'se/gpt_log' 目录存在或可被创建
    if not os.path.exists(BASE_LOG_DIR):
        os.makedirs(BASE_LOG_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=5001, debug=True)  # 在5001端口运行
    # 在生产环境中，应使用 Gunicorn 或 uWSGI 等WSGI服务器