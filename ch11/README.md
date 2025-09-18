### 의존성 설치

```bash
# jupyter notebook
uv add jupyter jupyterlab ipykernel

# https://python.langchain.com/docs/integrations/providers/google/
uv add langchain-google-genai

uv add python-dotenv

uv add pypdf langchain langchain_community

uv add langchain-ollama

uv add py-zerox

uv add nest_asyncio

uv add "unstructured[md]" nltk

uv add langchain-text-splitters

uv add beautifulsoup4

uv add langchain_postgres

# 비동기 HTTP 요청 처리
uv add httpx

# 도시 이름을 입력받아 위도와 경도를 반환하는 지오코딩 웹 서비스용 파이썬 클라이언트
uv add geopy
```

### 랭체인 구글 제미나이 임베딩

> 원문: <https://python.langchain.com/docs/integrations/text_embedding/google_generative_ai/>
