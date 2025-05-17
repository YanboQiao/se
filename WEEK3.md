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
验证码系统完整实现
完成了验证码生成和发送API
实现了基于Flask-Mail的邮件发送服务
添加了验证码存储与时效性管理
@app.route('/send-verify-code', methods=['POST'])
def send_verify_code():
    data = request.json
    email = data.get('email')
    role = data.get('role')
    
    if not email:
        return jsonify({"status": "error", "message": "邮箱不能为空"}), 400
    
    verify_code = ''.join(random.choices(string.digits, k=6))
    verification_codes[email] = verify_code
    
    try:
        send_verification_email(email, verify_code)
        return jsonify({"status": "success", "message": "验证码已发送"}), 200
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return jsonify({"status": "error", "message": f"邮件发送失败: {str(e)}"}), 500
验证码校验功能实现

开发了验证码校验API
实现了验证码有效性和过期检查
添加了验证成功后的状态管理

接口路径的规范
统一API路径命名规范，解决路由不匹配问题
添加路由重定向，兼容旧路径
遇到的主要问题与解决方案

问题1：邮箱验证码发送服务路径不匹配

分析：前端请求/send-verify-code但后端定义的是/api/send-verify-code
解决：统一路径命名，添加双路径支持
问题2：前后端参数命名不一致

分析：前端传递参数名为email但后端期望useremail
解决：统一使用email作为参数名，在SQL查询中映射到useremail字段
问题3：邮件发送授权问题

分析：需要QQ邮箱SMTP授权码但团队不熟悉获取方式
解决：编写授权码获取教程，实现安全的配置管理
关键成果与下阶段规划

已完成功能
✅ 用户登录与注册系统（支持学生/教师两种角色）
✅ 邮箱验证码发送与校验系统
✅ 邮箱格式验证与域名限制
✅ 安全的Token生成与验证机制

讨论并设计下阶段规划
安全性提升

实现密码加密存储（哈希+盐值）
添加登录失败次数限制
完善用户会话管理
功能扩展

开发用户信息修改功能
实现"记住我"登录选项
添加在线状态管理
性能优化

优化数据库查询性能
实现验证码缓存机制
改进错误处理与日志记录


李军：
修改密码接口实现
基于李天意同学完整的验证码功能，实现修改密码功能
完成了基于验证码的密码重置流程
实现了根据角色选择相应数据表的更新逻辑
添加了完整的错误处理和安全检查
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    verify_code = data.get('verifyCode')
    new_password = data.get('newPassword')
    role = data.get('role')
    
    if not all([email, verify_code, new_password, role]):
        return jsonify({"status": "error", "message": "信息不完整"}), 400
    
    stored_code = verification_codes.get(email)
    if not stored_code or stored_code != verify_code:
        return jsonify({"status": "error", "message": "验证码错误或已过期"}), 400
    
    # 根据角色选择表并更新密码
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            table = 'student' if role == 'student' else 'teacher'
            sql = f"UPDATE {table} SET password = %s WHERE useremail = %s"
            result = cursor.execute(sql, (new_password, email))
            
            if result == 0:
                return jsonify({"status": "error", "message": f"未找到该邮箱的{role}账号"}), 404
                
            conn.commit()
            del verification_codes[email]
            return jsonify({"status": "success", "message": "密码重置成功"}), 200
    finally:
        conn.close()

实现的功能：
✅ 数据库表的创建
✅ 邮箱验证码发送与校验系统
✅ 基于验证码的密码重置功能

讨论并设计下阶段规划
安全性提升

实现密码加密存储（哈希+盐值）
添加登录失败次数限制
完善用户会话管理
功能扩展

开发用户信息修改功能
实现"记住我"登录选项
添加在线状态管理
性能优化

优化数据库查询性能
实现验证码缓存机制
改进错误处理与日志记录
