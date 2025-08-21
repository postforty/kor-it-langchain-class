### 랭체인 구글 제미나이 의존성 설치

> 원문: <https://python.langchain.com/docs/integrations/providers/google/>

```bash
# jupyter notebook
uv add jupyter jupyterlab ipykernel

uv add docling

uv add langchain langchain-google-genai langchain_community

uv add python-dotenv

# ZoneInfoNotFoundError 발생시 설치
# - zoneinfo은 시간대 정보를 위해 tzdata 패키지에 의존함
uv add tzdata

# yfinance: 야후 파이낸스 API를 사용하여 주식 데이터를 조회하는 데 사용
uv add yfinance

uv add streamlit

# tabulate: pandas 라이브러리의 to_markdown() 함수가 데이터를 표 형식으로 변환하기 위해 필요
uv add tabulate

uv add pymupdf faiss-cpu

uv add langchain_upstage
```
