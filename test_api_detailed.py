"""Detailed test script for xAI Grok API"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_api_variations():
    """Test different API configurations"""
    api_key = os.getenv("XAI_API_KEY")
    
    if not api_key:
        print("[ERROR] XAI_API_KEY not found")
        return
    
    print(f"Testing API Key: {api_key[:15]}...{api_key[-10:]}")
    print(f"Key Length: {len(api_key)} characters\n")
    
    # Try different base URLs
    base_urls = [
        "https://api.x.ai/v1/chat/completions",
        "https://api.x.ai/v1/completions",
    ]
    
    # Try different models
    models = [
        "grok-beta",
        "grok-2",
        "grok",
    ]
    
    # Try with and without "xai-" prefix
    key_variations = [api_key]
    if api_key.startswith("xai-"):
        key_variations.append(api_key[4:])  # Without prefix
    
    for base_url in base_urls:
        for model in models:
            for key_var in key_variations:
                print(f"\nTesting: {base_url}")
                print(f"  Model: {model}")
                print(f"  Key format: {'with xai-' if key_var == api_key and api_key.startswith('xai-') else 'without xai-'}")
                
                try:
                    response = requests.post(
                        base_url,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {key_var}"
                        },
                        json={
                            "model": model,
                            "messages": [
                                {
                                    "role": "user",
                                    "content": "Hello"
                                }
                            ],
                            "max_tokens": 10
                        },
                        timeout=10
                    )
                    
                    print(f"  Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        print(f"  [SUCCESS] Working configuration found!")
                        print(f"  Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'N/A')}")
                        return True
                    elif response.status_code == 401:
                        print(f"  [AUTH ERROR] Unauthorized")
                    elif response.status_code == 400:
                        error_data = response.json() if response.text else {}
                        error_msg = error_data.get('error', response.text[:100])
                        print(f"  [CLIENT ERROR] {error_msg}")
                    else:
                        print(f"  [ERROR] {response.status_code}: {response.text[:100]}")
                        
                except Exception as e:
                    print(f"  [EXCEPTION] {str(e)[:100]}")
    
    return False

if __name__ == "__main__":
    print("=" * 60)
    print("xAI Grok API Detailed Test")
    print("=" * 60)
    print()
    
    success = test_api_variations()
    
    if not success:
        print("\n" + "=" * 60)
        print("RECOMMENDATIONS:")
        print("=" * 60)
        print("1. Verify your API key at https://console.x.ai/")
        print("2. Check if the key is activated and has credits")
        print("3. Ensure you're using the correct API endpoint")
        print("4. Check xAI documentation for any recent changes")
        print("=" * 60)

