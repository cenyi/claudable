    print("📦 Checking Python dependencies...")
    
    required_packages = [
        "tiktoken>=0.7.0",
        "fastapi>=0.112",
        "sqlalchemy>=2.0"
    ]
    
    for package in required_packages:
        package_name = package.split(">=")[0]
        try:
            __import__(package_name)
            print(f"  ✅ {package_name} is installed")
        except ImportError:
            print(f"  🔄 Installing {package}...")
            if not run_command(f"pip install {package}", f"Installing {package}"):
                return False
    
    return True

def setup_database():
    """Setup database"""
    print("🗄️ Setting up database...")
    
    # Run database migration
    migration_script = os.path.join(os.path.dirname(__file__), "migrate_conversation_history.py")
    if os.path.exists(migration_script):
        return run_command(f"python {migration_script}", "Running database migration")
    else:
        print("⚠️ Database migration script does not exist, skipping")
        return True

def check_api_keys():
    """Check API key configuration"""
    print("🔑 Checking API key configuration...")
    
    api_keys = {
        "DEEPSEEK_API_KEY": "DeepSeek",
        "QWEN_API_KEY": "Qwen", 
        "KIMI_API_KEY": "Kimi",
        "DOUBAO_API_KEY": "Doubao"
    }
    
    configured_count = 0
    for env_var, model_name in api_keys.items():
        if os.getenv(env_var):
            print(f"  ✅ {model_name} API key is configured")
            configured_count += 1
        else:
            print(f"  ⚠️ {model_name} API key is not configured ({env_var})")
    
    if configured_count == 0:
        print("  🚨 No API keys configured, some features will not be available")
        print("  💡 Please configure API keys in environment variables or .env file")
    else:
        print(f"  📊 {configured_count}/4 API keys configured")
    
    return True

def run_tests():
    """Run tests"""
    print("🧪 Running system tests...")
    
    test_script = os.path.join(os.path.dirname(__file__), "test_conversation_system.py")
    if os.path.exists(test_script):
        return run_command(f"python {test_script}", "Running conversation system tests", check=False)
    else:
        print("⚠️ Test script does not exist, skipping tests")
        return True

def update_frontend_dependencies():
    """Update frontend dependencies"""
    print("🎨 Checking frontend dependencies...")
    
    # Check if in the correct directory
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "apps", "web")
    if not os.path.exists(web_dir):
        print("⚠️ Frontend directory does not exist, skipping")
        return True
    
    # Check if new components exist
    components_to_check = [
        "components/SessionContinuityManager.tsx",
        "components/ConversationMonitor.tsx"
    ]
    
    missing_components = []
    for component in components_to_check:
        component_path = os.path.join(web_dir, component)
        if os.path.exists(component_path):
            print(f"  ✅ {component} exists")
        else:
            missing_components.append(component)
    
    if missing_components:
        print("  ⚠️ Missing components:")
        for component in missing_components:
            print(f"    - {component}")
    
    return True

def generate_config_summary():
    """Generate configuration summary"""
    print("📋 Generating configuration summary...")
    
    config = {
        "Intelligent Conversation Management System": {
            "token_calculation": "Precise calculation using tiktoken library",
            "persistent_storage": "Database-persistent conversation history",
            "context_optimization": "Intelligent context window management",
            "session_continuity": "Cross-window session continuity"
        },
        "Supported AI Models": [
            "DeepSeek (deepseek-coder, deepseek-chat)",
            "Qwen (qwen-max, qwen-plus, qwen-coder)",
            "Kimi (moonshot-v1-8k/32k/128k)",
            "Doubao (doubao-pro-4k/32k)"
        ],
        "New Features": [
            "Session Continuity Manager",
            "Real-time Conversation Monitoring Panel", 
            "Intelligent Token Optimization",
            "Persistent Conversation Storage"
        ]
    }
    
    print("\n" + "="*60)
    print("🎯 Intelligent Conversation Management System Configuration Summary")
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
    """Main function"""
    print("🚀 Intelligent Conversation Management System Deployment Starting...")
    print("Solving Issues:")
    print("  ✅ Prevent exceeding 200,000 tokens limit")
    print("  ✅ Support cross-window session continuity")
    print("  ✅ Persistent storage of conversation history")
    print("  ✅ Intelligent optimization and real-time monitoring")
    print("\n" + "="*50)
    
    steps = [
        (check_python_packages, "Check Python Dependencies"),
        (setup_database, "Setup Database"),
        (check_api_keys, "Check API Keys"),
        (update_frontend_dependencies, "Check Frontend Components"),
        (run_tests, "Run System Tests"),
        (generate_config_summary, "Generate Configuration Summary")
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for i, (step_func, step_name) in enumerate(steps, 1):
        print(f"\n[{i}/{total_steps}] {step_name}")
        print("-" * 40)
        
        try:
            if step_func():
                success_count += 1
                print(f"✅ Step {i} completed")
            else:
                print(f"❌ Step {i} failed")
        except Exception as e:
            print(f"❌ Step {i} exception: {e}")
    
    print("\n" + "="*50)
    print("📊 Deployment Results:")
    print(f"  Successful Steps: {success_count}/{total_steps}")
    print(f"  Success Rate: {success_count/total_steps*100:.1f}%")
    
    if success_count == total_steps:
        print("\n🎉 Intelligent Conversation Management System deployed successfully!")
        print("\n🔧 Usage Instructions:")
        print("  1. Start development server: npm run dev")
        print("  2. Access the project chat page")
        print("  3. Enjoy intelligent conversation management features!")
        print("\n📖 For more information, please check README_ZH.md")
        return True
    else:
        print("\n⚠️ Some steps failed, but the system may still be usable")
        print("Please check the failed steps and fix manually")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)