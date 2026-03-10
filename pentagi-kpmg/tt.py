"""
Test different KPMG API endpoint variations to find the correct one
"""
import requests
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Your configuration
SUBSCRIPTION_KEY = "7605a04d3fc44736a5bc86de1849d120"
CHARGE_CODE = "MFLK01"
MODEL = "gpt-4o-2024-11-20-dzs-we"

# Test payload
payload = {
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 10
}

# Different endpoint variations to test
endpoints = [
    # Original Azure OpenAI format
    ("Azure Standard", 
     f"https://api.workbench.kpmg/genai/azure/deployments/{MODEL}/chat/completions?api-version=2024-06-01"),
    
    # KPMG Inference format (your original)
    ("KPMG Inference", 
     "https://api.workbench.kpmg/genai/azure/inference/chat/completions?api-version=2024-04-01-preview"),
    
    # OpenAI with deployments
    ("OpenAI Deployments", 
     f"https://api.workbench.kpmg/genai/azure/openai/deployments/{MODEL}/chat/completions?api-version=2024-06-01"),
    
    # Without deployments
    ("Direct Chat", 
     "https://api.workbench.kpmg/genai/azure/chat/completions?api-version=2024-06-01"),
    
    # Inference with model in body
    ("Inference + Model",
     "https://api.workbench.kpmg/genai/azure/inference/chat/completions?api-version=2024-06-01"),
]

def test_endpoint(name, url, include_model_in_body=False):
    """Test an endpoint variation"""
    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")
    print(f"URL: {url}")
    
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
        "x-kpmg-charge-code": CHARGE_CODE,
    }
    
    test_payload = payload.copy()
    if include_model_in_body:
        test_payload["model"] = MODEL
        print(f"Model in body: {MODEL}")
    else:
        print(f"Model in URL: {MODEL}")
    
    try:
        response = requests.post(
            url,
            headers=headers,
            json=test_payload,
            verify=False,
            timeout=30
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✅✅✅ SUCCESS! This endpoint works!")
            print(f"\nResponse preview:")
            print(json.dumps(response.json(), indent=2)[:500])
            return True
        elif response.status_code == 401:
            print(f"❌ 401 Unauthorized - Invalid subscription key")
        elif response.status_code == 403:
            print(f"❌ 403 Forbidden - Valid key but no access to this endpoint")
        elif response.status_code == 404:
            print(f"❌ 404 Not Found - Endpoint doesn't exist")
        else:
            print(f"❌ {response.status_code} - {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

# Test all endpoints
print("="*70)
print("KPMG API Endpoint Discovery")
print("="*70)
print(f"Subscription Key: {'*' * 20}...{SUBSCRIPTION_KEY[-4:]}")
print(f"Charge Code: {CHARGE_CODE}")
print(f"Model: {MODEL}")

success = False
for name, url in endpoints:
    # Test without model in body
    if test_endpoint(name, url, include_model_in_body=False):
        success = True
        break
    
    # If it's an inference endpoint, also try with model in body
    if "inference" in url.lower():
        if test_endpoint(f"{name} (model in body)", url, include_model_in_body=True):
            success = True
            break

if success:
    print("\n" + "="*70)
    print("✅ FOUND WORKING ENDPOINT!")
    print("="*70)
else:
    print("\n" + "="*70)
    print("❌ No working endpoint found")
    print("="*70)
    print("\nNext steps:")
    print("1. Check F12 Network tab in browser for exact URL")
    print("2. Verify subscription key is complete and correct")
    print("3. Confirm charge code format with KPMG IT")
    print("4. Check if your subscription has access to this API product")