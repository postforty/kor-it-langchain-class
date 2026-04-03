# Ollama와 pgvector Docker Compose 연동하기

## 1. 개요

- Ollama는 로컬 환경에서 대규모 언어 모델(LLM)을 쉽게 실행할 수 있도록 돕는 솔루션이다.
- pgvector는 PostgreSQL에서 벡터 유사도 검색을 가능하게 하는 확장 기능이다.
- 이 글에서는 Docker Compose를 사용하여 Ollama와 pgvector를 함께 연동하는 방법을 다룬다.
- 모델 다운로드 방법부터 데이터베이스 설정까지 상세하게 설명하는 것이 목적이다.

## 2. 필요한 도구

### Docker

- 컨테이너화된 애플리케이션을 실행하기 위한 플랫폼
- Docker Desktop 설치 필요
- 설치: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

### Ollama

- 로컬 환경에서 대규모 언어 모델을 실행하기 위한 도구
- llama, gemma, qwen 등 다양한 오픈소스 모델 지원
- 간단한 명령어로 모델 다운로드 및 실행 가능
- 공식 사이트: [https://ollama.ai/](https://ollama.ai/)

### pgvector

- PostgreSQL을 위한 오픈소스 벡터 유사도 검색 확장 기능
- 임베딩 데이터를 저장하고 효율적으로 검색하는 데 사용됨

## 3. Docker Compose 파일 작성

- Ollama와 pgvector가 서로 통신할 수 있도록 같은 네트워크에 배치하는 것이 핵심이다.
- 아래는 Ollama와 pgvector를 연동하기 위한 `docker-compose.yml` 파일의 예시이다.

```yaml
services:
  ollama:
    image: ollama/ollama
    restart: always
    container_name: ollama
    ports:
      - "11434:11434"
    networks:
      - ollama_pgvector_net
    environment:
      - OLLAMA_HOST=0.0.0.0
    volumes:
      - C:/docker_data/ollama_models:/root/.ollama

  pgvector-db:
    image: pgvector/pgvector:pg17-trixie
    restart: always
    container_name: pgvector-db
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=langchain
      - POSTGRES_PASSWORD=langchain
      - POSTGRES_DB=vector_db
    volumes:
      - C:/docker_data/pgvector_data:/var/lib/postgresql/data
    networks:
      - ollama_pgvector_net

networks:
  ollama_pgvector_net:
    driver: bridge

volumes:
  pgvector_data:
  ollama_models:
```

- `ollama` 서비스에 설정된 `OLLAMA_HOST=0.0.0.0` 환경 변수는 컨테이너 외부에서의 접속을 허용하는 역할이다.
  | 서비스 | 기본 바인딩 | `0.0.0.0` 설정 필요 여부 | 이유 |
  | :--- | :--- | :--- | :--- |
  | **Ollama** | `127.0.0.1` | **필요** | 외부 및 컨테이너 간 통신을 허용하기 위함 |
  | **Postgres** | `0.0.0.0 (이미지 기본값)` | **불필요** | 이미 모든 네트워크 요청을 받도록 설정되어 있음 |
- `pgvector-db` 서비스는 `pgvector/pgvector:pg17-trixie` 이미지를 사용하며, PostgreSQL과 pgvector 확장 기능을 포함한다.
- `C:/docker_data/` 경로에 각 서비스의 데이터를 저장하여 컨테이너가 삭제되어도 데이터가 보존되도록 설정했다.
- `networks` 섹션의 `ollama_pgvector_net`을 통해 두 컨테이너가 서로의 이름을 호스트명처럼 사용하여 통신할 수 있다.


## 4. Docker Compose 기본 명령어 및 Ollama 모델 다운로드

### 4-1. Docker Compose 기본 명령어

- 작성된 `docker-compose.yml` 파일이 있는 디렉토리에서 다음 명령어를 실행한다.

#### 서비스 시작
```bash
docker compose up -d
```

#### 서비스 상태 확인
```bash
docker compose ps
```

#### 컨테이너 사용 중지
```bash
docker compose stop
```

#### 서비스 종료 (삭제)
```bash
docker compose down
```

### 4-2. Ollama 모델 다운로드

- `docker exec` 명령어를 사용하여 실행 중인 Ollama 컨테이너에 모델 다운로드 명령을 전달한다.

```bash
docker exec -it ollama ollama run gemma2:latest
```

- `ollama`는 컨테이너 이름이다.
- `ollama run gemma2:latest`는 컨테이너 내부에서 실행할 실제 명령이다.

## 5. 결론

- `docker-compose`를 사용하여 Ollama와 pgvector를 함께 구동하는 것은 로컬 RAG(Retrieval-Augmented Generation) 시스템을 구축하는 가장 효율적인 기초 작업이다.
- 이 구성을 통해 로컬 환경에서 외부 API 의존 없이 보안이 강화된 AI 애플리케이션을 개발할 수 있다.
