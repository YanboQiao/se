# ACCEED SE 第一周周会

## oncall总结 & 问题复盘
第一周还没有

## 重点模块进展

### 前端代码相关

乔彦博：


### 后端登录模块相关

### 后端大语言模型模块相关

## 每周组组内分享

李天意：
注册功能实现
——注册功能实现
	完成了/register路由的开发，支持学生/教师角色注册
	实现了邮箱唯一性检查，防止重复注册
	添加了基本的参数验证逻辑
	@app.route('/register', methods=['POST'])
	def register():
	    data = request.get_json()
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
——邮箱验证系统的开发
和李军同学讨论发现为每个邮箱都配置文件，很困难，因此探索和发现了Flask-Mail这个python数据包。它可以轻松实现发送验证码功能。
	配置Flask-Mail邮件发送服务
	实现基本的验证码生成算法
	Flask应用结构优化

	重构了应用结构，解决了之前存在的潜在问题
	优化了错误处理和日志记录机制
	遇到的问题与解决方案

问题：Flask应用实例重复定义，导致配置丢失
分析：在代码审查中发现两处app = Flask(__name__)定义，第二处覆盖了之前的配置
解决方案：
# 修复前
app = Flask(__name__)  # 第一处定义
app.config['MAIL_SERVER'] = 'smtp.qq.com'
# ... 其他配置 ...

# 某处代码后...
app = Flask(__name__)  # 第二处定义，覆盖了之前的配置

# 修复后
app = Flask(__name__)  # 仅保留一处定义
CORS(app)
app.config['MAIL_SERVER'] = 'smtp.qq.com'
# ... 其他配置 ...

——邮箱格式设定实现（基于Flask-Mail)
首先确定了我们之前定义好的类型。
限制只接受特定邮箱域名（如qq.com, 163.com等）
# 验证邮箱域名
valid_domains = ['qq.com', '163.com', 'gmail.com', 'outlook.com', '126.com', 'foxmail.com']
email_domain = useremail.split('@')[-1] if '@' in useremail else None

if not email_domain or email_domain not in valid_domains:
    return jsonify({
        "status": "error", 
        "message": "目前只支持：qq.com, 163.com, gmail.com, outlook.com, 126.com, foxmail.com"
    }), 400



李军：
邮箱验证系统的探索
——设计邮箱验证码系统架构
我们首先定义了邮箱的类型：如下所示
	valid_domains = ['qq.com', '163.com', 'gmail.com', 'outlook.com', '126.com', 'foxmail.com']
刚开始是采用直接和特定邮箱的服务器相联，探索这种路径是否可以实现。
	# 连接到163的POP3服务器
	pop_server = 'pop.163.com'
	username = '18161648525@163.com'  # 例如：'user@163.com'
	password = 'JAj5KRHUTXmk3p7t'  # 使用163邮箱的授权码作为密码

	try:
	    # 使用SSL连接
	    pop_conn = poplib.POP3_SSL(pop_server)
	except:
	    # 如果SSL连接失败，尝试普通连接
	    pop_conn = poplib.POP3(pop_server)
但是发现这种方法的弊端就是要为每一个邮箱类别编写一个python文件用于存放特定邮箱的信息。实现以及联合调用困难。
因此，我和李天意同学打算寻找其他方法，看是否存在其他好的方法实现。