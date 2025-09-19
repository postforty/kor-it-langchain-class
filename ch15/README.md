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

uv add langgraph

uv add fastmcp

# https://github.com/langchain-ai/langchain-mcp-adapters
uv add langchain-mcp-adapters

uv add langchain-google-vertexai
```
