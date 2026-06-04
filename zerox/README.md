## 의존성 설치

### 1. UV

```bash
# jupyter notebook
uv add jupyter jupyterlab ipykernel

# https://python.langchain.com/docs/integrations/providers/google/
uv add langchain-google-genai

uv add python-dotenv

uv add ddgs

uv add pypdf langchain langchain_community

uv add langgraph

uv add langchain-ollama

uv add langchain-text-splitters

uv add beautifulsoup4

# 비동기 HTTP 요청 처리
uv add httpx

# 도시 이름을 입력받아 위도와 경도를 반환하는 지오코딩 웹 서비스용 파이썬 클라이언트
uv add geopy

uv add selenium

uv add pyppeteer

uv add yfinance
```

---

### 2. pyenv

#### 1) 가상환경 생성 및 실행

```bash
# 가상환경 생성
# python -m venv 가상환경이름
python -m venv ch11_venv

# 가상환경 실행
ch11_venv\Scripts\activate.bat

# 가상환경 해제
ch11_venv\Scripts\deactivate.bat
```

#### 2) 의존성 설치

```bash
# jupyter notebook
pip install jupyter jupyterlab ipykernel

# https://python.langchain.com/docs/integrations/providers/google/
pip install langchain-google-genai

pip install python-dotenv

pip install langchain langchain_community

pip install langgraph

pip install beautifulsoup4

# 비동기 HTTP 요청 처리
pip install httpx

# 도시 이름을 입력받아 위도와 경도를 반환하는 지오코딩 웹 서비스용 파이썬 클라이언트
pip install geopy

pip install selenium

pip install pyppeteer
```

#### 3) 의존성 관리

```bash
# requirements.txt 내보내기
pip freeze > requirements.txt

# requirements.txt 설치하기
pip install -r requirements.txt
```
