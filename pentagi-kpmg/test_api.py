import requests
import json

def test_injector():
    url = "http://localhost:8080/v1/chat/completions"
    
    payload = {
        "model": "gpt-4o-2024-11-20-dzs-we",
        "messages": [
            {
                "role": "user",
                "content": "Hello from PentAGI"
            }
        ],
        "max_tokens": 50
    }
    
    print("=" * 70)
    print("Testing KPMG Injector")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"\nRequest Body:")
    print(json.dumps(payload, indent=2))
    print("\nSending request...")
    print("=" * 70)
    
    try:
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("\n🎉 SUCCESS! Response:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\n❌ ERROR: Status {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("Is the injector running? Check: docker compose ps")
    except requests.exceptions.Timeout:
        print(f"\n❌ Timeout after 60 seconds")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    test_injector()