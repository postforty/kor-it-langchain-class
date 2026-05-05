import requests
import json

url = "http://localhost:11434/api/rerank"
model = "dengcao/bge-reranker-v2-m3"
query = "배가 너무 고픈데 먹을 것 좀 추천해줘"
docs = ["점심 메뉴로는 따뜻한 국밥이나 비빔밥을 추천합니다.", "날씨가 좋네요."]

payload = {
    "model": model,
    "query": query,
    "documents": docs
}

print(f"Testing Ollama Rerank API with model: {model}")
try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Error Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
