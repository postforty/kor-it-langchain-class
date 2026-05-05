import requests
import json

url = "http://localhost:11434/api/tags"
print("Fetching Ollama models...")
try:
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json().get("models", [])
        for m in models:
            print(f"- {m['name']}")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
