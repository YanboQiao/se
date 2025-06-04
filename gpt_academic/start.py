#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start.py - GPT Academic 启动器
提供选择是否启用登录功能的启动方式
"""

import sys
import os
import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='GPT Academic 启动器')
    parser.add_argument(
        '--with-auth', 
        action='store_true', 
        help='启用登录认证功能'
    )
    parser.add_argument(
        '--test-auth', 
        action='store_true', 
        help='测试认证系统'
    )
    
    args = parser.parse_args()
    
    if args.test_auth:
        print("🧪 运行认证系统测试...")
        import test_auth_system
        test_auth_system.main()
        return
    
    if args.with_auth:
        print("🔐 启动带登录功能的GPT Academic...")
        print("请确保:")
        print("1. SE Backend数据库服务正在运行")
        print("2. 已正确配置数据库连接")
        print("3. 已安装所需依赖: pip install -r requirements.txt")
        print()
        
        # 动态启用登录功能
        try:
            import config
            config.ENABLE_LOGIN = True
            print("✅ 已启用登录功能")
        except:
            print("⚠️ 无法修改配置，请手动设置 config.py 中的 ENABLE_LOGIN = True")
        
        import main_with_auth
        main_with_auth.main()
    else:
        print("🚀 启动标准版GPT Academic...")
        import main
        main.main()

if __name__ == "__main__":
    main()
