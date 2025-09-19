### 의존성 설치

```bash
# jupyter notebook
uv add jupyter jupyterlab ipykernel

# https://python.langchain.com/docs/integrations/providers/google/
uv add langchain-google-genai

uv add python-dotenv

# ZoneInfoNotFoundError 발생시 설치
# - zoneinfo은 시간대 정보를 위해 tzdata 패키지에 의존함
uv add tzdata

# yfinance: 야후 파이낸스 API를 사용하여 주식 데이터를 조회하는 데 사용
uv add yfinance

# tabulate: pandas 라이브러리의 to_markdown() 함수가 데이터를 표 형식으로 변환하기 위해 필요
uv add tabulate

uv add pypdf langchain langchain_community

uv add langchain-ollama

uv add nest_asyncio

uv add "unstructured[md]" nltk

uv add langchain-text-splitters

uv add beautifulsoup4

uv add langchain_postgres

# 비동기 HTTP 요청 처리
uv add httpx

# 도시 이름을 입력받아 위도와 경도를 반환하는 지오코딩 웹 서비스용 파이썬 클라이언트
uv add geopy

uv add selenium

uv add fastmcp
```
