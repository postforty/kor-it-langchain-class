## Ollama

**로컬 환경**에서 대규모 언어 모델(LLM)을 쉽게 실행할 수 있도록 돕는 도구이다.

### 설치 명령

도커(Docker)를 이용한 설치 명령이다.

> 참고: <https://hub.docker.com/r/ollama/ollama>

```bash
docker run -d -v C:/docker_data/ollama_models:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

| **명령어/옵션**                                 | **설명**                                                                                    |
| :---------------------------------------------- | :------------------------------------------------------------------------------------------ |
| `docker run`                                    | 컨테이너를 생성하고 실행하는 명령어                                                         |
| `-d`                                            | 컨테이너를 백그라운드에서 실행하는 옵션                                                     |
| `-v C:/docker_data/ollama_models:/root/.ollama` | 호스트 PC의 디렉터리를 컨테이너 내부 디렉터리에 연결하는 볼륨 마운트 설정(데이터 영구 저장) |
| `-p 11434:11434`                                | 호스트 PC의 포트와 컨테이너 내부의 포트를 연결하는 포트 매핑                                |
| `--name ollama`                                 | 컨테이너에 `ollama`라는 이름을 부여하는 옵션                                                |
| `ollama/ollama`                                 | 컨테이너를 만드는 데 사용되는 Docker 이미지의 이름                                          |
