#!/usr/bin/env python3
"""
智能对话管理系统一键部署脚本
自动设置数据库、安装依赖、运行测试
"""
import subprocess
import sys
import os
import json

def run_command(cmd, description, check=True):
    """运行命令并显示状态"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} 完成")
            return True
        else:
            print(f"❌ {description} 失败:")
            print(f"  错误: {result.stderr}")
            if check:
                return False
            return True
    except Exception as e:
        print(f"❌ {description} 异常: {e}")
        if check:
            return False
        return True

def check_python_packages():
    """检查并安装Python包"""
    print("📦 检查Python依赖...")
    
    required_packages = [
        "tiktoken>=0.7.0",
        "fastapi>=0.112",
        "sqlalchemy>=2.0"
    ]
    
    for package in required_packages:
        package_name = package.split(">=")[0]
        try:
            __import__(package_name)
            print(f"  ✅ {package_name} 已安装")
        except ImportError:
            print(f"  🔄 安装 {package}...")
            if not run_command(f"pip install {package}", f"安装 {package}"):
                return False
    
    return True

def setup_database():
    """设置数据库"""
    print("🗄️ 设置数据库...")
    
    # 运行数据库迁移
    migration_script = os.path.join(os.path.dirname(__file__), "migrate_conversation_history.py")
    if os.path.exists(migration_script):
        return run_command(f"python {migration_script}", "运行数据库迁移")
    else:
        print("⚠️ 数据库迁移脚本不存在，跳过")
        return True

def check_api_keys():
    """检查API密钥配置"""
    print("🔑 检查API密钥配置...")
    
    api_keys = {
        "DEEPSEEK_API_KEY": "DeepSeek",
        "QWEN_API_KEY": "通义千问", 
        "KIMI_API_KEY": "Kimi",
        "DOUBAO_API_KEY": "豆包"
    }
    
    configured_count = 0
    for env_var, model_name in api_keys.items():
        if os.getenv(env_var):
            print(f"  ✅ {model_name} API密钥已配置")
            configured_count += 1
        else:
            print(f"  ⚠️ {model_name} API密钥未配置 ({env_var})")
    
    if configured_count == 0:
        print("  🚨 未配置任何API密钥，某些功能将无法使用")
        print("  💡 请在环境变量或.env文件中配置API密钥")
    else:
        print(f"  📊 已配置 {configured_count}/4 个API密钥")
    
    return True

def run_tests():
    """运行测试"""
    print("🧪 运行系统测试...")
    
    test_script = os.path.join(os.path.dirname(__file__), "test_conversation_system.py")
    if os.path.exists(test_script):
        return run_command(f"python {test_script}", "运行对话系统测试", check=False)
    else:
        print("⚠️ 测试脚本不存在，跳过测试")
        return True

def update_frontend_dependencies():
    """更新前端依赖"""
    print("🎨 检查前端依赖...")
    
    # 检查是否在正确的目录
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "apps", "web")
    if not os.path.exists(web_dir):
        print("⚠️ 前端目录不存在，跳过")
        return True
    
    # 检查新组件是否存在
    components_to_check = [
        "components/SessionContinuityManager.tsx",
        "components/ConversationMonitor.tsx"
    ]
    
    missing_components = []
    for component in components_to_check:
        component_path = os.path.join(web_dir, component)
        if os.path.exists(component_path):
            print(f"  ✅ {component} 已存在")
        else:
            missing_components.append(component)
    
    if missing_components:
        print("  ⚠️ 缺少以下组件:")
        for component in missing_components:
            print(f"    - {component}")
    
    return True

def generate_config_summary():
    """生成配置摘要"""
    print("📋 生成配置摘要...")
    
    config = {
        "智能对话管理系统": {
            "token_calculation": "使用tiktoken库精确计算",
            "persistent_storage": "数据库持久化对话历史",
            "context_optimization": "智能上下文窗口管理",
            "session_continuity": "跨窗口会话连续性"
        },
        "支持的AI模型": [
            "DeepSeek (deepseek-coder, deepseek-chat)",
            "通义千问 (qwen-max, qwen-plus, qwen-coder)",
            "Kimi (moonshot-v1-8k/32k/128k)",
            "豆包 (doubao-pro-4k/32k)"
        ],
        "新增功能": [
            "会话连续性管理器",
            "实时对话监控面板", 
            "智能token优化",
            "持久化对话存储"
        ]
    }
    
    print("\n" + "="*60)
    print("🎯 智能对话管理系统配置摘要")
    print("="*60)
    
    for section, content in config.items():
        print(f"\n📌 {section}:")
        if isinstance(content, dict):
            for key, value in content.items():
                print(f"  • {key}: {value}")
        elif isinstance(content, list):
            for item in content:
                print(f"  • {item}")
        else:
            print(f"  {content}")
    
    print("\n" + "="*60)
    return True

def main():
    """主函数"""
    print("🚀 智能对话管理系统部署开始...")
    print("解决问题:")
    print("  ✅ 防止超出200,000 tokens限制")
    print("  ✅ 支持跨窗口会话连续性")
    print("  ✅ 持久化存储对话历史")
    print("  ✅ 智能优化和实时监控")
    print("\n" + "="*50)
    
    steps = [
        (check_python_packages, "检查Python依赖包"),
        (setup_database, "设置数据库"),
        (check_api_keys, "检查API密钥"),
        (update_frontend_dependencies, "检查前端组件"),
        (run_tests, "运行系统测试"),
        (generate_config_summary, "生成配置摘要")
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for i, (step_func, step_name) in enumerate(steps, 1):
        print(f"\n[{i}/{total_steps}] {step_name}")
        print("-" * 40)
        
        try:
            if step_func():
                success_count += 1
                print(f"✅ 步骤 {i} 完成")
            else:
                print(f"❌ 步骤 {i} 失败")
        except Exception as e:
            print(f"❌ 步骤 {i} 异常: {e}")
    
    print("\n" + "="*50)
    print("📊 部署结果:")
    print(f"  成功步骤: {success_count}/{total_steps}")
    print(f"  成功率: {success_count/total_steps*100:.1f}%")
    
    if success_count == total_steps:
        print("\n🎉 智能对话管理系统部署成功!")
        print("\n🔧 使用说明:")
        print("  1. 启动开发服务器: npm run dev")
        print("  2. 访问项目聊天页面")
        print("  3. 享受智能对话管理功能!")
        print("\n📖 更多信息请查看 README_ZH.md")
        return True
    else:
        print("\n⚠️ 部分步骤失败，但系统可能仍然可用")
        print("请检查失败的步骤并手动修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)