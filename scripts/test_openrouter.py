#!/usr/bin/env python3
"""
Quick test script to verify OpenRouter API integration
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_openrouter_connection():
    try:
        # Get API key with fallback support
        api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
        
        # Initialize OpenRouter client
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        print("🧪 Testing OpenRouter connection...")
        
        # Test with a simple query
        response = client.chat.completions.create(
            model="anthropic/claude-3-haiku",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond in JSON format."},
                {"role": "user", "content": 'Please respond with: {"status": "success", "message": "OpenRouter is working!"}'}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "PDF Q&A System Test"
            }
        )
        
        result = response.choices[0].message.content
        print(f"✅ OpenRouter Response: {result}")
        return True
        
    except Exception as e:
        print(f"❌ OpenRouter test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing OpenRouter API Integration")
    print("=" * 50)
    
    # Check if API key is set (with fallback support)
    api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No API key found (OPENROUTER_API_KEY or OPENAI_API_KEY)")
        print("Please check your .env file")
    elif api_key == "your_openrouter_api_key_here":
        print("❌ Please update your .env file with a real OpenRouter API key")
        print("Get one from: https://openrouter.ai/keys")
    else:
        print(f"✅ API Key found: {api_key[:10]}...")
        test_openrouter_connection()
    
    print("=" * 50)
