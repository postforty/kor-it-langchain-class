### 랭체인 구글 제미나이 의존성 설치

> 원문: <https://python.langchain.com/docs/integrations/providers/google/>

```bash
# jupyter notebook
uv add jupyter jupyterlab ipykernel

# langchain & langchain-google-genai
uv add langchain langchain-google-genai

# python-dotenv
uv add python-dotenv
```

```bash
# ZoneInfoNotFoundError 발생시 설치
# - zoneinfo은 시간대 정보를 위해 tzdata 패키지에 의존함
uv add tzdata
```

```bash
# yfinance: 야후 파이낸스 API를 사용하여 주식 데이터를 조회하는 데 사용
uv add yfinance
```
