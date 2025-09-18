# 사내 RAG 챗봇 - 기술 설계 문서

## 1. 개요

이 문서는 '사내 RAG 챗봇' 프로젝트의 기술적 설계와 아키텍처를 정의한다. `prd.md`에 명시된 요구사항을 충족하기 위해 시스템을 구성하는 각 컴포넌트의 역할, 상호작용 방식, 그리고 구현에 사용될 기술 스택에 대해 상세히 기술한다.

## 2. 시스템 아키텍처

본 시스템은 분산 컴퓨팅 모델을 기반으로 하며, **클라이언트 애플리케이션**, **벡터 검색 API 서버**, **데이터베이스**의 세 가지 주요 컴포넌트로 구성된다.

### 2.1. 아키텍처 다이어그램

```mermaid
graph TD
    subgraph "사용자 PC (100대)"
        Client[클라이언트 앱 (Tkinter)] -- 1. 질문 전송 (HTTP Request) --> API_Server
        Client -- 5. LLM 답변 생성 --> LLM[Ollama (Local LLM)]
        Client -- 6. UI에 답변 표시 --> User([사용자])
    end

    subgraph "서버 PC (1대)"
        API_Server[벡터 검색 API 서버 (FastAPI)] -- 2. 질문 벡터화 --> Ollama_Embed[Ollama (Embedding Model)]
        API_Server -- 3. 벡터 검색 --> DB[(PGVector DB)]
        DB -- 4. 유사 문서 반환 --> API_Server
    end

    User -- 질문 입력 --> Client
    API_Server -- 4. 검색된 문서 반환 (HTTP Response) --> Client
    LLM -- 답변 --> Client
```

### 2.2. 데이터 흐름

1.  **질문 입력**: 사용자가 윈도우 클라이언트 앱(Tkinter)에 질문을 입력한다.
2.  **문서 검색 요청**: 클라이언트 앱은 FastAPI로 구축된 API 서버의 `/search` 엔드포인트로 사용자의 질문을 담아 HTTP 요청을 보낸다.
3.  **검색 및 반환**: API 서버는 수신된 질문을 Ollama 임베딩 모델을 사용해 벡터로 변환하고, 이 벡터를 사용해 PGVector DB에서 가장 유사한 문서 청크들을 검색한다. 검색된 문서 텍스트를 클라이언트 앱에 HTTP 응답으로 반환한다.
4.  **프롬프트 구성**: 클라이언트 앱은 서버로부터 받은 문서(맥락)와 사용자의 원본 질문을 조합하여 LLM에 전달할 프롬프트를 생성한다.
5.  **답변 생성**: 구성된 프롬프트를 로컬에 설치된 Ollama LLM으로 전달하여 최종 답변을 생성한다.
6.  **답변 표시**: 생성된 답변을 클라이언트 앱의 UI에 표시하여 사용자에게 보여준다.

## 3. 컴포넌트별 상세 설계

### 3.1. 데이터베이스 (PostgreSQL + PGVector)

- **역할**: 내부 지식 문서의 텍스트와 해당 텍스트의 벡터 임베딩을 저장하고, 유사도 검색 기능을 제공한다.
- **기술**: `PostgreSQL` + `PGVector` 확장
- **테이블 스키마**: `documents` 테이블
  | 컬럼명 | 데이터 타입 | 설명 |
  | --- | --- | --- |
  | `id` | `SERIAL PRIMARY KEY` | 각 문서 청크의 고유 식별자 |
  | `content` | `TEXT NOT NULL` | 원본 문서 청크 텍스트 |
  | `embedding` | `vector(768)` | `content`를 임베딩한 벡터 (사용 모델에 따라 차원 수 변경) |
  | `source` | `VARCHAR(255)` | 문서 출처 (예: 파일 경로) |
  | `created_at` | `TIMESTAMP` | 데이터 생성 시각 |
- **인덱싱**: `embedding` 컬럼에 HNSW 인덱스를 생성하여 대규모 데이터에서도 빠른 검색 속도를 보장한다.

### 3.2. 벡터 검색 API 서버 (FastAPI)

