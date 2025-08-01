#!/usr/bin/env python3
"""
Test script to verify the Docker setup works correctly
"""

import sys
import os
import subprocess
import time
import requests

def test_docker_build():
    """Test if Docker image builds successfully"""
    print("🏗️  Testing Docker build...")
    try:
        result = subprocess.run(
            ["docker", "build", "-t", "pdf-qa-test", "."],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode == 0:
            print("✅ Docker build successful")
            return True
        else:
            print(f"❌ Docker build failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Docker build error: {e}")
        return False

def test_docker_run():
    """Test if Docker container runs successfully"""
    print("🚀 Testing Docker run...")
    try:
        # Stop any existing container
        subprocess.run(["docker", "stop", "pdf-qa-test-container"], 
                      capture_output=True)
        subprocess.run(["docker", "rm", "pdf-qa-test-container"], 
                      capture_output=True)
        
        # Start new container
        result = subprocess.run([
            "docker", "run", "-d",
            "--name", "pdf-qa-test-container",
            "-p", "5001:5000",
            "-e", "OPENROUTER_API_KEY=test-key",
            "pdf-qa-test"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Docker container started")
            
            # Wait for container to be ready
            print("⏳ Waiting for container to be ready...")
            time.sleep(10)
            
            # Test health endpoint
            try:
                response = requests.get("http://localhost:5001/status", timeout=10)
                if response.status_code == 200:
                    print("✅ Container is healthy and responding")
                    return True
                else:
                    print(f"❌ Container health check failed: {response.status_code}")
                    return False
            except Exception as e:
                print(f"❌ Cannot connect to container: {e}")
                return False
        else:
            print(f"❌ Docker run failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Docker run error: {e}")
        return False
    finally:
        # Cleanup
        subprocess.run(["docker", "stop", "pdf-qa-test-container"], 
                      capture_output=True)
        subprocess.run(["docker", "rm", "pdf-qa-test-container"], 
                      capture_output=True)

def test_import_locally():
    """Test if imports work locally"""
    print("🐍 Testing Python imports...")
    try:
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # Test the smart import function
        try:
            from src.web_app import import_app_module
        except ModuleNotFoundError as e:
            raise ImportError(f"Could not find 'web_app.py' in {src_path}. Please ensure the file exists.") from e
        extract_text_from_pdf, create_document_embeddings, generate_response = import_app_module()
        
        print("✅ Local imports working correctly")
        return True
    except Exception as e:
        print(f"❌ Local import error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing PDF Q&A System Docker Setup")
    print("=" * 50)
    
    tests = [
        ("Python Imports", test_import_locally),
        ("Docker Build", test_docker_build),
        ("Docker Run", test_docker_run),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running test: {test_name}")
        if test_func():
            passed += 1
        else:
            print(f"💥 Test failed: {test_name}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your Docker setup is ready for deployment.")
        print("🚀 Users can now pull and run your Docker image without issues.")
    else:
        print("❌ Some tests failed. Please fix the issues before deployment.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
