import requests
url = "http://localhost:11434/api/version"
try:
    response = requests.get(url)
    print(f"Ollama Version: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
