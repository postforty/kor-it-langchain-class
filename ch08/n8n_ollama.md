# n8n과 Ollama Docker Compose 연동하기

## 1\. 개요

- n8n은 워크플로우 자동화를 위한 강력한 도구이다.
- Ollama는 로컬 환경에서 대규모 언어 모델(LLM)을 쉽게 실행할 수 있도록 돕는 솔루션이다.
- 이 글에서는 Docker Compose를 사용하여 n8n과 Ollama를 함께 연동하는 방법을 다룬다.
- `localhost` 네트워크 통신 문제 해결부터 모델 다운로드 방법까지 상세하게 설명하는 것이 목적이다.

## 2\. 필요한 도구

### Docker

- 컨테이너화된 애플리케이션을 실행하기 위한 플랫폼
- Docker Desktop 설치 필요
- 설치: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

### n8n

- 노드 기반 워크플로우 자동화 도구
- 다양한 서비스와 API를 연결하여 자동화 워크플로우 구성 가능
- 웹 기반 UI를 통한 직관적인 워크플로우 편집
- 공식 사이트: [https://n8n.io/](https://n8n.io/)

### Ollama

- 로컬 환경에서 대규모 언어 모델을 실행하기 위한 도구
- llama, gemma, qwen 등 다양한 오픈소스 모델 지원
- 간단한 명령어로 모델 다운로드 및 실행 가능
- 공식 사이트: [https://ollama.ai/](https://ollama.ai/)

## 3\. Docker Compose 파일 작성

- n8n과 Ollama가 서로 통신할 수 있도록 같은 네트워크에 배치하는 것이 핵심이다.
- 아래는 n8n과 Ollama를 연동하기 위한 `docker-compose.yml` 파일의 예시이다.

```yaml
version: "3.8"

services:
  n8n:
    image: n8nio/n8n
    restart: always
    container_name: n8n
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - n8n_ollama_net

  ollama:
    image: ollama/ollama
    restart: always
    container_name: ollama
    ports:
      - "11434:11434"
    networks:
      - n8n_ollama_net
    environment:
      - OLLAMA_HOST=0.0.0.0

networks:
  n8n_ollama_net:
    driver: bridge

volumes:
  n8n_data:
```

- `networks` 섹션은 `n8n_ollama_net`이라는 커스텀 네트워크를 정의하는 부분이다.
- 각 서비스(`n8n`과 `ollama`)는 이 네트워크에 연결되어 서로의 컨테이너 이름을 통해 통신할 수 있다.
- `ollama` 서비스에 설정된 `OLLAMA_HOST=0.0.0.0` 환경 변수는 컨테이너 외부에서의 접속을 허용하는 역할이다.

## 3\. Docker Compose 실행 및 Ollama 모델 다운로드

1.  **Docker Compose 실행**

- 작성된 `docker-compose.yml` 파일이 있는 디렉토리에서 다음 명령어를 실행하면 n8n과 Ollama 컨테이너가 동시에 구동된다.

```bash
docker-compose up -d

# 최신 Docker 버전에서 권장되는 방식
docker compose up -d
```

- `-d` 옵션은 컨테이너를 백그라운드에서 실행하도록 한다.

2.  **Ollama 모델 다운로드**

- `docker-compose`로 Ollama가 실행 중인 상태에서 모델을 다운로드하려면, `docker exec` 명령어를 사용해야 한다.
- 이 명령어는 실행 중인 컨테이너에 직접 명령을 전달하는 역할을 한다.

```bash
docker exec -it ollama ollama pull llama3
```

- `ollama`는 컨테이너 이름이다.
- `ollama pull llama3`는 컨테이너 내부에서 실행할 실제 명령이다(예: `llama3` 모델 설치).

## 4\. n8n 워크플로우 구성

- n8n UI에 접속하여 새로운 워크플로우를 만든다.
- **Ollama Chat Model** 노드를 추가하고, 다음과 같이 설정한다.
  1.  **Credentials**: `http://ollama:11434`
  2.  **Model**: 다운로드한 모델의 이름을 입력한다. (예: `llama3`)
  3.  **Prompt**: LLM에게 전달할 프롬프트를 작성한다.

## 5\. 결론

- `docker-compose`를 사용하여 n8n과 Ollama를 함께 구동하는 것은 로컬 LLM 워크플로우를 구축하는 가장 효율적인 방법 중 하나이다.
- 컨테이너 간의 네트워크 문제를 해결하고, `docker exec`를 통해 컨테이너 내부에서 모델을 관리하는 방법을 익히는 것이 중요하다.
- 이 방식을 통해 안정적인 환경에서 다양한 LLM 모델을 n8n 워크플로우에 활용할 수 있다.
