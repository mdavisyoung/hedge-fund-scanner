"""Test script for xAI Grok API"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_xai_api():
    """Test the xAI Grok API connection"""
    api_key = os.getenv("XAI_API_KEY")
    base_url = "https://api.x.ai/v1/chat/completions"
    
    if not api_key:
        print("[ERROR] XAI_API_KEY not found in .env file")
        return False
    
    print(f"[OK] API Key found: {api_key[:10]}...{api_key[-5:]}")
    print(f"[OK] Testing connection to {base_url}...\n")
    
    try:
        response = requests.post(
            base_url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": "grok-3",
                "messages": [
                    {
                        "role": "user",
                        "content": "Say 'API test successful' if you can read this."
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 50
            },
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            message = result["choices"][0]["message"]["content"]
            print(f"\n[SUCCESS] API is working correctly!")
            print(f"Response: {message}\n")
            return True
        else:
            print(f"\n[ERROR] API returned status {response.status_code}")
            print(f"Response: {response.text}\n")
            return False
            
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"\n[ERROR] {str(e)}")
        return False
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("xAI Grok API Test")
    print("=" * 50)
    print()
    
    success = test_xai_api()
    
    if success:
        print("[SUCCESS] API test completed successfully!")
        print("You can now use the hedge fund app with AI-powered strategies.")
    else:
        print("[WARNING] API test failed. Please check your API key and try again.")
    
    print("=" * 50)

