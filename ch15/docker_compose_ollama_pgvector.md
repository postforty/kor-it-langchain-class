# Ollama 및 pgvector Docker Compose 연동하기

## 1. 개요

- Ollama는 로컬 환경에서 대규모 언어 모델(LLM)을 쉽게 실행할 수 있도록 돕는 솔루션이다.
- 이 글에서는 Docker Compose를 사용하여 Ollama와 pgvector를 함께 연동하는 방법을 다룬다.
- `localhost` 네트워크 통신 문제 해결부터 모델 다운로드 방법까지 상세하게 설명하는 것이 목적이다.

## 2. 필요한 도구

### Docker

- 컨테이너화된 애플리케이션을 실행하기 위한 플랫폼이다.
- Docker Desktop 설치가 필요하다.
- 설치: [https://docs.docker.com/get-docker/](https://docs.docker.com/get-docker/)

### Ollama

- 로컬 환경에서 대규모 언어 모델을 실행하기 위한 도구이다.
- llama, gemma, qwen 등 다양한 오픈소스 모델을 지원한다.
- 간단한 명령어로 모델 다운로드 및 실행이 가능하다.
- 공식 사이트: [https://ollama.ai/](https://ollama.ai/)

## 3\. Docker Compose 파일 작성

### 3-1. Ollama 단독 구성

- 아래는 Ollama를 구동하기 위한 `docker-compose.yml` 파일의 예시이다.

```yaml
services:
  ollama:
    image: ollama/ollama
    restart: always
    container_name: ollama
    ports:
      - "11434:11434"
    networks:
      - ollama_net
    environment:
      - OLLAMA_HOST=0.0.0.0
    volumes:
      - C:/docker_data/ollama_models:/root/.ollama

networks:
  ollama_net:
    driver: bridge

volumes:
  ollama_models:
```

- `networks` 섹션은 `ollama_net`이라는 커스텀 네트워크를 정의하는 부분이다.
- `ollama` 서비스에 설정된 `OLLAMA_HOST=0.0.0.0` 환경 변수는 컨테이너 외부에서의 접속을 허용하는 역할이다.

### 3-2. Ollama & pgvector 구성

- 아래는 pgvector를 추가한 `docker-compose.yml` 파일의 예시이다.

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
      - POSTGRES_DB=langchain_db
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

- `pgvector-db` 서비스 추가: `pgvector/pgvector:pg17-trixie` 이미지를 사용하는 `pgvector-db`라는 새 서비스를 추가했다. 이 서비스는 PostgreSQL과 pgvector 확장 기능을 포함한다.
- 환경변수 설정: `pgvector-db` 서비스에 `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` 환경변수를 설정하여 데이터베이스 사용자, 비밀번호, 데이터베이스 이름을 정의했다.
- 볼륨 추가: `C:/docker_data/`경로에 `pgvector_data`라는 새 볼륨을 추가하여 pgvector 데이터가 컨테이너를 다시 시작해도 유지되도록 설정했다. `shared`는 로컬 파일을 불러오기 위해 추가했다.

## 3\. Docker Compose 기본 명령어 및 Ollama 모델 다운로드

### 3-1. Docker Compose 기본 명령어(참고)

- 작성된 `docker-compose.yml` 파일이 있는 디렉토리에서 다음 명령어를 실행하면 n8n과 Ollama 컨테이너가 동시에 구동된다.

#### 서비스 시작

```bash
docker compose up -d
```

- `-d` 옵션은 컨테이너를 백그라운드에서 실행하도록 한다.
- 현재 위치한 폴더명을 기본 **프로젝트 이름**을 사용한다.

#### 서비스 상태 확인

```bash
docker compose ps
```

#### 로그 확인

```bash
docker compose logs
```

#### 이미지 업데이트

- 서비스에서 사용하는 이미지를 최신 버전으로 내려받는다.

```bash
docker compose pull
```

#### 컨테이너 사용 중지

```bash
docker compose stop
```

#### 서비스 종료

- 실행 중인 서비스를 중지하고 컨테이너, 네트워크 등을 **모두 삭제**한다.

```bash
docker compose down
```

### 3-2. Ollama 모델 다운로드

- `docker-compose`로 Ollama가 실행 중인 상태에서 모델을 다운로드하려면, `docker exec` 명령어를 사용해야 한다.
- 이 명령어는 실행 중인 컨테이너에 직접 명령을 전달하는 역할을 한다.

#### 방법1

```bash
docker exec -it ollama ollama run gemma3n:latest
```

- `ollama`는 컨테이너 이름이다.
- `ollama run gemma3n:latest`는 컨테이너 내부에서 실행할 실제 명령이다(예: `gemma3n:latest` 모델 설치).

#### 방법2

```bash
docker exec -it ollama bash

ollama run gemma3n:latest

ollama
```

- 그 밖의 명령어는 Github 참고(<https://github.com/ollama/ollama>)

## 4. 도커 볼륨 관리 명령어

Named Volume은 도커 데몬에 의해 관리되므로, 터미널 명령어를 통해 관리해야 한다.

### 4.1. 볼륨 목록 확인

시스템에 존재하는 모든 Named Volume 목록을 확인한다.

```bash
docker volume ls
```

### 4.2. 볼륨 상세 정보 확인

특정 볼륨의 상세 정보(VM 내부의 실제 마운트 경로 포함)를 확인한다.

```bash
docker volume inspect pgvector_data
docker volume inspect ollama_models
```

### 4.3. 볼륨 삭제

컨테이너가 삭제되어 더 이상 사용되지 않는 Named Volume을 명시적으로 제거하여 디스크 공간을 확보한다.

```bash
docker volume rm pgvector_data
docker volume rm ollama_models
```

### 4.4. 사용되지 않는 볼륨 일괄 정리

어떤 컨테이너에도 연결되어 있지 않은 모든 Named Volume을 일괄적으로 삭제한다.

```bash
docker volume prune
```

**참고**: 도커 애플리케이션을 삭제한다고 해서 Named Volume은 자동으로 삭제되지 않는다. 데이터 영속성 유지를 위한 도커의 정책이다. 디스크 공간 확보를 위해서는 `docker volume rm` 또는 `docker volume prune` 명령어를 반드시 사용해야 한다.

## 5. 결론

- `docker-compose`를 사용하여 Ollama와 pgvector를 함께 구동하는 것은 로컬 LLM 환경을 구축하는 가장 효율적인 방법 중 하나이다.
- 컨테이너 간의 네트워크 문제를 해결하고, `docker exec`를 통해 컨테이너 내부에서 모델을 관리하는 방법을 익히는 것이 중요하다.
- 이 방식을 통해 안정적인 환경에서 다양한 LLM 모델을 활용할 수 있다.
