# 무료로 한국어🇰🇷 파인튜닝 모델 받아서 나만의 로컬 LLM 호스팅 하기(LangServe) + RAG 까지!!

## 공시 홈페이지

- 링크: https://python.langchain.com/docs/langserve/

## LangServe 에서 Ollama 체인 생성

app 폴더 진입 후

```bash
uv run server.py
```

## ngrok 에서 터널링(포트 포워드)

```bash
ngrok http localhost:8000
```

![](./images/capture-20240411-035817.png)

NGROK 도메인 등록 링크: https://dashboard.ngrok.com/cloud-edge/domains

> 고정 도메인이 있는 경우

```bash
ngrok http --domain=poodle-deep-marmot.ngrok-free.app 8000
```

## GPU 사용량 모니터링

Github Repo: https://github.com/tlkh/asitop

```bash
pip install asitop
```

패스워드 설정

```bash
sudo asitop
```

실행

```bash
asitop
```

## License

소스코드를 활용하실 때는 반드시 출처를 표기해 주시기 바랍니다.

```
MIT License

Copyright (c) 2024, 테디노트

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of
```