- **역할**: 클라이언트로부터 검색 요청을 받아 데이터베이스에서 관련 문서를 찾아 반환하는 중간 다리 역할을 한다.
- **기술**: `Python`, `FastAPI`, `Ollama`, `psycopg2`
- **API 엔드포인트**:
  - **`POST /search`**
    - **Request Body**:
      ```json
      {
        "query": "사용자의 질문 텍스트"
      }
      ```
    - **Response Body (Success)**:
      ```json
      {
        "documents": [
          "검색된 첫 번째 문서 청크 텍스트입니다.",
          "검색된 두 번째 문서 청크 텍스트입니다.",
          "..."
        ]
      }
      ```
    - **동작 로직**:
      1.  Request Body에서 `query`를 추출한다.
      2.  Ollama 임베딩 모델(`nomic-embed-text`)을 호출하여 `query`를 벡터로 변환한다.
      3.  PGVector DB에 연결하여 변환된 벡터와 코사인 유사도가 가장 높은 상위 N개의 `documents`를 검색한다.
      4.  검색된 문서의 `content`들을 리스트에 담아 JSON 형식으로 반환한다.

### 3.3. 클라이언트 애플리케이션 (Tkinter + LangGraph)

- **역할**: 사용자에게 GUI를 제공하고, 전체 RAG 프로세스를 조율(Orchestration)한다.
- **기술**: `Python`, `Tkinter`, `LangGraph`, `Ollama`, `requests`

#### 3.3.1. UI (Tkinter)

- `main.py`에서 구현된 기본 구조를 기반으로 한다.
- **주요 원칙**: UI의 반응성을 유지하기 위해 시간이 소요되는 작업(API 요청, LLM 추론)은 반드시 별도의 스레드(Thread)에서 처리한다. UI 업데이트는 메인 스레드에서 안전하게 수행한다.

#### 3.3.2. RAG 흐름 (LangGraph)

- LangGraph를 사용하여 상태 기반의 RAG 파이프라인을 구축한다. 이는 흐름의 각 단계를 명확하게 정의하고, 확장성을 용이하게 한다.

- **상태 (State) 정의**: 각 단계에서 공유될 데이터 구조

  ```python
  from typing import List, TypedDict

  class GraphState(TypedDict):
      question: str      # 사용자 원본 질문
      documents: List[str] # 검색된 문서 리스트
      answer: str        # LLM이 생성한 최종 답변
  ```

- **노드 (Nodes) 정의**: 그래프의 각 작업 단위

  1.  **`retrieve` (문서 검색 노드)**:
      - 입력: `state['question']`
      - 동작: FastAPI 서버의 `/search` 엔드포인트에 `question`을 전송하여 문서를 요청한다.
      - 출력: `{'documents': [검색된 문서들]}` 형태로 상태를 업데이트한다.
  2.  **`generate` (답변 생성 노드)**:
      - 입력: `state['question']`, `state['documents']`
      - 동작:
        - `documents`와 `question`을 조합하여 프롬프트를 생성한다.
        - 로컬 Ollama LLM(`gemma:2b`)을 호출하여 답변을 생성한다.
      - 출력: `{'answer': '생성된 답변'}` 형태로 상태를 업데이트한다.
  3.  **`fallback` (대체 응답 노드)**:
      - `retrieve` 노드에서 문서를 찾지 못했을 경우 실행된다.
      - 동작: "관련 정보를 찾을 수 없습니다."와 같은 고정된 메시지를 생성한다.
      - 출력: `{'answer': '고정 메시지'}` 형태로 상태를 업데이트한다.

- **엣지 (Edges) 정의**: 노드 간의 연결 관계
  - **`Entry Point` -> `retrieve`**: 워크플로우 시작
  - **`retrieve` -> `Conditional Edge`**: `documents`가 비어 있는지 여부에 따라 분기
    - `documents` 존재 시 -> `generate`
    - `documents` 비어 있을 시 -> `fallback`
  - **`generate` -> `END`**: 워크플로우 종료
  - **`fallback` -> `END`**: 워크플로우 종료

## 4. 주요 기술 결정 및 이유

- **PGVector**: 널리 사용되는 PostgreSQL 위에서 동작하여 안정적이고, 다른 관계형 데이터와 함께 관리하기 용이하다.
- **FastAPI**: Python 기반 웹 프레임워크 중 성능이 매우 뛰어나고, 자동 API 문서 생성을 지원하여 개발 및 협업에 효율적이다.
- **Ollama**: 다양한 오픈소스 LLM과 임베딩 모델을 로컬 환경에서 간편하게 설치하고 실행할 수 있게 해주어 개발 및 배포 복잡도를 크게 낮춘다.
- **LangGraph**: 복잡한 LLM 에이전트나 체인을 상태 그래프 형태로 명확하게 구현할 수 있어, 코드의 가독성과 유지보수성을 높인다.
- **Tkinter**: Python 표준 라이브러리로 별도의 설치가 필요 없으며, 사내용 간단한 데스크톱 애플리케이션을 신속하게 개발하기에 적합하다.
