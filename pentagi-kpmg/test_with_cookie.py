import requests
import json

# Your auth cookie from browser
AUTH_COOKIE = "s%3Ae%3Aede0705e50f2caba4638ffc7373144e7%3A1becf94d6c76afea1718b69d78cc978f03c4015e651b3f6fd84ae73bcda1f6f0bedac311fc0b79b63e6347f04182beada7c516747f583185b458101fdd6019cbb6b90d77622cd31757e4ffcf9e9de6895b7da2393525f3398d0c439d503f01da5ad0f0886d84bef6bf5b1d9a3430ea66b3f9da0d12a0bec6a52ab6e0ff32d58e.xn1pJm4FlM%2BZ9CZkse16UrCCHdgD2TSTdpH3lI00QU0"

# Your subscription key
SUBSCRIPTION_KEY = "YOUR_NEW_SUBSCRIPTION_KEY_HERE"  # ← PUT YOUR NEW KEY HERE

url = "https://api.workbench.kpmg/genai/azure/inference/chat/completions"

payload = {
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 50
}

headers = {
    "Content-Type": "application/json",
    "Ocp-Apim-Subscription-Key": SUBSCRIPTION_KEY,
    "Cookie": f"auth={AUTH_COOKIE}",
    "x-kpmg-charge-code": "MFLK01",
    "azureml-model-deployment": "gpt-4"
}

print(f"🔍 Testing with Cookie + Subscription Key")
print(f"URL: {url}")

try:
    response = requests.post(
        url,
        json=payload,
        headers=headers,
        verify=False,
        timeout=30
    )
    
    print(f"\n✅ Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"🎉🎉🎉 SUCCESS!")
        print(json.dumps(response.json(), indent=2))
    else:
        print(f"❌ Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {e}")