#!/usr/bin/env python3
"""
Environment Validation Script for PDF Q&A System
Checks all API key configurations and provides recommendations
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_env_file():
    """Check for .env file existence and content"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found")
        print("💡 Create one by copying .env.example:")
        print("   cp .env.example .env")
        return False
    
    print("✅ .env file found")
    return True

def check_api_keys():
    """Check API key configuration"""
    load_dotenv()
    
    openrouter_key = os.getenv('OPENROUTER_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if openrouter_key:
        if openrouter_key == "your_openrouter_api_key_here":
            print("⚠️  OPENROUTER_API_KEY is set to placeholder value")
            print("💡 Update with your real API key from https://openrouter.ai/keys")
            return False
        else:
            print("✅ OPENROUTER_API_KEY is configured")
            return True
    
    if openai_key:
        print("⚠️  Found OPENAI_API_KEY instead of OPENROUTER_API_KEY")
        print("💡 Recommended: Rename OPENAI_API_KEY to OPENROUTER_API_KEY")
        if openai_key.startswith('sk-or-'):
            print("✅ Key appears to be a valid OpenRouter key")
            return True
        else:
            print("❌ Key doesn't appear to be an OpenRouter key")
            return False
    
    print("❌ No API key found")
    print("💡 Add OPENROUTER_API_KEY to your .env file")
    return False

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'flask',
        'openai',
        'sentence-transformers',
        'faiss-cpu',
        'pdfplumber',
        'python-dotenv',
        'numpy',
        'transformers'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n💡 Install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_docker_env():
    """Check Docker environment variables"""
    docker_vars = {
        'PYTHONPATH': '/app/src',
        'FLASK_ENV': 'production',
        'PORT': '5000'
    }
    
    print("\n🐳 Docker Environment Variables:")
    for var, expected in docker_vars.items():
        current = os.getenv(var, 'Not set')
        status = "✅" if current else "⚠️ "
        print(f"   {status} {var}: {current}")

def fix_api_key_name():
    """Offer to fix API key naming automatically"""
    env_file = Path('.env')
    if not env_file.exists():
        return
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    if 'OPENAI_API_KEY=' in content and 'OPENROUTER_API_KEY=' not in content:
        print("\n🔧 API Key Fix Available:")
        print("   Found OPENAI_API_KEY in .env file")
        fix = input("   Rename to OPENROUTER_API_KEY? (y/n): ").lower()
        
        if fix == 'y':
            new_content = content.replace('OPENAI_API_KEY=', 'OPENROUTER_API_KEY=')
            with open(env_file, 'w') as f:
                f.write(new_content)
            print("✅ API key renamed successfully!")
            return True
    
    return False

def main():
    print("🔍 PDF Q&A System - Environment Validation")
    print("=" * 50)
    
    # Check .env file
    print("\n📄 Checking .env file...")
    env_exists = check_env_file()
    
    if env_exists:
        # Offer to fix API key naming
        fixed = fix_api_key_name()
        if fixed:
            print("🔄 Reloading environment...")
    
    # Check API keys
    print("\n🔑 Checking API Keys...")
    api_ok = check_api_keys()
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    deps_ok = check_dependencies()
    
    # Check Docker environment
    check_docker_env()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Summary:")
    print(f"   Environment file: {'✅' if env_exists else '❌'}")
    print(f"   API key: {'✅' if api_ok else '❌'}")
    print(f"   Dependencies: {'✅' if deps_ok else '❌'}")
    
    if all([env_exists, api_ok, deps_ok]):
        print("\n🎉 All checks passed! Your environment is ready.")
        print("🚀 Start the application with:")
        print("   docker-compose up -d")
        print("   or")
        print("   python src/web_app.py")
    else:
        print("\n⚠️  Some issues found. Please fix them before running the application.")
    
    return all([env_exists, api_ok, deps_ok])

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
