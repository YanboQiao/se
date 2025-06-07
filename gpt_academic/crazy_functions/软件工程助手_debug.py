"""
软件工程课程助手
包含需求分析、可行性分析、总体设计、详细设计、单元测试等功能
帮助学生和教师更好地学习和备课软件工程
"""

from toolbox import CatchException, report_exception, get_conf, update_ui_latest_msg, select_api_key, write_history_to_file
from .crazy_utils import request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency, input_clipping
import os
import re
import time

# 添加调试功能
def debug_log(message, chatbot=None):
    """调试日志函数"""
    print(f"[DEBUG 软件工程助手] {message}")
    if chatbot is not None:
        chatbot.append(("[DEBUG]", message))

@CatchException
def 需求分析助手(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    需求分析助手 - 帮助分析软件需求，生成需求规格说明书
    """
    debug_log(f"需求分析助手启动 - 输入文本长度: {len(txt)}", chatbot)
    debug_log(f"llm_kwargs: {llm_kwargs}", chatbot)
    
    try:
        chatbot.append(("需求分析助手启动", "正在分析您的软件需求..."))
        yield from update_ui_latest_msg("正在进行需求分析...", chatbot, history, delay=1)
        
        debug_log("正在构建分析提示词...", chatbot)
        
        # 需求分析提示词
        analysis_prompt = f"""
作为一名经验丰富的软件工程师和需求分析师，请对以下项目进行全面的需求分析：

项目描述：
{txt}

请按照以下结构进行需求分析：

## 1. 功能需求分析
### 1.1 核心功能
- 详细列出系统必须实现的核心功能
- 每个功能都要有清晰的描述和预期结果

### 1.2 辅助功能
- 列出支持核心功能的辅助功能
- 说明各功能之间的依赖关系

### 1.3 用户角色和权限
- 识别不同的用户类型
- 定义每种用户的权限和可执行操作

## 2. 非功能需求分析
### 2.1 性能需求
- 响应时间要求
- 并发用户数量
- 数据处理能力

### 2.2 可用性需求
- 系统可用性指标
- 故障恢复时间
- 备份和容灾机制

### 2.3 安全需求
- 数据安全保护
- 用户认证和授权
- 系统安全防护

### 2.4 兼容性需求
- 平台兼容性
- 浏览器兼容性
- 设备兼容性

## 3. 约束条件
### 3.1 技术约束
- 开发技术栈限制
- 第三方组件依赖
- 现有系统集成要求

### 3.2 时间约束
- 项目开发周期
- 关键里程碑
- 上线时间要求

### 3.3 资源约束
- 开发团队规模
- 预算限制
- 硬件资源限制

## 4. 验收标准
- 每个功能模块的验收标准
- 性能指标的量化标准
- 用户体验的评估标准

请确保分析内容具体、可量化、可验证，并考虑实际开发中可能遇到的问题和挑战。
"""
        
        debug_log("正在调用GPT模型...", chatbot)
        
        # 调用大模型进行需求分析
        gpt_say = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs=[analysis_prompt],
            inputs_show_user=[txt],
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=[[]],
            sys_prompt_array=["你是一名专业的软件工程师和需求分析师，擅长进行全面而详细的需求分析。"]
        )[0]
        
        debug_log("GPT响应完成，正在保存结果...", chatbot)
        
        # 保存分析结果
        write_history_to_file(gpt_say)
        chatbot.append(("需求分析完成", "已完成需求分析，建议保存结果用于后续设计阶段。"))
        yield from update_ui_latest_msg("需求分析已完成", chatbot, history, delay=1)
        
        debug_log("需求分析助手执行完成", chatbot)
        
    except Exception as e:
        debug_log(f"需求分析助手异常: {str(e)}", chatbot)
        chatbot.append(("需求分析失败", f"分析过程中出现错误：{str(e)}"))
        yield from update_ui_latest_msg("需求分析失败", chatbot, history, delay=1)

@CatchException
def 可行性分析助手(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    可行性分析助手 - 从技术、经济、操作等角度分析项目可行性
    """
    debug_log(f"可行性分析助手启动 - 输入文本长度: {len(txt)}", chatbot)
    
    try:
        chatbot.append(("可行性分析助手启动", "正在分析项目可行性..."))
        yield from update_ui_latest_msg("正在进行可行性分析...", chatbot, history, delay=1)
        
        # 可行性分析提示词
        feasibility_prompt = f"""
作为一名资深的项目经理和技术专家，请对以下项目进行全面的可行性分析：

项目描述：
{txt}

请从以下几个维度进行可行性分析：

## 1. 技术可行性分析
### 1.1 技术实现难度评估
- 核心技术的成熟度和可获得性
- 技术实现的复杂度评估（1-10分）
- 技术风险识别和应对策略

### 1.2 技术选型建议
- 推荐的技术架构和技术栈
- 各技术方案的优缺点对比
- 技术选型的理由和依据

### 1.3 技术团队能力要求
- 所需的技术技能清单
- 团队规模和经验要求
- 技能培训和学习成本

## 2. 经济可行性分析
### 2.1 成本估算
- 开发成本估算（人力、硬件、软件、培训等）
- 运营维护成本
- 总拥有成本(TCO)分析

### 2.2 收益分析
- 预期的直接经济收益
- 间接收益（效率提升、成本节约等）
- 投资回报率(ROI)计算

### 2.3 风险成本评估
- 项目失败的潜在损失
- 质量问题的修复成本

## 3. 操作可行性分析
### 3.1 用户接受度分析
- 目标用户群体分析
- 变更管理和用户培训需求
- 现有业务流程的适配性

### 3.2 组织适应性
- 管理层支持度评估
- 现有团队技能匹配度

### 3.3 实施可行性
- 项目实施的复杂度
- 实施风险和应对措施

## 4. 时间可行性分析
### 4.1 开发周期评估
- 各阶段时间估算
- 并行开发的可能性

### 4.2 市场时机分析
- 市场需求的紧迫性
- 技术发展趋势

## 5. 法律和合规性分析
### 5.1 法律法规符合性
- 数据保护和隐私合规
- 知识产权风险

### 5.2 标准和认证要求
- 行业标准符合性
- 安全认证要求
- 质量标准要求

## 6. 综合可行性结论
- 综合可行性评分（1-10分）
- 关键成功因素识别
- 项目实施建议
- 实施路径和里程碑建议

请提供详细、客观的分析，并给出明确的可行性结论和建议。
"""
        
        debug_log("正在调用GPT模型进行可行性分析...", chatbot)
        
        # 调用大模型进行可行性分析
        gpt_say = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs=[feasibility_prompt],
            inputs_show_user=[txt],
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=[[]],
            sys_prompt_array=["你是一名资深的项目经理和技术专家，具备丰富的项目可行性分析经验。"]
        )[0]
        
        # 保存分析结果
        write_history_to_file(gpt_say)
        chatbot.append(("可行性分析完成", "已完成项目可行性分析，请参考分析结果制定项目决策。"))
        yield from update_ui_latest_msg("可行性分析已完成", chatbot, history, delay=1)
        
    except Exception as e:
        debug_log(f"可行性分析助手异常: {str(e)}", chatbot)
        chatbot.append(("可行性分析失败", f"分析过程中出现错误：{str(e)}"))
        yield from update_ui_latest_msg("可行性分析失败", chatbot, history, delay=1)

