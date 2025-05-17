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
后端算法与接口的实现
——登录接口实现
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    useremail = data.get('useremail')
    password = data.get('password')
    role = data.get('role')

    if not all([useremail, password, role]):
        return jsonify({"status": "error", "message": "请提供用户邮箱、密码和身份"}), 400

    success, message, info = login_user(useremail, password, role)

    if success:
        return jsonify({"status": "success", "message": message, "data": info}), 200
    else:
        return jsonify({"status": "error", "message": message}), 401
——登录验证逻辑开发
	实现用户身份验证逻辑（邮箱存在性检查、密码匹配）
	登录成功后生成新Token并更新到数据库
	设计标准化的API响应格式（status/message/data结构）
——遇到的问题与解决方案
问题：MySQL连接配置错误，导致应用启动后无法连接数据库，与李军同学讨论是否是SQL语句导出错误或者版本不同导致的。
原因：PyMySQL版本与MySQL服务器版本不兼容，字符集配置不正确
解决方案：修改编写的DB_CONFIG文件，确保参数是符合本地运行数据库的。
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',
    'password': '12345678',
    'database': 'se_db',
    'charset': 'utf8mb4',  # 修改为utf8mb4确保兼容性
    'cursorclass': pymysql.cursors.DictCursor
}

李军：
结构设计和数据库表设计
——系统架构设计（与李天意同学讨论设计）
	完成了用户认证系统的基础架构设计与规划
	设计了学生/教师双角色登录认证流程
	设计了基于Token的身份验证机制
	确定了Token有效期为1小时，基于timestamp实现
———数据库表设计（基于我们的系统要求需要）
	设计并创建了student表和teacher表，分别存储不同角色用户信息。并导出SQL语句，用于他人直接创建。
	-- 使用 se_db 数据库
	USE se_db;

	-- 创建 teacher 表
	CREATE TABLE teacher (
	    email VARCHAR(100) PRIMARY KEY,
	    username VARCHAR(50) NOT NULL,
	    password VARCHAR(100) NOT NULL
	);

	-- 创建 student 表
	CREATE TABLE student (
	    email VARCHAR(100) PRIMARY KEY,
	    username VARCHAR(50) NOT NULL,
	    password VARCHAR(100) NOT NULL
	);
	ALTER TABLE teacher ADD COLUMN token VARCHAR(32);
	ALTER TABLE student ADD COLUMN token VARCHAR(32);

	ALTER TABLE teacher ADD UNIQUE (username);
	ALTER TABLE student ADD UNIQUE (username);

	INSERT INTO student (email, username, password, token)
	VALUES ('test@example.com', 'testuser', '123456', '');

	INSERT INTO teacher (email, username, password, token)
	VALUES ('teacher1@example.com', 'teacher1', '123456', '');

	字段设计：id(主键), username, useremail(唯一索引), password, token, create_time
	配置了MySQL连接参数，初步测试数据库连接