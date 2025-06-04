#!/usr/bin/env python3
"""
GPT Academic 智能启动器
自动检测登录配置并启动相应版本
"""

import os
import sys
from loguru import logger

def detect_login_config():
    """检测登录配置"""
    try:
        from toolbox import get_conf
        return get_conf('ENABLE_LOGIN')
    except Exception as e:
        logger.warning(f"无法读取配置: {e}")
        return False

def main():
    """主启动函数"""
    print("=" * 60)
    print("🚀 GPT Academic 智能启动器")
    print("🔧 自动检测登录配置并选择合适的版本")
    print("=" * 60)
    
    try:
        enable_login = detect_login_config()
        
        if enable_login:
            logger.info("检测到登录功能已启用 (ENABLE_LOGIN=True)")
            logger.info("启动认证版本...")
            print("📁 使用文件: main_with_auth.py")
            print("🔐 需要登录验证后才能使用系统")
            print("=" * 60)
            
            # 检查认证系统依赖
            try:
                from shared_utils.auth_integration import initialize_auth_system
                if not initialize_auth_system():
                    logger.error("认证系统初始化失败，请检查数据库连接")
                    logger.error("请确保 SE Backend 数据库服务正在运行")
                    sys.exit(1)
                    
                logger.info("认证系统初始化成功")
            except ImportError as e:
                logger.error(f"认证模块导入失败: {e}")
                logger.error("请确保已正确安装依赖: pip install -r requirements.txt")
                sys.exit(1)
            
            # 导入并运行认证版本
            from main_with_auth import main_with_auth as auth_main
            auth_main()
            
        else:
            logger.info("登录功能未启用 (ENABLE_LOGIN=False)")
            logger.info("启动标准版本...")
            print("📁 使用文件: main.py")
            print("🎯 无需登录，直接使用所有功能")
            print("=" * 60)
            
            # 导入并运行标准版本
            from main import main as standard_main
            standard_main()
            
    except KeyboardInterrupt:
        logger.info("用户取消启动")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        logger.error("请检查配置文件和依赖项")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
