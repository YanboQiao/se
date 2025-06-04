# GPT Academic 登录系统集成说明

## 概述

本项目为 GPT Academic 集成了与 SE Backend 共享的用户认证系统，实现统一的用户登录管理。

## 功能特性

### ✅ 已实现功能

1. **统一用户认证**
   - 与 SE Backend 共享同一数据库
   - 支持学生和教师账户登录
   - 密码验证和 Token 管理

2. **登录界面**
   - 简洁的 Gradio 登录界面
   - 用户注册功能
   - 会话管理和自动登出

3. **安全机制**
   - Token 有效期管理（7天）
   - 会话状态验证
   - 角色权限控制

### 📁 项目结构

```
gpt_academic/
├── main_with_auth.py              # 带登录功能的启动器
├── shared_utils/
│   ├── auth_integration.py        # 认证集成模块
│   └── login_interface.py         # 登录界面模块
├── config.py                      # 配置文件（已添加登录配置）
├── test_auth_system.py           # 认证系统测试
└── requirements.txt               # 依赖包（已添加PyMySQL）
```

### 🔧 配置说明

在 `config.py` 中添加了以下配置项：

```python
# 用户登录认证系统配置
ENABLE_LOGIN = False                          # 是否启用登录功能
LOGIN_REQUIRE_VERIFICATION = True            # 是否需要验证用户身份
LOGIN_ALLOWED_ROLES = ["student", "teacher"] # 允许登录的用户角色
```

## 安装和使用

### 1. 安装依赖

```bash
cd /path/to/gpt_academic
pip install -r requirements.txt
```

新增的依赖包：
- `PyMySQL>=1.0.2` - MySQL数据库连接
- `loguru` - 日志管理

### 2. 配置数据库

确保 SE Backend 的数据库正在运行，并且配置文件 `../se-backend/db_config.json` 存在：

```json
{
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root", 
    "password": "your_password",
    "database": "se_db_new",
    "charset": "utf8mb4"
}
```

### 3. 启用登录功能

修改 `config.py`：

```python
ENABLE_LOGIN = True  # 启用登录功能
```

### 4. 测试系统

运行测试脚本验证系统是否正常：

```bash
python test_auth_system.py
```

### 5. 启动应用

#### 方式一：带登录功能启动

```bash
python main_with_auth.py
```

#### 方式二：标准模式启动（无登录）

```bash
python main.py
```

## 系统架构

### 数据库集成

- **共享数据库**: 使用与 SE Backend 相同的 MySQL 数据库
- **用户表**: `student` 和 `teacher` 表
- **字段映射**:
  - `useremail`: 用户邮箱（登录账号）
  - `username`: 用户姓名
  - `password`: 密码（明文存储，与后端保持一致）
  - `token`: 认证令牌

### 认证流程

1. **用户登录**
   ```
   输入邮箱/密码 → 验证数据库 → 生成Token → 创建会话
   ```

2. **会话管理**
   ```
   登录成功 → 创建Session → 定期验证 → 自动清理过期会话
   ```

3. **权限控制**
   ```
   每次操作 → 检查会话 → 验证权限 → 执行/拒绝
   ```

### 安全特性

- **Token 有效期**: 7天（比后端更长，适合学术工具使用）
- **会话验证**: 每次操作都会验证会话有效性
- **自动登出**: 会话过期自动返回登录界面
- **角色控制**: 支持学生/教师不同角色权限

## API 参考

### 核心函数

#### `authenticate_user(useremail, password, role)`
用户登录认证
- **参数**: 邮箱、密码、角色
- **返回**: (成功标志, 消息, 用户信息)

#### `register_user(useremail, username, password, role)`
用户注册
- **参数**: 邮箱、用户名、密码、角色
- **返回**: (成功标志, 消息)

#### `verify_user_token(useremail, token, role_hint)`
验证用户令牌
- **参数**: 邮箱、令牌、角色提示
- **返回**: 用户角色或None

#### `session_manager`
会话管理器
- `create_session(user_info)`: 创建会话
- `get_session(session_id)`: 获取会话
- `remove_session(session_id)`: 删除会话

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查 `se-backend/db_config.json` 文件
   - 确认 MySQL 服务正在运行
   - 验证数据库用户权限

2. **登录失败**
   - 确认用户在数据库中存在
   - 检查密码是否正确
   - 验证角色选择是否匹配

3. **会话过期**
   - 默认7天有效期，可在 `auth_integration.py` 中修改
   - 检查系统时间是否正确

4. **依赖包问题**
   - 重新安装: `pip install -r requirements.txt`
   - 检查Python版本兼容性

### 调试方法

1. **查看日志**
   ```bash
   # 登录相关日志会自动输出到控制台
   python main_with_auth.py
   ```

2. **运行测试**
   ```bash
   python test_auth_system.py
   ```

3. **手动测试数据库**
   ```python
   from shared_utils.auth_integration import get_db_connection
   conn = get_db_connection()
   # 手动执行SQL查询
   ```

## 开发说明

### 扩展功能

1. **添加新的用户角色**
   - 修改 `config.py` 中的 `LOGIN_ALLOWED_ROLES`
   - 更新数据库表结构（如需要）

2. **自定义登录界面**
   - 修改 `login_interface.py`
   - 调整 Gradio 组件样式

3. **集成完整GPT Academic功能**
   - 在 `main_with_auth.py` 中导入完整的主应用
   - 添加权限检查装饰器

### 代码风格

- 使用类型提示 (Type Hints)
- 遵循 PEP 8 编码规范
- 添加详细的函数文档
- 使用 loguru 进行日志记录

## 许可证

本集成遵循 GPT Academic 项目的开源许可证。

## 更新日志

### v1.0.0 (2025-06-04)
- ✅ 初始版本发布
- ✅ 基础认证功能实现
- ✅ 登录界面集成
- ✅ 会话管理
- ✅ 测试脚本和文档