@CatchException
def 总体设计助手(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    总体设计助手 - 基于需求分析结果进行系统总体设计
    """
    debug_log(f"总体设计助手启动 - 输入文本长度: {len(txt)}", chatbot)
    
    try:
        chatbot.append(("总体设计助手启动", "正在进行系统总体设计..."))
        yield from update_ui_latest_msg("正在生成系统总体设计...", chatbot, history, delay=1)
        
        # 总体设计提示词
        design_prompt = f"""
作为一名资深的软件架构师，请基于以下需求信息进行系统总体设计：

需求信息：
{txt}

请按照以下结构进行总体设计：

## 1. 系统架构设计
### 1.1 架构模式选择
- 选择的架构模式（如分层架构、微服务架构、MVC等）
- 架构选择的理由和优势
- 架构的主要特点和约束

### 1.2 系统分层设计
- 表现层设计
- 业务逻辑层设计
- 数据访问层设计
- 数据存储层设计

### 1.3 系统组件规划
- 核心业务组件识别
- 公共服务组件设计
- 第三方集成组件规划

## 2. 技术架构设计
### 2.1 技术栈选择
- 前端技术栈
- 后端技术栈
- 数据库技术选择
- 中间件和框架选择

### 2.2 部署架构设计
- 物理部署拓扑
- 网络架构设计
- 负载均衡策略
- 容灾备份方案

### 2.3 安全架构设计
- 身份认证机制
- 权限控制体系
- 数据加密策略
- 安全防护措施

## 3. 数据架构设计
### 3.1 数据模型设计
- 概念数据模型
- 逻辑数据模型
- 主要实体关系图

### 3.2 数据存储设计
- 数据库选择和分布
- 数据分区和分片策略
- 数据备份和恢复策略

### 3.3 数据流设计
- 数据流向图
- 数据处理流程
- 数据同步和一致性保证

## 4. 接口设计
### 4.1 系统间接口
- 外部系统接口规范
- API设计原则
- 接口安全和版本管理

### 4.2 用户界面设计
- UI设计原则和规范
- 用户交互流程
- 响应式设计策略

## 5. 性能设计
### 5.1 性能目标
- 响应时间目标
- 吞吐量目标
- 并发用户数目标

### 5.2 性能优化策略
- 缓存策略设计
- 数据库优化方案
- 前端性能优化

## 6. 可靠性和可扩展性设计
### 6.1 可靠性设计
- 容错机制
- 故障恢复策略
- 监控和告警机制

### 6.2 可扩展性设计
- 水平扩展策略
- 垂直扩展策略

## 7. 开发和部署设计
### 7.1 开发环境设计
- 模块化设计原则
- 代码组织结构
- 文档和注释规范
- 版本控制策略

### 7.2 部署和运维设计
- 开发环境搭建
- 测试环境规划
- 生产环境配置
- 运维监控方案

请确保设计方案完整、合理、可实施，并考虑未来的扩展和维护需求。
"""
        
        debug_log("正在调用GPT模型进行总体设计...", chatbot)
        
        # 调用大模型进行总体设计
        gpt_say = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs=[design_prompt],
            inputs_show_user=[txt],
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=[[]],
            sys_prompt_array=["你是一名资深的软件架构师，擅长进行系统总体设计和架构规划。"]
        )[0]
        
        # 保存设计结果
        write_history_to_file(gpt_say)
        chatbot.append(("总体设计完成", "已完成系统总体设计，可以基于此设计进行详细设计和开发。"))
        yield from update_ui_latest_msg("总体设计已完成", chatbot, history, delay=1)
        
    except Exception as e:
        debug_log(f"总体设计助手异常: {str(e)}", chatbot)
        chatbot.append(("总体设计失败", f"设计过程中出现错误：{str(e)}"))
        yield from update_ui_latest_msg("总体设计失败", chatbot, history, delay=1)

@CatchException
def 详细设计助手(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    详细设计助手 - 基于总体设计进行详细的模块设计
    """
    debug_log(f"详细设计助手启动 - 输入文本长度: {len(txt)}", chatbot)
    
    try:
        chatbot.append(("详细设计助手启动", "正在进行系统详细设计..."))
        yield from update_ui_latest_msg("正在生成详细设计文档...", chatbot, history, delay=1)
        
        # 详细设计提示词
        detailed_design_prompt = f"""
作为一名经验丰富的软件设计师，请基于以下总体设计信息进行详细设计：

总体设计信息：
{txt}

请按照以下结构进行详细设计：

## 1. 模块详细设计
### 1.1 核心业务模块
对每个核心业务模块进行详细设计，包括：
- 模块功能描述
- 模块接口定义
- 模块内部结构
- 主要算法和数据结构

### 1.2 数据访问模块
- DAO层设计
- 数据映射策略
- 连接池配置
- 事务管理机制

请确保详细设计能够指导开发人员进行具体的编码实现，并提供相应的设计模式和最佳实践建议。
"""
        
        debug_log("正在调用GPT模型进行详细设计...", chatbot)
        
        # 调用大模型进行详细设计
        gpt_say = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs=[detailed_design_prompt],
            inputs_show_user=[txt],
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=[[]],
            sys_prompt_array=["你是一名经验丰富的软件设计师，擅长进行模块详细设计。"]
        )[0]
        
        # 保存设计结果
        write_history_to_file(gpt_say)
        chatbot.append(("详细设计完成", "已完成系统详细设计，可以开始编码实现。"))
        yield from update_ui_latest_msg("详细设计已完成", chatbot, history, delay=1)
        
    except Exception as e:
        debug_log(f"详细设计助手异常: {str(e)}", chatbot)
        chatbot.append(("详细设计失败", f"设计过程中出现错误：{str(e)}"))
        yield from update_ui_latest_msg("详细设计失败", chatbot, history, delay=1)

