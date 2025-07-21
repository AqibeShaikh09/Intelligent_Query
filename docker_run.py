#!/usr/bin/env python3
"""
Portable entry point for the PDF Q&A System
This script ensures the application works in any Docker environment
"""

import os
import sys
import subprocess
import time

def setup_python_path():
    """Setup Python path to ensure imports work correctly"""
    # Get the current script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add src directory to Python path
    src_dir = os.path.join(script_dir, 'src')
    if os.path.exists(src_dir) and src_dir not in sys.path:
        sys.path.insert(0, src_dir)
        print(f"✅ Added {src_dir} to Python path")
    
    # Set PYTHONPATH environment variable
    current_pythonpath = os.environ.get('PYTHONPATH', '')
    new_pythonpath = f"{src_dir}:{script_dir}:{current_pythonpath}".strip(':')
    os.environ['PYTHONPATH'] = new_pythonpath
    print(f"✅ Set PYTHONPATH to: {new_pythonpath}")

def check_dependencies():
    """Check if all required dependencies are available"""
    required_modules = [
        'flask', 'werkzeug', 'requests', 'pdfplumber', 
        'faiss-cpu', 'sentence_transformers', 'numpy'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module.replace('-', '_'))
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"❌ Missing dependencies: {', '.join(missing_modules)}")
        print("Please install them with: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are available")
    return True

def check_environment():
    """Check environment variables and configuration"""
    # Check for API key with fallback support
    api_key_found = bool(os.environ.get('OPENROUTER_API_KEY') or os.environ.get('OPENAI_API_KEY'))
    warnings = []
    
    if not api_key_found:
        warnings.append("⚠️  No API key found (OPENROUTER_API_KEY or OPENAI_API_KEY)")
    elif os.environ.get('OPENAI_API_KEY') and not os.environ.get('OPENROUTER_API_KEY'):
        warnings.append("⚠️  Using OPENAI_API_KEY - Consider renaming to OPENROUTER_API_KEY")
    
    if warnings:
        print("\n".join(warnings))
        print("💡 Create a .env file with your API keys")
    else:
        print("✅ Environment variables are configured")
    
    return len(warnings) == 0

def start_application():
    """Start the Flask application"""
    print("🚀 Starting PDF Q&A System...")
    
    # Setup Python path
    setup_python_path()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment (warnings only, don't exit)
    check_environment()
    
    # Get port from environment
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🌐 Starting server on {host}:{port}")
    print(f"🔧 Environment: {os.environ.get('FLASK_ENV', 'development')}")
    
    try:
        # Try to import and run the Flask app
        sys.path.insert(0, 'src')
        from web_app import app
        
        # Run the application
        app.run(
            host=host,
            port=port,
            debug=os.environ.get('FLASK_ENV') == 'development',
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure src/web_app.py and src/app.py exist")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_application()
