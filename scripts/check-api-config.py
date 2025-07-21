#!/usr/bin/env python3
"""
Comprehensive API Configuration Checker for Intelligent Query System
This script validates all API-related configurations and provides detailed feedback
"""

import os
import sys
import json
import requests
from pathlib import Path

def print_header():
    print("=" * 60)
    print("    🔍 API Configuration Checker")
    print("    Intelligent Query PDF Q&A System")
    print("=" * 60)
    print()

def check_env_file():
    """Check if .env file exists and has API key"""
    print("📁 Checking .env file...")
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file not found")
        return False, None, None
    
    print("✅ .env file found")
    
    # Read .env file
    env_vars = {}
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()
    
    # Check for API keys
    openrouter_key = env_vars.get('OPENROUTER_API_KEY')
    openai_key = env_vars.get('OPENAI_API_KEY')
    
    if openrouter_key:
        print(f"✅ OPENROUTER_API_KEY found: {openrouter_key[:8]}...")
        return True, openrouter_key, 'OPENROUTER_API_KEY'
    elif openai_key:
        print(f"⚠️  OPENAI_API_KEY found: {openai_key[:8]}...")
        print("   Consider renaming to OPENROUTER_API_KEY")
        return True, openai_key, 'OPENAI_API_KEY'
    else:
        print("❌ No API key found in .env file")
        return False, None, None

def check_environment_variables():
    """Check environment variables"""
    print("\n🌍 Checking environment variables...")
    
    openrouter_key = os.environ.get('OPENROUTER_API_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    if openrouter_key:
        print(f"✅ OPENROUTER_API_KEY in environment: {openrouter_key[:8]}...")
        return openrouter_key, 'OPENROUTER_API_KEY'
    elif openai_key:
        print(f"⚠️  OPENAI_API_KEY in environment: {openai_key[:8]}...")
        return openai_key, 'OPENAI_API_KEY'
    else:
        print("❌ No API key in environment variables")
        return None, None

def validate_api_key_format(api_key):
    """Validate API key format"""
    print(f"\n🔑 Validating API key format...")
    
    if not api_key:
        print("❌ No API key to validate")
        return False
    
    print(f"   Key preview: {api_key[:8]}...")
    print(f"   Key length: {len(api_key)}")
    
    if api_key.startswith('sk-or-'):
        print("✅ OpenRouter API key format detected")
        return True
    elif api_key.startswith('sk-'):
        print("✅ Standard API key format detected")
        return True
    elif api_key.startswith('or-'):
        print("✅ OpenRouter format detected")
        return True
    else:
        print("⚠️  Unusual API key format")
        return False

def test_api_connection(api_key):
    """Test API connection (basic validation)"""
    print(f"\n🌐 Testing API connection...")
    
    if not api_key:
        print("❌ No API key to test")
        return False
    
    # Basic headers test
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Test with a simple models request
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ API connection successful")
            models = response.json()
            print(f"   Available models: {len(models.get('data', []))}")
            return True
        elif response.status_code == 401:
            print("❌ API key authentication failed")
            return False
        elif response.status_code == 403:
            print("❌ API key access forbidden")
            return False
        else:
            print(f"⚠️  API responded with status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("⚠️  API request timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Network connection error")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def check_app_imports():
    """Check if app modules can be imported"""
    print(f"\n📦 Checking app module imports...")
    
    try:
        # Add src to path
        src_path = Path('src')
        if src_path.exists():
            sys.path.insert(0, str(src_path))
        
        from app import extract_text_from_pdf, create_document_embeddings, generate_response
        print("✅ Core app functions imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_local_server():
    """Test if local server is running"""
    print(f"\n🚀 Checking local server...")
    
    try:
        response = requests.get('http://localhost:5000/status', timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("✅ Local server is running")
            print(f"   API configured: {status.get('api_configured', 'Unknown')}")
            print(f"   Document loaded: {status.get('document_loaded', 'Unknown')}")
            return True
        else:
            print(f"⚠️  Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Local server not accessible (not running?)")
        return False
    except Exception as e:
        print(f"❌ Server test error: {e}")
        return False

def generate_recommendations():
    """Generate recommendations based on findings"""
    print(f"\n💡 RECOMMENDATIONS:")
    print("=" * 40)
    
    # Check .env file
    env_exists, api_key, key_source = check_env_file()
    
    if not env_exists:
        print("1. Create a .env file with:")
        print("   OPENROUTER_API_KEY=your_actual_api_key_here")
        print()
    
    if key_source == 'OPENAI_API_KEY':
        print("2. Consider renaming OPENAI_API_KEY to OPENROUTER_API_KEY")
        print("   for better clarity")
        print()
    
    if api_key and not validate_api_key_format(api_key):
        print("3. Verify your API key format")
        print("   OpenRouter keys typically start with 'sk-or-' or 'sk-'")
        print()
    
    print("4. Test the configuration by:")
    print("   - Running: docker-compose up -d")
    print("   - Opening: http://localhost:5000")
    print("   - Checking: http://localhost:5000/status")

def main():
    """Main checker function"""
    print_header()
    
    # All checks
    checks = []
    
    # 1. Check .env file
    env_exists, env_api_key, env_key_source = check_env_file()
    checks.append(('ENV_FILE', env_exists))
    
    # 2. Check environment variables
    env_var_key, env_var_source = check_environment_variables()
    checks.append(('ENV_VARS', env_var_key is not None))
    
    # 3. Determine final API key
    final_api_key = env_var_key or env_api_key
    final_source = env_var_source or env_key_source
    
    # 4. Validate API key format
    valid_format = validate_api_key_format(final_api_key)
    checks.append(('API_FORMAT', valid_format))
    
    # 5. Test API connection
    api_works = test_api_connection(final_api_key)
    checks.append(('API_CONNECTION', api_works))
    
    # 6. Check imports
    imports_work = check_app_imports()
    checks.append(('IMPORTS', imports_work))
    
    # 7. Test local server
    server_running = test_local_server()
    checks.append(('LOCAL_SERVER', server_running))
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print("=" * 40)
    
    for check_name, result in checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:15} {status}")
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if final_api_key:
        print(f"API Key Source: {final_source}")
        print(f"API Key Preview: {final_api_key[:8]}...")
    
    # Recommendations
    generate_recommendations()

if __name__ == '__main__':
    main()