@CatchException
def 单元测试助手(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    单元测试助手 - 基于代码或设计文档生成单元测试用例
    """
    debug_log(f"单元测试助手启动 - 输入文本长度: {len(txt)}", chatbot)
    
    try:
        chatbot.append(("单元测试助手启动", "正在生成单元测试用例..."))
        yield from update_ui_latest_msg("正在分析代码并生成测试用例...", chatbot, history, delay=1)
        
        debug_log("更新了UI消息", chatbot)
        
        # 单元测试提示词
        test_prompt = f"""
作为一名专业的测试工程师和质量保证专家，请基于以下代码或设计信息生成完整的单元测试：

代码/设计信息：
{txt}

请按照以下结构生成单元测试：

## 1. 测试策略分析
### 1.1 测试范围识别
- 需要测试的函数/方法列表
- 测试的边界条件
- 异常情况和错误处理

### 1.2 测试方法选择
- 白盒测试策略
- 黑盒测试策略
- 等价类划分
- 边界值分析

## 2. 测试用例设计
### 2.1 正常流程测试
为每个函数/方法设计正常流程的测试用例：
- 测试用例ID
- 测试描述
- 输入参数
- 期望输出
- 前置条件

### 2.2 边界值测试
- 最小值边界测试
- 最大值边界测试
- 空值和null测试
- 特殊字符测试

### 2.3 异常流程测试
- 无效输入测试
- 异常抛出测试
- 超时测试
- 资源不足测试

## 3. 测试代码实现
### 3.1 测试框架选择
根据编程语言选择合适的测试框架：
- Java: JUnit, TestNG, Mockito
- Python: unittest, pytest, mock
- JavaScript: Jest, Mocha, Chai
- C#: NUnit, xUnit, Moq

### 3.2 测试代码编写
为每个测试用例编写具体的测试代码

请确保生成的测试用例具有完整性、可执行性和高覆盖率。
"""
        
        debug_log("正在调用GPT模型生成测试用例...", chatbot)
        
        # 调用大模型生成测试用例
        gpt_say = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs=[test_prompt],
            inputs_show_user=[txt],
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=[[]],
            sys_prompt_array=["你是一名专业的测试工程师，擅长设计和编写高质量的单元测试。"]
        )[0]
        
        debug_log("GPT响应完成，正在保存测试结果...", chatbot)
        
        # 保存测试结果
        write_history_to_file(gpt_say)
        chatbot.append(("单元测试设计完成", "已完成单元测试用例设计，请根据生成的测试代码进行实际测试。"))
        yield from update_ui_latest_msg("单元测试设计已完成", chatbot, history, delay=1)
        
    except Exception as e:
        debug_log(f"单元测试助手异常: {str(e)}", chatbot)
        chatbot.append(("单元测试设计失败", f"生成过程中出现错误：{str(e)}"))
        yield from update_ui_latest_msg("单元测试设计失败", chatbot, history, delay=1)

@CatchException
def 软件工程流程助手(txt, llm_kwargs, plugin_kwargs, chatbot, history, system_prompt, user_request):
    """
    软件工程流程助手 - 提供完整的软件工程流程指导
    """
    debug_log(f"软件工程流程助手启动 - 输入文本长度: {len(txt)}", chatbot)
    
    try:
        chatbot.append(("软件工程流程助手启动", "正在生成软件工程流程指导..."))
        yield from update_ui_latest_msg("正在生成完整的软件工程流程...", chatbot, history, delay=1)
        
        # 软件工程流程提示词
        process_prompt = f"""
作为一名资深的项目经理和软件工程专家，请为以下项目提供完整的软件工程流程指导：

项目信息：
{txt}

请提供完整的软件工程流程，包括以下各个阶段的详细指导：

## 1. 项目启动阶段
### 1.1 项目立项
- 项目背景和目标
- 干系人识别和分析
- 项目范围定义
- 初步可行性评估

### 1.2 团队组建
- 项目组织结构
- 团队成员技能要求
- 沟通机制建立

### 1.3 项目计划制定
- 工作分解结构(WBS)
- 进度计划和里程碑
- 风险管理计划

## 2. 需求工程阶段
### 2.1 需求获取
- 干系人访谈计划
- 需求收集方法和技术
- 需求获取工具和模板
- 需求优先级划分

### 2.2 需求分析
- 功能需求分析
- 非功能需求分析
- 需求建模技术
- 需求冲突解决

### 2.3 需求规格说明
- SRS文档编写规范
- 需求评审流程
- 需求变更管理

## 3. 系统设计阶段
### 3.1 架构设计
- 系统架构设计方法
- 技术选型决策
- 设计模式应用
- 架构评审标准

### 3.2 详细设计
- 模块设计方法
- 数据库设计流程
- 设计文档模板

### 3.3 设计评审
- 设计评审检查清单
- 设计问题跟踪
- 设计优化建议

## 4. 编码实现阶段
### 4.1 编码标准
- 编码规范制定
- 代码审查流程
- 版本控制策略
- 持续集成配置

### 4.2 开发管理
- 敏捷开发实践
- 每日站会流程
- 开发进度跟踪

### 4.3 质量控制
- 代码质量检查
- 单元测试要求

## 5. 测试阶段
### 5.1 测试计划
- 测试策略制定
- 集成测试计划
- 缺陷管理流程

### 5.2 测试执行
- 测试环境准备
- 测试数据准备
- 测试人员分工
- 功能测试执行
- 性能测试执行
- 安全测试执行
- 用户验收测试

### 5.3 缺陷管理
- 缺陷发现和记录
- 缺陷修复和验证
- 缺陷报告生成

## 6. 部署上线阶段
### 6.1 部署准备
- 生产环境准备
- 部署脚本编写
- 数据迁移计划
- 回滚方案制定

### 6.2 部署实施
- 部署步骤执行
- 性能监控配置
- 用户培训实施

### 6.3 上线验证
- 功能验证测试
- 性能验证测试
- 安全验证测试
- 用户反馈收集

## 7. 维护运营阶段
### 7.1 运维监控
- 系统监控配置
- 告警机制设置
- 日志分析流程
- 性能优化策略

### 7.2 版本管理
- 版本发布计划
- 变更控制流程
- 配置管理规范

### 7.3 持续改进
- 用户反馈处理
- 系统优化建议
- 技术债务管理
- 经验总结归档

## 8. 项目管理最佳实践
### 8.1 风险管理
- 风险识别和评估
- 风险应对策略
- 风险监控和报告
- 应急预案制定

### 8.2 质量管理
- 质量标准制定
- 质量保证活动
- 质量控制检查
- 质量改进措施

### 8.3 沟通管理
- 沟通计划制定
- 会议管理规范
- 文档管理标准
- 知识管理体系

请确保流程指导具有实操性和可执行性，并提供相应的模板和检查清单。
"""
        
        debug_log("正在调用GPT模型生成流程指导...", chatbot)
        
        # 调用大模型生成流程指导
        gpt_say = yield from request_gpt_model_multi_threads_with_very_awesome_ui_and_high_efficiency(
            inputs=[process_prompt],
            inputs_show_user=[txt],
            llm_kwargs=llm_kwargs,
            chatbot=chatbot,
            history_array=[[]],
            sys_prompt_array=["你是一名资深的项目经理和软件工程专家，具备丰富的软件工程流程管理经验。"]
        )[0]
        
        # 保存流程指导结果
        write_history_to_file(gpt_say)
        chatbot.append(("软件工程流程指导完成", "已完成软件工程流程指导，请参考执行各阶段工作。"))
        yield from update_ui_latest_msg("软件工程流程指导已完成", chatbot, history, delay=1)
        
    except Exception as e:
        debug_log(f"软件工程流程助手异常: {str(e)}", chatbot)
        chatbot.append(("流程指导生成失败", f"生成过程中出现错误：{str(e)}"))
        yield from update_ui_latest_msg("流程指导生成失败", chatbot, history, delay=1)
